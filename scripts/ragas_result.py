import glob
import os

import pandas as pd


def analyze_ragas_results(folder_path):
    # 設定要計算平均值的指標欄位
    metrics = [
        "faithfulness",
        "context_precision",
        "context_recall",
        "answer_relevancy",
        "answer_correctness",
    ]

    # 搜尋資料夾下的所有 CSV 檔案
    csv_files = glob.glob(os.path.join(folder_path, "*.csv"))

    if not csv_files:
        print(f"❌ 在 '{folder_path}' 找不到任何 CSV 檔案。")
        return

    summary_data = []

    print(f"🔍 正在分析 {len(csv_files)} 個評估結果檔案...\n")

    for file_path in csv_files:
        try:
            df = pd.read_csv(file_path)
            file_name = os.path.basename(file_path)

            # 準備該檔案的結果字典
            row_result = {"Dataset / Model": file_name}

            # 計算每個指標的平均值
            for metric in metrics:
                if metric in df.columns:
                    # 計算平均值並四捨五入到小數點後 4 位
                    row_result[metric] = round(df[metric].mean(), 4)
                else:
                    row_result[metric] = None

            summary_data.append(row_result)

        except Exception as e:
            print(f"⚠️ 無法讀取 {file_path}: {e}")

    # 將結果轉為 DataFrame 以便漂亮地列印
    if summary_data:
        # --- 修正的部分開始 ---
        # 先建立 DataFrame，再設定 Index
        summary_df = pd.DataFrame(summary_data).set_index("Dataset / Model")
        # --- 修正的部分結束 ---

        # 根據 answer_correctness (通常是最重要的指標) 進行排序
        if "answer_correctness" in summary_df.columns:
            summary_df = summary_df.sort_values(
                by="answer_correctness", ascending=False
            )

        print("-" * 120)  # 稍微加長分隔線以適應長檔名
        print("🏆 Ragas Evaluation Summary (Average Scores)")
        print("-" * 120)
        print(summary_df.to_string())
        print("-" * 120)

        # 儲存結果
        output_summary = "ragas_summary_report.csv"
        summary_df.to_csv(output_summary)
        print(f"\n✅ 彙整報告已儲存至: {output_summary}")


if __name__ == "__main__":
    TARGET_DIR = "./data/ragas_result"
    analyze_ragas_results(TARGET_DIR)
