"""Tests for benchmark runner and benchmark output validation."""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
for p in [str(REPO_ROOT), str(REPO_ROOT / "backend"), str(REPO_ROOT / "ml")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from ml.benchmark.run_benchmark import run_benchmark

ARTIFACTS_DIR = REPO_ROOT / "ml" / "artifacts"
DOCS_DIR = REPO_ROOT / "docs"
IMG_DIR = DOCS_DIR / "img"


def test_quick_benchmark_finishes_under_two_minutes():
    """Verify that quick benchmark finishes in well under 2 minutes (120 seconds)."""
    start_time = time.perf_counter()
    result = run_benchmark(profile="quick")
    elapsed = time.perf_counter() - start_time

    assert elapsed < 120.0, f"Quick benchmark took {elapsed:.2f}s, exceeding 120s limit"
    assert result["metadata"]["profile"] == "quick"
    assert result["metadata"]["total_duration_seconds"] < 120.0


def test_benchmark_json_schema():
    """Verify benchmark_quick.json has valid schema and all required fields."""
    json_path = ARTIFACTS_DIR / "benchmark_quick.json"
    assert json_path.exists(), f"Missing artifact {json_path}"

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Validate metadata
    assert "metadata" in data
    meta = data["metadata"]
    for field_name in [
        "profile",
        "timestamp",
        "total_duration_seconds",
        "fixtures_evaluated",
        "demand_profiles",
        "seeds",
        "time_limit_seconds",
        "total_runs",
    ]:
        assert field_name in meta, f"Metadata missing {field_name}"

    assert meta["profile"] == "quick"
    assert len(meta["fixtures_evaluated"]) == 3
    assert meta["demand_profiles"] == ["P50"]

    # Validate runs array
    assert "runs" in data
    runs = data["runs"]
    assert len(runs) == 6  # 3 fixtures * 2 methods (cpsat, greedy)

    required_run_fields = [
        "method",
        "fixture",
        "demand_profile",
        "seed",
        "time_limit",
        "feasible",
        "status",
        "objective_value",
        "mean_fit",
        "gini",
        "std_dev",
        "max_min_gap",
        "hard_violations",
        "solve_time_seconds",
        "variable_count",
        "variables_avoided",
        "peak_memory_mb",
        "assigned_sections_count",
    ]

    for run in runs:
        for fld in required_run_fields:
            assert fld in run, f"Run record missing {fld}"

        assert run["method"] in ["cpsat", "greedy"]
        assert isinstance(run["feasible"], bool)
        assert run["solve_time_seconds"] >= 0.0
        assert run["peak_memory_mb"] >= 0.0
        assert run["hard_violations"] >= 0
        assert 0.0 <= run["gini"] <= 1.0


def test_benchmark_docs_and_images_generated():
    """Verify docs/benchmark.md and PNG charts exist and are non-empty."""
    doc_path = DOCS_DIR / "benchmark.md"
    assert doc_path.exists(), f"Missing {doc_path}"
    assert doc_path.stat().st_size > 500, f"Benchmark doc too short: {doc_path.stat().st_size} bytes"

    content = doc_path.read_text(encoding="utf-8")
    assert "Comparison Table" in content
    assert "Trade-Off Analysis" in content
    assert "Selected approach and rationale" in content
    assert "CP-SAT" in content
    assert "Greedy" in content

    # Check images
    for img_name in ["benchmark_solve_time.png", "benchmark_tradeoffs.png", "benchmark_memory.png"]:
        img_path = IMG_DIR / img_name
        assert img_path.exists(), f"Missing chart {img_path}"
        assert img_path.stat().st_size > 1000, f"Chart image {img_name} too small: {img_path.stat().st_size} bytes"

