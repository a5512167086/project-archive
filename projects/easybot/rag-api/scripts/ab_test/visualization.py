from __future__ import annotations

import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

# ============================
# Path Config
# ============================

BASE_AB_TEST_DIR = Path(r"./data/eval_result/ab_test")
OUTDIR = Path(r"./data/chart/ab_test")

RAGAS_PATH = BASE_AB_TEST_DIR / "summary_report.json"
TRAD_PATH = BASE_AB_TEST_DIR / "traditional_summary_report.json"


# ============================
# Metric Config
# ============================

RAGAS_METRICS = [
    "answer_relevancy",
    "answer_correctness",
    "context_precision",
    "context_recall",
    "faithfulness",
]

TRAD_METRICS = [
    "rouge-1-precision",
    "rouge-1-recall",
    "rouge-1-f1",
    "rouge-l-f1",
    "bertscore",
]

ALL_METRICS = RAGAS_METRICS + TRAD_METRICS

# ============================
# 2. 定義三大面向與對應的指標 (注意需符合本檔的 snake_case 命名)
# ============================
THREE_DIMENSIONS = {
    "Retrieval Correctness": ["context_precision", "context_recall"],
    "Answer Correctness": ["answer_correctness", "faithfulness", "bertscore"],
    "Answer Relevancy": ["answer_relevancy"],
}

# ============================
# Utils
# ============================


def ensure_outdir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def extract_variant(run_key: str) -> str:
    """
    從 key 中抓出 v1 / v2 / v3
    例如:
    ragas_eval_local_model_rag_testset_hybrid_rerank_v1 -> v1
    """
    m = re.search(r"(v\d+)$", run_key)
    if m:
        return m.group(1)
    return run_key


def variant_sort_key(variant: str) -> int:
    m = re.search(r"v(\d+)", variant.lower())
    return int(m.group(1)) if m else 999


def load_metric_json(path: Path, source: str) -> list[dict]:
    if not path.exists():
        print(f"[Warn] File not found: {path}")
        return []

    data = json.loads(path.read_text(encoding="utf-8"))
    rows = []

    for run_key, metrics in data.items():
        variant = extract_variant(run_key)
        for metric_name, value in metrics.items():
            rows.append({
                "source": source,
                "variant": variant,
                "metric": metric_name,
                "value": float(value),
            })

    return rows


def annotate_bars(ax) -> None:
    for p in ax.patches:
        h = p.get_height()
        if pd.notna(h) and h > 0:
            ax.annotate(
                f"{h:.3f}",
                (p.get_x() + p.get_width() / 2, h),
                ha="center",
                va="bottom",
                fontsize=9,
                xytext=(0, 4),
                textcoords="offset points",
            )


# ============================
# Plotting
# ============================


def plot_grouped_bar(
    df: pd.DataFrame,
    source: str,
    metric_order: list[str],
    out_path: Path,
    title: str,
) -> None:
    sub = df[(df["source"] == source) & (df["metric"].isin(metric_order))].copy()
    if sub.empty:
        print(f"[Warn] No data for source={source}")
        return

    pivot = sub.pivot_table(
        index="metric", columns="variant", values="value", aggfunc="mean"
    ).reindex(metric_order)

    sorted_cols = sorted(pivot.columns.tolist(), key=variant_sort_key)
    pivot = pivot[sorted_cols]

    fig_w = max(10, len(metric_order) * 1.5)
    fig, ax = plt.subplots(figsize=(fig_w, 6))

    pivot.plot(kind="bar", ax=ax, width=0.8)

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Metric")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.05)
    ax.set_xticklabels(pivot.index.tolist(), rotation=25, ha="right")
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.6)
    ax.legend(
        title="Variant",
        loc="upper left",
        bbox_to_anchor=(1.01, 1.0),
        frameon=False,
    )
    annotate_bars(ax)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved grouped bar: {out_path.resolve()}")


