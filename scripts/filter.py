import ast
import json
import os

import pandas as pd

# === 檔案設定 ===
CONFIG = {
    # 基礎路徑
    "base_path": "./data/ragas_result/",
    "output_path": "./data/chart/",
    # 檔案名稱中包含的資料集標籤
    "datasets": ["ecomm", "wke"],
    # 模型設定
    # key: 檔案名稱中的模型標籤 (e.g., "gemini_google")
    # value: "name" 是 JSON 輸出時的顯示名稱
    "models": {
        "gemini_google": {"name": "Gemini 2.5 flash"},
        "gpt35_azure": {"name": "GPT 3.5 Turbo"},
        "huggingface_local": {"name": "Qwen3 4B"},
    },
    # 檔案名稱模板
    "filename_template": "ragas_results_ragas_eval_{model}_{dataset}.csv",
    # 用於合併的基準欄位 (這些欄位在所有 CSV 中都相同)
    "key_cols": ["user_input", "retrieved_contexts", "reference"],
    # 需要為每個模型加上前綴的欄位
    "metrics_cols": [
        "response",
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
        "answer_correctness",
    ],
}

# === 輔助函數 (來自前一個腳本) ===


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
    if value.startswith("[") and value.endswith("]"):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            try:
                return ast.literal_eval(value)
            except Exception:
                pass
    return [value]


def df_to_grouped_json(df, model_config):
    """
    將 "寬" DataFrame 轉換為分組的 JSON 結構
    """
    output_data = []
    for _, row in df.iterrows():
        answers_data = {}
        for prefix, config in model_config.items():
            model_name = config["name"]
            answers_data[model_name] = {
                "answer": row.get(f"{prefix}_response"),
                # 確保 NaN 值在 JSON 中顯示為 null
                "answer_relevancy": row.get(f"{prefix}_answer_relevancy")
                if not pd.isna(row.get(f"{prefix}_answer_relevancy"))
                else None,
                "answer_correctness": row.get(f"{prefix}_answer_correctness")
                if not pd.isna(row.get(f"{prefix}_answer_correctness"))
                else None,
            }

        output_data.append({
            "question": row.get("user_input"),
            "contexts": safe_parse_contexts(row.get("retrieved_contexts")),
            "ground_truth": row.get("reference"),
            "answers": answers_data,
        })
    return output_data


# === 主處理邏輯 ===

print("🚀 開始處理 Ragas 評估結果...")

# 確保輸出目錄存在
os.makedirs(CONFIG["output_path"], exist_ok=True)

# 遍歷每個資料集 (ecomm, wke)
for dataset in CONFIG["datasets"]:
    print(f"\n--- 正在處理資料集: {dataset} ---")

    merged_df = None
    model_prefixes = list(CONFIG["models"].keys())

    # 1. 讀取並合併每個模型的 CSV
    for prefix in model_prefixes:
        model_config = CONFIG["models"][prefix]
        filename = CONFIG["filename_template"].format(model=prefix, dataset=dataset)
        filepath = os.path.join(CONFIG["base_path"], filename)

        try:
            df = pd.read_csv(filepath)
        except FileNotFoundError:
            print(f"⚠️ 警告: 找不到檔案 {filepath}，將跳過此模型。")
            continue
        except Exception as e:
            print(f"❌ 讀取 {filepath} 時發生錯誤: {e}")
            continue

        # 檢查 key_cols 是否存在
        missing_keys = [k for k in CONFIG["key_cols"] if k not in df.columns]
        if missing_keys:
            print(
                f"❌ 錯誤: {filepath} 缺少合併所需的欄位: {missing_keys}。跳過此檔案。"
            )
            continue

        # 建立要重命名的欄位
        rename_map = {
            col: f"{prefix}_{col}"
            for col in CONFIG["metrics_cols"]
            if col in df.columns
        }
        df.rename(columns=rename_map, inplace=True)

        # 將此模型的 DF 合併到主 DF
        if merged_df is None:
            merged_df = df
        else:
            # 使用 outer join 以保留所有問題，即使某個模型沒有回答
            merged_df = pd.merge(merged_df, df, on=CONFIG["key_cols"], how="outer")

    if merged_df is None or merged_df.empty:
        print(f"ℹ️ {dataset} 資料集沒有載入任何資料，跳過。")
        continue

    print(f"✅ {dataset} 資料集已合併，共 {len(merged_df)} 筆資料。")

    # 2. 數值欄位處理
    relevancy_cols_to_check = []
    correctness_cols_to_check = []

    for prefix in model_prefixes:
        rel_col = f"{prefix}_answer_relevancy"
        cor_col = f"{prefix}_answer_correctness"

        if rel_col in merged_df.columns:
            merged_df[rel_col] = pd.to_numeric(merged_df[rel_col], errors="coerce")
            relevancy_cols_to_check.append(rel_col)

        if cor_col in merged_df.columns:
            merged_df[cor_col] = pd.to_numeric(merged_df[cor_col], errors="coerce")
            correctness_cols_to_check.append(cor_col)

    # 3. 篩選
    # 篩選：只要「任一」模型的 relevancy 分數為 0 或 NaN
    relevancy_mask = (merged_df[relevancy_cols_to_check] == 0).any(axis=1) | (
        merged_df[relevancy_cols_to_check].isna()
    ).any(axis=1)
    relevancy_zero_df = merged_df[relevancy_mask]

    # --- 💡 修改點 (1) ---
    # 篩選：只要「任一」模型的 correctness 分數低於 0.3 或 NaN
    correctness_mask = (merged_df[correctness_cols_to_check] < 0.3).any(axis=1) | (
        merged_df[correctness_cols_to_check].isna()
    ).any(axis=1)
    correctness_low_df = merged_df[correctness_mask]  # 變數名稱更新
    # --- 💡 修改結束 ---

    # 4. 轉換成 JSON
    relevancy_json = df_to_grouped_json(relevancy_zero_df, CONFIG["models"])

    # --- 💡 修改點 (2) ---
    correctness_low_json = df_to_grouped_json(
        correctness_low_df, CONFIG["models"]
    )  # 變數名稱更新
    # --- 💡 修改結束 ---

    # 5. 寫出檔案
    relevancy_file = os.path.join(
        CONFIG["output_path"], f"relevancy_zero_{dataset}.json"
    )

    # --- 💡 修改點 (3) ---
    correctness_file = os.path.join(
        CONFIG["output_path"],
        f"correctness_low_{dataset}.json",  # 檔名更新
    )
    # --- 💡 修改結束 ---

    with open(relevancy_file, "w", encoding="utf-8") as f:
        json.dump(relevancy_json, f, ensure_ascii=False, indent=2)

    # --- 💡 修改點 (4) ---
    with open(correctness_file, "w", encoding="utf-8") as f:
        json.dump(correctness_low_json, f, ensure_ascii=False, indent=2)  # 變數名稱更新
    # --- 💡 修改結束 ---

    print(
        f"  ➡️ 已輸出 {len(relevancy_json)} 筆 low relevancy (=0) 資料到 {relevancy_file}"
    )

    # --- 💡 修改點 (5) ---
    print(
        f"  ➡️ 已輸出 {len(correctness_low_json)} 筆 low correctness (<0.3) 資料到 {correctness_file}"  # 變數與文字更新
    )
    # --- 💡 修改結束 ---

print("\n🎉 全部處理完畢！")
