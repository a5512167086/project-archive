import asyncio
import glob
import logging
import os
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
from dotenv import load_dotenv
from langchain_core.tracers.langchain import wait_for_all_tracers
from openai import AsyncAzureOpenAI
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
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_DEPLOYMENT,
    AZURE_OPENAI_ENDPOINT,
    EMBEDDING_MODEL,
)

load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")
logger = logging.getLogger(__name__)


def df_to_ragas_dataset(df: pd.DataFrame, batch_name: str = "batch") -> Dataset:
    """Helper to convert a pandas DataFrame chunk into a Ragas Dataset."""
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

    # Initialize scorers
    # Note: Initializing these inside the loop might be slightly inefficient but ensures isolation per task
    answer_relevancy_scorer = AnswerRelevancy(llm=llm, embeddings=embeddings)
    answer_correctness_scorer = AnswerCorrectness(llm=llm, embeddings=embeddings)
    contexts_precision_scorer = ContextPrecision(llm=llm)
    context_recall_scorer = ContextRecall(llm=llm)
    faithfulness_scorer = Faithfulness(llm=llm)

    # Calculate metrics
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

    # Return evaluation results
    result = {
        **row,
        "faithfulness": faithfulness.value,
        "context_precision": contexts_precision.value,
        "context_recall": context_recall.value,
        "answer_relevancy": answer_relevancy.value,
        "answer_correctness": answer_correctness.value,
    }

    return result


async def process_single_file(file_path: str, llm_instance, embedding_instance):
    """
    處理單一 JSON 檔案的評估邏輯
    """
    file_name = os.path.basename(file_path)
    logger.info(f"🚀 Starting evaluation for file: {file_name}")

    try:
        full_df = pd.read_json(file_path)
    except Exception as e:
        logger.error(f"Failed to read {file_name}: {e}")
        return

    total_records = len(full_df)
    logger.info(f"Total records to evaluate in {file_name}: {total_records}")

    # 設定批次參數
    BATCH_SIZE = 10
    SLEEP_SECONDS = 5

    all_batch_results: List[pd.DataFrame] = []

    # 批次迴圈
    for i in range(0, total_records, BATCH_SIZE):
        batch_df = full_df.iloc[i : i + BATCH_SIZE]
        current_batch_num = (i // BATCH_SIZE) + 1
        total_batches = (total_records + BATCH_SIZE - 1) // BATCH_SIZE

        logger.info(
            f"[{file_name}] Processing Batch {current_batch_num}/{total_batches} "
            f"(Records {i} to {min(i + BATCH_SIZE, total_records) - 1})..."
        )

        # 將此批次轉為 Ragas Dataset
        batch_dataset = df_to_ragas_dataset(
            batch_df, batch_name=f"batch_{current_batch_num}"
        )

        try:
            # 執行實驗
            # 使用檔名的一部分作為實驗名稱，避免重複
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
            logger.error(
                f"[{file_name}] Error processing batch {current_batch_num}: {e}"
            )

        # 如果不是該檔案的最後一批，則休息
        if i + BATCH_SIZE < total_records:
            logger.info(f"Sleeping for {SLEEP_SECONDS} seconds...")
            await asyncio.sleep(SLEEP_SECONDS)

    # 合併結果並存檔
    if not all_batch_results:
        logger.warning(f"No results generated for {file_name}")
        return

    final_results_df = pd.concat(all_batch_results, ignore_index=True)

    # 輸出統計
    metrics = [
        "faithfulness",
        "context_precision",
        "context_recall",
        "answer_relevancy",
        "answer_correctness",
    ]
    print(f"\n📊 Summary for {file_name}:")
    for metric in metrics:
        if metric in final_results_df.columns:
            print(f"  - {metric:<25}: {final_results_df[metric].mean():.4f}")

    # 建立輸出路徑
    output_dir = "./data/ragas_result"
    os.makedirs(output_dir, exist_ok=True)

    # 使用原始檔名作為輸出的基礎 (去除 .json)
    base_name = os.path.splitext(file_name)[0]
    output_csv = os.path.join(output_dir, f"result_{base_name}.csv")

    final_results_df.to_csv(output_csv, index=False)
    logger.info(f"✅ Saved results to {output_csv}\n" + "-" * 50)


async def run_all_experiments():
    # 1. 準備全域設定 (LLM & Embeddings)
    # 只需初始化一次，傳入處理函式重複使用
    client = AsyncAzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version=AZURE_OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
    )

    llm_instance = llm_factory(
        AZURE_OPENAI_DEPLOYMENT,
        client=client,
        temperature=1,
        top_p=1,
        max_tokens=8192,
    )
    embedding_instance = embedding_factory(
        provider="huggingface", model=EMBEDDING_MODEL
    )

    # 2. 獲取所有目標 JSON 檔案
    input_dir = "./data/eval_dataset"
    # 使用 glob 抓取所有 json 檔
    json_files = glob.glob(os.path.join(input_dir, "*.json"))

    if not json_files:
        logger.warning(f"No JSON files found in {input_dir}")
        return

    logger.info(
        f"Found {len(json_files)} files to evaluate: {[os.path.basename(f) for f in json_files]}"
    )
    print("=" * 50)

    # 3. 迴圈執行每個檔案
    for file_path in json_files:
        await process_single_file(file_path, llm_instance, embedding_instance)

    logger.info("🎉 All files processed successfully.")


if __name__ == "__main__":
    try:
        asyncio.run(run_all_experiments())
    finally:
        wait_for_all_tracers()
        print("LangSmith traces uploaded.")
