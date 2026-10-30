"""Evaluation metrics: MAE, RMSE, WAPE, and P10-P90 interval coverage."""

from __future__ import annotations

import math


def compute_metrics(
    y_true: list[float],
    p10: list[float],
    p50: list[float],
    p90: list[float],
) -> dict[str, float]:
    """Compute quantile forecast evaluation metrics.

    Args:
        y_true: Actual enrollment values.
        p10: 10th percentile forecasts.
        p50: 50th percentile (median) forecasts.
        p90: 90th percentile forecasts.

    Returns:
        Dict with keys: mae, rmse, wape, p10_p90_coverage.
    """
    n = len(y_true)
    if n == 0:
        return {
            "mae": float("nan"),
            "rmse": float("nan"),
            "wape": float("nan"),
            "p10_p90_coverage": float("nan"),
        }

    abs_errors = [abs(y - p) for y, p in zip(y_true, p50)]
    sq_errors = [(y - p) ** 2 for y, p in zip(y_true, p50)]

    mae = sum(abs_errors) / n
    rmse = math.sqrt(sum(sq_errors) / n)

    total_actual = sum(y_true)
    wape = (sum(abs_errors) / total_actual * 100.0) if total_actual > 0 else float("nan")

    in_interval = sum(1 for y, lo, hi in zip(y_true, p10, p90) if lo <= y <= hi)
    coverage = in_interval / n

    return {
        "mae": round(mae, 4),
        "rmse": round(rmse, 4),
        "wape": round(wape, 4),
        "p10_p90_coverage": round(coverage, 4),
    }
