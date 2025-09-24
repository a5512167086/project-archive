import json
import os
from typing import Any, Dict, List
from uuid import UUID

import pandas as pd
import torch
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings

from app.services.llm_service import LLMFactory  # 假設 LLMFactory 在此路徑
from app.services.vector_service import VectorService

load_dotenv()
TEST_BOT_UUID = "fbc137c9-85f7-411b-81c5-d221cc943399"
FAQ_DATASET_PATH = "./data/faq_dataset.csv"

# 用於記錄詳細資料的全域變數
detailed_logs = []


def load_test_data() -> List[Dict[str, str]]:
    """載入測試資料"""
    try:
        df = pd.read_csv(FAQ_DATASET_PATH)
        test_data = []

        for idx, row in df.iterrows():
            question = str(row["question"]).strip()
            answer = str(row["answer"]).strip()

            # 跳過空值
            if not question or not answer or question == "nan" or answer == "nan":
                print(f"跳過第 {idx} 行：包含空值")
                continue

            test_data.append({
                "question": question,
                "ground_truth": answer,
            })

        print(f"成功載入 {len(test_data)} 筆有效測試資料")
        return test_data

    except FileNotFoundError:
        print(f"錯誤：找不到檔案 {FAQ_DATASET_PATH}")
        return []
    except Exception as e:
        print(f"載入資料時發生錯誤：{e}")
        return []


def validate_retrieved_contexts(contexts: List[str]) -> List[str]:
    """驗證和清理檢索到的上下文"""
    valid_contexts = []

    for ctx in contexts:
        if ctx and isinstance(ctx, str) and ctx.strip():
            # 清理上下文文字
            cleaned_ctx = ctx.strip()
            if len(cleaned_ctx) > 0:
                valid_contexts.append(cleaned_ctx)

    # 如果沒有有效的上下文，提供一個預設值
    if not valid_contexts:
        valid_contexts = ["沒有找到相關的上下文資訊"]

    return valid_contexts


def print_detailed_info(
    idx: int, question: str, contexts: List[str], answer: str, ground_truth: str
):
    """詳細印出每次的問題、上下文和回答"""
    print(f"\n{'=' * 80}")
    print(f"第 {idx + 1} 筆資料")
    print(f"{'=' * 80}")

    print(f"📝 問題: {question}")
    print(f"\n📚 檢索到的上下文 ({len(contexts)} 個):")
    for i, ctx in enumerate(contexts, 1):
        print(f"  Context {i}: {ctx[:200]}{'...' if len(ctx) > 200 else ''}")

    print(f"\n🤖 生成的回答: {answer}")
    print(f"\n✅ 標準答案: {ground_truth}")


