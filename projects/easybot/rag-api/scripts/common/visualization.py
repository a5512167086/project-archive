from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# ==========================================
# 1. 路徑定義
# ==========================================
BASE_EVAL_DIR = Path(r"./data/eval_result")
SINGLE_TURN_DIR = BASE_EVAL_DIR / "single_turn"
MULTI_TURN_DIR = BASE_EVAL_DIR / "multi_turn"

OUTDIR_BASE = Path(r"./data/chart")

# ==========================================
# 2. 定義四大面向與對應的指標
# ==========================================
FOUR_DIMENSIONS = {
    "Retrieval Correctness": ["context precision", "context recall"],
    "Answer Correctness": ["answer correctness", "faithfulness", "bertscore"],
    "Answer Relevancy": ["answer relevancy"],
    "Multi-Turn Capability": ["coreference success", "topic switch success"],
}

# ----------------------------
# Parsing
# ----------------------------


@dataclass(frozen=True)
class RunKey:
    dataset: str
    retrieval: str
    module: str


def parse_run_key(key: str) -> RunKey:
    dataset_name = "WKE" if "_wke_" in key.lower() else "Daedo"

    retrievals = ["vector", "lexical", "hybrid"]
    retrieval_type = "unknown"
    for r in retrievals:
        if f"_{r}_" in key or key.endswith(f"_{r}"):
            retrieval_type = r
            break

    if retrieval_type != "unknown":
        parts = key.split(f"_{retrieval_type}")
        if len(parts) > 1 and parts[1]:
            module_str = parts[1].lstrip("_")
        else:
            module_str = "baseline"
    else:
        module_str = "unknown"

    return RunKey(dataset=dataset_name, retrieval=retrieval_type, module=module_str)


def normalize_module(module: str) -> str:
    module = module.strip().lower()
    mapping = {
        "baseline": "baseline",
        "rerank": "rerank",
        "rewrite": "rewrite",
        "baseline_rewrite": "rewrite",
        "rerank_rewrite": "rerank+rewrite",
    }
    return mapping.get(module, module)


def ensure_outdir(outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)


# ----------------------------
# Plotting Functions
# ----------------------------


def get_filtered_module_order(turn_type: str) -> list[str]:
    """根據 Turn Type 過濾掉不需要的模組"""
    if turn_type == "Single-Turn":
        return ["baseline", "rerank"]
    return ["baseline", "rerank", "rewrite", "rerank+rewrite"]


def plot_by_retrieval_lines(
    df: pd.DataFrame,
    outdir: Path,
    retrieval_order: list[str],
    metric_order: list[str],
    turn_type: str,
    dataset_name: str,
    group_name: str,
) -> None:
    current_module_order = get_filtered_module_order(turn_type)

    df_plot = df[
        (df["metric"].isin(metric_order))
        & (df["turn_type"] == turn_type)
        & (df["dataset_name"] == dataset_name)
        & (df["module"].isin(current_module_order))
    ].copy()

    if df_plot.empty:
        return

    df_plot["dataset_mod"] = df_plot["module"]
    retrievals = [r for r in retrieval_order if r in set(df_plot["retrieval"].unique())]

    def dataset_sort_key(module_name: str) -> int:
        return {m: i for i, m in enumerate(current_module_order)}.get(module_name, 99)

    for retrieval in retrievals:
        sub = df_plot[df_plot["retrieval"] == retrieval].copy()
        pivot = sub.pivot_table(
            index="dataset_mod", columns="metric", values="value", aggfunc="mean"
        ).reindex(columns=[m for m in metric_order if m in sub["metric"].values])
        pivot = pivot.loc[sorted(pivot.index, key=dataset_sort_key)]

        fig, ax = plt.subplots(figsize=(10, 5))
        xs = list(range(len(pivot.columns)))
        for mod in pivot.index:
            ys = pivot.loc[mod].tolist()
            ax.plot(xs, ys, marker="o", linewidth=1.5, label=mod)

        ax.set_title(
            f"{group_name} Metrics - {turn_type} ({dataset_name}) - {retrieval.capitalize()}"
        )
        ax.set_xlabel("Metric")
        ax.set_ylabel("Score")
        ax.set_ylim(0.4, 1.0)
        ax.set_xticks(xs)
        ax.set_xticklabels(pivot.columns, rotation=25, ha="right")
        ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.6)
        ax.legend(
            title="Module", loc="center left", bbox_to_anchor=(1.02, 0.5), frameon=False
        )

        plt.tight_layout()
        out_path = outdir / f"lines_{group_name.lower()}_{retrieval}.png"
        plt.savefig(out_path, dpi=200, bbox_inches="tight")
        plt.close()


