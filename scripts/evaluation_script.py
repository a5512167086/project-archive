from __future__ import annotations

import asyncio
import json
import logging
import shutil  # 新增：用於移動檔案
import time
from collections import defaultdict
from pathlib import Path

from dotenv import load_dotenv

# from openai import AsyncOpenAI
from openai import AsyncAzureOpenAI
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

# -----------------------------------------------------------------------------
# 全域設定
# -----------------------------------------------------------------------------
MAX_CONCURRENT_REQUESTS = 5

# 設定目錄路徑
DATASET_DIR = "data/eval_dataset"
DATASET_DONE_DIR = "data/eval_dataset_done"
RESULT_DIR = "data/eval_result"

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

load_dotenv()


# -----------------------------------------------------------------------------
# 檔案與資料處理工具
# -----------------------------------------------------------------------------


def load_eval_datasets(dataset_dir: str = DATASET_DIR) -> dict[str, list[dict]]:
    """載入評估資料集目錄下的所有 JSON 檔案"""
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
            logger.info(f"讀取檔案: {json_file.name}")
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            if isinstance(data, list):
                datasets[file_name] = data
                logger.info(f"  - 從 {json_file.name} 載入 {len(data)} 筆資料")
            else:
                logger.warning(f"  - {json_file.name} 的內容不是列表格式，跳過")

        except Exception as e:
            logger.error(f"讀取檔案失敗: {json_file.name}, 錯誤: {str(e)}")

    total_items = sum(len(data) for data in datasets.values())
    logger.info(f"總共載入 {len(datasets)} 個資料集，包含 {total_items} 筆評估資料")
    return datasets


def print_datasets_info(datasets: dict[str, list[dict]]) -> None:
    """列印資料集資訊"""
    logger.info("=" * 80)
    logger.info("資料集內容總覽")
    logger.info("=" * 80)
    for file_name, data in datasets.items():
        logger.info(f"  {file_name}.json: {len(data)} 筆")
    logger.info(f"  總計: {sum(len(data) for data in datasets.values())} 筆")
    logger.info("=" * 80)


def save_dataset_result(
    dataset_name: str,
    results: list[dict],
    averages: dict[str, float],
    output_dir: str = RESULT_DIR,
) -> None:
    """儲存單一資料集的詳細評估結果"""
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
        logger.info(f"已儲存詳細評估結果至: {file_path}")
    except Exception as e:
        logger.error(f"儲存檔案失敗 {file_path}: {str(e)}")