def generate_evaluation_data(test_data: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    """生成評估資料"""
    global detailed_logs

    if not test_data:
        print("錯誤：沒有測試資料")
        return []

    print("Loading models directly in the script...")

    # 載入嵌入模型
    try:
        model_name = os.getenv("EMBEDDING_MODEL")
        device = "cuda" if torch.cuda.is_available() else "cpu"
        embedding_model = HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={"device": device},
            cache_folder="../cache",
        )
        print(f"Embedding model '{model_name}' loaded on {device}.")
    except Exception as e:
        print(f"載入嵌入模型時發生錯誤：{e}")
        return []

    # 載入 LLM 服務
    try:
        llm_factory = LLMFactory()
        llm_service = llm_factory.get_service("ollama_local")
        print("LLM service for 'ollama_local' initialized.")
    except Exception as e:
        print(f"初始化 LLM 服務時發生錯誤：{e}")
        return []

    # 初始化向量服務
    try:
        vector_service = VectorService(model=embedding_model)
        bot_uuid = UUID(TEST_BOT_UUID)
    except Exception as e:
        print(f"初始化向量服務時發生錯誤：{e}")
        return []

    evaluation_results = []
    failed_count = 0

    print(f"\n開始處理 {len(test_data)} 筆資料...")

    for idx, item in enumerate(test_data):
        question = item["question"]
        ground_truth = item["ground_truth"]

        print(f"\n⏳ 處理第 {idx + 1}/{len(test_data)} 個問題...")

        try:
            # a. 檢索 (Retrieval)
            print("🔍 檢索相關文件...")
            retrieved_docs = vector_service.search_faq(
                bot_uuid=bot_uuid, query_text=question, top_k=3, score_threshold=0.3
            )
            # 提取並驗證上下文
            raw_contexts = [doc.get("answer", "") for doc in retrieved_docs if doc]
            contexts = validate_retrieved_contexts(raw_contexts)

            print(f"   找到 {len(contexts)} 個相關上下文")

            # b. 生成 (Generation)
            try:
                print("🤖 生成回答...")
                context_dicts_for_llm = [{"answer": c} for c in contexts]
                final_answer = llm_service.generate(question, context_dicts_for_llm)

                # 確保答案不為空
                if not final_answer or not isinstance(final_answer, str):
                    final_answer = "無法生成回答"
                    print("   ⚠️  生成空回答，使用預設回答")
                else:
                    print("   ✅ 成功生成回答")

            except Exception as e:
                print(f"   ❌ 生成回答時發生錯誤：{e}")
                final_answer = "生成回答時發生錯誤"

            # 詳細顯示這次的結果
            print_detailed_info(idx, question, contexts, final_answer, ground_truth)

            # 記錄詳細資料
            detailed_log = {
                "index": idx + 1,
                "question": question,
                "retrieved_contexts": contexts.copy(),
                "generated_answer": final_answer,
                "ground_truth": ground_truth,
                "context_count": len(contexts),
                "answer_length": len(final_answer),
                "ground_truth_length": len(ground_truth),
            }
            detailed_logs.append(detailed_log)

            # c. 收集結果 (使用 RAGAS 期望的欄位名稱)
            result_item = {
                "user_input": question,  # RAGAS 期望的使用者輸入欄位
                "retrieved_contexts": contexts,  # 必須是字串列表
                "response": final_answer.strip(),  # RAGAS 期望的回應欄位
                "ground_truth": ground_truth,  # 用於 answer_correctness 評估
            }

            # 最終驗證
            if (
                result_item["user_input"]
                and result_item["retrieved_contexts"]
                and result_item["response"]
                and result_item["ground_truth"]
            ):
                evaluation_results.append(result_item)
                print("✅ 成功處理並加入評估資料集")
            else:
                print("❌ 跳過：資料不完整")
                failed_count += 1

        except Exception as e:
            print(f"❌ 處理問題時發生錯誤：{e}")
            failed_count += 1
            continue

    print(f"\n{'=' * 80}")
    print(f"處理完成：成功 {len(evaluation_results)} 筆，失敗 {failed_count} 筆")
    print(f"{'=' * 80}")

    return evaluation_results


