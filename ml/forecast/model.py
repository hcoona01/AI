"""LightGBM quantile regression training for P10, P50, and P90 section demand."""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd

FEATURE_NAMES: list[str] = [
    "credits",
    "is_lab",
    "is_elective",
    "level_enc",
    "lag1_enrolled",
    "lag2_enrolled",
    "rolling3_mean",
    "term_index_norm",
    "season_enc",
    "prereq_cohort_size",
]

LEVEL_ENC: dict[str, int] = {"undergraduate": 0, "graduate": 1, "doctoral": 2}
SEASON_ENC: dict[str, int] = {"Summer": 0, "Spring": 1, "Fall": 2}
TERM_INDEX_SCALE: float = 12.0
SECTION_CAP_DEFAULT: int = 50


def _is_elective(course_code: str) -> int:
    """Return 1 if numeric suffix of course_code >= 300, else 0."""
    match = re.search(r"\d+", course_code)
    if match is None:
        return 0
    return 1 if int(match.group()) >= 300 else 0


def build_feature_row(
    course_record: dict[str, Any],
    context: list[dict[str, Any]],
    target_term_index: int,
    target_season: str,
) -> list[float]:
    """Build a single feature row for a (course, target_term) pair."""
    credits = float(course_record.get("credits", 3))
    is_lab = float(1 if course_record.get("is_lab", False) else 0)
    course_code = course_record.get("course_code", "")
    is_elective = float(_is_elective(course_code))
    level_enc = float(LEVEL_ENC.get(course_record.get("level", "undergraduate"), 0))

    enrollments = [r["enrolled_students"] for r in context]

    lag1 = float(enrollments[-1]) if len(enrollments) >= 1 else 0.0
    lag2 = float(enrollments[-2]) if len(enrollments) >= 2 else 0.0
    rolling3 = float(np.mean(enrollments[-3:])) if enrollments else 0.0

    term_index_norm = float(target_term_index) / TERM_INDEX_SCALE
    season_enc = float(SEASON_ENC.get(target_season, 0))
    prereq_cohort_size = lag1

    return [
        credits,
        is_lab,
        is_elective,
        level_enc,
        lag1,
        lag2,
        rolling3,
        term_index_norm,
        season_enc,
        prereq_cohort_size,
    ]


def build_feature_df(
    history: list[dict[str, Any]],
    target_records: list[dict[str, Any]],
) -> tuple[pd.DataFrame, list[float]]:
    """Build a feature DataFrame for target records using history for lookback."""
    from collections import defaultdict

    hist_by_course: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for rec in history:
        hist_by_course[rec["course_id"]].append(rec)
    for cid in hist_by_course:
        hist_by_course[cid].sort(key=lambda r: r["term_index"])

    rows: list[list[float]] = []
    targets: list[float] = []

    for rec in target_records:
        cid = rec["course_id"]
        ti = rec["term_index"]
        season = rec["season"]

        context = [r for r in hist_by_course[cid] if r["term_index"] < ti]
        row = build_feature_row(rec, context, ti, season)
        rows.append(row)
        targets.append(float(rec.get("enrolled_students", 0.0)))

    df = pd.DataFrame(rows, columns=FEATURE_NAMES)
    for col in df.columns:
        df[col] = df[col].astype("float32")

    return df, targets


def train_quantile_models(
    X_train: np.ndarray,
    y_train: list[float] | np.ndarray,
    random_state: int = 42,
) -> dict[str, Any]:
    """Train three LightGBM quantile regressors for P10, P50, P90.

    Adheres to compute budget: n_jobs=1, num_leaves<=15, n_estimators<=300.
    """
    import lightgbm as lgb

    alphas = {"p10": 0.1, "p50": 0.5, "p90": 0.9}
    models: dict[str, Any] = {}

    y_arr = np.asarray(y_train, dtype=np.float32)

    for key, alpha in alphas.items():
        params = {
            "objective": "quantile",
            "alpha": alpha,
            "n_jobs": 1,
            "num_leaves": 15,
            "n_estimators": 150,
            "random_state": random_state,
            "verbose": -1,
            "min_child_samples": 5,
            "learning_rate": 0.05,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
        }
        model = lgb.LGBMRegressor(**params)
        model.fit(X_train, y_arr, feature_name=FEATURE_NAMES)
        models[key] = model.booster_

    return models
