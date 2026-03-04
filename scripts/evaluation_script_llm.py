import asyncio
import json
import logging
import os
import re
import shutil
import time
from collections import defaultdict
from logging.handlers import RotatingFileHandler
from pathlib import Path

from dotenv import load_dotenv
from langchain_core.tracers.context import tracing_v2_enabled
from langsmith.run_helpers import trace
from langsmith.wrappers import wrap_openai
from openai import AsyncOpenAI

# from openai import AsyncAzureOpenAI
from ragas.embeddings.base import embedding_factory
from ragas.llms import llm_factory
from ragas.metrics.collections import (
    AnswerCorrectness,
    AnswerRelevancy,
    ContextPrecision,
    ContextRecall,
    Faithfulness,
)

# from app.configs.config import (
#     AZURE_OPENAI_API_KEY,
#     AZURE_OPENAI_API_VERSION,
#     AZURE_OPENAI_ENDPOINT,
# )
from app.configs.config import (
    OLLAMA_BASE_URL,
    OLLAMA_EMBED_NAME,
    OLLAMA_LLM_NAME,
)

MAX_CONCURRENT_REQUESTS = 5
DATASET_DIR = "data/eval_dataset"
DATASET_DONE_DIR = "data/eval_dataset_done"
RESULT_DIR = "data/eval_result"
MAX_CONTEXTS_PREVIEW = 3
MAX_TEXT_PREVIEW_CHARS = 1200

Path(DATASET_DONE_DIR).mkdir(parents=True, exist_ok=True)
log_file = Path(DATASET_DONE_DIR) / "ragas_eval.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        RotatingFileHandler(
            log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
        ),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)

load_dotenv()
# Enable langsmith
os.environ["LANGSMITH_TRACING"] = "true"


def _clip_text(s: str, max_chars: int = MAX_TEXT_PREVIEW_CHARS) -> str:
    s = (s or "").strip()
    if len(s) <= max_chars:
        return s
    return s[: max_chars - 3] + "..."


def _contexts_preview(contexts) -> dict:
    if not isinstance(contexts, list):
        return {"contexts_len": None, "contexts_preview": contexts}
    preview = contexts[:MAX_CONTEXTS_PREVIEW]
    preview = [_clip_text(str(x), 800) for x in preview]
    return {"contexts_len": len(contexts), "contexts_preview": preview}


def detect_dataset_language(dataset: list[dict]) -> str:
    """自動偵測資料集語言：抽樣前幾筆，若包含中文字元則判斷為繁體中文，否則為英文"""
    sample_text = ""
    for item in dataset[:5]:
        sample_text += item.get("question", "") + item.get("answer", "")

    if re.search(r"[\u4e00-\u9fff]", sample_text):
        return "traditional-chinese"
    return "english"


def load_eval_datasets(dataset_dir: str = DATASET_DIR) -> dict[str, list[dict]]:
    logger.info(f"開始載入評估資料集，目錄: {dataset_dir}")
    dataset_path = Path(dataset_dir)
    if not dataset_path.exists():
        logger.error(f"資料集目錄不存在: {dataset_dir}")
        raise FileNotFoundError(f"目錄不存在: {dataset_dir}")
    datasets = {}
    json_files = list(dataset_path.glob("*.json"))
    if not json_files:
        logger.warning(f"在 {dataset_dir} 目錄下沒有找到任何 JSON 檔案")
        return datasets
    logger.info(f"找到 {len(json_files)} 個 JSON 檔案")
    for json_file in json_files:
        try:
            file_name = json_file.stem
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                datasets[file_name] = data
            else:
                logger.warning(f"  - {json_file.name} 的內容不是列表格式，跳過")
        except Exception as e:
            logger.error(f"讀取檔案失敗: {json_file.name}, 錯誤: {str(e)}")
    return datasets


def print_datasets_info(datasets: dict[str, list[dict]]) -> None:
    logger.info("=" * 80)
    for file_name, data in datasets.items():
        logger.info(f"  {file_name}.json: {len(data)} 筆")
    logger.info("=" * 80)


