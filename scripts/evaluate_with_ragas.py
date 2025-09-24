import json
import os

from datasets import Dataset
from dotenv import load_dotenv
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_openai import AzureChatOpenAI
from ragas import evaluate
from ragas.metrics import (
    answer_correctness,
    answer_relevancy,
    context_precision,
    context_recall,
    faithfulness,
)

load_dotenv()


def validate_evaluation_data(data):
    """驗證和清理評估資料"""
    cleaned_data = []
    skipped_count = 0

    for i, item in enumerate(data):
        try:
            # 檢查必要欄位
            if not item.get("user_input") or not item.get("response"):
                print(f"跳過項目 {i}: 缺少 user_input 或 response")
                skipped_count += 1
                continue

            # 確保 retrieved_contexts 是非空列表
            contexts = item.get("retrieved_contexts", [])

            # 如果是字符串，轉換為列表
            if isinstance(contexts, str):
                contexts = [contexts]
            elif not isinstance(contexts, list):
                print(f"跳過項目 {i}: retrieved_contexts 不是列表格式")
                skipped_count += 1
                continue

            # 過濾空字符串和 None 值
            contexts = [
                ctx for ctx in contexts if ctx and isinstance(ctx, str) and ctx.strip()
            ]

            if len(contexts) == 0:
                print(f"跳過項目 {i}: 沒有有效的 contexts")
                skipped_count += 1
                continue

            # 確保 ground_truth 存在（用於 answer_correctness）
            if "ground_truth" not in item or not item["ground_truth"]:
                item["ground_truth"] = item["response"]

            item["retrieved_contexts"] = contexts
            cleaned_data.append(item)

        except Exception as e:
            print(f"處理項目 {i} 時發生錯誤: {e}")
            skipped_count += 1
            continue

    print(
        f"原始資料: {len(data)} 項，有效資料: {len(cleaned_data)} 項，跳過: {skipped_count} 項"
    )
    return cleaned_data


# 設定模型
embedding_model = HuggingFaceEmbeddings(
    model_name="Qwen/Qwen3-Embedding-4B",
    model_kwargs={"device": "cuda"},
    cache_folder="../cache",
)

azure_llm_for_eval = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT", "IT108_gpt35"),
    openai_api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2023-07-01-preview"),
    temperature=0.3,  # 稍微提高
    max_tokens=2048,  # 增加 token 限制
    request_timeout=60,  # 增加超時時間
)

# --- 1. 載入並驗證資料 ---
print("載入評估資料...")
try:
    with open("./data/ragas_eval_data.json", "r", encoding="utf-8") as f:
        raw_data = json.load(f)
        print(f"載入 {len(raw_data)} 筆資料")
    # 驗證和清理資料
    evaluation_data = validate_evaluation_data(raw_data)

    if len(evaluation_data) == 0:
        print("錯誤: 沒有有效的評估資料")
        exit(1)

except FileNotFoundError:
    print("錯誤: 找不到 ragas_eval_data.json 檔案")
    exit(1)
except json.JSONDecodeError:
    print("錯誤: JSON 檔案格式錯誤")
    exit(1)

# --- 2. 轉換為 Hugging Face Dataset 格式 ---
try:
    ragas_dataset = Dataset.from_list(evaluation_data)
    print(f"建立資料集成功，共 {len(ragas_dataset)} 筆資料")

    # 顯示資料集架構
    print("資料集欄位:", ragas_dataset.column_names)

except Exception as e:
    print(f"建立資料集時發生錯誤: {e}")
    exit(1)

# --- 3. 執行 RAGAS 評估 ---
print("開始 RAGAS 評估...")
try:
    result = evaluate(
        dataset=ragas_dataset,
        metrics=[
            faithfulness,
            answer_relevancy,
            context_precision,
            context_recall,
            answer_correctness,
        ],
        llm=azure_llm_for_eval,
        embeddings=embedding_model,
    )

    # --- 4. 顯示結果 ---
    print("RAGAS 評估結果:")
    print(result)

    # 轉換為 Pandas DataFrame
    df = result.to_pandas()
    print("\n前5筆資料:")
    print(df.head())

    # 儲存結果
    df.to_csv("./data/ragas_evaluation_results.csv", index=False, encoding="utf-8-sig")
    print("結果已儲存到 ./data/ragas_evaluation_results.csv")

    # 顯示平均分數
    print("\n平均分數:")
    for metric in [
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
        "answer_correctness",
    ]:
        if metric in df.columns:
            avg_score = df[metric].mean()
            print(f"{metric}: {avg_score:.4f}")

except Exception as e:
    print(f"評估過程中發生錯誤: {e}")
    import traceback

    traceback.print_exc()
