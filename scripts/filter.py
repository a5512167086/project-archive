import ast
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

# === 檔案設定 ===
CONFIG = {
    # 基礎路徑
    "base_path": Path("./data/ragas_result/"),
    "output_path": Path("./data/chart/"),
    # 資料集與模型定義
    "datasets": ["ecomm", "wke"],
    "models": {
        "gemini_2.5_flash": {"name": "Gemini 2.5 flash"},
        "gpt_5_mini": {"name": "GPT o4 mini"},
        "qwen3_local": {"name": "Qwen3 4B"},
    },
    # 檔案與欄位模板
    "filename_template": "ragas_results_ragas_eval_{model}_{dataset}.csv",
    "key_cols": ["user_input", "retrieved_contexts", "reference"],
    "metrics_cols": [
        "response",
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
        "answer_correctness",
    ],
    # 💡 重構重點：篩選條件由設定檔驅動
    # 在此定義所有要篩選並獨立輸出的條件
    # 鍵名 (例如 'low_relevancy') 是內部標識符
    "filter_criteria": {
        "low_relevancy": {
            "metric": "answer_relevancy",  # 要檢查的指標
            "threshold": 0.5,  # 閾值
            "operator": "<",  # 運算符 (目前僅支援 <)
            "output_filename": "relevancy_low_{dataset}.json",
            "log_message": "low relevancy (< 0.5)",
        },
        "low_correctness": {
            "metric": "answer_correctness",  # 要檢查的指標
            "threshold": 0.3,  # 閾值
            "operator": "<",  # 運算符 (目前僅支援 <)
            "output_filename": "correctness_low_{dataset}.json",
            "log_message": "low correctness (< 0.3)",
        },
    },
}

ModelConfig = Dict[str, Dict[str, str]]


def safe_parse_contexts(value: Any) -> List[str]:
    """
    嘗試把 retrieved_contexts 字串轉成 list[str]
    - 支援 JSON list
    - 支援 Python list 字串 (單引號)
    - fallback 成單一字串 list
    """
    if pd.isna(value) or value is None:
        return ["無內容"]

    if isinstance(value, list):
        return value

    if not isinstance(value, str):
        return [str(value)]

    value = value.strip()
    if value == "":
        return ["無內容"]

    if value.startswith("[") and value.endswith("]"):
        try:
            # 嘗試 JSON (最標準)
            return json.loads(value)
        except json.JSONDecodeError:
            try:
                # 嘗試 ast (可處理單引號)
                return ast.literal_eval(value)
            except Exception:
                # 如果解析失敗，當作單一字串處理 (去除方括號)
                return [value[1:-1]]

    # 最終 fallback
    return [value]


def df_to_grouped_json(
    df: pd.DataFrame, model_config: ModelConfig
) -> List[Dict[str, Any]]:
    """
    將 "寬" DataFrame 轉換為分組的 JSON 結構
    """

    def _to_json_number(val: Any) -> Optional[float]:
        """輔助函數：確保 NaN 值在 JSON 中顯示為 null"""
        if pd.isna(val):
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None

    output_data = []
    for _, row in df.iterrows():
        answers_data = {}
        for prefix, config in model_config.items():
            model_name = config["name"]
            answers_data[model_name] = {
                "answer": row.get(f"{prefix}_response"),
                "answer_relevancy": _to_json_number(
                    row.get(f"{prefix}_answer_relevancy")
                ),
                "answer_correctness": _to_json_number(
                    row.get(f"{prefix}_answer_correctness")
                ),
            }

        output_data.append({
            "question": row.get("user_input"),
            "contexts": safe_parse_contexts(row.get("retrieved_contexts")),
            "ground_truth": row.get("reference"),
            "answers": answers_data,
        })
    return output_data