def save_dataset_result(
    dataset_name: str,
    results: list[dict],
    averages: dict[str, float],
    output_dir: str = RESULT_DIR,
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / f"{dataset_name}_result.json"
    output_data = {
        "dataset_name": dataset_name,
        "summary": {"total_items": len(results), "average_scores": averages},
        "details": results,
    }
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        logger.info(f"評估明細已儲存至: {file_path}")
    except Exception as e:
        logger.error(f"儲存檔案失敗 {file_path}: {str(e)}")


def update_summary_report(
    dataset_name: str, averages: dict[str, float], output_dir: str = RESULT_DIR
) -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / "summary_report.json"
    current_data = {}
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        except Exception:
            pass
    current_data[dataset_name] = averages
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
        logger.info(f"總報表已更新: {file_path}")
    except Exception as e:
        logger.error(f"更新總表失敗: {str(e)}")


def move_dataset_to_done(dataset_name: str) -> None:
    source_path = Path(DATASET_DIR) / f"{dataset_name}.json"
    dest_path = Path(DATASET_DONE_DIR) / f"{dataset_name}.json"
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if source_path.exists():
        try:
            shutil.move(str(source_path), str(dest_path))
            logger.info(f"已將處理完畢的資料集移動至: {DATASET_DONE_DIR}")
        except Exception as e:
            logger.error(f"移動檔案失敗: {e}")


async def adapt_prompt_helper(
    metric_obj,
    prompt_attr_name: str,
    llm,
    language: str,
    parent_run=None,
):
    metric_name = type(metric_obj).__name__
    span_name = f"adapt_prompt:{metric_name}.{prompt_attr_name}"
    async with trace(
        name=span_name,
        run_type="tool",
        parent=parent_run,
        inputs={"language": language},
    ) as r:
        try:
            logger.info(
                f"正在為 {metric_name} 適配 {prompt_attr_name} 到 {language}..."
            )
            start_time = time.time()
            current_prompt = getattr(metric_obj, prompt_attr_name)
            adapted_prompt = await current_prompt.adapt(
                target_language=language, llm=llm, adapt_instruction=True
            )
            setattr(metric_obj, prompt_attr_name, adapted_prompt)
            elapsed = round(time.time() - start_time, 4)
            logger.info(f"完成 {metric_name} 適配 (耗時 {elapsed}s)")
            r.end(outputs={"status": "ok", "elapsed_sec": elapsed})
        except Exception as e:
            logger.warning(f"適配 Prompt 失敗 ({span_name})，將使用預設英文: {e}")
            r.end(outputs={"status": "failed", "error": str(e)})


async def get_or_build_metrics(
    language: str, client, metrics_cache: dict, parent_run=None
) -> dict:
    if language in metrics_cache:
        logger.info(f"從快取中取得 {language} 的 Metrics。")
        return metrics_cache[language]

    async with trace(
        name=f"build_metrics_{language}",
        run_type="chain",
        parent=parent_run,
        inputs={"llm_model": OLLAMA_LLM_NAME, "language": language},
    ) as run:
        logger.info(f"建立 Ragas Metric 物件 (目標語言: {language})...")

        llm_instance = llm_factory(
            model=OLLAMA_LLM_NAME,
            client=client,
            max_tokens=8192,
            temperature=0.0,
        )

        embedding_instance = embedding_factory(
            model=OLLAMA_EMBED_NAME,
            client=client,
        )

        answer_relevancy = AnswerRelevancy(
            llm=llm_instance, embeddings=embedding_instance, strictness=1
        )
        answer_correctness = AnswerCorrectness(
            llm=llm_instance, embeddings=embedding_instance
        )
        context_precision = ContextPrecision(llm=llm_instance)
        context_recall = ContextRecall(llm=llm_instance)
        faithfulness = Faithfulness(llm=llm_instance)

        metrics = {
            "answer_relevancy": answer_relevancy,
            "answer_correctness": answer_correctness,
            "faithfulness": faithfulness,
            "context_precision": context_precision,
            "context_recall": context_recall,
        }

        if language.lower() != "english":
            logger.info(f"語言非英文，開始並行適配 Prompt 到 {language}...")
            adapt_parent = run
            await asyncio.gather(
                adapt_prompt_helper(
                    answer_relevancy,
                    "prompt",
                    llm_instance,
                    language,
                    parent_run=adapt_parent,
                ),
                adapt_prompt_helper(
                    answer_correctness,
                    "correctness_classifier_prompt",
                    llm_instance,
                    language,
                    parent_run=adapt_parent,
                ),
                adapt_prompt_helper(
                    answer_correctness,
                    "statement_generator_prompt",
                    llm_instance,
                    language,
                    parent_run=adapt_parent,
                ),
                adapt_prompt_helper(
                    faithfulness,
                    "nli_statement_prompt",
                    llm_instance,
                    language,
                    parent_run=adapt_parent,
                ),
                adapt_prompt_helper(
                    faithfulness,
                    "statement_generator_prompt",
                    llm_instance,
                    language,
                    parent_run=adapt_parent,
                ),
                adapt_prompt_helper(
                    context_precision,
                    "prompt",
                    llm_instance,
                    language,
                    parent_run=adapt_parent,
                ),
                adapt_prompt_helper(
                    context_recall,
                    "prompt",
                    llm_instance,
                    language,
                    parent_run=adapt_parent,
                ),
            )
        else:
            logger.info("偵測為英文，使用 Ragas 預設 Prompt，無需適配。")

        metrics_cache[language] = metrics
        run.end(outputs={"status": "ok"})
        return metrics


async def _score_metric(metric_name: str, coro, parent_run) -> tuple[str, float]:
    async with trace(
        name=f"metric:{metric_name}", run_type="tool", parent=parent_run
    ) as mrun:
        try:
            result = await coro
            val = (
                result.value
                if hasattr(result, "value") and result.value is not None
                else 0.0
            )
            mrun.end(outputs={"score": float(val)})
            return metric_name, float(val)
        except Exception as e:
            logger.error(f"{metric_name} 評估失敗: {e}")
            mrun.end(outputs={"score": 0.0, "error": str(e)})
            return metric_name, 0.0


async def process_single_item(
    sem: asyncio.Semaphore, metrics: dict, item: dict, idx: int, total: int, parent_run
) -> dict:
    async with sem:
        start_time = time.time()
        question, contexts, answer, ground_truth = (
            item.get("question", ""),
            item.get("contexts", []),
            item.get("answer", ""),
            item.get("ground_truth", ""),
        )

        ctx_meta = _contexts_preview(contexts)
        async with trace(
            name=f"item:{idx}/{total}",
            run_type="chain",
            parent=parent_run,
            inputs={
                "index": idx,
                "question": _clip_text(question),
                "answer_preview": _clip_text(answer),
                "ground_truth_preview": _clip_text(ground_truth),
                **ctx_meta,
            },
        ) as item_run:
            logger.info(f"--- 處理項目 {idx}/{total} ---")

            pairs = await asyncio.gather(
                _score_metric(
                    "answer_relevancy",
                    metrics["answer_relevancy"].ascore(
                        user_input=question, response=answer
                    ),
                    item_run,
                ),
                _score_metric(
                    "answer_correctness",
                    metrics["answer_correctness"].ascore(
                        user_input=question, response=answer, reference=ground_truth
                    ),
                    item_run,
                ),
                _score_metric(
                    "context_precision",
                    metrics["context_precision"].ascore(
                        user_input=question,
                        reference=ground_truth,
                        retrieved_contexts=contexts,
                    ),
                    item_run,
                ),
                _score_metric(
                    "context_recall",
                    metrics["context_recall"].ascore(
                        user_input=question,
                        reference=ground_truth,
                        retrieved_contexts=contexts,
                    ),
                    item_run,
                ),
                _score_metric(
                    "faithfulness",
                    metrics["faithfulness"].ascore(
                        user_input=question,
                        response=answer,
                        retrieved_contexts=contexts,
                    ),
                    item_run,
                ),
                return_exceptions=False,
            )

            scores = dict(pairs)
            elapsed = time.time() - start_time
            score_str = ", ".join([f"{k}: {v:.4f}" for k, v in scores.items()])
            logger.info(
                f"完成項目 {idx}/{total} (耗時: {elapsed:.2f}s) | 分數: {score_str}"
            )

            item_run.end(outputs={"elapsed_sec": round(elapsed, 4), "scores": scores})
            return {
                "index": idx,
                "question": question,
                "contexts": contexts,
                "answer": answer,
                "ground_truth": ground_truth,
                "scores": scores,
            }


async def evaluate_datasets(
    datasets: dict[str, list[dict]], client, parent_run
) -> dict[str, dict]:
    logger.info("\n" + "=" * 80)
    logger.info(
        f"開始進行 RAG 評估 (Ollama 模式, Max Concurrency={MAX_CONCURRENT_REQUESTS})"
    )
    all_results = {}
    sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)
    metrics_cache = {}

    async with trace(
        name="evaluate_datasets",
        run_type="chain",
        parent=parent_run,
        inputs={"datasets": list(datasets.keys())},
    ) as eval_run:
        for dataset_name, dataset in datasets.items():
            dataset_start_time = time.time()

            lang = detect_dataset_language(dataset)
            logger.info(
                f"\n>>>> 評估資料集: {dataset_name} (共 {len(dataset)} 筆, 偵測語言: {lang})"
            )

            current_metrics = await get_or_build_metrics(
                lang, client, metrics_cache, parent_run=eval_run
            )

            async with trace(
                name=f"dataset:{dataset_name}",
                run_type="chain",
                parent=eval_run,
                inputs={
                    "dataset_name": dataset_name,
                    "count": len(dataset),
                    "language": lang,
                },
            ) as dataset_run:
                tasks = [
                    process_single_item(
                        sem,
                        current_metrics,
                        item,
                        idx,
                        len(dataset),
                        parent_run=dataset_run,
                    )
                    for idx, item in enumerate(dataset, 1)
                ]
                dataset_results = await asyncio.gather(*tasks)
                dataset_results.sort(key=lambda x: x["index"])

                avg_scores = defaultdict(float)
                valid_count = len(dataset_results)
                if valid_count > 0:
                    for res in dataset_results:
                        for key, val in res["scores"].items():
                            avg_scores[key] += val
                    for key in avg_scores:
                        avg_scores[key] = round(avg_scores[key] / valid_count, 4)

                save_dataset_result(dataset_name, dataset_results, dict(avg_scores))
                update_summary_report(dataset_name, dict(avg_scores))
                move_dataset_to_done(dataset_name)

                dataset_elapsed = time.time() - dataset_start_time
                all_results[dataset_name] = {
                    "total_items": valid_count,
                    "average_scores": dict(avg_scores),
                    "results": dataset_results,
                }
                logger.info(
                    f"完成資料集 {dataset_name} | 總耗時: {dataset_elapsed:.2f}s | 平均分: {json.dumps(dict(avg_scores), ensure_ascii=False)}"
                )
                dataset_run.end(
                    outputs={
                        "elapsed_sec": round(dataset_elapsed, 4),
                        "total_items": valid_count,
                        "average_scores": dict(avg_scores),
                    }
                )
        eval_run.end(outputs={"status": "ok"})
    return all_results


