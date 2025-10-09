import ast
import json

import pandas as pd

# === 檔案設定 ===
INPUT_FILE = "./data/ragas_result/ragas_results_ragas_eval_gpt35_azure_ecomm.csv"
RELEVANCY_ZERO_FILE = "./data/eval_dataset/relevancy_zero.json"
CORRECTNESS_ZERO_FILE = "./data/eval_dataset/correctness_zero.json"

# === 讀取 CSV ===
df = pd.read_csv(INPUT_FILE)

# === 欄位檢查 ===
required_cols = [
    "user_input",
    "retrieved_contexts",
    "response",
    "reference",
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
    "answer_correctness",
]
missing_cols = [c for c in required_cols if c not in df.columns]
if missing_cols:
    raise ValueError(f"❌ 缺少欄位: {missing_cols}")

# === 數值欄位處理 ===
df["answer_relevancy"] = pd.to_numeric(df["answer_relevancy"], errors="coerce")
df["answer_correctness"] = pd.to_numeric(df["answer_correctness"], errors="coerce")

# === 篩選 ===
relevancy_zero = df[(df["answer_relevancy"].isna()) | (df["answer_relevancy"] == 0)]
correctness_zero = df[
    (df["answer_correctness"].isna()) | (df["answer_correctness"] == 0)
]


# === 安全解析 retrieved_contexts ===
def safe_parse_contexts(value):
    """
    嘗試把 retrieved_contexts 字串轉成 list[str]
    - 支援 JSON list
    - 支援 Python list 字串 (單引號)
    - fallback 成單一字串 list
    """
    if pd.isna(value) or str(value).strip() == "":
        return ["無內容"]
    if isinstance(value, list):
        return value
    if not isinstance(value, str):
        return [str(value)]

    value = value.strip()
    # 嘗試 JSON 解析
    if value.startswith("[") and value.endswith("]"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(value)
            except Exception:
                pass
    # fallback 成單一元素 list
    return [value]


# === 轉換成 JSON 結構 ===
def df_to_json(df):
    return [
        {
            "question": row["user_input"],
            "contexts": safe_parse_contexts(row["retrieved_contexts"]),
            "answer": row["response"],
            "ground_truth": row["reference"],
        }
        for _, row in df.iterrows()
    ]


# === 生成 JSON ===
relevancy_json = df_to_json(relevancy_zero)
correctness_json = df_to_json(correctness_zero)

# === 寫出檔案 ===
with open(RELEVANCY_ZERO_FILE, "w", encoding="utf-8") as f:
    json.dump(relevancy_json, f, ensure_ascii=False, indent=2)

with open(CORRECTNESS_ZERO_FILE, "w", encoding="utf-8") as f:
    json.dump(correctness_json, f, ensure_ascii=False, indent=2)

print(
    f"✅ 已輸出 {len(relevancy_json)} 筆 answer_relevancy=0 或空值的資料到 {RELEVANCY_ZERO_FILE}"
)
print(
    f"✅ 已輸出 {len(correctness_json)} 筆 answer_correctness=0 或空值的資料到 {CORRECTNESS_ZERO_FILE}"
)
