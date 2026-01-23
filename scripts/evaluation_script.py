import asyncio
import glob
import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
from dotenv import load_dotenv
from langchain_core.tracers.langchain import wait_for_all_tracers
from openai import AsyncOpenAI
from ragas import Dataset, experiment
from ragas.embeddings.base import embedding_factory
from ragas.llms import llm_factory
from ragas.metrics.collections import (
    AnswerCorrectness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    Faithfulness,
)

from app.configs.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_ENDPOINT,
    EMBEDDING_MODEL,
)

load_dotenv()

# -----------------------------
# Logging
# -----------------------------
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)

# -----------------------------
# File name parser (from generation_script output)
# e.g. ragas_eval_{model}_{dataset_key}_{retrieval_mode}_{exp}.json
# -----------------------------
FILENAME_RE = re.compile(
    r"^ragas_eval_(?P<model>.+?)_(?P<dataset>.+?)_(?P<retrieval>.+?)_(?P<exp>.+?)\.json$"
)


def _normalize_contexts(v: Any) -> List[str]:
    """
    Ensure contexts is always List[str] for RAGAS.
    Accepts:
      - List[str]
      - str
      - None
      - List[dict]/dict (will stringify)
    """
    if v is None:
        return ["沒有找到相關的上下文資訊"]

    if isinstance(v, str):
        vv = v.strip()
        return [vv] if vv else ["沒有找到相關的上下文資訊"]

    if isinstance(v, list):
        out: List[str] = []
        for item in v:
            if item is None:
                continue
            if isinstance(item, str):
                s = item.strip()
                if s:
                    out.append(s)
            else:
                # If contexts accidentally contains dicts/objects, stringify safely
                try:
                    out.append(json.dumps(item, ensure_ascii=False))
                except Exception:
                    out.append(str(item))
        return out or ["沒有找到相關的上下文資訊"]

    # fallback for dict/other types
    try:
        return [json.dumps(v, ensure_ascii=False)]
    except Exception:
        return [str(v)]


def _normalize_row(row: Dict[str, Any]) -> Dict[str, Any]:
    """
    Normalize one record into the schema expected by ragas:
      - question: str
      - contexts: List[str]
      - answer: str
      - ground_truth: str
    """
    q = str(row.get("question", "") or "").strip()
    a = str(row.get("answer", "") or "").strip()
    gt = str(row.get("ground_truth", "") or "").strip()
    ctx = _normalize_contexts(row.get("contexts"))

    # Keep your original fallback semantics
    if not a:
        a = "無法生成回答"
    if not q:
        q = "(missing question)"

    return {
        **row,
        "question": q,
        "answer": a,
        "ground_truth": gt,
        "contexts": ctx,
    }


def _read_generation_json(file_path: str) -> pd.DataFrame:
    """
    Read JSON produced by generation_script.save_json():
      - JSON array (indent=2)
    Also tries to be resilient if the file is JSONL.
    """
    # First attempt: JSON array
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif (
            isinstance(data, dict) and "data" in data and isinstance(data["data"], list)
        ):
            df = pd.DataFrame(data["data"])
        else:
            # fallback: wrap dict as single row
            df = pd.DataFrame([data])
        return df

    except json.JSONDecodeError:
        # Fallback: try JSONL
        rows: List[Dict[str, Any]] = []
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rows.append(json.loads(line))
        return pd.DataFrame(rows)


def _attach_metadata_from_filename(df: pd.DataFrame, file_name: str) -> pd.DataFrame:
    """
    Attach columns: model, dataset, retrieval_mode, exp
    based on generation_script naming convention.
    """
    m = FILENAME_RE.match(file_name)
    if not m:
        # If the file isn't following the pattern, keep empty metadata
        df["model"] = ""
        df["dataset"] = ""
        df["retrieval_mode"] = ""
        df["exp"] = ""
        return df

    df["model"] = m.group("model")
    df["dataset"] = m.group("dataset")
    df["retrieval_mode"] = m.group("retrieval")
    df["exp"] = m.group("exp")
    return df


def df_to_ragas_dataset(df: pd.DataFrame, batch_name: str = "batch") -> Dataset:
    dataset = Dataset(name=batch_name, backend="local/jsonl", root_dir=".")
    for _, row in df.iterrows():
        dataset.append({
            "question": row["question"],
            "contexts": row["contexts"],
            "answer": row["answer"],
            "ground_truth": row["ground_truth"],
        })
    return dataset


