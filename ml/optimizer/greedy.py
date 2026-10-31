"""Deterministic greedy assignment baseline heuristic for university course allocation.

Assigns sections by most-constrained first, selecting the best-fit faculty candidate
with available contractual capacity. Serves as the comparative quality/feasibility
baseline against the Google OR-Tools CP-SAT solver.
"""

from __future__ import annotations

import logging
import sys
import time
import tracemalloc
from collections import defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
for p in [str(REPO_ROOT), str(REPO_ROOT / "backend"), str(REPO_ROOT / "ml")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from app.schemas.assignment import Assignment
from app.schemas.common import AssignmentSource
from ml.fit.scoring import fit
from ml.optimizer.cpsat import PreFilterResult, SolveResult, _extract_id, prefilter_eligible_pairs
from ml.optimizer.fairness import compute_fairness_summary

logger = logging.getLogger("ml.optimizer.greedy")


def solve_greedy(
    faculty: list[Any],
    courses: list[Any],
    sections: list[Any],
    resources: list[Any] | None = None,
    timeslots: list[Any] | None = None,
    previous_assignments: list[Any] | None = None,
    weights: dict[str, float] | None = None,
    demand_profile: str = "P50",
    run_id: str | None = None,
) -> SolveResult:
    """Run deterministic greedy course allocation baseline.

    Algorithm:
    1. Pre-filter candidates by static eligibility (HC-01, HC-04, HC-07).
    2. Short-circuit if any section has zero candidates.
    3. Order sections: Most-constrained first (fewest eligible instructors ascending,
       then contact hours descending).
    4. For each section, select the eligible faculty member with highest fit score
       who satisfies dynamic load limits (HC-02), timeslot non-conflict (HC-03),
       and preparation limits (HC-05).
    """
    tracemalloc.start()
    t_start = time.perf_counter()
    run_token = run_id or f"greedy-{int(t_start * 1000)}"

    course_map = {_extract_id(c): c for c in courses}
    faculty_map = {_extract_id(f): f for f in faculty}
    section_map = {_extract_id(s): s for s in sections}

    # STEP 1: Pre-filtering
    prefilter = prefilter_eligible_pairs(
        faculty=faculty,
        courses=courses,
        sections=sections,
        resources=resources,
        demand_profile=demand_profile,
    )

    # STEP 2: Short-circuit check for zero-eligible sections
    for sec in sections:
        sec_id = _extract_id(sec)
        eligible_fac = prefilter.pairs_by_section.get(sec_id, [])
        if not eligible_fac:
            t_end = time.perf_counter()
            _, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            blocking = prefilter.blocking_reasons_by_section.get(sec_id, ["HC-01"])
            cid = sec.get("course_id", "") if isinstance(sec, dict) else getattr(sec, "course_id", "")
            reason = (
                f"Section '{sec_id}' (course '{cid}') has zero eligible instructors "
                f"under greedy pre-filtering due to {', '.join(blocking)}."
            )
            return SolveResult(
                feasible=False,
                status="INFEASIBLE",
                assignments=[],
                solve_time_seconds=round(t_end - t_start, 4),
                objective_value=None,
                objective_bound=None,
                variable_count=len(prefilter.eligible_pairs),
                variables_avoided=prefilter.variables_avoided,
                peak_memory_mb=round(peak_mem / (1024 * 1024), 2),
                fairness={"gini": 0.0, "std_dev": 0.0, "max_min_gap": 0.0},
                fit_summary={"mean_fit": 0.0, "min_fit": 0.0},
                conflicts=[{"section_id": sec_id, "blocking_rules": blocking, "reason": reason}],
                explanation=reason,
                blocking_rule_ids=blocking,
            )

    # STEP 3: Most-constrained section ordering
    # Primary: count of eligible candidates ascending.
    # Secondary: section contact hours descending.
    def section_constraint_key(sec_obj: Any) -> tuple[int, float]:
        sid = _extract_id(sec_obj)
        cand_count = len(prefilter.pairs_by_section.get(sid, []))
        cid = sec_obj.get("course_id", "") if isinstance(sec_obj, dict) else getattr(sec_obj, "course_id", "")
        c_obj = course_map.get(cid)
        chours = (
            c_obj.get("contact_hours", 3.0)
            if isinstance(c_obj, dict)
            else getattr(c_obj, "contact_hours", 3.0)
        ) if c_obj else 3.0
        return (cand_count, -chours)

    sorted_sections = sorted(sections, key=section_constraint_key)

    # Dynamic tracking state
    assigned_load: dict[str, float] = { _extract_id(f): 0.0 for f in faculty }
    assigned_count: dict[str, int] = { _extract_id(f): 0 for f in faculty }
    assigned_preps: dict[str, set[str]] = { _extract_id(f): set() for f in faculty }
    assigned_slots: dict[str, set[str]] = { _extract_id(f): set() for f in faculty }

    assignments: list[Assignment] = []
    fit_scores_collected: list[float] = []

    for idx, sec in enumerate(sorted_sections):
        sid = _extract_id(sec)
        cid = sec.get("course_id", "") if isinstance(sec, dict) else getattr(sec, "course_id", "")
        cou_obj = course_map.get(cid)
        chours = (
            cou_obj.get("contact_hours", 3.0)
            if isinstance(cou_obj, dict)
            else getattr(cou_obj, "contact_hours", 3.0)
        ) if cou_obj else 3.0
        slot_id = sec.get("time_slot_id", None) if isinstance(sec, dict) else getattr(sec, "time_slot_id", None)

        candidate_fids = prefilter.pairs_by_section.get(sid, [])
        valid_candidates = []

        for fid in candidate_fids:
            fac_obj = faculty_map[fid]
            max_load = float(
                fac_obj.get("max_weekly_load_hours", 12.0)
                if isinstance(fac_obj, dict)
                else getattr(fac_obj, "max_weekly_load_hours", 12.0)
            )
            max_courses = int(
                fac_obj.get("max_courses", 4)
                if isinstance(fac_obj, dict)
                else getattr(fac_obj, "max_courses", 4)
            )
            max_preps = int(
                fac_obj.get("max_preparations", 2)
                if isinstance(fac_obj, dict)
                else getattr(fac_obj, "max_preparations", 2)
            )

            # HC-02: Contact hours limit
            if assigned_load[fid] + chours > max_load + 1e-6:
                continue

            # HC-02: Max courses limit
            if max_courses > 0 and assigned_count[fid] + 1 > max_courses:
                continue

            # HC-03: Time clash
            if slot_id and slot_id in assigned_slots[fid]:
                continue

            # HC-05: Preparations limit
            new_preps = assigned_preps[fid] | {cid}
            if max_preps > 0 and len(new_preps) > max_preps:
                continue

            # Candidate is feasible: compute fit score and spare capacity
            fit_res = fit(fac_obj, cou_obj)
            score_val = float(fit_res)
            spare_capacity = max_load - (assigned_load[fid] + chours)

            preferred = (
                fac_obj.get("preferred_course_ids", [])
                if isinstance(fac_obj, dict)
                else getattr(fac_obj, "preferred_course_ids", [])
            )
            pref_bonus = 0.05 if cid in preferred else 0.0

            valid_candidates.append({
                "faculty_id": fid,
                "fit_score": score_val,
                "breakdown": fit_res.breakdown,
                "spare_capacity": spare_capacity,
                "pref_bonus": pref_bonus,
            })

        if not valid_candidates:
            # Greedy heuristic hit a dead end (infeasible under greedy choices)
            t_end = time.perf_counter()
            _, peak_mem = tracemalloc.get_traced_memory()
            tracemalloc.stop()

            reason = (
                f"Greedy allocation failed: No faculty has sufficient capacity, open time slot, "
                f"or prep headroom for section '{sid}' (course '{cid}')."
            )
            return SolveResult(
                feasible=False,
                status="INFEASIBLE",
                assignments=[],
                solve_time_seconds=round(t_end - t_start, 4),
                objective_value=None,
                objective_bound=None,
                variable_count=len(prefilter.eligible_pairs),
                variables_avoided=prefilter.variables_avoided,
                peak_memory_mb=round(peak_mem / (1024 * 1024), 2),
                fairness={"gini": 0.0, "std_dev": 0.0, "max_min_gap": 0.0},
                fit_summary={"mean_fit": 0.0, "min_fit": 0.0},
                conflicts=[{"section_id": sid, "reason": reason}],
                explanation=reason,
                blocking_rule_ids=["HC-02", "HC-03", "HC-05"],
            )

        # Pick best candidate: Highest fit score, then highest spare capacity
        valid_candidates.sort(
            key=lambda c: (c["fit_score"] + c["pref_bonus"], c["spare_capacity"]),
            reverse=True,
        )
        chosen = valid_candidates[0]
        chosen_fid = chosen["faculty_id"]

        # Commit assignment
        assigned_load[chosen_fid] += chours
        assigned_count[chosen_fid] += 1
        assigned_preps[chosen_fid].add(cid)
        if slot_id:
            assigned_slots[chosen_fid].add(slot_id)

        fit_scores_collected.append(chosen["fit_score"])

        numeric_breakdown = {
            k: float(v) for k, v in chosen["breakdown"].items() if isinstance(v, (int, float))
        }

        asgn = Assignment(
            id=f"asgn-{run_token}-{idx}",
            section_id=sid,
            faculty_id=chosen_fid,
            source=AssignmentSource.BASELINE,
            fit_score=round(chosen["fit_score"], 4),
            fit_breakdown=numeric_breakdown,
            rule_ids_satisfied=["HC-01", "HC-02", "HC-03", "HC-04", "HC-05", "HC-06", "HC-07"],
            rule_ids_violated=[],
            run_id=run_token,
            created_at=datetime.now(UTC),
        )
        assignments.append(asgn)

    t_end = time.perf_counter()
    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    faculty_ranks = {
        _extract_id(f): (f.get("rank", "") if isinstance(f, dict) else getattr(f, "rank", ""))
        for f in faculty
    }
    fairness_metrics = compute_fairness_summary(assigned_load, faculty_ranks)
    fit_summary = {
        "mean_fit": round(float(sum(fit_scores_collected) / len(fit_scores_collected)), 4) if fit_scores_collected else 0.0,
        "min_fit": round(min(fit_scores_collected), 4) if fit_scores_collected else 0.0,
        "max_fit": round(max(fit_scores_collected), 4) if fit_scores_collected else 0.0,
        "total_assigned_sections": len(assignments),
    }

    return SolveResult(
        feasible=True,
        status="FEASIBLE",
        assignments=assignments,
        solve_time_seconds=round(t_end - t_start, 4),
        objective_value=round(sum(fit_scores_collected), 4),
        objective_bound=None,
        variable_count=len(prefilter.eligible_pairs),
        variables_avoided=prefilter.variables_avoided,
        peak_memory_mb=round(peak_mem / (1024 * 1024), 2),
        fairness=fairness_metrics,
        fit_summary=fit_summary,
        conflicts=[],
        explanation="Feasible schedule generated by greedy baseline heuristic.",
        blocking_rule_ids=[],
    )