def plot_original_heatmap(
    df: pd.DataFrame,
    outdir: Path,
    metric_order: list[str],
    retrieval_order: list[str],
    turn_type: str,
    dataset_name: str,
) -> None:
    current_module_order = get_filtered_module_order(turn_type)

    df_plot = df[
        (df["turn_type"] == turn_type)
        & (df["dataset_name"] == dataset_name)
        & (df["module"].isin(current_module_order))
    ].copy()

    if df_plot.empty:
        return

    df_plot["run_id"] = df_plot.apply(
        lambda r: f"{r['retrieval']} | {r['module']}", axis=1
    )

    valid_metrics = [m for m in metric_order if m in df_plot["metric"].unique()]
    pivot = df_plot.pivot_table(
        index="run_id", columns="metric", values="value", aggfunc="mean"
    ).reindex(columns=valid_metrics)

    pivot = pivot.dropna(axis=1, how="all")

    retrieval_rank = {r: i for i, r in enumerate(retrieval_order)}
    module_rank = {m: i for i, m in enumerate(current_module_order)}

    def sort_key(run_id: str) -> tuple:
        retrieval, module = [x.strip() for x in run_id.split("|")]
        return (retrieval_rank.get(retrieval, 99), module_rank.get(module, 99))

    pivot = pivot.loc[sorted(pivot.index, key=sort_key)]

    n_rows, n_cols = pivot.shape
    fig_w = max(10, 1.2 * n_cols + 3)
    fig_h = max(6, 0.4 * n_rows + 2)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    im = ax.imshow(pivot.values, vmin=0.5, vmax=1.0, aspect="auto", cmap="viridis")

    ax.set_title(
        f"Evaluation Heatmap - {turn_type} ({dataset_name})",
        pad=20,
        fontsize=14,
        fontweight="bold",
    )
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(pivot.columns.tolist(), rotation=35, ha="right")
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(pivot.index.tolist())

    for i in range(n_rows):
        for j in range(n_cols):
            v = pivot.values[i, j]
            if not pd.isna(v):
                color = "white" if v < 0.75 else "black"
                ax.text(
                    j, i, f"{v:.3f}", ha="center", va="center", fontsize=10, color=color
                )

    cbar = fig.colorbar(im, ax=ax, fraction=0.02, pad=0.02)
    cbar.set_label("Score", rotation=270, labelpad=15)

    plt.tight_layout()
    out_path = outdir / "heatmap_original.png"
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"[OK] Saved Original Heatmap: {out_path.resolve()}")


def plot_dimensions_bar_all_retrievals(
    df: pd.DataFrame,
    outdir: Path,
    turn_type: str,
    dataset_name: str,
    retrieval_order: list[str],
) -> None:
    current_module_order = get_filtered_module_order(turn_type)

    df_plot = df[
        (df["turn_type"] == turn_type)
        & (df["dataset_name"] == dataset_name)
        & (df["module"].isin(current_module_order))
    ].copy()

    if df_plot.empty:
        return

    active_dimensions = []
    for dim_name, metrics in FOUR_DIMENSIONS.items():
        if turn_type == "Single-Turn" and dim_name == "Multi-Turn Capability":
            continue
        active_dimensions.append((dim_name, metrics))

    # 動態決定名稱 (3 或 4 面向)
    dim_count = len(active_dimensions)
    dim_title = "Three" if dim_count == 3 else "Four"

    def plot_chunk(dimensions_chunk, suffix):
        n_cols = len(dimensions_chunk)
        # 【視覺升級】進一步加寬畫布，給橫向文字足夠的空間 (10.0 per col)
        fig_width = 10.0 * n_cols
        fig, axes = plt.subplots(1, n_cols, figsize=(fig_width, 7.5))

        if n_cols == 1:
            axes = [axes]

        # 使用動態標題
        fig.suptitle(
            f"{dim_title} Dimensions Performance - {turn_type} ({dataset_name})",
            fontsize=20,
            fontweight="bold",
            y=0.98,
        )

        colors = ["#66c2a5", "#fc8d62", "#8da0cb"]

        for idx, (dim_name, metrics) in enumerate(dimensions_chunk):
            ax = axes[idx]

            plot_data = []
            for mod in current_module_order:
                row = {"Module": mod}
                df_mod = df_plot[df_plot["module"] == mod]
                for ret in retrieval_order:
                    df_ret = df_mod[df_mod["retrieval"] == ret]
                    vals = df_ret[df_ret["metric"].isin(metrics)]["value"]
                    row[ret] = vals.mean() if not vals.empty else 0
                plot_data.append(row)

            df_bar = pd.DataFrame(plot_data).set_index("Module")

            if (df_bar == 0).all().all():
                ax.text(
                    0.5,
                    0.5,
                    "No Data",
                    ha="center",
                    va="center",
                    fontsize=14,
                    color="gray",
                )
                ax.set_title(dim_name, fontsize=16, fontweight="bold")
                ax.axis("off")
                continue

            # 【視覺升級】柱子加寬到 0.75，讓長條圖看起來很飽滿
            df_bar.plot(kind="bar", ax=ax, width=0.75, color=colors)

            # 動態計算 Y 軸起點，放大分數差距
            all_vals = df_bar.values.flatten()
            non_zero_vals = all_vals[all_vals > 0]
            if len(non_zero_vals) > 0:
                min_val = non_zero_vals.min()
                y_min = max(0.0, min_val - 0.08)
            else:
                y_min = 0.4

            ax.set_title(dim_name, fontsize=16, fontweight="bold")
            ax.set_xlabel("Modules", fontsize=12)
            ax.set_ylabel("Average Score", fontsize=12)
            ax.set_ylim(y_min, 1.05)
            ax.tick_params(axis="x", rotation=0, labelsize=11)
            ax.legend(title="Retrieval", loc="lower right", fontsize=10)
            ax.grid(axis="y", linestyle="--", alpha=0.7)

            # 【視覺升級】取消旋轉，恢復水平文字
            for p in ax.patches:
                val = p.get_height()
                if val > 0:
                    ax.annotate(
                        f"{val:.3f}",
                        (p.get_x() + p.get_width() / 2.0, p.get_height()),
                        ha="center",
                        va="bottom",
                        xytext=(0, 5),
                        textcoords="offset points",
                        fontsize=10,  # 恢復水平
                    )

        plt.tight_layout(rect=[0, 0, 1, 0.93])

        # 檔名與 Log 也改為動態
        out_path = outdir / f"{dim_count}_dim_bar_{suffix}.png"
        plt.savefig(out_path, dpi=200)
        plt.close()
        print(
            f"[OK] Saved {dim_count}-Dimensions Bar Chart ({suffix}): {out_path.resolve()}"
        )

    if turn_type == "Multi-Turn":
        plot_chunk(active_dimensions[:2], "part1")
        plot_chunk(active_dimensions[2:], "part2")
    else:
        plot_chunk(active_dimensions, "all")