def update_summary_report(
    dataset_name: str, averages: dict[str, float], output_dir: str = RESULT_DIR
) -> None:
    """
    [修改] 增量更新總表：讀取現有報告 -> 更新此資料集分數 -> 寫回
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    file_path = output_path / "summary_report.json"

    current_data = {}

    # 1. 如果檔案存在，先讀取舊資料
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                current_data = json.load(f)
        except Exception as e:
            logger.warning(f"讀取現有 summary_report 失敗，將建立新檔: {e}")

    # 2. 更新當前資料集的分數
    current_data[dataset_name] = averages

    # 3. 寫回檔案
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
        logger.info(f"已更新總表 summary_report.json (加入: {dataset_name})")
    except Exception as e:
        logger.error(f"更新總表失敗: {str(e)}")


def move_dataset_to_done(dataset_name: str) -> None:
    """
    [新增] 將處理完的原始檔案移動到 done 目錄
    """
    source_path = Path(DATASET_DIR) / f"{dataset_name}.json"
    dest_dir = Path(DATASET_DONE_DIR)
    dest_path = dest_dir / f"{dataset_name}.json"

    # 確保目標目錄存在
    dest_dir.mkdir(parents=True, exist_ok=True)

    if source_path.exists():
        try:
            # 使用 shutil.move 可以跨檔案系統移動，且若目標存在會覆蓋(視實作而定)或報錯
            # 這裡我們使用 rename (同磁碟) 或 shutil.move
            shutil.move(str(source_path), str(dest_path))
            logger.info(f"原始檔案已移動至: {dest_path}")
        except Exception as e:
            logger.error(f"移動檔案失敗 {source_path} -> {dest_path}: {e}")
    else:
        logger.warning(f"找不到原始檔案以進行移動: {source_path}")


# -----------------------------------------------------------------------------
# Ragas 指標與 Prompt 處理
# -----------------------------------------------------------------------------


async def adapt_prompt_helper(
    metric_obj, prompt_attr_name: str, llm, language: str = "traditional-chinese"
):
    """
    輔助函式：非同步執行單一 Prompt 的適配，並設定回物件屬性中
    """
    metric_name = type(metric_obj).__name__
    start_time = time.time()
    logger.info(f"開始適配 Prompt: {metric_name}.{prompt_attr_name} ...")

    try:
        # 取得目前的 prompt 物件
        current_prompt = getattr(metric_obj, prompt_attr_name)
        # 執行 adapt
        adapted_prompt = await current_prompt.adapt(
            target_language=language, llm=llm, adapt_instruction=True
        )
        # 將結果寫回物件
        setattr(metric_obj, prompt_attr_name, adapted_prompt)

        elapsed = time.time() - start_time
        logger.info(
            f"  -> 完成適配: {metric_name}.{prompt_attr_name} (耗時: {elapsed:.2f}s)"
        )

    except Exception as e:
        logger.error(f"適配失敗 {metric_name}.{prompt_attr_name}: {e}")
        # 失敗時不拋出錯誤，讓程式繼續使用預設 Prompt


async def build_metrics_and_adapt_prompts():
    logger.info("初始化 Azure OpenAI 與 Ragas 指標...")

    try:
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

        # 建立指標物件
        logger.info("建立 Ragas Metric 物件...")
        answer_relevancy = AnswerRelevancy(
            llm=llm_instance, embeddings=embedding_instance, strictness=1
        )
        answer_correctness = AnswerCorrectness(
            llm=llm_instance, embeddings=embedding_instance
        )
        context_precision = ContextPrecision(llm=llm_instance)
        context_recall = ContextRecall(llm=llm_instance)
        faithfulness = Faithfulness(llm=llm_instance)

        logger.info("開始並行適配 Prompt 到繁體中文...")

        # 定義所有需要適配的任務
        adapt_tasks = [
            # AnswerRelevancy
            adapt_prompt_helper(answer_relevancy, "prompt", llm_instance),
            # AnswerCorrectness (有兩個 prompt)
            adapt_prompt_helper(
                answer_correctness, "correctness_classifier_prompt", llm_instance
            ),
            adapt_prompt_helper(
                answer_correctness, "statement_generator_prompt", llm_instance
            ),
            # Faithfulness (有兩個 prompt)
            adapt_prompt_helper(faithfulness, "nli_statement_prompt", llm_instance),
            adapt_prompt_helper(
                faithfulness, "statement_generator_prompt", llm_instance
            ),
            # ContextPrecision
            adapt_prompt_helper(context_precision, "prompt", llm_instance),
            # ContextRecall
            adapt_prompt_helper(context_recall, "prompt", llm_instance),
        ]

        # 並發執行所有適配任務
        await asyncio.gather(*adapt_tasks)

        logger.info("所有評估指標與 Prompt 適配完成")

        return {
            "metrics": {
                "answer_relevancy": answer_relevancy,
                "answer_correctness": answer_correctness,
                "faithfulness": faithfulness,
                "context_precision": context_precision,
                "context_recall": context_recall,
            },
        }

    except Exception as e:
        logger.error(f"建立指標時發生錯誤: {str(e)}", exc_info=True)
        raise


# -----------------------------------------------------------------------------
# 評估邏輯
# -----------------------------------------------------------------------------


async def process_single_item(
    sem: asyncio.Semaphore, metrics: dict, item: dict, idx: int, total: int
) -> dict:
    """
    處理單一筆資料，包含並發計算 5 個指標
    """
    async with sem:  # 限制同時處理的「題目」數量
        start_time = time.time()
        logger.info(f"開始評估項目: {idx}/{total}")

        question = item.get("question", "")
        contexts = item.get("contexts", [])
        answer = item.get("answer", "")
        ground_truth = item.get("ground_truth", "")

        # DEBUG: 檢查資料完整性
        if not question:
            logger.warning(f"  [Item {idx}] 警告: 'question' 為空")
        if not contexts:
            logger.warning(
                f"  [Item {idx}] 警告: 'contexts' 為空，這將導致 Context 相關指標為 0"
            )
        if not ground_truth:
            logger.warning(f"  [Item {idx}] 警告: 'ground_truth' 為空")

        # 定義 5 個指標的計算任務 (這 5 個會同時跑)
        metric_tasks = {
            "answer_relevancy": metrics["answer_relevancy"].ascore(
                user_input=question, response=answer
            ),
            "answer_correctness": metrics["answer_correctness"].ascore(
                user_input=question, response=answer, reference=ground_truth
            ),
            "context_precision": metrics["context_precision"].ascore(
                user_input=question, reference=ground_truth, retrieved_contexts=contexts
            ),
            "context_recall": metrics["context_recall"].ascore(
                user_input=question, reference=ground_truth, retrieved_contexts=contexts
            ),
            "faithfulness": metrics["faithfulness"].ascore(
                user_input=question, response=answer, retrieved_contexts=contexts
            ),
        }

        # 並發等待結果
        results = await asyncio.gather(*metric_tasks.values(), return_exceptions=True)

        scores = {}
        keys = list(metric_tasks.keys())

        for i, result in enumerate(results):
            metric_name = keys[i]
            if isinstance(result, Exception):
                logger.error(f"  [Item {idx}] {metric_name} 計算錯誤: {result}")
                scores[metric_name] = 0.0
            else:
                # 處理可能的 None
                val = (
                    result.value
                    if hasattr(result, "value") and result.value is not None
                    else 0.0
                )
                scores[metric_name] = val

                if val == 0.0 and metric_name != "answer_relevancy":
                    logger.debug(f"  [Item {idx}] {metric_name} 分數為 0.0")

        elapsed = time.time() - start_time

        # ---------------------------------------------------------------------
        # 即時印出該題分數
        # ---------------------------------------------------------------------
        score_str = ", ".join([f"{k}: {v:.4f}" for k, v in scores.items()])
        logger.info(
            f"完成評估項目: {idx}/{total} (耗時: {elapsed:.2f}s) | 分數: {score_str}"
        )

        return {
            "index": idx,
            "question": question,
            "contexts": contexts,
            "answer": answer,
            "ground_truth": ground_truth,
            "scores": scores,
        }


async def evaluate_datasets(
    datasets: dict[str, list[dict]], metrics: dict
) -> dict[str, dict]:
    logger.info("\n" + "=" * 80)
    logger.info(
        f"開始進行 RAG 評估 (Async Mode, Max Concurrency={MAX_CONCURRENT_REQUESTS})"
    )
    logger.info("=" * 80)

    all_results = {}

    # 建立信號量控制全域並發
    sem = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    for dataset_name, dataset in datasets.items():
        dataset_start_time = time.time()
        logger.info(f"\n{'#' * 80}")
        logger.info(f"評估資料集: {dataset_name} (共 {len(dataset)} 筆)")
        logger.info(f"{'#' * 80}")

        # 建立該資料集的所有任務
        tasks = [
            process_single_item(sem, metrics, item, idx, len(dataset))
            for idx, item in enumerate(dataset, 1)
        ]

        # 等待所有任務完成
        dataset_results = await asyncio.gather(*tasks)

        # 排序確保順序正確
        dataset_results.sort(key=lambda x: x["index"])

        # 計算平均分
        avg_scores = defaultdict(float)
        valid_count = len(dataset_results)

        if valid_count > 0:
            for res in dataset_results:
                for key, val in res["scores"].items():
                    avg_scores[key] += val

            for key in avg_scores:
                avg_scores[key] = round(avg_scores[key] / valid_count, 4)

        # 1. 存檔 (詳細結果)
        save_dataset_result(dataset_name, dataset_results, dict(avg_scores))

        # 2. 增量更新總表 (Summary Report)
        update_summary_report(dataset_name, dict(avg_scores))

        # 3. 移動原始檔案到 Done 資料夾
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

    logger.info("\n" + "=" * 80)
    logger.info("所有資料集評估完成")
    logger.info("=" * 80)

    return all_results


# -----------------------------------------------------------------------------
# 主程式
# -----------------------------------------------------------------------------


async def main() -> None:
    logger.info("=== 程式開始執行 ===")
    total_start_time = time.time()

    # 確保輸出目錄存在
    Path(DATASET_DONE_DIR).mkdir(parents=True, exist_ok=True)
    Path(RESULT_DIR).mkdir(parents=True, exist_ok=True)

    try:
        # 1. 載入資料 (只會載入還沒被移走的)
        eval_datasets = load_eval_datasets()

        if not eval_datasets:
            logger.info("沒有找到任何待評估的資料集，程式結束。")
            return

        print_datasets_info(eval_datasets)

        # 2. 建立指標並並行適配 Prompt
        result = await build_metrics_and_adapt_prompts()

        # 3. 並行評估
        # 這裡面已經包含了: 存詳細結果、更新 Summary、移動檔案
        evaluation_results = await evaluate_datasets(eval_datasets, result["metrics"])

        # 4. 終端機顯示報表 (顯示本次執行的結果)
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
        logger.info(f"結果已儲存於 {RESULT_DIR}，原始檔已移動至 {DATASET_DONE_DIR}")

        total_elapsed = time.time() - total_start_time
        logger.info(f"=== 程式執行成功 (總執行時間: {total_elapsed:.2f}s) ===")

    except Exception as e:
        logger.error(f"=== 程式執行失敗 ===: {str(e)}", exc_info=True)
        raise


if __name__ == "__main__":
    asyncio.run(main())
