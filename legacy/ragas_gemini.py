import asyncio
import json
import os
import traceback
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from datasets import Dataset
from dotenv import load_dotenv
from langchain_core.tracers.context import tracing_v2_enabled
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from ragas import evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    AnswerCorrectness,
    FactualCorrectness,
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)
from ragas.metrics.base import Metric

from app.configs.config import (
    EMBEDDING_MODEL,
    GOOGLE_API_KEY,
    LLM_MAX_NEW_TOKENS,
    LLM_TEMPERATURE,
)

# --- 1. 組態設定 (Configuration) ---
load_dotenv()

BASE_DATA_DIR = "./data"
INPUT_DATA_DIR = os.path.join(BASE_DATA_DIR, "eval_dataset")
OUTPUT_DATA_DIR = os.path.join(BASE_DATA_DIR, "ragas_result")
CACHE_DIR = "./cache"
SUMMARY_FILENAME = "_ragas_evaluation_summary.csv"
SUMMARY_CSV_PATH = os.path.join(OUTPUT_DATA_DIR, SUMMARY_FILENAME)


# --- 2. 核心輔助函式 (Core Helper Functions) ---


def validate_evaluation_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    (此函式與您原本的邏輯相同，保持不變)
    """
    cleaned_data = []
    skipped_count = 0
    REQUIRED_COLS = {"question", "answer", "contexts", "ground_truth"}

    for i, item in enumerate(data):
        try:
            if not REQUIRED_COLS.issubset(item.keys()):
                print(
                    f"Skipping item #{i}: Missing one of required keys {REQUIRED_COLS}"
                )
                skipped_count += 1
                continue

            contexts = item.get("contexts", [])
            if isinstance(contexts, str):
                contexts = [contexts]

            valid_contexts = [
                ctx for ctx in contexts if isinstance(ctx, str) and ctx.strip()
            ]
            if not valid_contexts:
                print(f"Skipping item #{i}: No valid contexts found.")
                skipped_count += 1
                continue

            if (
                not item.get("question")
                or not item.get("answer")
                or not item.get("ground_truth")
            ):
                print(
                    f"Skipping item #{i}: question, answer, or ground_truth is empty."
                )
                skipped_count += 1
                continue

            item["contexts"] = valid_contexts
            cleaned_data.append(item)

        except Exception as e:
            print(f"Error processing item #{i}: {e}")
            skipped_count += 1
            continue

    print(
        f"Validation complete. Original items: {len(data)}, Valid items: {len(cleaned_data)}, Skipped: {skipped_count}"
    )
    return cleaned_data


async def adapt_prompt_for_metric(metric: Metric, language: str, llm):
    """
    (新函式) 抽象化：為單一 RAGAS 指標適配提示詞。
    (!! 這就是您用來關閉 translate_statements log 的地方 !!)
    """
    try:
        # 暫時關閉 LangSmith 追蹤，以避免記錄 'translate_statements'
        with tracing_v2_enabled(False):
            print(f"Adapting prompts for {metric.name}...")
            adapted_prompts = await metric.adapt_prompts(language=language, llm=llm)
            metric.set_prompts(**adapted_prompts)
    except Exception as e:
        print(f"⚠️ Warning: Failed to adapt prompts for {metric.name}: {e}")


async def setup_evaluation_models(
    language: str = "traditional-chinese",
) -> Tuple[
    Optional[ChatGoogleGenerativeAI], Optional[HuggingFaceEmbeddings], List[Metric]
]:
    print("Setting up evaluation models...")
    try:
        # --- MODIFIED: LLM Initialization ---
        # 1. (Embedding 模型保持不變)
        embedding_model = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"device": "cuda"},
            cache_folder=CACHE_DIR,
        )

        # 2. 檢查 Google API Key
        google_api_key = GOOGLE_API_KEY
        if not google_api_key:
            raise ValueError(
                "❌ GOOGLE_API_KEY environment variable not set. Please add it to your .env file."
            )

        # 3. 初始化 Gemini 2.5 Flash
        print("Initializing Judge LLM: Gemini 2.5 Flash...")
        gemini_llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=float(LLM_TEMPERATURE),
            max_output_tokens=int(LLM_MAX_NEW_TOKENS),
        )
        wrapped_llm = LangchainLLMWrapper(gemini_llm)
        # --- END MODIFIED ---

        # 在一處定義所有指標
        all_metrics = [
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
            AnswerCorrectness(),
            FactualCorrectness(),
        ]

        # 使用 asyncio.gather 平行處理所有提示詞適配，速度更快
        # (這裡會呼叫上面那個關閉 tracing 的 adapt_prompt_for_metric 函式)
        tasks = [
            adapt_prompt_for_metric(metric, language, wrapped_llm)
            for metric in all_metrics
        ]
        await asyncio.gather(*tasks)

        print("✅ Model and prompt setup complete.")
        return gemini_llm, embedding_model, all_metrics

    except Exception as e:
        print(f"❌ Error initializing models: {e}")
        traceback.print_exc()
        return None, None, []


def find_evaluation_files(directory: str) -> List[str]:
    """
    (新函式) 職責分離：在指定目錄中尋找所有待評估的 JSON 檔案。
    (此函式與您原本的邏輯相同，保持不變)
    """
    try:
        files = [
            f
            for f in os.listdir(directory)
            if f.startswith("ragas_eval_") and f.endswith(".json")
        ]
        if not files:
            print(
                f"⚠️ WARNING: No evaluation files found in '{directory}'. Please run the generation script first."
            )
        return files
    except FileNotFoundError:
        print(f"❌ ERROR: Input directory not found: '{directory}'")
        return []


def process_evaluation_file(
    filename: str,
    input_dir: str,
    output_dir: str,
    llm: ChatGoogleGenerativeAI,  # <-- MODIFIED: Type Hint
    embeddings: HuggingFaceEmbeddings,
    metrics: List[Metric],
) -> Optional[Dict[str, Any]]:
    """
    (新函式) 職責分離：處理單一評估檔案的完整流程（載入、驗證、評估、儲存詳細結果）。
    """
    print(f"\n{'=' * 80}")
    print(f"🔥 Starting Evaluation for: {filename}")
    print(f"{'=' * 80}")

    file_path = os.path.join(input_dir, filename)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)

        evaluation_data = validate_evaluation_data(raw_data)
        if not evaluation_data:
            print("No valid data after validation. Skipping file.")
            return None

        ragas_dataset = Dataset.from_list(evaluation_data)

        print(f"🚀 Evaluating dataset ({len(evaluation_data)} items)...")
        # Ragas evaluate 函式可以直接接受 LangChain LLM 物件
        result = evaluate(
            dataset=ragas_dataset,
            metrics=metrics,
            llm=llm,  # <-- 傳入 Gemini LLM
            embeddings=embeddings,
            raise_exceptions=False,  # 保持 robustness
        )

        df = result.to_pandas()

        # 儲存詳細結果
        output_csv_path = os.path.join(
            output_dir, f"ragas_results_{filename.replace('.json', '.csv')}"
        )
        df.to_csv(output_csv_path, index=False, encoding="utf-8-sig")
        print(f"✅ Detailed results saved to: {output_csv_path}")

        # 準備總結資料
        summary = {"dataset": filename.replace("ragas_eval_", "").replace(".json", "")}
        summary.update(df.mean(numeric_only=True).to_dict())
        return summary

    except Exception as e:
        print(f"❌ An error occurred while processing {filename}: {e}")
        traceback.print_exc()
        return None


def check_existing_summary(summary_path: str) -> bool:
    """
    (新函式) 職責分離：檢查並顯示已存在的總結報告。
    (此函式與您原本的邏輯相同，保持不變)
    """
    if not os.path.exists(summary_path):
        return False

    print(f"🎉 發現已存在的總結報告: {summary_path}")
    print("將直接顯示結果並跳過重新評估。")
    print(f"{'=' * 80}")
    try:
        summary_df = pd.read_csv(summary_path, index_col="dataset")
        print(summary_df.round(4))
        print(f"{'=' * 80}")
        print("✅ 已成功顯示總結報告。")
    except Exception as e:
        print(f"❌ 讀取總結報告失敗: {e}")
    return True


def save_summary_report(summaries: List[Dict[str, Any]], output_path: str):
    """
    (新函式) 職責分離：將所有評估結果匯總並儲存為最終的 CSV 總結報告。
    (此函式與您原本的邏輯相同，保持不變)
    """
    if not summaries:
        print("\nNo evaluations were successfully completed. No summary to save.")
        return

    print(f"\n{'=' * 80}")
    print("🎉 Final RAGAS Evaluation Summary")
    print(f"{'=' * 80}")

    try:
        summary_df = pd.DataFrame(summaries).set_index("dataset")
        print(summary_df.round(4))

        summary_df.to_csv(output_path, encoding="utf-8-sig")
        print(f"\n✅ Summary report saved to: {output_path}")
    except Exception as e:
        print(f"❌ Failed to save summary report: {e}")
    finally:
        print(f"{'=' * 80}")


# --- 3. 主執行流程 (Main Orchestration) ---


async def main():
    """
    (重構後) 主函式，作為高階流程的協調者。
    """
    # 確保輸出目錄存在
    os.makedirs(OUTPUT_DATA_DIR, exist_ok=True)

    # 1. 檢查快取
    if check_existing_summary(SUMMARY_CSV_PATH):
        return

    # 2. 初始化 (MODIFIED)
    gemini_llm, embedding_model, metrics = await setup_evaluation_models()
    if not gemini_llm or not embedding_model or not metrics:
        print("❌ Aborting due to model setup failure.")
        return

    # 3. 尋找檔案
    files_to_evaluate = find_evaluation_files(INPUT_DATA_DIR)
    if not files_to_evaluate:
        return

    # 4. 執行評估 (MODIFIED)
    all_results_summary = []
    for filename in files_to_evaluate:
        summary_data = process_evaluation_file(
            filename=filename,
            input_dir=INPUT_DATA_DIR,
            output_dir=OUTPUT_DATA_DIR,
            llm=gemini_llm,  # <-- 傳入 Gemini LLM
            embeddings=embedding_model,
            metrics=metrics,
        )
        if summary_data:
            all_results_summary.append(summary_data)

    # 5. 儲存總結
    save_summary_report(all_results_summary, SUMMARY_CSV_PATH)


if __name__ == "__main__":
    asyncio.run(main())