def plot_heatmap_all_metrics(
    df: pd.DataFrame,
    metric_order: list[str],
    out_path: Path,
) -> None:
    sub = df[df["metric"].isin(metric_order)].copy()
    if sub.empty:
        print("[Warn] No data for heatmap.")
        return

    pivot = sub.pivot_table(
        index="variant", columns="metric", values="value", aggfunc="mean"
    ).reindex(columns=metric_order)

    pivot = pivot.loc[sorted(pivot.index.tolist(), key=variant_sort_key)]

    n_rows, n_cols = pivot.shape
    fig_w = max(12, n_cols * 1.2)
    fig_h = max(4, n_rows * 1.2)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    im = ax.imshow(pivot.values, vmin=0.0, vmax=1.0, aspect="auto", cmap="viridis")

    ax.set_title(
        "AB Test Heatmap - All Metrics", fontsize=14, fontweight="bold", pad=16
    )
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(pivot.columns.tolist(), rotation=30, ha="right")
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(pivot.index.tolist())

    for i in range(n_rows):
        for j in range(n_cols):
            v = pivot.values[i, j]
            if not pd.isna(v):
                color = "white" if v < 0.75 else "black"
                ax.text(
                    j,
                    i,
                    f"{v:.3f}",
                    ha="center",
                    va="center",
                    fontsize=10,
                    color=color,
                )

    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Score", rotation=270, labelpad=15)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved heatmap: {out_path.resolve()}")


def plot_delta_vs_baseline(
    df: pd.DataFrame,
    metric_order: list[str],
    baseline_variant: str,
    out_path: Path,
) -> None:
    sub = df[df["metric"].isin(metric_order)].copy()
    if sub.empty:
        print("[Warn] No data for delta heatmap.")
        return

    pivot = sub.pivot_table(
        index="variant", columns="metric", values="value", aggfunc="mean"
    ).reindex(columns=metric_order)

    pivot = pivot.loc[sorted(pivot.index.tolist(), key=variant_sort_key)]

    if baseline_variant not in pivot.index:
        print(f"[Warn] Baseline variant '{baseline_variant}' not found.")
        return

    delta = pivot.subtract(pivot.loc[baseline_variant], axis=1)
    delta = delta.drop(index=baseline_variant, errors="ignore")

    if delta.empty:
        print("[Warn] Delta result is empty.")
        return

    n_rows, n_cols = delta.shape
    fig_w = max(12, n_cols * 1.2)
    fig_h = max(3, n_rows * 1.2)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    vmax = max(abs(delta.min().min()), abs(delta.max().max()))
    vmax = max(vmax, 0.05)

    im = ax.imshow(delta.values, vmin=-vmax, vmax=vmax, aspect="auto", cmap="bwr")

    ax.set_title(
        f"AB Test Delta vs {baseline_variant.upper()}",
        fontsize=14,
        fontweight="bold",
        pad=16,
    )
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(delta.columns.tolist(), rotation=30, ha="right")
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(delta.index.tolist())

    for i in range(n_rows):
        for j in range(n_cols):
            v = delta.values[i, j]
            if not pd.isna(v):
                color = "white" if abs(v) > vmax * 0.45 else "black"
                ax.text(
                    j,
                    i,
                    f"{v:+.3f}",
                    ha="center",
                    va="center",
                    fontsize=10,
                    color=color,
                )

    cbar = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Delta", rotation=270, labelpad=15)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved delta heatmap: {out_path.resolve()}")


def plot_variant_profile_lines(
    df: pd.DataFrame,
    source: str,
    metric_order: list[str],
    out_path: Path,
    title: str,
) -> None:
    sub = df[(df["source"] == source) & (df["metric"].isin(metric_order))].copy()
    if sub.empty:
        print(f"[Warn] No data for source={source}")
        return

    pivot = sub.pivot_table(
        index="variant", columns="metric", values="value", aggfunc="mean"
    ).reindex(columns=metric_order)
    pivot = pivot.loc[sorted(pivot.index.tolist(), key=variant_sort_key)]

    xs = list(range(len(pivot.columns)))
    fig, ax = plt.subplots(figsize=(10, 5))

    for variant in pivot.index:
        ys = pivot.loc[variant].tolist()
        ax.plot(xs, ys, marker="o", linewidth=2, label=variant)
        for x, y in zip(xs, ys):
            ax.text(x, y + 0.015, f"{y:.3f}", ha="center", va="bottom", fontsize=9)

    ax.set_title(title, fontsize=14, fontweight="bold")
    ax.set_xlabel("Metric")
    ax.set_ylabel("Score")
    ax.set_ylim(0, 1.05)
    ax.set_xticks(xs)
    ax.set_xticklabels(pivot.columns.tolist(), rotation=25, ha="right")
    ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.6)
    ax.legend(title="Variant", frameon=False)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"[OK] Saved profile line chart: {out_path.resolve()}")