async def main() -> None:
    logger.info("=== Ragas 評估程式啟動 ===")
    Path(DATASET_DONE_DIR).mkdir(parents=True, exist_ok=True)
    Path(RESULT_DIR).mkdir(parents=True, exist_ok=True)

    with tracing_v2_enabled():
        async with trace(
            name="ragas_eval_run",
            run_type="chain",
            inputs={
                "dataset_dir": DATASET_DIR,
                "max_concurrency": MAX_CONCURRENT_REQUESTS,
            },
            tags=["ragas", "eval", "ollama_local"],
        ) as root_run:
            try:
                eval_datasets = load_eval_datasets()
                if not eval_datasets:
                    logger.info("沒有找到任何待評估的資料集，程式結束。")
                    root_run.end(outputs={"status": "no_datasets"})
                    return

                print_datasets_info(eval_datasets)

                logger.info(
                    f"初始化指向本機 Ollama ({OLLAMA_LLM_NAME}) 的 OpenAI Client..."
                )

                # For GPT
                # client = wrap_openai(
                #     AsyncAzureOpenAI(
                #         api_key=AZURE_OPENAI_API_KEY,
                #         api_version=AZURE_OPENAI_API_VERSION,
                #         azure_endpoint=AZURE_OPENAI_ENDPOINT,
                #     )
                # )

                client = wrap_openai(
                    AsyncOpenAI(
                        base_url=f"{OLLAMA_BASE_URL}/v1",
                        api_key="ollama",
                    )
                )

                evaluation_results = await evaluate_datasets(
                    eval_datasets, client, parent_run=root_run
                )

                logger.info("\n" + "=" * 120)
                logger.info("=== 本次評估作業完成，平均分數摘要 ===")
                logger.info("=" * 120)
                headers = [
                    "Dataset",
                    "Faithfulness",
                    "Answer Relevancy",
                    "Answer Correctness",
                    "Context Precision",
                    "Context Recall",
                ]
                row_format = "{:<20} | {:<12} | {:<18} | {:<20} | {:<19} | {:<16}"
                logger.info(row_format.format(*headers))
                logger.info("-" * 120)

                for name, data in evaluation_results.items():
                    avgs = data["average_scores"]
                    logger.info(
                        row_format.format(
                            name[:19],
                            f"{avgs.get('faithfulness', 0):.4f}",
                            f"{avgs.get('answer_relevancy', 0):.4f}",
                            f"{avgs.get('answer_correctness', 0):.4f}",
                            f"{avgs.get('context_precision', 0):.4f}",
                            f"{avgs.get('context_recall', 0):.4f}",
                        )
                    )

                logger.info("=" * 120)
                root_run.end(
                    outputs={
                        "status": "ok",
                        "datasets": list(evaluation_results.keys()),
                    }
                )
                logger.info("=== 程式執行完畢 ===")

            except Exception as e:
                logger.error(f"=== 程式執行失敗 ===: {str(e)}", exc_info=True)
                root_run.end(outputs={"status": "error", "error": str(e)})
                raise


if __name__ == "__main__":
    asyncio.run(main())
