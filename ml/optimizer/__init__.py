"""Constraint optimization and workload balancing subpackage."""

from ml.optimizer.cpsat import PreFilterResult, SolveResult, prefilter_eligible_pairs, solve_cpsat
from ml.optimizer.explain import ConflictDetail, ExplanationResult, generate_explanation
from ml.optimizer.fairness import (
    compute_fairness_summary,
    compute_gini,
    compute_max_min_gap,
    compute_standard_deviation,
)
from ml.optimizer.greedy import solve_greedy
from ml.optimizer.repair import RepairAlternative, generate_repairs

__all__ = [
    "ConflictDetail",
    "ExplanationResult",
    "PreFilterResult",
    "RepairAlternative",
    "SolveResult",
    "compute_fairness_summary",
    "compute_gini",
    "compute_max_min_gap",
    "compute_standard_deviation",
    "generate_explanation",
    "generate_repairs",
    "prefilter_eligible_pairs",
    "solve_cpsat",
    "solve_greedy",
]