def save_evaluation_data(
    results: List[Dict[str, Any]], filename: str = "ragas_eval_data.json"
):
    """儲存評估資料並進行最終驗證"""
    if not results:
        print("錯誤：沒有結果可以儲存")
        return False

    # 最終驗證每筆資料
    valid_results = []
    for i, result in enumerate(results):
        try:
            # 檢查必要欄位
            required_fields = [
                "user_input",
                "retrieved_contexts",
                "response",
                "ground_truth",
            ]
            if all(field in result and result[field] for field in required_fields):
                # 確保 retrieved_contexts 是列表
                if isinstance(result["retrieved_contexts"], str):
                    result["retrieved_contexts"] = [result["retrieved_contexts"]]
                elif not isinstance(result["retrieved_contexts"], list):
                    print(f"跳過結果 {i}：retrieved_contexts 格式錯誤")
                    continue

                valid_results.append(result)
            else:
                print(f"跳過結果 {i}：缺少必要欄位")
        except Exception as e:
            print(f"驗證結果 {i} 時發生錯誤：{e}")

    if not valid_results:
        print("錯誤：沒有有效的結果可以儲存")
        return False

    try:
        # 儲存 RAGAS 評估資料
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(valid_results, f, ensure_ascii=False, indent=2)

        print(f"\n✅ 評估資料已儲存到 {filename}")
        print(f"   總共 {len(valid_results)} 筆有效資料")

        # 顯示統計資訊
        print("\n📊 統計資訊:")
        if detailed_logs:
            avg_context_count = sum(
                log["context_count"] for log in detailed_logs
            ) / len(detailed_logs)
            avg_answer_length = sum(
                log["answer_length"] for log in detailed_logs
            ) / len(detailed_logs)
            avg_ground_truth_length = sum(
                log["ground_truth_length"] for log in detailed_logs
            ) / len(detailed_logs)

            print(f"   平均上下文數量: {avg_context_count:.1f}")
            print(f"   平均生成回答長度: {avg_answer_length:.1f} 字元")
            print(f"   平均標準答案長度: {avg_ground_truth_length:.1f} 字元")

        # 顯示第一筆資料的結構作為參考
        if valid_results:
            print("\n📋 第一筆資料結構：")
            first_item = valid_results[0]
            for key, value in first_item.items():
                if key == "retrieved_contexts":
                    print(f"   {key}: {len(value)} 個上下文")
                    for i, ctx in enumerate(value, 1):
                        preview = ctx[:50] + "..." if len(ctx) > 50 else ctx
                        print(f"      Context {i}: {preview}")
                else:
                    preview = (
                        str(value)[:100] + "..."
                        if len(str(value)) > 100
                        else str(value)
                    )
                    print(f"   {key}: {preview}")

        return True

    except Exception as e:
        print(f"儲存檔案時發生錯誤：{e}")
        return False


def print_summary():
    """印出處理摘要"""
    if not detailed_logs:
        return

    print(f"\n{'=' * 80}")
    print("處理摘要")
    print(f"{'=' * 80}")

    successful_items = [
        log
        for log in detailed_logs
        if log["generated_answer"] not in ["無法生成回答", "生成回答時發生錯誤"]
    ]
    failed_items = [
        log
        for log in detailed_logs
        if log["generated_answer"] in ["無法生成回答", "生成回答時發生錯誤"]
    ]

    print(f"📈 總處理數量: {len(detailed_logs)}")
    print(f"✅ 成功生成: {len(successful_items)}")
    print(f"❌ 失敗數量: {len(failed_items)}")
    print(f"📊 成功率: {len(successful_items) / len(detailed_logs) * 100:.1f}%")

    if failed_items:
        print("\n❌ 失敗的問題:")
        for item in failed_items:
            print(f"   第 {item['index']} 個: {item['question'][:50]}...")


def main():
    """主函數"""
    print("🚀 開始生成 RAGAS 評估資料集")
    print("=" * 80)

    # 1. 載入測試資料
    test_data = load_test_data()
    if not test_data:
        print("❌ 無法載入測試資料，程式結束")
        return

    # 2. 生成評估資料
    results = generate_evaluation_data(test_data)
    if not results:
        print("❌ 無法生成評估資料，程式結束")
        return

    # 3. 顯示處理摘要
    print_summary()

    # 4. 儲存結果
    if save_evaluation_data(results):
        print("\n🎉 資料集生成完成")
        print("📁 檔案已生成:")
        print("   - ragas_eval_data.json (RAGAS 評估用)")
        print("   - detailed_rag_logs.json (詳細記錄)")
        print("   - detailed_rag_logs.csv (CSV 格式)")
        print("\n▶️  接下來可以執行 RAGAS 評估")
    else:
        print("❌ 儲存資料時發生錯誤")


if __name__ == "__main__":
    main()
