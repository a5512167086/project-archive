import glob
import os
import warnings

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


# --- 主程式 ---
def main():
    """
    主執行函數，讀取 Ragas CSV 檔案，產生分析圖表與表格。
    """
    print(
        "--- Running RAG Model Evaluation Analysis Script (with Low-Score Analysis) ---"
    )
    warnings.filterwarnings("ignore", category=UserWarning)

    # 1. 穩健地讀取並整合所有評估資料
    all_data = load_and_process_data()
    if all_data is None or all_data.empty:
        print("Error: No data loaded, terminating script.")
        return

    # 2. 計算量化指標的平均分數
    metrics_to_evaluate = [
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
        "answer_correctness",
    ]
    agg_scores = (
        all_data.groupby(["dataset", "model"])[metrics_to_evaluate].mean().reset_index()
    )

    # 3. 產生視覺化圖表
    for dataset in agg_scores["dataset"].unique():
        print(f"--- Generating charts for '{dataset}' dataset ---")
        dataset_df = agg_scores[agg_scores["dataset"] == dataset].copy()
        create_bar_chart(dataset_df, dataset, metrics_to_evaluate)
        create_radar_chart(dataset_df, dataset, metrics_to_evaluate)

    # 4. 產生用於質化分析的並列比較表
    create_qualitative_comparison_table(all_data)

    # 5. 【新增功能】分析並儲存分數低於 0.5 的案例
    analyze_low_score_cases(all_data)

    print("\n--- All tasks completed! All files have been successfully generated. ---")


def load_and_process_data():
    """
    動態尋找並讀取所有 ragas_results_*.csv 檔案。
    """
    print("\n--- Step 1: Loading and processing CSV files ---")
    file_pattern = "./data/ragas_result/ragas_results_*.csv"
    csv_files = glob.glob(file_pattern, recursive=True)

    if not csv_files:
        # If not found in ./data/ragas_result, try the current directory
        print(
            f"Warning: No files found in '{file_pattern}'. Trying current directory..."
        )
        file_pattern = "ragas_results_*.csv"
        csv_files = glob.glob(file_pattern)

    if not csv_files:
        print(
            "Error: No files matching pattern found in ./data/ragas_result/ or the current directory."
        )
        return None

    print(f"Found {len(csv_files)} evaluation files.")
    all_data_list = []

    model_name_map = {
        "gemini_2.5_flash": "Gemini 2.5 flash",
        "gpt_o4_azure": "GPT o4 mini",
        "qwen3_local": "Qwen3 4B",
    }

    for file_path in csv_files:
        try:
            filename = os.path.basename(file_path)
            parts = filename.replace(".csv", "").split("_")

            model_key = f"{parts[4]}_{parts[5]}"
            dataset_name = parts[6]

            model_name = model_name_map.get(model_key)

            if model_name:
                df = pd.read_csv(file_path)
                df["model"] = model_name
                df["dataset"] = dataset_name
                all_data_list.append(df)
                print(f"  > Successfully loaded: {filename}")
            else:
                print(
                    f"Warning: Could not parse model key '{model_key}' from filename '{filename}'. Skipped."
                )
        except IndexError:
            print(
                f"Warning: Filename '{filename}' has an unexpected structure. Skipped."
            )
        except Exception as e:
            print(
                f"Warning: An error occurred while processing {file_path}: {e}. Skipped."
            )

    if not all_data_list:
        return None

    return pd.concat(all_data_list, ignore_index=True)


def create_bar_chart(df, dataset_name, metrics):
    """產生並儲存指標比較條形圖"""
    plt.style.use("seaborn-v0_8-talk")
    fig, ax = plt.subplots(figsize=(16, 9))

    df["model"] = pd.Categorical(
        df["model"], ["GPT o4 mini", "Gemini 2.5 flash", "Qwen-4B"], ordered=True
    )
    df = df.sort_values("model")
    models = df["model"].unique()

    n_models = len(models)
    n_metrics = len(metrics)
    bar_width = 0.2
    index = np.arange(n_metrics)

    for i, model in enumerate(models):
        model_scores = df[df["model"] == model][metrics].values.flatten()
        ax.bar(index + i * bar_width, model_scores, bar_width, label=model)

    ax.set_xlabel("Ragas Evaluation Metrics", fontsize=16, fontweight="bold")
    ax.set_ylabel("Score (Average)", fontsize=16, fontweight="bold")
    ax.set_title(
        f'Model Comparison on Ragas Metrics for "{dataset_name}" Dataset',
        fontsize=20,
        fontweight="bold",
    )
    ax.set_xticks(index + bar_width * (n_models - 1) / 2)
    ax.set_xticklabels(metrics, rotation=15, ha="right")
    ax.legend(fontsize=14)
    ax.grid(axis="y", linestyle="--", alpha=0.7)
    plt.tight_layout()

    output_dir = "./data/chart/"
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, f"bar_chart_{dataset_name}.png")
    plt.savefig(output_filename, dpi=300)
    plt.close()
    print(f"✓ Generated bar chart: {output_filename}")