# ----------------------------
# Main Logic
# ----------------------------


def load_and_preprocess(path: Path, turn_type: str) -> list[dict]:
    if not path.exists():
        print(f"[Warn] File not found: {path}")
        return []

    data = json.loads(path.read_text(encoding="utf-8"))
    rows = []

    for k, metrics in data.items():
        rk = parse_run_key(k)
        module = normalize_module(rk.module)

        if "overall" in metrics:
            flat_metrics = metrics["overall"]
        else:
            flat_metrics = {
                mk: mv for mk, mv in metrics.items() if not isinstance(mv, dict)
            }

        for metric_name, value in flat_metrics.items():
            clean_metric_name = metric_name.lower().replace("_", " ")
            rows.append({
                "turn_type": turn_type,
                "dataset_name": rk.dataset,
                "retrieval": rk.retrieval,
                "module": module,
                "metric": clean_metric_name,
                "value": float(value),
            })
    return rows


def main() -> None:
    single_ragas = load_and_preprocess(
        SINGLE_TURN_DIR / "summary_report.json", "Single-Turn"
    )
    single_trad = load_and_preprocess(
        SINGLE_TURN_DIR / "traditional_summary_report.json", "Single-Turn"
    )

    multi_ragas = load_and_preprocess(
        MULTI_TURN_DIR / "summary_report.json", "Multi-Turn"
    )
    multi_trad = load_and_preprocess(
        MULTI_TURN_DIR / "traditional_summary_report.json", "Multi-Turn"
    )

    all_rows = single_ragas + single_trad + multi_ragas + multi_trad

    if not all_rows:
        print("No data found to plot. Please check your JSON paths.")
        return

    df = pd.DataFrame(all_rows)

    ragas_metrics = [
        "answer relevancy",
        "answer correctness",
        "context precision",
        "context recall",
        "faithfulness",
        "coreference success",
        "topic switch success",
    ]
    trad_metrics = [
        "rouge-1-precision",
        "rouge-1-recall",
        "rouge-1-f1",
        "rouge-l-f1",
        "bertscore",
    ]
    all_metrics = ragas_metrics + trad_metrics

    retrieval_order = ["lexical", "vector", "hybrid"]

    combinations = [
        ("Single-Turn", "WKE", OUTDIR_BASE / "single-turn" / "wke"),
        ("Single-Turn", "Daedo", OUTDIR_BASE / "single-turn" / "daedo"),
        ("Multi-Turn", "Daedo", OUTDIR_BASE / "multi-turn"),
    ]

    for turn, dataset, outdir in combinations:
        if not ((df["turn_type"] == turn) & (df["dataset_name"] == dataset)).any():
            continue

        ensure_outdir(outdir)

        plot_by_retrieval_lines(
            df, outdir, retrieval_order, ragas_metrics, turn, dataset, "RAGAS"
        )
        plot_by_retrieval_lines(
            df, outdir, retrieval_order, trad_metrics, turn, dataset, "Traditional"
        )
        plot_original_heatmap(df, outdir, all_metrics, retrieval_order, turn, dataset)
        plot_dimensions_bar_all_retrievals(df, outdir, turn, dataset, retrieval_order)

    print(
        f"\n✨ All charts successfully generated and organized under: {OUTDIR_BASE.resolve()}"
    )


if __name__ == "__main__":
    main()
