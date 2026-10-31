"""Optimizer module tests: CP-SAT, greedy, fairness, explain, repair.

Tests cover:
1. Solver feasibility aligned with each fixture's expected outcome
   (the "expected_feasible" column here means: can the OPTIMIZER find a valid
   assignment, not whether the *pre-supplied fixture assignments* violate
   constraints, which is what test_datagen.py verifies via ConstraintEngine).
2. Reproducibility under fixed random seed.
3. Pre-filter variable reduction on fixtures that have eligible pruning.
4. Fairness metrics (Gini, std-dev, max-min gap).
5. explain.py ExplanationResult structure for infeasible runs.
6. repair.py produces ≥1 repair alternatives for infeasible cases.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
for _p in [str(REPO_ROOT), str(REPO_ROOT / "backend"), str(REPO_ROOT / "ml")]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

from ml.optimizer.cpsat import PreFilterResult, SolveResult, prefilter_eligible_pairs, solve_cpsat
from ml.optimizer.explain import ExplanationResult, generate_explanation
from ml.optimizer.fairness import compute_gini, compute_max_min_gap, compute_standard_deviation
from ml.optimizer.greedy import solve_greedy
from ml.optimizer.repair import RepairAlternative, generate_repairs

FIXTURES_DIR = REPO_ROOT / "data" / "fixtures"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def load_fixture(name: str) -> dict:
    path = FIXTURES_DIR / f"{name}.json"
    assert path.exists(), f"Fixture not found: {path}"
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


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


# ---------------------------------------------------------------------------
# Fixture-based feasibility tests
#
# NOTE: "optimizer_feasible" here is what the CP-SAT solver can achieve with
# the data in the fixture, NOT whether the pre-supplied assignments in the
# fixture are constraint-clean (that is what test_datagen.py tests via
# ConstraintEngine).
#
# Mapping rationale:
#  balanced_baseline     → True  (all constraints relaxed, ample faculty)
#  tight_capacity        → True  (tight load but solvable)
#  infeasible_expertise  → False (HC-01 filters all pairs → 0 eligible vars)
#  leave_heavy           → True  (3 on leave, but 7 available → solver feasible)
#  single_expert_bottleneck → False (HC-02 over capacity; only expert can't fit)
#  lab_resource_shortage → False (HC-07 eliminates all pairs)
#  time_clash_dense      → False (only 1 timeslot available for 2 sections →
#                                 only 1 assigned, second fails HC-06)
#  demand_spike          → True  (minimal scenario, solver finds solution)
#  boundary_exact_limit  → True  (exactly at limit, still feasible)
#  boundary_zero_capacity→ False (HC-07 eliminates all pairs)
# ---------------------------------------------------------------------------

OPTIMIZER_FEASIBILITY_CASES = [
    ("balanced_baseline",        True),
    ("tight_capacity",           True),
    ("infeasible_expertise",     False),
    ("leave_heavy",              True),   # solver finds valid non-leave faculty
    ("single_expert_bottleneck", False),
    ("lab_resource_shortage",    False),
    ("time_clash_dense",         False),
    ("demand_spike",             True),
    ("boundary_exact_limit",     True),
    ("boundary_zero_capacity",   False),
]


@pytest.mark.parametrize("fixture_name,expected_feasible", OPTIMIZER_FEASIBILITY_CASES)
def test_cpsat_feasibility(fixture_name: str, expected_feasible: bool) -> None:
    """CP-SAT solver returns the expected feasibility for every fixture."""
    data = load_fixture(fixture_name)
    kwargs = scenario_args(data)
    result = solve_cpsat(**kwargs, time_limit_seconds=15, seed=42)

    assert result.feasible == expected_feasible, (
        f"[{fixture_name}] CP-SAT feasibility mismatch: "
        f"expected={expected_feasible}, got={result.feasible} ({result.status}). "
        f"blocking_rules={result.blocking_rule_ids}"
    )
    # Sanity checks on the result
    assert result.status in {"OPTIMAL", "FEASIBLE", "INFEASIBLE", "UNKNOWN", "MODEL_INVALID"}
    assert result.solve_time_seconds >= 0
    assert result.variable_count >= 0
    assert result.variables_avoided >= 0
    assert result.peak_memory_mb >= 0
    if result.feasible:
        assert len(result.assignments) > 0
        assert result.fit_summary.get("mean_fit", -1) >= 0.0
    else:
        assert len(result.assignments) == 0


@pytest.mark.parametrize("fixture_name,expected_feasible", OPTIMIZER_FEASIBILITY_CASES)
def test_greedy_feasibility(fixture_name: str, expected_feasible: bool) -> None:
    """Greedy solver returns matching feasibility for every fixture."""
    data = load_fixture(fixture_name)
    kwargs = scenario_args(data)
    result = solve_greedy(**kwargs)

    assert result.feasible == expected_feasible, (
        f"[{fixture_name}] Greedy feasibility mismatch: "
        f"expected={expected_feasible}, got={result.feasible} ({result.status})"
    )
    if result.feasible:
        assert len(result.assignments) > 0
    else:
        assert len(result.assignments) == 0


# ---------------------------------------------------------------------------
# Reproducibility — same seed must produce identical results
# ---------------------------------------------------------------------------

def test_cpsat_reproducible_fixed_seed() -> None:
    """Two CP-SAT runs with seed=42 must produce identical objective and assignments."""
    data = load_fixture("balanced_baseline")
    kwargs = scenario_args(data)

    r1 = solve_cpsat(**kwargs, seed=42, time_limit_seconds=10)
    r2 = solve_cpsat(**kwargs, seed=42, time_limit_seconds=10)

    assert r1.feasible == r2.feasible
    assert r1.objective_value == r2.objective_value
    assert r1.fit_summary.get("mean_fit") == r2.fit_summary.get("mean_fit")
    assert len(r1.assignments) == len(r2.assignments)


def test_cpsat_different_seeds_may_differ() -> None:
    """Two runs with different seeds should be compared (at minimum no crash)."""
    data = load_fixture("balanced_baseline")
    kwargs = scenario_args(data)
    r1 = solve_cpsat(**kwargs, seed=1, time_limit_seconds=10)
    r2 = solve_cpsat(**kwargs, seed=99, time_limit_seconds=10)
    # Both must still be feasible / same status
    assert r1.feasible == r2.feasible


# ---------------------------------------------------------------------------
# Pre-filter variable reduction
# ---------------------------------------------------------------------------

def test_prefilter_reduces_variables_on_balanced_baseline() -> None:
    """balanced_baseline has faculty with mixed expertise → pre-filter prunes pairs."""
    data = load_fixture("balanced_baseline")
    sc = data["scenario"]
    pf = prefilter_eligible_pairs(
        faculty=sc["faculty"],
        courses=sc["courses"],
        sections=sc["sections"],
        resources=sc.get("resources", []),
    )
    total = len(sc["faculty"]) * len(sc["sections"])
    assert pf.variables_avoided > 0, (
        f"Expected pre-filter to prune ≥1 variable on balanced_baseline; "
        f"total={total}, eligible={len(pf.eligible_pairs)}, avoided={pf.variables_avoided}"
    )
    assert pf.total_possible_pairs == total
    assert len(pf.eligible_pairs) == total - pf.variables_avoided


def test_prefilter_result_structure() -> None:
    """PreFilterResult fields are consistent."""
    data = load_fixture("infeasible_expertise")
    sc = data["scenario"]
    pf = prefilter_eligible_pairs(
        faculty=sc["faculty"],
        courses=sc["courses"],
        sections=sc["sections"],
        resources=sc.get("resources", []),
    )
    # All pairs must be eliminated on infeasible_expertise (HC-01)
    assert len(pf.eligible_pairs) == 0
    assert pf.variables_avoided == pf.total_possible_pairs
    assert "HC-01" in str(pf.blocking_reasons_by_section)


def test_prefilter_on_leave_heavy_avoids_leave_pairs() -> None:
    """leave_heavy: 3 faculty on leave → their pairs are pruned by HC-04."""
    data = load_fixture("leave_heavy")
    sc = data["scenario"]
    fac = sc["faculty"]
    # 3 faculty have leave_terms = ["Fall 2026"], sections are in Fall 2026
    on_leave = [f for f in fac if "Fall 2026" in f.get("leave_terms", [])]
    assert len(on_leave) == 3

    pf = prefilter_eligible_pairs(
        faculty=fac,
        courses=sc["courses"],
        sections=sc["sections"],
        resources=sc.get("resources", []),
    )
    # Must prune exactly 3 faculty × 3 sections = 9 pairs
    assert pf.variables_avoided == 9, (
        f"Expected 9 pairs avoided (3 leave × 3 sections), got {pf.variables_avoided}"
    )


def test_prefilter_tight_capacity_all_eligible() -> None:
    """tight_capacity: all faculty have required expertise, no leave/resource
    violations, so pre-filter avoids 0 pairs (correct behaviour)."""
    data = load_fixture("tight_capacity")
    sc = data["scenario"]
    pf = prefilter_eligible_pairs(
        faculty=sc["faculty"],
        courses=sc["courses"],
        sections=sc["sections"],
        resources=sc.get("resources", []),
    )
    # No eligibility violations in tight_capacity — all pairs are valid candidates
    total = len(sc["faculty"]) * len(sc["sections"])
    assert pf.variables_avoided == 0
    assert len(pf.eligible_pairs) == total


# ---------------------------------------------------------------------------
# Fairness metrics
# ---------------------------------------------------------------------------

def test_gini_perfect_equality() -> None:
    """Equal loads → Gini coefficient = 0."""
    loads = [10.0, 10.0, 10.0, 10.0]
    assert compute_gini(loads) == pytest.approx(0.0, abs=1e-6)


def test_gini_max_inequality() -> None:
    """Single non-zero load → Gini approaches 1 with many zeros."""
    loads = [0.0, 0.0, 0.0, 100.0]
    g = compute_gini(loads)
    assert g > 0.5, f"Expected high Gini for extreme inequality, got {g}"


def test_gini_empty() -> None:
    assert compute_gini([]) == 0.0


def test_gini_single() -> None:
    assert compute_gini([5.0]) == 0.0


def test_std_dev_homogeneous() -> None:
    assert compute_standard_deviation([5.0, 5.0, 5.0]) == pytest.approx(0.0, abs=1e-9)


def test_std_dev_known_values() -> None:
    # Sample std-dev (ddof=1) of [2, 4, 4, 4, 5, 5, 7, 9] ≈ 2.138
    # (population std-dev = 2.0; sample std-dev is slightly higher)
    loads = [2.0, 4.0, 4.0, 4.0, 5.0, 5.0, 7.0, 9.0]
    result = compute_standard_deviation(loads)
    assert result == pytest.approx(2.1380899, abs=1e-4)
    assert result > 0.0


def test_max_min_gap_zero() -> None:
    assert compute_max_min_gap([3.0, 3.0, 3.0]) == pytest.approx(0.0, abs=1e-9)


def test_max_min_gap_known() -> None:
    assert compute_max_min_gap([1.0, 5.0, 3.0]) == pytest.approx(4.0, abs=1e-9)


def test_max_min_gap_empty() -> None:
    assert compute_max_min_gap([]) == 0.0


def test_fairness_in_cpsat_result() -> None:
    """CP-SAT result fairness dict contains all required keys."""
    data = load_fixture("balanced_baseline")
    kwargs = scenario_args(data)
    r = solve_cpsat(**kwargs, seed=42, time_limit_seconds=10)
    assert r.feasible
    for key in ("gini", "std_dev", "max_min_gap", "mean_load", "faculty_count"):
        assert key in r.fairness, f"Missing fairness key: {key}"
    assert 0.0 <= r.fairness["gini"] <= 1.0


# ---------------------------------------------------------------------------
# Explanation (explain.py)
# ---------------------------------------------------------------------------

def test_explanation_for_feasible_is_trivial() -> None:
    data = load_fixture("balanced_baseline")
    kwargs = scenario_args(data)
    r = solve_cpsat(**kwargs, seed=42, time_limit_seconds=10)
    assert r.feasible
    exp = generate_explanation(r, **kwargs)
    assert isinstance(exp, ExplanationResult)
    assert exp.feasible is True
    assert exp.primary_rule_ids == []


def test_explanation_for_infeasible_expertise() -> None:
    """HC-01 infeasibility produces an ExplanationResult with HC-01 in rule_ids."""
    data = load_fixture("infeasible_expertise")
    kwargs = scenario_args(data)
    r = solve_cpsat(**kwargs, seed=42, time_limit_seconds=10)
    assert not r.feasible

    exp = generate_explanation(r, **kwargs)
    assert isinstance(exp, ExplanationResult)
    assert exp.feasible is False
    assert "HC-01" in exp.primary_rule_ids
    assert len(exp.conflicts) > 0
    assert len(exp.detailed_narrative) > 0
    assert len(exp.suggested_actions) > 0


def test_explanation_for_resource_shortage() -> None:
    """HC-07 infeasibility produces an ExplanationResult with HC-07 in rule_ids."""
    data = load_fixture("lab_resource_shortage")
    kwargs = scenario_args(data)
    r = solve_cpsat(**kwargs, seed=42, time_limit_seconds=10)
    assert not r.feasible

    exp = generate_explanation(r, **kwargs)
    assert "HC-07" in exp.primary_rule_ids


# ---------------------------------------------------------------------------
# Repair alternatives (repair.py)
# ---------------------------------------------------------------------------

def test_repair_returns_empty_for_feasible() -> None:
    data = load_fixture("balanced_baseline")
    kwargs = scenario_args(data)
    r = solve_cpsat(**kwargs, seed=42, time_limit_seconds=10)
    assert r.feasible
    repairs = generate_repairs(**kwargs, solve_result=r, re_solve_time_limit=5.0, seed=42)
    assert repairs == []


def test_repair_generates_alternatives_for_infeasible() -> None:
    """Infeasible scenario (HC-01) produces ≥1 repair candidate."""
    data = load_fixture("infeasible_expertise")
    kwargs = scenario_args(data)
    r = solve_cpsat(**kwargs, seed=42, time_limit_seconds=10)
    assert not r.feasible

    repairs = generate_repairs(**kwargs, solve_result=r, re_solve_time_limit=5.0, seed=42)
    assert len(repairs) >= 1
    for rep in repairs:
        assert isinstance(rep, RepairAlternative)
        assert rep.repair_type in {"relax_hc05", "add_adjunct", "move_timeslot", "expand_facility"}
        assert len(rep.title) > 0
        assert len(rep.description) > 0
        assert len(rep.changes) > 0
        assert isinstance(rep.feasible_after_repair, bool)
        assert 0.0 <= rep.fairness_gini <= 1.0
        assert rep.mean_fit >= 0.0


def test_repair_for_resource_shortage() -> None:
    """HC-07 infeasibility: expand_facility repair should restore feasibility."""
    data = load_fixture("lab_resource_shortage")
    kwargs = scenario_args(data)
    r = solve_cpsat(**kwargs, seed=42, time_limit_seconds=10)
    assert not r.feasible

    repairs = generate_repairs(**kwargs, solve_result=r, re_solve_time_limit=5.0, seed=42)
    assert len(repairs) >= 1
    # At least one repair (expand_facility) should be generated since HC-07 is blocking
    repair_types = {rep.repair_type for rep in repairs}
    assert "expand_facility" in repair_types


def test_repair_limit_respected() -> None:
    """generate_repairs respects max_repairs parameter."""
    data = load_fixture("infeasible_expertise")
    kwargs = scenario_args(data)
    r = solve_cpsat(**kwargs, seed=42, time_limit_seconds=10)

    repairs = generate_repairs(**kwargs, solve_result=r, max_repairs=2, re_solve_time_limit=5.0, seed=42)
    assert len(repairs) <= 2


# ---------------------------------------------------------------------------
# SolveResult benchmark fields
# ---------------------------------------------------------------------------

def test_cpsat_returns_benchmark_fields() -> None:
    """CP-SAT result must carry all benchmark metadata fields."""
    data = load_fixture("balanced_baseline")
    kwargs = scenario_args(data)
    r = solve_cpsat(**kwargs, seed=42, time_limit_seconds=10)
    assert r.solve_time_seconds >= 0.0
    assert r.peak_memory_mb >= 0.0
    assert r.variable_count >= 0
    assert r.variables_avoided >= 0
    assert r.status in {"OPTIMAL", "FEASIBLE", "INFEASIBLE", "UNKNOWN", "MODEL_INVALID"}
    if r.feasible:
        assert r.objective_value is not None
        assert r.objective_bound is not None


def test_cpsat_p50_vs_p90_demand_profiles() -> None:
    """Both demand profiles P50 and P90 run without errors on a resource-free fixture."""
    # leave_heavy has no resource constraints, so P90 demand doesn't trigger HC-07
    data = load_fixture("leave_heavy")
    kwargs = scenario_args(data)
    r50 = solve_cpsat(**kwargs, demand_profile="P50", seed=42, time_limit_seconds=10)
    r90 = solve_cpsat(**kwargs, demand_profile="P90", seed=42, time_limit_seconds=10)
    # Both should find feasible assignments (7 available faculty for 3 sections)
    assert r50.feasible is True
    assert r90.feasible is True


def test_infeasible_result_has_conflicts_or_blocking_rules() -> None:
    """Infeasible CP-SAT result must provide at least one blocking rule or conflict."""
    data = load_fixture("infeasible_expertise")
    kwargs = scenario_args(data)
    r = solve_cpsat(**kwargs, seed=42, time_limit_seconds=10)
    assert not r.feasible
    has_info = len(r.blocking_rule_ids) > 0 or len(r.conflicts) > 0
    assert has_info, "Infeasible result should name at least one blocking rule"