@experiment()
async def evaluate_rag(row: Dict[str, Any], llm, embeddings) -> Dict[str, Any]:
    question = row["question"]
    answer = row["answer"]
    contexts = row["contexts"]
    ground_truth = row["ground_truth"]

    # Initialize scorers per task (safe isolation; slower but robust)
    answer_relevancy_scorer = AnswerRelevancy(
        llm=llm, embeddings=embeddings, strictness=1
    )
    answer_correctness_scorer = AnswerCorrectness(llm=llm, embeddings=embeddings)
    contexts_precision_scorer = ContextPrecision(llm=llm)
    context_recall_scorer = ContextRecall(llm=llm)
    faithfulness_scorer = Faithfulness(llm=llm)

    faithfulness = await faithfulness_scorer.ascore(
        user_input=question, response=answer, retrieved_contexts=contexts
    )
    contexts_precision = await contexts_precision_scorer.ascore(
        user_input=question, reference=answer, retrieved_contexts=contexts
    )
    context_recall = await context_recall_scorer.ascore(
        user_input=question, reference=answer, retrieved_contexts=contexts
    )
    answer_relevancy = await answer_relevancy_scorer.ascore(
        user_input=question, response=answer
    )
    answer_correctness = await answer_correctness_scorer.ascore(
        user_input=question, response=answer, reference=ground_truth
    )

    return {
        **row,
        "faithfulness": faithfulness.value,
        "context_precision": contexts_precision.value,
        "context_recall": context_recall.value,
        "answer_relevancy": answer_relevancy.value,
        "answer_correctness": answer_correctness.value,
    }


async def process_single_file(
    file_path: str,
    llm_instance,
    embedding_instance,
    output_dir: str = "./data/ragas_result",
    batch_size: int = 10,
    sleep_seconds: int = 5,
) -> None:
    file_name = os.path.basename(file_path)
    logger.info(f"Starting evaluation for file: {file_name}")

    try:
        df = _read_generation_json(file_path)
    except Exception as e:
        logger.error(f"Failed to read {file_name}: {e}")
        return

    if df.empty:
        logger.warning(f"No records in {file_name}")
        return

    # attach metadata (model/dataset/retrieval/exp) for later aggregation
    df = _attach_metadata_from_filename(df, file_name)

    # normalize schema/types
    records = [_normalize_row(r) for r in df.to_dict(orient="records")]
    full_df = pd.DataFrame(records)

    total_records = len(full_df)
    logger.info(f"Total records to evaluate in {file_name}: {total_records}")

    all_batch_results: List[pd.DataFrame] = []

    for i in range(0, total_records, batch_size):
        batch_df = full_df.iloc[i : i + batch_size].copy()
        current_batch_num = (i // batch_size) + 1
        total_batches = (total_records + batch_size - 1) // batch_size

        logger.info(
            f"[{file_name}] Batch {current_batch_num}/{total_batches} "
            f"(Records {i} to {min(i + batch_size, total_records) - 1})"
        )

        batch_dataset = df_to_ragas_dataset(
            batch_df, batch_name=f"batch_{current_batch_num}"
        )

        try:
            clean_name = os.path.splitext(file_name)[0]
            batch_result_obj = await evaluate_rag.arun(
                batch_dataset,
                name=f"ragas_{clean_name}_b{current_batch_num}_{datetime.now().strftime('%H%M%S')}",
                llm=llm_instance,
                embeddings=embedding_instance,
            )

            all_batch_results.append(batch_result_obj.to_pandas())
            logger.info(f"[{file_name}] Batch {current_batch_num} completed.")

        except Exception as e:
            logger.error(f"[{file_name}] Error in batch {current_batch_num}: {e}")

        if i + batch_size < total_records:
            await asyncio.sleep(sleep_seconds)

    if not all_batch_results:
        logger.warning(f"No results generated for {file_name}")
        return

    final_results_df = pd.concat(all_batch_results, ignore_index=True)

    metrics = [
        "faithfulness",
        "context_precision",
        "context_recall",
        "answer_relevancy",
        "answer_correctness",
    ]
    print(f"\nSummary for {file_name}:")
    for metric in metrics:
        if metric in final_results_df.columns:
            print(f"  - {metric:<25}: {final_results_df[metric].mean():.4f}")

    os.makedirs(output_dir, exist_ok=True)
    base_name = os.path.splitext(file_name)[0]
    output_csv = os.path.join(output_dir, f"result_{base_name}.csv")
    final_results_df.to_csv(output_csv, index=False)
    logger.info(f"Saved results to {output_csv}")


async def run_all_experiments():
    # 1) LLM & Embeddings init once
    client = AsyncOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        base_url=f"{AZURE_OPENAI_ENDPOINT}/openai/v1/",
    )

    llm_instance = llm_factory(
        AZURE_OPENAI_DEPLOYMENT,
        client=client,
        temperature=1,
        top_p=1,
        max_tokens=8192,
    )

    # Keep your current embeddings choice; this is for RAGAS metrics needing embeddings
    embedding_instance = embedding_factory(
        provider="huggingface", model=EMBEDDING_MODEL
    )

    # 2) Find files produced by generation_script
    input_dir = "./data/eval_dataset"

    # Prefer your generation_script naming convention first
    json_files = sorted(glob.glob(os.path.join(input_dir, "ragas_eval_*.json")))

    # If none matched, fallback to all json in directory
    if not json_files:
        json_files = sorted(glob.glob(os.path.join(input_dir, "*.json")))

    if not json_files:
        logger.warning(f"No JSON files found in {input_dir}")
        return

    logger.info(f"Found {len(json_files)} files to evaluate.")
    logger.info("Files: %s", [os.path.basename(f) for f in json_files])

    for file_path in json_files:
        await process_single_file(file_path, llm_instance, embedding_instance)

    logger.info("All files processed.")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_experiments())
    finally:
        wait_for_all_tracers()
        print("LangSmith traces uploaded.")
