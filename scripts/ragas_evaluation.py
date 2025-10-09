import asyncio
import json
import os

import pandas as pd
from datasets import Dataset
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import AzureChatOpenAI
from ragas import evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import (
    answer_correctness,
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

load_dotenv()


def validate_evaluation_data(data):
    """
    Validates and cleans the evaluation data, ensuring correct column names and formats.
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


async def main():
    # --- 新增的程式碼 START ---
    data_dir = "./data/ragas_result"
    summary_filename = "_ragas_evaluation_summary.csv"
    summary_csv_path = os.path.join(data_dir, summary_filename)

    if os.path.exists(summary_csv_path):
        print(f"🎉 發現已存在的總結報告: {summary_csv_path}")
        print("將直接顯示結果並跳過重新評估。")
        print(f"{'=' * 80}")
        try:
            summary_df = pd.read_csv(summary_csv_path, index_col="dataset")
            print(summary_df.round(4))
            print(f"{'=' * 80}")
            print("✅ 已成功顯示總結報告。")
        except Exception as e:
            print(f"❌ 讀取總結報告失敗: {e}")
        return  # 直接結束函式
    # --- 新增的程式碼 END ---

    print("Setting up evaluation models...")
    try:
        embedding_model = HuggingFaceEmbeddings(
            model_name=os.getenv("EMBEDDING_MODEL"),
            model_kwargs={"device": "cuda"},
            cache_folder="./cache",
        )

        azure_llm_for_eval = AzureChatOpenAI(
            azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "IT108_gpt35"),
            openai_api_version=os.getenv(
                "AZURE_OPENAI_API_VERSION", "2023-07-01-preview"
            ),
            temperature=0.1,
            max_tokens=4096,
            request_timeout=120,
        )
        adapted_prompts_llm = LangchainLLMWrapper(azure_llm_for_eval)
        adapted_prompts = await answer_relevancy.adapt_prompts(
            language="chinese", llm=adapted_prompts_llm
        )
        print(adapted_prompts)
        answer_relevancy.set_prompts(**adapted_prompts)
    except Exception as e:
        print(f"Error initializing models: {e}")
        return

    # `data_dir` 已在前面定義，此處無需重複
    files_to_evaluate = [
        f
        for f in os.listdir(data_dir)
        if f.startswith("ragas_eval_") and f.endswith(".json")
    ]

    if not files_to_evaluate:
        print(
            f"ERROR: No evaluation files found in '{data_dir}'. Please run the generation script first."
        )
        return

    all_results_summary = []

    for filename in files_to_evaluate:
        print(f"\n{'=' * 80}")
        print(f"🔥 Starting Evaluation for: {filename}")
        print(f"{'=' * 80}")

        file_path = os.path.join(data_dir, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_data = json.load(f)

            evaluation_data = validate_evaluation_data(raw_data)
            if not evaluation_data:
                print("No valid data after validation. Skipping file.")
                continue

            ragas_dataset = Dataset.from_list(evaluation_data)

            metrics = [
                faithfulness,
                answer_relevancy,
                context_precision,
                context_recall,
                answer_correctness,
            ]

            print(f"🚀 Evaluating entire dataset ({len(evaluation_data)} items)...")

            result = evaluate(
                dataset=ragas_dataset,
                metrics=metrics,
                llm=azure_llm_for_eval,
                embeddings=embedding_model,
                raise_exceptions=False,
            )

            df = result.to_pandas()

            output_csv_path = os.path.join(
                data_dir, f"ragas_results_{filename.replace('.json', '.csv')}"
            )
            df.to_csv(output_csv_path, index=False, encoding="utf-8-sig")
            print(f"Detailed results saved to: {output_csv_path}")

            summary = {
                "dataset": filename.replace("ragas_eval_", "").replace(".json", "")
            }
            summary.update(df.mean(numeric_only=True).to_dict())
            all_results_summary.append(summary)

        except Exception as e:
            print(f"❌ An error occurred while processing {filename}: {e}")
            import traceback

            traceback.print_exc()

    if not all_results_summary:
        print("\nNo evaluations were successfully completed.")
        return

    print(f"\n{'=' * 80}")
    print("🎉 Final RAGAS Evaluation Summary")
    print(f"{'=' * 80}")

    summary_df = pd.DataFrame(all_results_summary).set_index("dataset")
    print(summary_df.round(4))

    # `summary_csv_path` 已在前面定義，此處無需重複
    summary_df.to_csv(summary_csv_path, encoding="utf-8-sig")
    print(f"\n✅ Summary report saved to: {summary_csv_path}")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    asyncio.run(main())
