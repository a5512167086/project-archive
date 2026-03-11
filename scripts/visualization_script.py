from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

import matplotlib.pyplot as plt
import pandas as pd

RAGAS_INPUT_PATH = Path(r"./data/eval_result/summary_report.json")
TRAD_INPUT_PATH = Path(r"./data/eval_result/traditional_summary_report.json")
OUTDIR = Path(r"./data/chart")

# ----------------------------
# Parsing
# ----------------------------


@dataclass(frozen=True)
class RunKey:
    model: str
    retrieval: str
    module: str


def parse_run_key(key: str) -> RunKey:
    parts = key.split("_")
    if len(parts) < 3:
        raise ValueError(f"Unrecognized key format: {key}")

    module = parts[-1]
    retrieval = parts[-2]
    model = "_".join(parts[:-2])

    return RunKey(model=model, retrieval=retrieval, module=module)


def normalize_module(module: str) -> str:
    module = module.strip().lower()
    mapping = {
        "baseline": "baseline",
        "rerank": "rerank",
        "rewrite": "rewrite",
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
) -> None:
    df_plot = df[df["metric"].isin(metric_order)].copy()
    if df_plot.empty:
        return

    df_plot["dataset"] = df_plot.apply(
        lambda r: f"{r['model']} | {r['module']}", axis=1
    )
    retrievals = [r for r in retrieval_order if r in set(df_plot["retrieval"].unique())]

    def dataset_sort_key(s: str) -> tuple:
        model, module = [x.strip() for x in s.split("|")]
        module_rank = {m: i for i, m in enumerate(module_order)}.get(module, 99)
        return (module_rank, model, s)

    for retrieval in retrievals:
        sub = df_plot[df_plot["retrieval"] == retrieval].copy()
        pivot = sub.pivot_table(
            index="dataset", columns="metric", values="value", aggfunc="mean"
        ).reindex(columns=metric_order)
        pivot = pivot.loc[sorted(pivot.index, key=dataset_sort_key)]

        fig, ax = plt.subplots(figsize=(12, 6))
        xs = list(range(len(metric_order)))
        for dataset in pivot.index:
            ys = pivot.loc[dataset].tolist()
            ax.plot(xs, ys, marker="o", linewidth=1.5, label=dataset)

        ax.set_title(f"{group_name} Metrics (retrieval={retrieval})")
        ax.set_xlabel("Metric")
        ax.set_ylabel("Score")
        ax.set_ylim(0, 1.05)
        ax.set_xticks(xs)
        ax.set_xticklabels(metric_order, rotation=25, ha="right")
        ax.grid(axis="y", linestyle="--", linewidth=0.5, alpha=0.6)
        ax.legend(
            title="Dataset",
            loc="center left",
            bbox_to_anchor=(1.02, 0.5),
            frameon=False,
        )

        plt.tight_layout()
        out_path = outdir / f"lines_{group_name.lower()}_{retrieval}.png"
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
        lambda r: f"{r['model']} | {r['retrieval']} | {r['module']}", axis=1
    )

    pivot = df.pivot_table(
        index="run_id", columns="metric", values="value", aggfunc="mean"
    ).reindex(columns=metric_order)

    retrieval_rank = {r: i for i, r in enumerate(retrieval_order)}
    module_rank = {m: i for i, m in enumerate(module_order)}

    def sort_key(run_id: str) -> tuple:
        model, retrieval, module = [x.strip() for x in run_id.split("|")]
        return (
            model,
            retrieval_rank.get(retrieval, 99),
            module_rank.get(module, 99),
            run_id,
        )

    pivot = pivot.loc[sorted(pivot.index, key=sort_key)]

    n_rows, n_cols = pivot.shape
    fig_w = max(12, 1.2 * n_cols + 4)
    fig_h = max(6, 0.4 * n_rows + 2)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    im = ax.imshow(pivot.values, vmin=0.0, vmax=1.0, aspect="auto", cmap="viridis")

    ax.set_title("Combined Evaluation Heatmap (RAGAS & Traditional)", pad=20)
    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(pivot.columns.tolist(), rotation=35, ha="right")
    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(pivot.index.tolist())

    for i in range(n_rows):
        for j in range(n_cols):
            v = pivot.values[i, j]
            if not pd.isna(v):
                color = "white" if v < 0.5 else "black"
                ax.text(
                    j, i, f"{v:.3f}", ha="center", va="center", fontsize=8, color=color
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


def load_and_preprocess(path: Path) -> List[dict]:
    if not path.exists():
        print(f"[Warn] File not found: {path}")
        return []

    data = json.loads(path.read_text(encoding="utf-8"))
    rows = []
    for k, metrics in data.items():
        rk = parse_run_key(k)
        module = normalize_module(rk.module)
        for metric_name, value in metrics.items():
            # 這裡動態把指標名稱轉小寫，並把底線換成空格
            clean_metric_name = metric_name.lower().replace("_", " ")
            rows.append({
                "model": rk.model,
                "retrieval": rk.retrieval,
                "module": module,
                "metric": clean_metric_name,
                "value": float(value),
            })
    return rows


def main() -> None:
    ensure_outdir(OUTDIR)

    ragas_rows = load_and_preprocess(RAGAS_INPUT_PATH)
    trad_rows = load_and_preprocess(TRAD_INPUT_PATH)

    if not ragas_rows and not trad_rows:
        print("No data found to plot.")
        return

    df = pd.DataFrame(ragas_rows + trad_rows)

    # 修改這裡的名稱以匹配轉換後的乾淨格式
    ragas_metrics = [
        "answer relevancy",
        "answer correctness",
        "context precision",
        "context recall",
        "faithfulness",
    ]
    trad_metrics = [
        "precision",
        "recall",
        "f1 score",
        "rouge-1",
        "rouge-l",
        "bertscore",
    ]
    all_metrics = ragas_metrics + trad_metrics

    retrieval_order = ["lexical", "vector", "hybrid"]
    module_order = ["baseline", "rerank", "rewrite", "rerank+rewrite"]

    plot_by_retrieval_lines(
        df, OUTDIR, retrieval_order, ragas_metrics, module_order, "RAGAS"
    )
    plot_by_retrieval_lines(
        df, OUTDIR, retrieval_order, trad_metrics, module_order, "Traditional"
    )
    plot_one_heatmap(df, OUTDIR, all_metrics, retrieval_order, module_order)

    print(f"\n✨ All charts saved under: {OUTDIR.resolve()}")


if __name__ == "__main__":
    main()
