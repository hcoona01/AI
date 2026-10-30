"""Inference: load text-format LightGBM artifacts and predict demand quantiles."""

from __future__ import annotations

import json
from math import ceil
from pathlib import Path
from typing import Any

import numpy as np

ARTIFACTS_DIR: Path = Path(__file__).resolve().parents[1] / "artifacts"


class ArtifactsNotFoundError(RuntimeError):
    """Raised when required ML artifact files are missing."""


def _artifact_path(name: str) -> Path:
    return ARTIFACTS_DIR / name


def check_artifacts_exist() -> None:
    """Raise ArtifactsNotFoundError if any required artifact is missing."""
    required = [
        "forecast_p10.txt",
        "forecast_p50.txt",
        "forecast_p90.txt",
        "feature_config.json",
    ]
    missing = [f for f in required if not _artifact_path(f).exists()]
    if missing:
        raise ArtifactsNotFoundError(
            f"ML artifacts missing: {missing}. "
            "Run 'make train' to generate them before using the forecast endpoint."
        )


def load_models() -> dict[str, Any]:
    """Load the three LightGBM booster text artifacts.

    Returns:
        Dict mapping 'p10', 'p50', 'p90' to lgb.Booster instances.

    Raises:
        ArtifactsNotFoundError: If model files are absent.
    """
    import lightgbm as lgb  # lazy import: only called in model mode

    check_artifacts_exist()

    return {
        "p10": lgb.Booster(model_file=str(_artifact_path("forecast_p10.txt"))),
        "p50": lgb.Booster(model_file=str(_artifact_path("forecast_p50.txt"))),
        "p90": lgb.Booster(model_file=str(_artifact_path("forecast_p90.txt"))),
    }


def load_feature_config() -> dict[str, Any]:
    """Load the feature configuration JSON artifact.

    Returns:
        Dict with feature_names, encoding maps, section_cap, etc.

    Raises:
        ArtifactsNotFoundError: If feature_config.json is absent.
    """
    path = _artifact_path("feature_config.json")
    if not path.exists():
        raise ArtifactsNotFoundError(
            "feature_config.json not found. Run 'make train' to generate artifacts."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def predict(
    models: dict[str, Any],
    X: np.ndarray,
) -> dict[str, np.ndarray]:
    """Run quantile predictions and enforce P10 <= P50 <= P90 monotonicity.

    Args:
        models: Dict from load_models() with 'p10', 'p50', 'p90' boosters.
        X: Feature matrix of shape (n_samples, n_features).

    Returns:
        Dict with 'p10', 'p50', 'p90' arrays (sorted per row to enforce monotonicity).
    """
    raw_p10 = np.asarray(models["p10"].predict(X), dtype=np.float32)
    raw_p50 = np.asarray(models["p50"].predict(X), dtype=np.float32)
    raw_p90 = np.asarray(models["p90"].predict(X), dtype=np.float32)

    # Clip negatives (enrollment cannot be negative)
    raw_p10 = np.clip(raw_p10, 0, None)
    raw_p50 = np.clip(raw_p50, 0, None)
    raw_p90 = np.clip(raw_p90, 0, None)

    # Sort per row to enforce P10 <= P50 <= P90
    stacked = np.stack([raw_p10, raw_p50, raw_p90], axis=1)
    sorted_preds = np.sort(stacked, axis=1)

    return {
        "p10": sorted_preds[:, 0],
        "p50": sorted_preds[:, 1],
        "p90": sorted_preds[:, 2],
    }


def predict_sections(
    preds: dict[str, np.ndarray],
    section_cap: int = 50,
) -> dict[str, list[int]]:
    """Convert enrollment quantile predictions to section counts.

    Args:
        preds: Dict with 'p10', 'p50', 'p90' arrays (float).
        section_cap: Maximum students per section.

    Returns:
        Dict with 'p10', 'p50', 'p90' integer enrollments and
        'n_sections' (ceil(p50/cap)), 'p90_risk_sections' (ceil(p90/cap)).
    """
    p10 = np.round(preds["p10"]).astype(int)
    p50 = np.round(preds["p50"]).astype(int)
    p90 = np.round(preds["p90"]).astype(int)

    n_sections = np.array([ceil(max(int(v), 1) / section_cap) for v in p50])
    p90_risk = np.array([ceil(max(int(v), 1) / section_cap) for v in p90])

    return {
        "p10": p10.tolist(),
        "p50": p50.tolist(),
        "p90": p90.tolist(),
        "n_sections": n_sections.tolist(),
        "p90_risk_sections": p90_risk.tolist(),
    }


def load_precomputed() -> list[dict[str, Any]]:
    """Load precomputed forecasts from the JSON artifact.

    Returns:
        List of forecast dicts.

    Raises:
        ArtifactsNotFoundError: If precomputed_forecasts.json is absent.
    """
    path = _artifact_path("precomputed_forecasts.json")
    if not path.exists():
        raise ArtifactsNotFoundError(
            "precomputed_forecasts.json not found. Run 'make train' to generate artifacts."
        )
    return json.loads(path.read_text(encoding="utf-8"))