def plot_three_dimensions_bar(df: pd.DataFrame, out_path: Path) -> None:
    """繪製 AB Test 的三大面向長條圖"""
    n_cols = len(THREE_DIMENSIONS)
    fig_width = 7.0 * n_cols
    fig, axes = plt.subplots(1, n_cols, figsize=(fig_width, 6.5))

    if n_cols == 1:
        axes = [axes]

    fig.suptitle(
        "Three Dimensions Performance - AB Test",
        fontsize=20,
        fontweight="bold",
        y=0.98,
    )

    colors = ["#66c2a5", "#fc8d62", "#8da0cb", "#e78ac3", "#a6d854", "#ffd92f"]

    for idx, (dim_name, metrics) in enumerate(THREE_DIMENSIONS.items()):
        ax = axes[idx]

        # 過濾屬於該面向的指標
        sub = df[df["metric"].isin(metrics)].copy()

        if sub.empty:
            ax.text(
                0.5, 0.5, "No Data", ha="center", va="center", fontsize=14, color="gray"
            )
            ax.set_title(dim_name, fontsize=16, fontweight="bold")
            ax.axis("off")
            continue

        # 計算每個版本在該面向的平均分數
        pivot = sub.groupby("variant")["value"].mean().reset_index()
        pivot["sort_key"] = pivot["variant"].apply(variant_sort_key)
        pivot = pivot.sort_values("sort_key")

        x_labels = pivot["variant"].tolist()
        y_values = pivot["value"].tolist()

        # 繪製長條圖，給不同版本不同的顏色
        bars = ax.bar(x_labels, y_values, width=0.6, color=colors[: len(x_labels)])

        # 動態計算 Y 軸起點放大差異
        if len(y_values) > 0 and min(y_values) > 0:
            y_min = max(0.0, min(y_values) - 0.08)
        else:
            y_min = 0.4

        ax.set_title(dim_name, fontsize=16, fontweight="bold")
        ax.set_xlabel("Variants", fontsize=12)
        ax.set_ylabel("Average Score", fontsize=12)
        ax.set_ylim(y_min, 1.05)
        ax.tick_params(axis="x", labelsize=11)
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        # 標註數字
        for bar in bars:
            val = bar.get_height()
            if val > 0:
                ax.annotate(
                    f"{val:.3f}",
                    (bar.get_x() + bar.get_width() / 2.0, val),
                    ha="center",
                    va="bottom",
                    xytext=(0, 5),
                    textcoords="offset points",
                    fontsize=11,
                )

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"[OK] Saved 3-Dimensions Bar Chart: {out_path.resolve()}")


# ============================
# Main
# ============================


def main() -> None:
    ensure_outdir(OUTDIR)

    ragas_rows = load_metric_json(RAGAS_PATH, "ragas")
    trad_rows = load_metric_json(TRAD_PATH, "traditional")

    all_rows = ragas_rows + trad_rows
    if not all_rows:
        print("No data found. Please check your AB test JSON paths.")
        return

    df = pd.DataFrame(all_rows)

    # grouped bars
    plot_grouped_bar(
        df=df,
        source="ragas",
        metric_order=RAGAS_METRICS,
        out_path=OUTDIR / "ab_bar_ragas.png",
        title="AB Test - RAGAS Metrics",
    )

    plot_grouped_bar(
        df=df,
        source="traditional",
        metric_order=TRAD_METRICS,
        out_path=OUTDIR / "ab_bar_traditional.png",
        title="AB Test - Traditional Metrics",
    )

    # line profiles
    plot_variant_profile_lines(
        df=df,
        source="ragas",
        metric_order=RAGAS_METRICS,
        out_path=OUTDIR / "ab_line_ragas.png",
        title="AB Test - RAGAS Variant Profiles",
    )

    plot_variant_profile_lines(
        df=df,
        source="traditional",
        metric_order=TRAD_METRICS,
        out_path=OUTDIR / "ab_line_traditional.png",
        title="AB Test - Traditional Variant Profiles",
    )

    # combined heatmap
    plot_heatmap_all_metrics(
        df=df,
        metric_order=ALL_METRICS,
        out_path=OUTDIR / "ab_heatmap_all_metrics.png",
    )

    # delta vs baseline
    plot_delta_vs_baseline(
        df=df,
        metric_order=ALL_METRICS,
        baseline_variant="v1",
        out_path=OUTDIR / "ab_delta_vs_v1.png",
    )

    # 🚀 NEW: Three Dimensions
    plot_three_dimensions_bar(df=df, out_path=OUTDIR / "ab_three_dimensions.png")

    print(f"\n✨ All AB test charts saved under: {OUTDIR.resolve()}")


if __name__ == "__main__":
    main()