def load_and_merge_data(dataset: str, config: Dict[str, Any]) -> Optional[pd.DataFrame]:
    """
    為指定的資料集讀取所有模型的 CSV 檔案，並將它們合併。
    """
    print(f"\n--- 正在讀取與合併資料集: {dataset} ---")

    merged_df: Optional[pd.DataFrame] = None
    model_prefixes = list(config["models"].keys())
    base_path: Path = config["base_path"]

    for prefix in model_prefixes:
        filename = config["filename_template"].format(model=prefix, dataset=dataset)
        filepath = base_path / filename

        try:
            df = pd.read_csv(filepath)
        except FileNotFoundError:
            print(f"⚠️ 警告: 找不到檔案 {filepath}，將跳過此模型。")
            continue
        except Exception as e:
            print(f"❌ 讀取 {filepath} 時發生錯誤: {e}")
            continue

        # 檢查 key_cols 是否存在
        missing_keys = [k for k in config["key_cols"] if k not in df.columns]
        if missing_keys:
            print(
                f"❌ 錯誤: {filepath} 缺少合併所需的欄位: {missing_keys}。跳過此檔案。"
            )
            continue

        # 建立要重命名的欄位
        rename_map = {
            col: f"{prefix}_{col}"
            for col in config["metrics_cols"]
            if col in df.columns
        }
        df.rename(columns=rename_map, inplace=True)

        # 將此模型的 DF 合併到主 DF
        if merged_df is None:
            merged_df = df
        else:
            # 使用 outer join 以保留所有問題，即使某個模型沒有回答
            merged_df = pd.merge(merged_df, df, on=config["key_cols"], how="outer")

    if merged_df is None or merged_df.empty:
        print(f"ℹ️ {dataset} 資料集沒有載入任何資料，跳過。")
        return None

    print(f"✅ {dataset} 資料集已合併，共 {len(merged_df)} 筆資料。")
    return merged_df


def main():
    """
    主處理邏輯
    """
    print("🚀 開始處理 Ragas 評估結果...")

    config = CONFIG
    output_path: Path = config["output_path"]

    # 確保輸出目錄存在
    output_path.mkdir(parents=True, exist_ok=True)

    # 遍歷每個資料集 (ecomm, wke)
    for dataset in config["datasets"]:
        merged_df = load_and_merge_data(dataset, config)

        if merged_df is None:
            continue

        model_prefixes = list(config["models"].keys())

        # 2. 數值欄位處理
        # 收集所有需要被篩選的指標
        metrics_to_process = {
            criteria["metric"] for criteria in config["filter_criteria"].values()
        }

        all_metric_cols = []
        for prefix in model_prefixes:
            for metric in metrics_to_process:
                col_name = f"{prefix}_{metric}"
                if col_name in merged_df.columns:
                    all_metric_cols.append(col_name)

        # 一次性轉換所有相關欄位為數值
        for col in all_metric_cols:
            merged_df[col] = pd.to_numeric(merged_df[col], errors="coerce")

        print(f"📊 {dataset} 資料集開始進行篩選...")

        # 3. 篩選、轉換、寫出 (Data-Driven Loop)
        for filter_name, criteria in config["filter_criteria"].items():
            metric = criteria["metric"]
            threshold = criteria["threshold"]
            # 找到所有模型中對應此指標的欄位
            metric_cols = [
                f"{p}_{metric}"
                for p in model_prefixes
                if f"{p}_{metric}" in merged_df.columns
            ]

            if not metric_cols:
                print(f"ℹ️ 找不到 {metric} 的欄位，跳過 {filter_name} 篩選。")
                continue

            # 建立篩選遮罩：
            # 只要「任一」模型的指標分數 < threshold 或為 NaN
            mask = (merged_df[metric_cols] < threshold).any(axis=1) | (
                merged_df[metric_cols].isna()
            ).any(axis=1)

            filtered_df = merged_df[mask]

            # 4. 轉換成 JSON
            grouped_json = df_to_grouped_json(filtered_df, config["models"])

            # 5. 寫出檔案
            output_filename = criteria["output_filename"].format(dataset=dataset)
            output_file_path = output_path / output_filename

            with open(output_file_path, "w", encoding="utf-8") as f:
                json.dump(grouped_json, f, ensure_ascii=False, indent=2)

            print(
                f" ➡️ 已輸出 {len(grouped_json):>3} 筆 {criteria['log_message']} 資料到 {output_file_path}"
            )

    print("\n🎉 全部處理完畢！")


if __name__ == "__main__":
    main()
