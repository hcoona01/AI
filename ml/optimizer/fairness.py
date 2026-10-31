"""Fairness metrics computation for faculty workload distribution.

Provides:
- Gini coefficient of workload distribution across faculty and ranks
- Standard deviation of assigned contact/credit hours
- Max-min workload gap
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any

import numpy as np


def compute_gini(loads: list[float] | np.ndarray) -> float:
    """Compute the Gini coefficient of a distribution of workload hours.

    Args:
        loads: List or 1D array of assigned workload hours (non-negative).

    Returns:
        Gini coefficient in [0.0, 1.0]. A value of 0.0 represents perfect equality.
    """
    arr = np.asarray(loads, dtype=np.float64)
    arr = arr[arr >= 0.0]
    n = len(arr)
    if n <= 1:
        return 0.0

    total_sum = np.sum(arr)
    if total_sum == 0.0:
        return 0.0

    # Fast vectorized Gini calculation:
    # G = (2 * sum_{i=1}^n i * y_i) / (n * sum y) - (n + 1) / n
    sorted_arr = np.sort(arr)
    index = np.arange(1, n + 1, dtype=np.float64)
    gini = (2.0 * np.sum(index * sorted_arr)) / (n * total_sum) - (n + 1.0) / n
    return float(np.clip(gini, 0.0, 1.0))


def compute_standard_deviation(loads: list[float] | np.ndarray) -> float:
    """Compute the sample standard deviation of assigned workloads.

    Args:
        loads: List or array of workload hours.

    Returns:
        Standard deviation in hours (0.0 if fewer than 2 data points).
    """
    arr = np.asarray(loads, dtype=np.float64)
    if len(arr) <= 1:
        return 0.0
    return float(np.std(arr, ddof=1))


def compute_max_min_gap(loads: list[float] | np.ndarray) -> float:
    """Compute the difference between the maximum and minimum assigned workload hours.

    Args:
        loads: List or array of workload hours.

    Returns:
        Max-min gap in hours (0.0 if empty).
    """
    arr = np.asarray(loads, dtype=np.float64)
    if len(arr) == 0:
        return 0.0
    return float(np.max(arr) - np.min(arr))


def compute_fairness_summary(
    loads_by_faculty: dict[str, float],
    faculty_ranks: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Calculate comprehensive departmental fairness metrics, overall and by rank.

    Args:
        loads_by_faculty: Mapping of faculty_id -> assigned workload hours.
        faculty_ranks: Optional mapping of faculty_id -> academic appointment rank.

    Returns:
        Dictionary with overall gini, std_dev, max_min_gap, and breakdown by rank.
    """
    all_loads = list(loads_by_faculty.values())
    if not all_loads:
        return {
            "gini": 0.0,
            "std_dev": 0.0,
            "max_min_gap": 0.0,
            "mean_load": 0.0,
            "faculty_count": 0,
            "by_rank": {},
        }

    overall_gini = compute_gini(all_loads)
    overall_std = compute_standard_deviation(all_loads)
    overall_gap = compute_max_min_gap(all_loads)
    mean_load = float(sum(all_loads) / len(all_loads))

    by_rank: dict[str, dict[str, Any]] = {}
    if faculty_ranks:
        rank_loads: dict[str, list[float]] = defaultdict(list)
        for fid, load in loads_by_faculty.items():
            rank = faculty_ranks.get(fid, "Unknown")
            rank_loads[rank].append(load)

        for rank, r_loads in rank_loads.items():
            by_rank[rank] = {
                "gini": round(compute_gini(r_loads), 4),
                "std_dev": round(compute_standard_deviation(r_loads), 4),
                "max_min_gap": round(compute_max_min_gap(r_loads), 4),
                "mean_load": round(float(sum(r_loads) / len(r_loads)), 4),
                "faculty_count": len(r_loads),
            }

    return {
        "gini": round(overall_gini, 4),
        "std_dev": round(overall_std, 4),
        "max_min_gap": round(overall_gap, 4),
        "mean_load": round(mean_load, 4),
        "faculty_count": len(all_loads),
        "by_rank": by_rank,
    }
