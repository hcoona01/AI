"""Baseline demand forecasting heuristics: seasonal-naive and 3-term moving average."""

from __future__ import annotations

from typing import Any


def seasonal_naive(
    history: list[dict[str, Any]],
    course_id: str,
    target_season: str,
) -> float | None:
    """Predict next occurrence of a season by returning the most recent same-season enrollment.

    Args:
        history: List of enrollment records (sorted ascending by term_index).
        course_id: Course to forecast.
        target_season: Season to predict ('Fall', 'Spring', 'Summer').

    Returns:
        Most recent same-season enrollment, or None if no prior season match.
    """
    matching = [
        r["enrolled_students"]
        for r in history
        if r["course_id"] == course_id and r["season"] == target_season
    ]
    return float(matching[-1]) if matching else None


def moving_average_3(
    history: list[dict[str, Any]],
    course_id: str,
) -> float | None:
    """Compute 3-term moving average over the most recent three enrollment observations.

    Args:
        history: List of enrollment records sorted ascending by term_index.
        course_id: Course to forecast.

    Returns:
        Mean of the last 3 enrollments, or all available if fewer than 3.
        Returns None if no observations exist.
    """
    observations = [
        r["enrolled_students"]
        for r in history
        if r["course_id"] == course_id
    ]
    if not observations:
        return None
    last_k = observations[-3:]
    return float(sum(last_k) / len(last_k))


def evaluate_baseline(
    val_records: list[dict[str, Any]],
    train_records: list[dict[str, Any]],
    mode: str = "moving_average_3",
) -> dict[str, float]:
    """Compute MAE and RMSE for a baseline on validation records.

    Args:
        val_records: Validation set records (held-out, time-ordered).
        train_records: Training set records (used for lookback).
        mode: 'moving_average_3' or 'seasonal_naive'.

    Returns:
        Dict with 'mae' and 'rmse'.
    """
    import math

    errors: list[float] = []

    for rec in val_records:
        cid = rec["course_id"]
        actual = float(rec["enrolled_students"])

        # Only use train records with earlier term_index as context
        context = [
            r for r in train_records
            if r["course_id"] == cid and r["term_index"] < rec["term_index"]
        ]

        if mode == "seasonal_naive":
            pred = seasonal_naive(context, cid, rec["season"])
        else:
            pred = moving_average_3(context, cid)

        if pred is not None:
            errors.append(actual - pred)

    if not errors:
        return {"mae": float("nan"), "rmse": float("nan")}

    mae = float(sum(abs(e) for e in errors) / len(errors))
    rmse = float(math.sqrt(sum(e ** 2 for e in errors) / len(errors)))
    return {"mae": round(mae, 4), "rmse": round(rmse, 4)}
