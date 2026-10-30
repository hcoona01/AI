"""Offline training script: python ml/scripts/train.py  (make train).

NEVER called by the backend server.
Trains three LightGBM quantile regressors and serializes all artifacts.
"""

from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup: ensure ml/ and repo root are importable
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve()
REPO_ROOT = SCRIPT_DIR.parents[2]
ML_DIR = REPO_ROOT / "ml"

for p in [str(REPO_ROOT), str(ML_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

# ---------------------------------------------------------------------------
# Project imports
# ---------------------------------------------------------------------------
import lightgbm as lgb
import numpy as np
import sklearn
from forecast.baselines import evaluate_baseline
from forecast.evaluate import compute_metrics
from forecast.model import (
    FEATURE_NAMES,
    LEVEL_ENC,
    SEASON_ENC,
    SECTION_CAP_DEFAULT,
    TERM_INDEX_SCALE,
    build_feature_df,
    train_quantile_models,
)
from forecast.predict import ARTIFACTS_DIR, predict, predict_sections

DATA_PATH = REPO_ROOT / "data" / "seed" / "enrollment_history.json"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

UPCOMING_TERMS = [
    {"term": "Fall 2026", "season": "Fall", "year": 2026, "term_index": 10},
    {"term": "Spring 2027", "season": "Spring", "year": 2027, "term_index": 11},
    {"term": "Summer 2027", "season": "Summer", "year": 2027, "term_index": 12},
]


def load_history() -> tuple[list[dict], str]:
    """Load enrollment history and return (records, sha256_hex)."""
    raw_bytes = DATA_PATH.read_bytes()
    sha256 = hashlib.sha256(raw_bytes).hexdigest()
    records = json.loads(raw_bytes.decode("utf-8"))
    print(f"  Loaded {len(records)} enrollment records from {DATA_PATH.name}")
    print(f"  SHA-256: {sha256[:16]}...")
    return records, sha256


def time_split(
    history: list[dict],
    train_cutoff: int = 7,
) -> tuple[list[dict], list[dict]]:
    """Split by term_index: train <= cutoff, val > cutoff."""
    train = [r for r in history if r["term_index"] <= train_cutoff]
    val = [r for r in history if r["term_index"] > train_cutoff]
    return train, val


def run() -> None:
    t_start = time.perf_counter()

    print("\n=== Section Demand Forecaster — Offline Training ===\n")

    # 1. Load data
    print("[1/6] Loading training data...")
    history, sha256 = load_history()

    # 2. Time-ordered train/val split (no leakage)
    print("[2/6] Splitting data (train: term_index <= 7, val: >= 8)...")
    train_recs, val_recs = time_split(history, train_cutoff=7)
    print(f"  Train: {len(train_recs)} records | Val: {len(val_recs)} records")

    # 3. Build feature matrices
    print("[3/6] Engineering features...")
    X_train_df, y_train = build_feature_df(train_recs, train_recs)
    X_val_df, y_val = build_feature_df(history, val_recs)

    X_train = X_train_df.values.astype("float32")
    X_val = X_val_df.values.astype("float32")
    print(f"  Train features: {X_train.shape} | Val features: {X_val.shape}")

    # 4. Train LightGBM models
    print("[4/6] Training LightGBM quantile models (p10, p50, p90)...")
    models = train_quantile_models(X_train, y_train, random_state=42)

    # 5. Evaluate on validation set
    print("[5/6] Evaluating on validation set...")
    val_preds = predict(models, X_val)

    p10_arr = np.round(np.clip(val_preds["p10"], 0, None)).astype(int).tolist()
    p50_arr = np.round(np.clip(val_preds["p50"], 0, None)).astype(int).tolist()
    p90_arr = np.round(np.clip(val_preds["p90"], 0, None)).astype(int).tolist()

    lgb_metrics = compute_metrics(y_val, p10_arr, p50_arr, p90_arr)

    baseline_sn = evaluate_baseline(val_recs, train_recs, mode="seasonal_naive")
    baseline_ma = evaluate_baseline(val_recs, train_recs, mode="moving_average_3")

    print(
        f"\n  LightGBM    - MAE: {lgb_metrics['mae']:.2f}, RMSE: {lgb_metrics['rmse']:.2f}, "
        f"WAPE: {lgb_metrics['wape']:.1f}%, Coverage: {lgb_metrics['p10_p90_coverage']:.1%}"
    )
    print(
        f"  SeasonNaive - MAE: {baseline_sn['mae']:.2f}, RMSE: {baseline_sn['rmse']:.2f}"
    )
    print(
        f"  MovingAvg3  - MAE: {baseline_ma['mae']:.2f}, RMSE: {baseline_ma['rmse']:.2f}"
    )

    # 6. Save artifacts
    print("\n[6/6] Saving artifacts...")

    for key, booster in models.items():
        out_path = ARTIFACTS_DIR / f"forecast_{key}.txt"
        booster.save_model(str(out_path))
        size_kb = out_path.stat().st_size / 1024
        print(f"  {out_path.name}: {size_kb:.1f} KB")

    feature_config = {
        "feature_names": FEATURE_NAMES,
        "level_enc": LEVEL_ENC,
        "season_enc": SEASON_ENC,
        "section_cap": SECTION_CAP_DEFAULT,
        "term_index_scale": TERM_INDEX_SCALE,
    }
    (ARTIFACTS_DIR / "feature_config.json").write_text(
        json.dumps(feature_config, indent=2), encoding="utf-8"
    )
    print("  feature_config.json: saved")

    metrics_record = {
        "lightgbm": {
            "mae": lgb_metrics["mae"],
            "rmse": lgb_metrics["rmse"],
            "wape": lgb_metrics["wape"],
            "p10_p90_coverage": lgb_metrics["p10_p90_coverage"],
        },
        "baselines": {
            "seasonal_naive": {"mae": baseline_sn["mae"], "rmse": baseline_sn["rmse"]},
            "moving_average_3": {
                "mae": baseline_ma["mae"],
                "rmse": baseline_ma["rmse"],
            },
        },
        "seed": 42,
        "random_state": 42,
        "training_date": datetime.now(timezone.utc).isoformat(),
        "training_data_sha256": sha256,
        "library_versions": {
            "lightgbm": lgb.__version__,
            "numpy": np.__version__,
            "scikit_learn": sklearn.__version__,
        },
        "train_samples": len(train_recs),
        "val_samples": len(val_recs),
        "features": FEATURE_NAMES,
        "hyperparameters": {
            "n_jobs": 1,
            "num_leaves": 15,
            "n_estimators": 150,
            "random_state": 42,
        },
    }
    (ARTIFACTS_DIR / "metrics.json").write_text(
        json.dumps(metrics_record, indent=2), encoding="utf-8"
    )
    print("  metrics.json: saved")

    print("\n  Generating precomputed forecasts for upcoming terms...")
    precomputed: list[dict] = []

    courses_seen: dict[str, dict] = {}
    for rec in history:
        cid = rec["course_id"]
        if cid not in courses_seen:
            courses_seen[cid] = rec

    for upcoming in UPCOMING_TERMS:
        target_records_for_term = [
            {
                **courses_seen[cid],
                "term_index": upcoming["term_index"],
                "season": upcoming["season"],
            }
            for cid in courses_seen
        ]

        X_up_df, _ = build_feature_df(history, target_records_for_term)
        X_up = X_up_df.values.astype("float32")
        up_preds = predict(models, X_up)
        sections = predict_sections(up_preds, section_cap=SECTION_CAP_DEFAULT)

        for i, cid in enumerate(courses_seen):
            precomputed.append(
                {
                    "course_id": cid,
                    "course_code": courses_seen[cid]["course_code"],
                    "term": upcoming["term"],
                    "season": upcoming["season"],
                    "year": upcoming["year"],
                    "p10": sections["p10"][i],
                    "p50": sections["p50"][i],
                    "p90": sections["p90"][i],
                    "n_sections": sections["n_sections"][i],
                    "p90_risk_sections": sections["p90_risk_sections"][i],
                }
            )

    (ARTIFACTS_DIR / "precomputed_forecasts.json").write_text(
        json.dumps(precomputed, indent=2), encoding="utf-8"
    )
    print(f"  precomputed_forecasts.json: {len(precomputed)} records saved")

    t_end = time.perf_counter()
    elapsed = t_end - t_start
    print(f"\n[OK] Training complete in {elapsed:.1f}s")
    print(f"  Artifacts written to: {ARTIFACTS_DIR}")

    for fname in [
        "forecast_p10.txt",
        "forecast_p50.txt",
        "forecast_p90.txt",
        "feature_config.json",
        "metrics.json",
        "precomputed_forecasts.json",
    ]:
        fpath = ARTIFACTS_DIR / fname
        if fpath.exists():
            size_mb = fpath.stat().st_size / (1024 * 1024)
            status = "OK" if size_mb < 5.0 else "WARNING: exceeds 5MB!"
            print(f"  {fname}: {size_mb:.3f} MB - {status}")


if __name__ == "__main__":
    run()