def create_radar_chart(df, dataset_name, metrics):
    """產生並儲存模型能力雷達圖"""
    num_vars = len(metrics)
    angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

    df["model"] = pd.Categorical(
        df["model"], ["GPT o4 mini", "Gemini 2.5 flash", "Qwen-4B"], ordered=True
    )
    df = df.sort_values("model")

    for _, row in df.iterrows():
        model = row["model"]
        values = row[metrics].tolist()
        values += values[:1]
        ax.plot(angles, values, label=model, linewidth=2)
        ax.fill(angles, values, alpha=0.25)

    ax.set_yticklabels([])
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metrics, size=12)
    ax.set_title(
        f'Model Capability Radar Chart for "{dataset_name}" Dataset',
        size=20,
        color="black",
        y=1.1,
    )
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))

    output_dir = "./data/chart/"
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, f"radar_chart_{dataset_name}.png")
    plt.savefig(output_filename, dpi=300)
    plt.close()
    print(f"✓ Generated radar chart: {output_filename}")


def create_qualitative_comparison_table(all_data):
    """產生並儲存用於質化分析的並列比較表"""
    qualitative_df = all_data[
        ["dataset", "user_input", "model", "response", "retrieved_contexts"]
    ]
    comparison_table = qualitative_df.pivot_table(
        index=["dataset", "user_input", "retrieved_contexts"],
        columns="model",
        values="response",
        aggfunc="first",
    ).reset_index()

    all_models = ["GPT o4 mini", "Gemini 2.5 flash", "Qwen-4B"]
    for model in all_models:
        if model not in comparison_table.columns:
            comparison_table[model] = np.nan

    column_order = ["dataset", "user_input"] + all_models + ["retrieved_contexts"]
    # Reorder to ensure all columns exist before indexing
    final_cols = [col for col in column_order if col in comparison_table.columns]
    comparison_table = comparison_table[final_cols]

    output_dir = "./data/chart/"
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, "qualitative_comparison_table.csv")
    comparison_table.to_csv(output_filename, index=False, encoding="utf-8-sig")
    print(f"✓ Generated qualitative comparison table: {output_filename}")


def analyze_low_score_cases(all_data):
    """
    【新增功能】
    篩選出 answer_relevancy 或 answer_correctness 低於 0.5 的案例，並儲存成報告。
    """
    print("\n--- Step 5: Analyzing low-score cases (score < 0.5) ---")

    # 設定篩選條件
    low_score_condition = (all_data["answer_relevancy"] < 0.5) | (
        all_data["answer_correctness"] < 0.5
    )

    # 篩選出符合條件的資料
    low_score_df = all_data[low_score_condition]

    if low_score_df.empty:
        print(
            "✓ No cases with answer_relevancy or answer_correctness below 0.5 found. Great!"
        )
        return

    # 選擇要顯示的欄位，並依照資料集和模型排序
    columns_to_show = [
        "dataset",
        "model",
        "user_input",
        "response",
        "answer_relevancy",
        "answer_correctness",
        "retrieved_contexts",
    ]

    # 確保所有欄位都存在
    final_columns = [col for col in columns_to_show if col in low_score_df.columns]

    report_df = low_score_df[final_columns].sort_values(by=["dataset", "model"])

    # 儲存報告
    output_dir = "./data/chart/"
    os.makedirs(output_dir, exist_ok=True)
    output_filename = os.path.join(output_dir, "low_score_analysis_report.csv")

    report_df.to_csv(output_filename, index=False, encoding="utf-8-sig")

    print(f"✓ Generated low-score analysis report: {output_filename}")


if __name__ == "__main__":
    main()
