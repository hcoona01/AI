"""Unit and validation tests for section-demand ML artifacts, monotonicity, and inference."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch
import sys

import numpy as np
import pytest

from ml.forecast.baselines import moving_average_3, seasonal_naive
from ml.forecast.evaluate import compute_metrics
from ml.forecast.predict import (
    ARTIFACTS_DIR,
    ArtifactsNotFoundError,
    check_artifacts_exist,
    load_feature_config,
    load_models,
    load_precomputed,
    predict,
    predict_sections,
)

REQUIRED_ARTIFACT_FILES = [
    "forecast_p10.txt",
    "forecast_p50.txt",
    "forecast_p90.txt",
    "feature_config.json",
    "metrics.json",
    "precomputed_forecasts.json",
]


class TestArtifactPresenceAndSize:
    """Validate that all required artifacts are present and satisfy the < 5 MB rule."""

    @pytest.mark.parametrize("filename", REQUIRED_ARTIFACT_FILES)
    def test_artifact_exists_and_under_5mb(self, filename: str) -> None:
        path = ARTIFACTS_DIR / filename
        assert path.exists(), f"Required artifact {filename} does not exist in {ARTIFACTS_DIR}"
        size_bytes = path.stat().st_size
        max_bytes = 5 * 1024 * 1024  # 5 MB
        assert size_bytes < max_bytes, (
            f"Artifact {filename} is {size_bytes / (1024 * 1024):.2f} MB, which exceeds 5 MB limit!"
        )

    def test_metrics_schema(self) -> None:
        metrics_path = ARTIFACTS_DIR / "metrics.json"
        assert metrics_path.exists()
        data = json.loads(metrics_path.read_text(encoding="utf-8"))

        assert "lightgbm" in data
        assert "mae" in data["lightgbm"]
        assert "rmse" in data["lightgbm"]
        assert "wape" in data["lightgbm"]
        assert "p10_p90_coverage" in data["lightgbm"]

        assert "baselines" in data
        assert "seasonal_naive" in data["baselines"]
        assert "moving_average_3" in data["baselines"]

        assert "training_data_sha256" in data
        assert "training_date" in data
        assert "seed" in data
        assert "library_versions" in data
        assert "lightgbm" in data["library_versions"]
        assert "numpy" in data["library_versions"]
        assert "scikit_learn" in data["library_versions"]

    def test_feature_config_schema(self) -> None:
        config_path = ARTIFACTS_DIR / "feature_config.json"
        assert config_path.exists()
        cfg = json.loads(config_path.read_text(encoding="utf-8"))

        assert "feature_names" in cfg
        assert isinstance(cfg["feature_names"], list)
        assert len(cfg["feature_names"]) >= 8
        assert "section_cap" in cfg
        assert cfg["section_cap"] > 0


class TestMonotonicityAndInvariants:
    """Verify P10 <= P50 <= P90 invariant across precomputed forecasts and model predictions."""

    def test_precomputed_monotonicity(self) -> None:
        records = load_precomputed()
        assert len(records) > 0, "precomputed_forecasts.json must not be empty"

        for rec in records:
            p10 = rec["p10"]
            p50 = rec["p50"]
            p90 = rec["p90"]
            assert (
                p10 <= p50 <= p90
            ), f"Monotonicity violation in course {rec.get('course_id')}: p10={p10}, p50={p50}, p90={p90}"
            assert rec["n_sections"] >= 1
            assert rec["p90_risk_sections"] >= rec["n_sections"]

    def test_predict_monotonicity_enforcement(self) -> None:
        # Construct synthetic unordered raw predictions
        class DummyBooster:
            def __init__(self, val: float):
                self.val = val

            def predict(self, X: np.ndarray) -> np.ndarray:
                return np.full((X.shape[0],), self.val)

        # Invert order: p10=100, p50=50, p90=10
        dummy_models = {
            "p10": DummyBooster(100.0),
            "p50": DummyBooster(50.0),
            "p90": DummyBooster(10.0),
        }
        X_dummy = np.zeros((5, 10), dtype=np.float32)
        preds = predict(dummy_models, X_dummy)

        for i in range(5):
            assert preds["p10"][i] <= preds["p50"][i] <= preds["p90"][i]
            assert preds["p10"][i] == 10.0
            assert preds["p50"][i] == 50.0
            assert preds["p90"][i] == 100.0

    def test_predict_sections_conversion(self) -> None:
        preds = {
            "p10": np.array([15.0, 45.0, 95.0]),
            "p50": np.array([25.0, 50.0, 110.0]),
            "p90": np.array([40.0, 85.0, 160.0]),
        }
        sections = predict_sections(preds, section_cap=50)
        # 25 -> 1 section, 50 -> 1 section, 110 -> 3 sections
        assert sections["n_sections"] == [1, 1, 3]
        # 40 -> 1 section, 85 -> 2 sections, 160 -> 4 sections
        assert sections["p90_risk_sections"] == [1, 2, 4]


class TestBaselinesAndMetrics:
    """Verify baseline heuristics and evaluation computation."""

    def test_seasonal_naive(self) -> None:
        history = [
            {"course_id": "c1", "season": "Fall", "term_index": 1, "enrolled_students": 50},
            {"course_id": "c1", "season": "Spring", "term_index": 2, "enrolled_students": 30},
            {"course_id": "c1", "season": "Fall", "term_index": 4, "enrolled_students": 55},
        ]
        pred_fall = seasonal_naive(history, "c1", "Fall")
        assert pred_fall == 55.0

        pred_spring = seasonal_naive(history, "c1", "Spring")
        assert pred_spring == 30.0

        pred_summer = seasonal_naive(history, "c1", "Summer")
        assert pred_summer is None

    def test_moving_average_3(self) -> None:
        history = [
            {"course_id": "c1", "term_index": 1, "enrolled_students": 30},
            {"course_id": "c1", "term_index": 2, "enrolled_students": 40},
            {"course_id": "c1", "term_index": 3, "enrolled_students": 50},
            {"course_id": "c1", "term_index": 4, "enrolled_students": 60},
        ]
        pred = moving_average_3(history, "c1")
        # Last 3: 40, 50, 60 -> mean 50.0
        assert pred == 50.0

    def test_compute_metrics(self) -> None:
        y_true = [10.0, 20.0, 30.0]
        p10 = [8.0, 18.0, 28.0]
        p50 = [10.0, 22.0, 29.0]
        p90 = [12.0, 25.0, 32.0]
        metrics = compute_metrics(y_true, p10, p50, p90)
        assert metrics["mae"] == round((0.0 + 2.0 + 1.0) / 3, 4)
        assert metrics["p10_p90_coverage"] == 1.0


class TestModelDeterminism:
    """Verify that model inference is deterministic."""

    def test_deterministic_predictions(self) -> None:
        models = load_models()
        X = np.random.RandomState(42).randn(10, 10).astype(np.float32)
        preds1 = predict(models, X)
        preds2 = predict(models, X)

        np.testing.assert_array_almost_equal(preds1["p10"], preds2["p10"])
        np.testing.assert_array_almost_equal(preds1["p50"], preds2["p50"])
        np.testing.assert_array_almost_equal(preds1["p90"], preds2["p90"])


class TestBackendArtifactGuardAndPrecomputed:
    """Validate 503 error when artifacts missing and precomputed mode without lightgbm."""

    def test_check_artifacts_exist_raises_when_missing(self, monkeypatch: pytest.MonkeyPatch) -> None:
        with monkeypatch.context() as m:
            fake_dir = ARTIFACTS_DIR / "non_existent_dir_xyz"
            m.setattr("ml.forecast.predict.ARTIFACTS_DIR", fake_dir)
            with pytest.raises(ArtifactsNotFoundError):
                check_artifacts_exist()

    def test_backend_service_raises_503_when_artifacts_missing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import asyncio
        from app.core.config import settings
        from app.core.errors import ServiceUnavailableError
        from app.services.forecast_service import ForecastService

        monkeypatch.setattr(settings, "FORECAST_MODE", "model")
        fake_dir = ARTIFACTS_DIR / "non_existent_xyz"
        monkeypatch.setattr("app.services.forecast_service.ARTIFACTS_DIR", fake_dir)

        service = ForecastService()
        with pytest.raises(ServiceUnavailableError) as exc_info:
            asyncio.run(service.run_forecast())
        assert exc_info.value.status_code == 503
        assert "make train" in exc_info.value.message

    def test_precomputed_mode_without_lightgbm(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify precomputed mode succeeds even if lightgbm is blocked/missing."""
        import asyncio
        from app.core.config import settings
        from app.services.forecast_service import ForecastService

        monkeypatch.setattr(settings, "FORECAST_MODE", "precomputed")

        # Mock sys.modules to simulate lightgbm not being installed
        with patch.dict(sys.modules, {"lightgbm": None}):
            service = ForecastService()
            response = asyncio.run(service.run_forecast(term="Fall 2026"))
            assert response.status == "ok"
            assert response.forecast_mode == "precomputed"
            assert response.courses_forecasted > 0
