from __future__ import annotations

import json
import logging
import math
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Tuple

# -----------------------------------------------------------------------------
# 設定
# -----------------------------------------------------------------------------
RESULT_DIR = Path("data/eval_result")
RESULT_PATTERN = "ragas_eval_*.json"
SUMMARY_REPORT_PATH = RESULT_DIR / "summary_report.json"

METRIC_KEYS = [
    "answer_relevancy",
    "answer_correctness",
    "context_precision",
    "context_recall",
    "faithfulness",
]

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("summary_report_builder")


# -----------------------------------------------------------------------------
# 分數清洗
# -----------------------------------------------------------------------------
def _is_nan(x: Any) -> bool:
    return isinstance(x, float) and math.isnan(x)


def _to_float_or_zero(x: Any) -> float:
    """
    規則：NaN / None / 無法轉成 float / 字串 'nan' 'null' 都視為 0.0
    """
    if x is None:
        return 0.0
    if _is_nan(x):
        return 0.0

    if isinstance(x, dict):
        if "value" in x:
            return _to_float_or_zero(x.get("value"))
        return 0.0

    if isinstance(x, (int, float)):
        v = float(x)
        return 0.0 if _is_nan(v) else v

    if isinstance(x, str):
        s = x.strip().lower()
        if s in ("", "nan", "null", "none"):
            return 0.0
        try:
            v = float(s)
            return 0.0 if _is_nan(v) else v
        except Exception:
            return 0.0

    return 0.0


# -----------------------------------------------------------------------------
# 檔名解析：ragas_eval_xxx.json -> xxx
# -----------------------------------------------------------------------------
def _dataset_name_from_filename(filename: str) -> str:
    stem = Path(filename).stem
    m = re.match(r"ragas_eval_(.+)$", stem)
    return m.group(1) if m else stem


# -----------------------------------------------------------------------------
# 讀取 details 並重算平均
# -----------------------------------------------------------------------------
def _extract_details(obj: Any) -> List[Dict[str, Any]]:
    """
    兼容：
    - { ..., "details": [ ... ] }
    - 或 obj 本身就是 list
    """
    if isinstance(obj, dict):
        details = obj.get("details")
        return details if isinstance(details, list) else []
    if isinstance(obj, list):
        return obj
    return []


def _compute_averages_from_details(
    details: List[Dict[str, Any]],
) -> Tuple[Dict[str, float], int]:
    """
    固定以 METRIC_KEYS 算平均：
    - 每一筆若缺該 metric -> 當 0
    - 每一筆若是 NaN/null -> 當 0
    - 分母 = len(details)
    """
    n = len(details)
    if n == 0:
        return {k: 0.0 for k in METRIC_KEYS}, 0

    sums = defaultdict(float)

    for item in details:
        scores = item.get("scores") if isinstance(item, dict) else None
        scores = scores if isinstance(scores, dict) else {}

        for k in METRIC_KEYS:
            sums[k] += _to_float_or_zero(scores.get(k))

    avgs = {k: round(sums[k] / n, 4) for k in METRIC_KEYS}
    return avgs, n


# -----------------------------------------------------------------------------
# 主流程：掃描 eval_result 產 summary_report
# -----------------------------------------------------------------------------
def build_summary_report(
    result_dir: Path = RESULT_DIR,
    pattern: str = RESULT_PATTERN,
    output_path: Path = SUMMARY_REPORT_PATH,
) -> Dict[str, Dict[str, float]]:
    if not result_dir.exists() or not result_dir.is_dir():
        raise FileNotFoundError(
            f"Result dir not found or not a directory: {result_dir}"
        )

    files = sorted(result_dir.glob(pattern))
    logger.info(f"Scanning: {result_dir}/{pattern} -> {len(files)} files")

    report: Dict[str, Dict[str, float]] = {}

    for fp in files:
        dataset_name = _dataset_name_from_filename(fp.name)

        try:
            with fp.open("r", encoding="utf-8") as f:
                obj = json.load(f)
        except Exception as e:
            logger.error(f"Failed to read JSON: {fp} | err={e}")
            continue

        details = _extract_details(obj)
        avgs, n = _compute_averages_from_details(details)

        report[dataset_name] = avgs
        logger.info(f"Aggregated: {dataset_name} | items={n} | avgs={avgs}")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    logger.info(f"Saved summary report: {output_path}")
    return report


def main() -> None:
    build_summary_report()


if __name__ == "__main__":
    main()
