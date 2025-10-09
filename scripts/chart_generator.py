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
    print("--- Running RAG Model Evaluation Analysis Script (Streamlined Version) ---")
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

    print("\n--- All tasks completed! All files have been successfully generated. ---")


def load_and_process_data():
    """
    動態尋找並讀取所有 ragas_results_*.csv 檔案。
    """
    print("\n--- Step 1: Loading and processing CSV files ---")
    file_pattern = "./data/ragas_result/ragas_results_*.csv"
    csv_files = glob.glob(file_pattern)

    if not csv_files:
        # If not found in ./data/ragas_result, try the current directory
        print(
            f"Warning: No files found in '{file_pattern}'. Trying current directory..."
        )
        file_pattern = "ragas_results_*.csv"
        csv_files = glob.glob(file_pattern)

    if not csv_files:
        print(
            f"Error: No files matching '{file_pattern}' found in ./data or the current directory."
        )
        return None

    print(f"Found {len(csv_files)} evaluation files.")
    all_data_list = []

    model_name_map = {
        "gemini_google": "Gemini 2.5 flash",
        "gpt35_azure": "GPT-3.5 Turbo",
        "huggingface_local": "Qwen-4B",
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
        df["model"], ["GPT-3.5 Turbo", "Gemini 2.5 flash", "Qwen-4B"], ordered=True
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

    output_filename = f"./data/chart/bar_chart_{dataset_name}.png"
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
        df["model"], ["GPT-3.5 Turbo", "Gemini 2.5 flash", "Qwen-4B"], ordered=True
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

    output_filename = f"./data/chart/radar_chart_{dataset_name}.png"
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

    all_models = ["GPT-3.5 Turbo", "Gemini 2.5 flash", "Qwen-4B"]
    for model in all_models:
        if model not in comparison_table.columns:
            comparison_table[model] = np.nan

    column_order = ["dataset", "user_input"] + all_models + ["retrieved_contexts"]
    comparison_table = comparison_table[column_order]

    output_filename = "./data/chart/qualitative_comparison_table.csv"
    comparison_table.to_csv(output_filename, index=False, encoding="utf-8-sig")
    print(f"✓ Generated qualitative comparison table: {output_filename}")


if __name__ == "__main__":
    main()
