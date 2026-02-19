from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import matplotlib.pyplot as plt
import pandas as pd

INPUT_PATH = Path(r"./data/eval_result/summary_report.json")
OUTDIR = Path(r"./data/chart")


# ----------------------------
# Parsing
# ----------------------------


@dataclass(frozen=True)
class RunKey:
    model: str
    retrieval: str
    module: str


KEY_RE = re.compile(r"^(?P<prefix>.+)_wke_opt_(?P<rest>.+)_result$")


def parse_run_key(key: str) -> RunKey:
    m = KEY_RE.match(key)
    if not m:
        raise ValueError(f"Unrecognized key format: {key}")

    model = m.group("prefix")
    rest = m.group("rest")
    parts = rest.split("_", 1)
    if len(parts) != 2:
        raise ValueError(f"Unrecognized rest format: {rest} (from key={key})")

    retrieval, module = parts[0], parts[1]
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
# Plot: 3 figures (by retrieval)
#   x = metrics
#   line = dataset (model | module)
# ----------------------------


def plot_by_retrieval_lines_dataset_over_metrics(
    df: pd.DataFrame,
    outdir: Path,
    retrieval_order: List[str],
    metric_order: List[str],
    module_order: List[str],
) -> None:
    df = df.copy()

    # dataset = model + module
    df["dataset"] = df.apply(lambda r: f"{r['model']} | {r['module']}", axis=1)

    retrievals = [r for r in retrieval_order if r in set(df["retrieval"].unique())]
    modules = [m for m in module_order if m in set(df["module"].unique())]

    def dataset_sort_key(s: str) -> tuple:
        # s = "model | module"
        model, module = [x.strip() for x in s.split("|")]
        module_rank = {m: i for i, m in enumerate(modules)}.get(module, 99)
        return (module_rank, model, s)

    for retrieval in retrievals:
        sub = df[df["retrieval"] == retrieval].copy()
        if sub.empty:
            continue

        pivot = sub.pivot_table(
            index="dataset", columns="metric", values="value", aggfunc="mean"
        ).reindex(columns=metric_order)
        pivot = pivot.loc[sorted(pivot.index, key=dataset_sort_key)]

        fig, ax = plt.subplots(figsize=(12, 6))

        xs = list(range(len(metric_order)))
        for dataset in pivot.index:
            ys = pivot.loc[dataset].tolist()
            ax.plot(xs, ys, marker="o", linewidth=1.5, label=dataset)

        ax.set_title(
            f"RAGAS Metrics (retrieval={retrieval}) | lines=datasets(model|module)"
        )
        ax.set_xlabel("Metric")
        ax.set_ylabel("Score")
        ax.set_ylim(0, 1.0)
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
        out_path = outdir / f"lines_over_metrics__{retrieval}.png"
        plt.savefig(out_path, dpi=200, bbox_inches="tight")
        plt.close()
        print(f"[OK] Saved: {out_path.resolve()}")


# ----------------------------
# Plot: 1 heatmap (all runs)
#   rows = model | retrieval | module
#   cols = metrics
# ----------------------------


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
    fig_w = max(10, 1.8 * n_cols + 6)
    fig_h = max(6, 0.35 * n_rows + 2)

    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    im = ax.imshow(pivot.values, vmin=0.0, vmax=1.0, aspect="auto")

    ax.set_title("RAGAS Summary Heatmap (model | retrieval | module)", pad=12)
    ax.set_xlabel("Metric")
    ax.set_ylabel("Run")

    ax.set_xticks(range(n_cols))
    ax.set_xticklabels(pivot.columns.tolist(), rotation=25, ha="right")

    ax.set_yticks(range(n_rows))
    ax.set_yticklabels(pivot.index.tolist())

    # Grid lines between cells
    ax.set_xticks([x - 0.5 for x in range(1, n_cols)], minor=True)
    ax.set_yticks([y - 0.5 for y in range(1, n_rows)], minor=True)
    ax.grid(which="minor", linestyle="-", linewidth=0.3, alpha=0.3)
    ax.tick_params(which="minor", bottom=False, left=False)

    cbar = fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    cbar.set_label("Score")

    # Annotate each cell
    for i in range(n_rows):
        for j in range(n_cols):
            v = pivot.values[i, j]
            if pd.isna(v):
                continue
            ax.text(j, i, f"{v:.3f}", ha="center", va="center", fontsize=8)

    out_path = outdir / "all_results_heatmap.png"
    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close()
    print(f"[OK] Saved: {out_path.resolve()}")


# ----------------------------
# Main
# ----------------------------


def main() -> None:
    in_path = INPUT_PATH
    outdir = OUTDIR

    if not in_path.exists():
        raise FileNotFoundError(f"Input JSON not found: {in_path.resolve()}")

    ensure_outdir(outdir)
    data: Dict[str, Any] = json.loads(in_path.read_text(encoding="utf-8"))

    rows = []
    for k, metrics in data.items():
        rk = parse_run_key(k)
        module = normalize_module(rk.module)

        if not isinstance(metrics, dict):
            raise ValueError(
                f"Metrics value must be dict, got {type(metrics)} for key={k}"
            )

        for metric_name, value in metrics.items():
            rows.append({
                "model": rk.model,
                "retrieval": rk.retrieval,
                "module": module,
                "metric": metric_name,
                "value": float(value),
                "raw_key": k,
            })

    df = pd.DataFrame(rows)

    # Save flattened CSV
    csv_path = outdir / "results_flat.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"[OK] Wrote: {csv_path.resolve()}")

    retrieval_order = ["lexical", "vector", "hybrid"]
    metric_order = [
        "answer_relevancy",
        "answer_correctness",
        "context_precision",
        "context_recall",
        "faithfulness",
    ]
    module_order = ["baseline", "rerank", "rewrite", "rerank+rewrite"]

    # 3 line charts (by retrieval)
    plot_by_retrieval_lines_dataset_over_metrics(
        df=df,
        outdir=outdir,
        retrieval_order=retrieval_order,
        metric_order=metric_order,
        module_order=module_order,
    )

    # 1 heatmap (all runs)
    plot_one_heatmap(
        df=df,
        outdir=outdir,
        metric_order=metric_order,
        retrieval_order=retrieval_order,
        module_order=module_order,
    )

    print(f"[OK] Input: {in_path.resolve()}")
    print(f"[OK] Charts saved under: {outdir.resolve()}")


if __name__ == "__main__":
    main()
