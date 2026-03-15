from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import pandas as pd

# 更新路徑定義，指向對應的資料夾
BASE_EVAL_DIR = Path(r"./data/eval_result")
SINGLE_TURN_DIR = BASE_EVAL_DIR / "single_turn"
MULTI_TURN_DIR = BASE_EVAL_DIR / "multi_turn"
OUTDIR = Path(r"./data/chart")

# ----------------------------
# Parsing
# ----------------------------


@dataclass(frozen=True)
class RunKey:
    retrieval: str
    module: str


def parse_run_key(key: str) -> RunKey:
    # 1. 判斷 Retrieval 類型
    retrievals = ["vector", "lexical", "hybrid"]
    retrieval_type = "unknown"
    for r in retrievals:
        if f"_{r}_" in key or key.endswith(f"_{r}"):
            retrieval_type = r
            break

    # 2. 判斷 Module (取 retrieval 之後的所有字串)
    if retrieval_type != "unknown":
        parts = key.split(f"_{retrieval_type}")
        if len(parts) > 1 and parts[1]:
            # parts[1] 會像是 "_baseline" 或 "_rerank_rewrite"
            module_str = parts[1].lstrip("_")
        else:
            module_str = "baseline"
    else:
        module_str = "unknown"

    return RunKey(retrieval=retrieval_type, module=module_str)


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


def plot_by_retrieval_lines(
    df: pd.DataFrame,
    outdir: Path,
    retrieval_order: List[str],
    metric_order: List[str],
    module_order: List[str],
    group_name: str,
    turn_type: str,
) -> None:
    df_plot = df[
        (df["metric"].isin(metric_order)) & (df["turn_type"] == turn_type)
    ].copy()
    if df_plot.empty:
        return

    df_plot["dataset"] = df_plot["module"]
    retrievals = [r for r in retrieval_order if r in set(df_plot["retrieval"].unique())]

    def dataset_sort_key(module_name: str) -> int:
        return {m: i for i, m in enumerate(module_order)}.get(module_name, 99)

    for retrieval in retrievals:
        sub = df_plot[df_plot["retrieval"] == retrieval].copy()
        pivot = sub.pivot_table(
            index="dataset", columns="metric", values="value", aggfunc="mean"
        ).reindex(columns=[m for m in metric_order if m in sub["metric"].values])
        pivot = pivot.loc[sorted(pivot.index, key=dataset_sort_key)]

        fig, ax = plt.subplots(figsize=(10, 5))
        xs = list(range(len(pivot.columns)))
        for dataset in pivot.index:
            ys = pivot.loc[dataset].tolist()
            ax.plot(xs, ys, marker="o", linewidth=1.5, label=dataset)

        ax.set_title(
            f"{group_name} Metrics - {turn_type} (Retrieval: {retrieval.capitalize()})"
        )
        ax.set_xlabel("Metric")
        ax.set_ylabel("Score")
        ax.set_ylim(0.4, 1.05)
        ax.set_xticks(xs)
        ax.set_xticklabels(pivot.columns, rotation=25, ha="right")
        ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.6)
        ax.legend(
            title="Module",
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
        )

        plt.tight_layout()
        out_path = (
            outdir / f"lines_{group_name.lower()}_{turn_type.lower()}_{retrieval}.png"
        )
        plt.savefig(out_path, dpi=200, bbox_inches="tight")
        plt.close()


def plot_one_heatmap(
    df: pd.DataFrame,
    outdir: Path,
    metric_order: List[str],
    retrieval_order: List[str],
    module_order: List[str],
) -> None:
    df = df.copy()
    df["run_id"] = df.apply(
        lambda r: f"{r['turn_type']} | {r['retrieval']} | {r['module']}", axis=1
    )

    valid_metrics = [m for m in metric_order if m in df["metric"].unique()]
    pivot = df.pivot_table(
        index="run_id", columns="metric", values="value", aggfunc="mean"
    ).reindex(columns=valid_metrics)

    retrieval_rank = {r: i for i, r in enumerate(retrieval_order)}
    module_rank = {m: i for i, m in enumerate(module_order)}
    turn_rank = {"Single-Turn": 0, "Multi-Turn": 1}

    def sort_key(run_id: str) -> tuple:
        turn, retrieval, module = [x.strip() for x in run_id.split("|")]
        return (
            turn_rank.get(turn, 99),
            retrieval_rank.get(retrieval, 99),
            module_rank.get(module, 99),
        )

    pivot = pivot.loc[sorted(pivot.index, key=sort_key)]

    n_rows, n_cols = pivot.shape
    fig_w = max(12, 1.2 * n_cols + 4)
    fig_h = max(6, 0.4 * n_rows + 2)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    im = ax.imshow(pivot.values, vmin=0.5, vmax=1.0, aspect="auto", cmap="viridis")

    ax.set_title("Combined Evaluation Heatmap (Single vs Multi-Turn)", pad=20)
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
                    j, i, f"{v:.3f}", ha="center", va="center", fontsize=9, color=color
                )

    fig.colorbar(im, ax=ax, label="Score", fraction=0.02, pad=0.02)
    plt.tight_layout()
    out_path = outdir / "all_results_heatmap_combined.png"
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"[OK] Saved Combined Heatmap: {out_path.resolve()}")


# ----------------------------
# Main Logic
# ----------------------------


def load_and_preprocess(path: Path, turn_type: str) -> List[dict]:
    """讀取 JSON 並在過程中直接標記 turn_type"""
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
                "retrieval": rk.retrieval,
                "module": module,
                "metric": clean_metric_name,
                "value": float(value),
            })
    return rows


def main() -> None:
    ensure_outdir(OUTDIR)

    # 分別從兩個資料夾讀取四份檔案
    ragas_single = load_and_preprocess(
        SINGLE_TURN_DIR / "summary_report.json", "Single-Turn"
    )
    trad_single = load_and_preprocess(
        SINGLE_TURN_DIR / "traditional_summary_report.json", "Single-Turn"
    )

    ragas_multi = load_and_preprocess(
        MULTI_TURN_DIR / "summary_report.json", "Multi-Turn"
    )
    trad_multi = load_and_preprocess(
        MULTI_TURN_DIR / "traditional_summary_report.json", "Multi-Turn"
    )

    all_rows = ragas_single + trad_single + ragas_multi + trad_multi

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
    module_order = ["baseline", "rerank", "rewrite", "rerank+rewrite"]
    turn_types = ["Single-Turn", "Multi-Turn"]

    for turn in turn_types:
        plot_by_retrieval_lines(
            df, OUTDIR, retrieval_order, ragas_metrics, module_order, "RAGAS", turn
        )
        plot_by_retrieval_lines(
            df, OUTDIR, retrieval_order, trad_metrics, module_order, "Traditional", turn
        )

    plot_one_heatmap(df, OUTDIR, all_metrics, retrieval_order, module_order)

    print(f"\n✨ All charts saved under: {OUTDIR.resolve()}")


if __name__ == "__main__":
    main()
