"""Reproducibility test: Verify identical assignments for fixed fixture and seed."""

import json
from pathlib import Path
import pytest
from ml.optimizer.cpsat import solve_cpsat
from ml.optimizer.greedy import solve_greedy

REPO_ROOT = Path(__file__).resolve().parents[2]
FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"


def load_fixture(name: str) -> dict:
    with open(FIXTURES_DIR / f"{name}.json", "r", encoding="utf-8") as f:
        return json.load(f)


def scenario_args(data: dict) -> dict:
    sc = data["scenario"]
    return {
        "faculty": sc["faculty"],
        "courses": sc["courses"],
        "sections": sc["sections"],
        "resources": sc.get("resources", []),
        "timeslots": sc.get("timeslots", []),
        "previous_assignments": sc.get("previous_assignments", []),
    }


@pytest.mark.parametrize("fixture_name", ["balanced_baseline", "tight_capacity"])
def test_cpsat_identical_assignments_fixed_seed(fixture_name: str):
    """CP-SAT solver must produce 100% identical assignments across repeated runs with identical seed."""
    fixture = load_fixture(fixture_name)
    kwargs = scenario_args(fixture)

    run_1 = solve_cpsat(**kwargs, seed=42, time_limit_seconds=10)
    run_2 = solve_cpsat(**kwargs, seed=42, time_limit_seconds=10)

    assert run_1.feasible == run_2.feasible == True
    assert run_1.objective_value == run_2.objective_value

    map_1 = {getattr(a, "section_id", None) or a["section_id"]: getattr(a, "faculty_id", None) or a["faculty_id"] for a in run_1.assignments}
    map_2 = {getattr(a, "section_id", None) or a["section_id"]: getattr(a, "faculty_id", None) or a["faculty_id"] for a in run_2.assignments}
    assert map_1 == map_2

    fit_1 = {getattr(a, "section_id", None) or a["section_id"]: getattr(a, "fit_score", None) for a in run_1.assignments}
    fit_2 = {getattr(a, "section_id", None) or a["section_id"]: getattr(a, "fit_score", None) for a in run_2.assignments}
    assert fit_1 == fit_2


def test_greedy_identical_assignments():
    """Greedy solver must produce 100% deterministic identical assignments."""
    fixture = load_fixture("balanced_baseline")
    kwargs = scenario_args(fixture)

    run_1 = solve_greedy(**kwargs)
    run_2 = solve_greedy(**kwargs)

    assert run_1.feasible == run_2.feasible == True
    assert run_1.objective_value == run_2.objective_value

    map_1 = {getattr(a, "section_id", None) or a["section_id"]: getattr(a, "faculty_id", None) or a["faculty_id"] for a in run_1.assignments}
    map_2 = {getattr(a, "section_id", None) or a["section_id"]: getattr(a, "faculty_id", None) or a["faculty_id"] for a in run_2.assignments}
    assert map_1 == map_2
