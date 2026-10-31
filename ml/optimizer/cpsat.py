"""Google OR-Tools CP-SAT formulation for constrained, fair course assignment.

Adheres strictly to the CPU-only compute budget and 512 MB RAM envelope:
- STEP 1 (Pre-filtering): Prunes invalid (faculty, section) pairs violating HC-01, HC-04,
  or HC-07 before variable instantiation.
- STEP 2: Immediate infeasibility short-circuit if any section has zero eligible instructors.
- Single-threaded CP-SAT execution (num_workers=1) with integer-scaled multi-objective:
    Maximize w1 * fit - w2 * fairness_gap - w3 * pref_miss + w4 * continuity
"""

from __future__ import annotations

import logging
import sys
import time
import tracemalloc
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
for p in [str(REPO_ROOT), str(REPO_ROOT / "backend"), str(REPO_ROOT / "ml")]:
    if p not in sys.path:
        sys.path.insert(0, p)

from ortools.sat.python import cp_model

from app.schemas.assignment import Assignment
from app.schemas.common import AssignmentSource
from ml.fit.scoring import check_hc01, fit
from ml.optimizer.fairness import compute_fairness_summary

logger = logging.getLogger("ml.optimizer.cpsat")

SCALE_FACTOR = 1000


@dataclass
class PreFilterResult:
    """Outcome of STEP 1 pre-filtering."""

    eligible_pairs: list[tuple[str, str]]  # list of (faculty_id, section_id)
    pairs_by_section: dict[str, list[str]]  # section_id -> list[faculty_id]
    pairs_by_faculty: dict[str, list[str]]  # faculty_id -> list[section_id]
    total_possible_pairs: int
    variables_avoided: int
    blocking_reasons_by_section: dict[str, list[str]]  # section_id -> list[str] of rule_ids


@dataclass
class SolveResult:
    """Comprehensive solver output with diagnostic and benchmark metrics."""

    feasible: bool
    status: str  # OPTIMAL, FEASIBLE, INFEASIBLE, UNKNOWN
    assignments: list[Assignment]
    solve_time_seconds: float
    objective_value: float | None
    objective_bound: float | None
    variable_count: int
    variables_avoided: int
    peak_memory_mb: float
    fairness: dict[str, Any]
    fit_summary: dict[str, Any]
    conflicts: list[dict[str, Any]]
    explanation: str | None
    blocking_rule_ids: list[str] = field(default_factory=list)
    raw_status: int = 0


def _extract_id(obj: Any) -> str:
    """Retrieve string identifier from domain model or dictionary."""
    if isinstance(obj, dict):
        return str(obj.get("id", obj.get("rule_id", "")))
    return str(getattr(obj, "id", getattr(obj, "rule_id", "")))


def prefilter_eligible_pairs(
    faculty: list[Any],
    courses: list[Any],
    sections: list[Any],
    resources: list[Any] | None = None,
    demand_profile: str = "P50",
) -> PreFilterResult:
    """STEP 1: Prune invalid (faculty, section) pairs violating HC-01, HC-04, or HC-07.

    Creates decision variables ONLY for eligible pairs in E, drastically cutting problem scale.
    """
    course_map = {_extract_id(c): c for c in courses}
    resource_map = {_extract_id(r): r for r in (resources or [])}

    total_possible = len(faculty) * len(sections)
    eligible_pairs: list[tuple[str, str]] = []
    pairs_by_section: dict[str, list[str]] = defaultdict(list)
    pairs_by_faculty: dict[str, list[str]] = defaultdict(list)
    blocking_reasons_by_section: dict[str, list[str]] = defaultdict(list)

    for sec in sections:
        sec_id = _extract_id(sec)
        cid = sec.get("course_id", "") if isinstance(sec, dict) else getattr(sec, "course_id", "")
        course = course_map.get(cid)
        if not course:
            continue

        term = sec.get("term", "") if isinstance(sec, dict) else getattr(sec, "term", "")
        slot_id = sec.get("time_slot_id", None) if isinstance(sec, dict) else getattr(sec, "time_slot_id", None)

        # Section size based on demand profile
        if demand_profile.upper() == "P90":
            sec_size = (
                sec.get("size_p90", sec.get("expected_size", 0))
                if isinstance(sec, dict)
                else getattr(sec, "size_p90", getattr(sec, "expected_size", 0))
            )
        else:
            sec_size = (
                sec.get("size_p50", sec.get("expected_size", 0))
                if isinstance(sec, dict)
                else getattr(sec, "size_p50", getattr(sec, "expected_size", 0))
            )

        # HC-07 check (Course required resources)
        req_res_ids = (
            course.get("required_resource_ids", [])
            if isinstance(course, dict)
            else getattr(course, "required_resource_ids", [])
        )
        resource_violated = False
        res_violation_reason = ""
        for r_id in req_res_ids:
            res = resource_map.get(r_id)
            if not res:
                continue
            r_cap = res.get("capacity", 0) if isinstance(res, dict) else getattr(res, "capacity", 0)
            r_unavail = (
                res.get("unavailable_slots", [])
                if isinstance(res, dict)
                else getattr(res, "unavailable_slots", [])
            )
            if slot_id and slot_id in r_unavail:
                resource_violated = True
                res_violation_reason = f"Resource '{r_id}' is unavailable in slot '{slot_id}' (HC-07)"
                break
            if r_cap < sec_size:
                resource_violated = True
                res_violation_reason = f"Resource '{r_id}' capacity ({r_cap}) < section size ({sec_size}) (HC-07)"
                break

        for fac in faculty:
            fac_id = _extract_id(fac)
            reasons: list[str] = []

            # HC-07 Check
            if resource_violated:
                reasons.append("HC-07")

            # HC-01 Check: Minimum proficiency on required tags
            eligible_hc01, _ = check_hc01(fac, course)
            if not eligible_hc01:
                reasons.append("HC-01")

            # HC-04 Check: Sabbatical leave or unavailable time slot
            leave_terms = (
                fac.get("leave_terms", [])
                if isinstance(fac, dict)
                else getattr(fac, "leave_terms", [])
            )
            if term and term in leave_terms:
                reasons.append("HC-04")

            unavail_slots = (
                fac.get("unavailable_slots", [])
                if isinstance(fac, dict)
                else getattr(fac, "unavailable_slots", [])
            )
            if slot_id and slot_id in unavail_slots:
                reasons.append("HC-04")

            if not reasons:
                eligible_pairs.append((fac_id, sec_id))
                pairs_by_section[sec_id].append(fac_id)
                pairs_by_faculty[fac_id].append(sec_id)
            else:
                for r in reasons:
                    if r not in blocking_reasons_by_section[sec_id]:
                        blocking_reasons_by_section[sec_id].append(r)

    avoided = total_possible - len(eligible_pairs)
    logger.info(
        f"Pre-filtering pruned {avoided} / {total_possible} variables "
        f"({len(eligible_pairs)} active candidate variables)"
    )

    return PreFilterResult(
        eligible_pairs=eligible_pairs,
        pairs_by_section=dict(pairs_by_section),
        pairs_by_faculty=dict(pairs_by_faculty),
        total_possible_pairs=total_possible,
        variables_avoided=avoided,
        blocking_reasons_by_section=dict(blocking_reasons_by_section),
    )


def solve_cpsat(
    faculty: list[Any],
    courses: list[Any],
    sections: list[Any],
    resources: list[Any] | None = None,
    timeslots: list[Any] | None = None,
    previous_assignments: list[Any] | None = None,
    weights: dict[str, float] | None = None,
    demand_profile: str = "P50",
    time_limit_seconds: float = 20.0,
    seed: int = 42,
    enable_assumptions: bool = True,
    run_id: str | None = None,
) -> SolveResult:
    """Optimize course section allocations using Google OR-Tools CP-SAT.

    Enforces HC-01 through HC-07 while maximizing multi-objective fairness, fit,
    preferences, and continuity within constrained CPU runtime.
    """
    tracemalloc.start()
    t_start = time.perf_counter()
    run_token = run_id or f"run-{int(t_start * 1000)}"

    rule_weights = {
        "SC-01": 3.0,
        "SC-02": 2.0,
        "SC-03": 1.5,
        "SC-04": 1.0,
        "SC-05": 2.5,
    }
    if weights:
        rule_weights.update(weights)

    # -------------------------------------------------------------------------
    # STEP 1: Pre-filtering
    # -------------------------------------------------------------------------
    prefilter = prefilter_eligible_pairs(
        faculty=faculty,
        courses=courses,
        sections=sections,
        resources=resources,
        demand_profile=demand_profile,
    )

    # -------------------------------------------------------------------------
    # STEP 2: Short-circuit check for zero-eligible sections
    # -------------------------------------------------------------------------
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
                f"due to pre-filter rule(s): {', '.join(blocking)}."
            )
            logger.warning(f"Immediate infeasibility: {reason}")

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
                raw_status=cp_model.INFEASIBLE,
            )

    # -------------------------------------------------------------------------
    # CP-SAT Model Formulation
    # -------------------------------------------------------------------------
    model = cp_model.CpModel()
    course_map = {_extract_id(c): c for c in courses}
    faculty_map = {_extract_id(f): f for f in faculty}
    section_map = {_extract_id(s): s for s in sections}

    # Binary variables x[f, s] ONLY for (f, s) in E
    x: dict[tuple[str, str], cp_model.IntVar] = {}
    for fid, sid in prefilter.eligible_pairs:
        x[(fid, sid)] = model.NewBoolVar(f"x_{fid}_{sid}")

    # Assumption literals for explainability if model is proven infeasible
    assumption_literals: list[cp_model.IntVar] = []
    assumption_info: dict[int, tuple[str, str, str]] = {}  # lit_index -> (rule_id, entity_id, description)

    def add_guarded_constraint(ct, rule_id: str, entity_id: str, desc: str):
        if enable_assumptions:
            lit = model.NewBoolVar(f"assume_{rule_id}_{entity_id}_{len(assumption_literals)}")
            model.Add(ct).OnlyEnforceIf(lit)
            assumption_literals.append(lit)
            assumption_info[lit.Index()] = (rule_id, entity_id, desc)
        else:
            model.Add(ct)

    # HC-06: Exactly one faculty member assigned to each section
    for sec in sections:
        sid = _extract_id(sec)
        sec_fac = prefilter.pairs_by_section.get(sid, [])
        cand_vars = [x[(fid, sid)] for fid in sec_fac if (fid, sid) in x]
        add_guarded_constraint(
            sum(cand_vars) == 1,
            rule_id="HC-06",
            entity_id=sid,
            desc=f"Section {sid} must have exactly one instructor assigned",
        )

    # HC-02: Maximum weekly contact hours and course caps
    for fac in faculty:
        fid = _extract_id(fac)
        max_load = float(
            fac.get("max_weekly_load_hours", 12.0)
            if isinstance(fac, dict)
            else getattr(fac, "max_weekly_load_hours", 12.0)
        )
        max_courses = int(
            fac.get("max_courses", 4)
            if isinstance(fac, dict)
            else getattr(fac, "max_courses", 4)
        )

        assigned_secs = prefilter.pairs_by_faculty.get(fid, [])
        if not assigned_secs:
            continue

        # Contact hours constraint (scaled by 10 for integer exactness)
        hour_terms = []
        for sid in assigned_secs:
            sec_obj = section_map[sid]
            cid = sec_obj.get("course_id", "") if isinstance(sec_obj, dict) else getattr(sec_obj, "course_id", "")
            cou_obj = course_map.get(cid)
            chours = (
                cou_obj.get("contact_hours", 3.0)
                if isinstance(cou_obj, dict)
                else getattr(cou_obj, "contact_hours", 3.0)
            ) if cou_obj else 3.0
            hour_terms.append(int(round(chours * 10)) * x[(fid, sid)])

        add_guarded_constraint(
            sum(hour_terms) <= int(round(max_load * 10)),
            rule_id="HC-02",
            entity_id=fid,
            desc=f"Faculty {fid} weekly contact hours must not exceed {max_load}h",
        )

        # Max courses constraint
        if max_courses > 0:
            add_guarded_constraint(
                sum(x[(fid, sid)] for sid in assigned_secs) <= max_courses,
                rule_id="HC-02",
                entity_id=fid,
                desc=f"Faculty {fid} course section count must not exceed {max_courses}",
            )

    # HC-03: No time clashes (grouped by timeslot)
    for fac in faculty:
        fid = _extract_id(fac)
        assigned_secs = prefilter.pairs_by_faculty.get(fid, [])

        # Group sections by timeslot
        slot_groups: dict[str, list[str]] = defaultdict(list)
        for sid in assigned_secs:
            sec_obj = section_map[sid]
            slot = sec_obj.get("time_slot_id", None) if isinstance(sec_obj, dict) else getattr(sec_obj, "time_slot_id", None)
            if slot:
                slot_groups[slot].append(sid)

        for slot, slot_sids in slot_groups.items():
            if len(slot_sids) > 1:
                add_guarded_constraint(
                    sum(x[(fid, sid)] for sid in slot_sids) <= 1,
                    rule_id="HC-03",
                    entity_id=f"{fid}_{slot}",
                    desc=f"Faculty {fid} cannot teach multiple sections in slot '{slot}'",
                )

    # HC-05: Maximum distinct course preparations
    for fac in faculty:
        fid = _extract_id(fac)
        max_preps = int(
            fac.get("max_preparations", 2)
            if isinstance(fac, dict)
            else getattr(fac, "max_preparations", 2)
        )
        assigned_secs = prefilter.pairs_by_faculty.get(fid, [])

        # Map distinct courses taught by this faculty candidate
        courses_for_fac: dict[str, list[str]] = defaultdict(list)
        for sid in assigned_secs:
            sec_obj = section_map[sid]
            cid = sec_obj.get("course_id", "") if isinstance(sec_obj, dict) else getattr(sec_obj, "course_id", "")
            courses_for_fac[cid].append(sid)

        y_vars: list[cp_model.IntVar] = []
        for cid, course_sids in courses_for_fac.items():
            y_fc = model.NewBoolVar(f"y_{fid}_{cid}")
            y_vars.append(y_fc)
            for sid in course_sids:
                model.Add(x[(fid, sid)] <= y_fc)

        if max_preps > 0 and y_vars:
            add_guarded_constraint(
                sum(y_vars) <= max_preps,
                rule_id="HC-05",
                entity_id=fid,
                desc=f"Faculty {fid} distinct course preps must not exceed {max_preps}",
            )

    if enable_assumptions and assumption_literals:
        model.AddAssumptions(assumption_literals)

    # -------------------------------------------------------------------------
    # Multi-Objective Function Construction
    # -------------------------------------------------------------------------
    # 1. SC-01: Expertise fit score
    fit_terms = []
    cached_fit_scores: dict[tuple[str, str], float] = {}
    cached_breakdowns: dict[tuple[str, str], dict[str, Any]] = {}

    for fid, sid in prefilter.eligible_pairs:
        fac_obj = faculty_map[fid]
        sec_obj = section_map[sid]
        cid = sec_obj.get("course_id", "") if isinstance(sec_obj, dict) else getattr(sec_obj, "course_id", "")
        cou_obj = course_map.get(cid)

        res = fit(fac_obj, cou_obj)
        score_val = float(res)
        cached_fit_scores[(fid, sid)] = score_val
        cached_breakdowns[(fid, sid)] = res.breakdown

        coeff = int(round(rule_weights["SC-01"] * score_val * SCALE_FACTOR))
        fit_terms.append(coeff * x[(fid, sid)])

    # 2. SC-02: Fairness penalty (Minimizing max-min gap of normalized load)
    # Normalized load = sum(contact_hours) / max_weekly_load_hours
    norm_load_vars: list[cp_model.IntVar] = []
    for fac in faculty:
        fid = _extract_id(fac)
        max_load = float(
            fac.get("max_weekly_load_hours", 12.0)
            if isinstance(fac, dict)
            else getattr(fac, "max_weekly_load_hours", 12.0)
        )
        assigned_secs = prefilter.pairs_by_faculty.get(fid, [])
        if max_load <= 0.0 or not assigned_secs:
            continue

        load_expr_terms = []
        for sid in assigned_secs:
            sec_obj = section_map[sid]
            cid = sec_obj.get("course_id", "") if isinstance(sec_obj, dict) else getattr(sec_obj, "course_id", "")
            cou_obj = course_map.get(cid)
            chours = (
                cou_obj.get("contact_hours", 3.0)
                if isinstance(cou_obj, dict)
                else getattr(cou_obj, "contact_hours", 3.0)
            ) if cou_obj else 3.0

            scaled_fraction = int(round((chours / max_load) * SCALE_FACTOR))
            load_expr_terms.append(scaled_fraction * x[(fid, sid)])

        fac_norm_var = model.NewIntVar(0, SCALE_FACTOR * 2, f"norm_load_{fid}")
        model.Add(fac_norm_var == sum(load_expr_terms))
        norm_load_vars.append(fac_norm_var)

    fairness_penalty_term = 0
    if len(norm_load_vars) >= 2:
        max_load_var = model.NewIntVar(0, SCALE_FACTOR * 2, "max_norm_load")
        min_load_var = model.NewIntVar(0, SCALE_FACTOR * 2, "min_norm_load")
        model.AddMaxEquality(max_load_var, norm_load_vars)
        model.AddMinEquality(min_load_var, norm_load_vars)

        gap_var = model.NewIntVar(0, SCALE_FACTOR * 2, "fairness_gap")
        model.Add(gap_var == max_load_var - min_load_var)
        fairness_penalty_term = int(round(rule_weights["SC-02"] * SCALE_FACTOR)) * gap_var

    # 3. SC-03: Preference miss penalty
    pref_miss_terms = []
    for fid, sid in prefilter.eligible_pairs:
        fac_obj = faculty_map[fid]
        sec_obj = section_map[sid]
        cid = sec_obj.get("course_id", "") if isinstance(sec_obj, dict) else getattr(sec_obj, "course_id", "")
        preferred = (
            fac_obj.get("preferred_course_ids", [])
            if isinstance(fac_obj, dict)
            else getattr(fac_obj, "preferred_course_ids", [])
        )
        if cid not in preferred:
            coeff = int(round(rule_weights["SC-03"] * SCALE_FACTOR))
            pref_miss_terms.append(coeff * x[(fid, sid)])

    # 4. SC-04: Pedagogical continuity bonus
    prev_instructors_by_course: dict[str, set[str]] = defaultdict(set)
    if previous_assignments:
        for pa in previous_assignments:
            pid = pa.get("faculty_id", "") if isinstance(pa, dict) else getattr(pa, "faculty_id", "")
            pcid = pa.get("course_id", "") if isinstance(pa, dict) else getattr(pa, "course_id", "")
            if pid and pcid:
                prev_instructors_by_course[pcid].add(pid)

    continuity_terms = []
    for fid, sid in prefilter.eligible_pairs:
        sec_obj = section_map[sid]
        cid = sec_obj.get("course_id", "") if isinstance(sec_obj, dict) else getattr(sec_obj, "course_id", "")
        if fid in prev_instructors_by_course[cid]:
            coeff = int(round(rule_weights["SC-04"] * SCALE_FACTOR))
            continuity_terms.append(coeff * x[(fid, sid)])

    # Total Objective
    total_objective = (
        sum(fit_terms)
        - fairness_penalty_term
        - sum(pref_miss_terms)
        + sum(continuity_terms)
    )
    model.Maximize(total_objective)

    # -------------------------------------------------------------------------
    # Solver Invocation (Single-threaded CPU budget)
    # -------------------------------------------------------------------------
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = float(time_limit_seconds)
    solver.parameters.num_workers = 1
    solver.parameters.random_seed = int(seed)

    status_code = solver.Solve(model)
    t_end = time.perf_counter()
    solve_duration = round(t_end - t_start, 4)

    _, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    peak_mem_mb = round(peak_mem / (1024 * 1024), 2)

    status_str = solver.StatusName(status_code)
    is_feasible = status_code in (cp_model.OPTIMAL, cp_model.FEASIBLE)

    if not is_feasible:
        # Extract minimal conflicting core via assumption literals
        conflicts = []
        blocking_rules: list[str] = []
        if enable_assumptions and status_code == cp_model.INFEASIBLE:
            core_lits = solver.SufficientAssumptionsForInfeasibility()
            for lit_idx in core_lits:
                if lit_idx in assumption_info:
                    r_id, ent_id, desc = assumption_info[lit_idx]
                    conflicts.append({"rule_id": r_id, "entity_id": ent_id, "description": desc})
                    if r_id not in blocking_rules:
                        blocking_rules.append(r_id)

        explanation = (
            f"Schedule optimization is {status_str} after {solve_duration}s. "
            f"Active conflict rules: {', '.join(blocking_rules) if blocking_rules else 'Capacity / Feasibility exhaustion'}."
        )

        return SolveResult(
            feasible=False,
            status=status_str,
            assignments=[],
            solve_time_seconds=solve_duration,
            objective_value=None,
            objective_bound=solver.BestObjectiveBound() if hasattr(solver, "BestObjectiveBound") else None,
            variable_count=len(prefilter.eligible_pairs),
            variables_avoided=prefilter.variables_avoided,
            peak_memory_mb=peak_mem_mb,
            fairness={"gini": 0.0, "std_dev": 0.0, "max_min_gap": 0.0},
            fit_summary={"mean_fit": 0.0, "min_fit": 0.0},
            conflicts=conflicts,
            explanation=explanation,
            blocking_rule_ids=blocking_rules,
            raw_status=status_code,
        )

    # -------------------------------------------------------------------------
    # Parse Solution Assignments
    # -------------------------------------------------------------------------
    assignments: list[Assignment] = []
    loads_by_faculty: dict[str, float] = { _extract_id(f): 0.0 for f in faculty }
    fit_scores_collected: list[float] = []

    for idx, (fid, sid) in enumerate(prefilter.eligible_pairs):
        if solver.BooleanValue(x[(fid, sid)]):
            fit_val = cached_fit_scores.get((fid, sid), 0.8)
            bdown = cached_breakdowns.get((fid, sid), {})
            fit_scores_collected.append(fit_val)

            sec_obj = section_map[sid]
            cid = sec_obj.get("course_id", "") if isinstance(sec_obj, dict) else getattr(sec_obj, "course_id", "")
            cou_obj = course_map.get(cid)
            chours = (
                cou_obj.get("contact_hours", 3.0)
                if isinstance(cou_obj, dict)
                else getattr(cou_obj, "contact_hours", 3.0)
            ) if cou_obj else 3.0

            loads_by_faculty[fid] = loads_by_faculty.get(fid, 0.0) + chours

            numeric_breakdown = {
                k: float(v) for k, v in bdown.items() if isinstance(v, (int, float))
            }

            asgn = Assignment(
                id=f"asgn-{run_token}-{idx}",
                section_id=sid,
                faculty_id=fid,
                source=AssignmentSource.SOLVER,
                fit_score=round(fit_val, 4),
                fit_breakdown=numeric_breakdown,
                rule_ids_satisfied=["HC-01", "HC-02", "HC-03", "HC-04", "HC-05", "HC-06", "HC-07"],
                rule_ids_violated=[],
                run_id=run_token,
                created_at=datetime.now(UTC),
            )
            assignments.append(asgn)

    # Departmental fairness and fit metrics
    faculty_ranks = {
        _extract_id(f): (f.get("rank", "") if isinstance(f, dict) else getattr(f, "rank", ""))
        for f in faculty
    }
    fairness_metrics = compute_fairness_summary(loads_by_faculty, faculty_ranks)
    fit_summary = {
        "mean_fit": round(float(sum(fit_scores_collected) / len(fit_scores_collected)), 4) if fit_scores_collected else 0.0,
        "min_fit": round(min(fit_scores_collected), 4) if fit_scores_collected else 0.0,
        "max_fit": round(max(fit_scores_collected), 4) if fit_scores_collected else 0.0,
        "total_assigned_sections": len(assignments),
    }

    return SolveResult(
        feasible=True,
        status=status_str,
        assignments=assignments,
        solve_time_seconds=solve_duration,
        objective_value=round(solver.ObjectiveValue() / SCALE_FACTOR, 4),
        objective_bound=round(solver.BestObjectiveBound() / SCALE_FACTOR, 4),
        variable_count=len(prefilter.eligible_pairs),
        variables_avoided=prefilter.variables_avoided,
        peak_memory_mb=peak_mem_mb,
        fairness=fairness_metrics,
        fit_summary=fit_summary,
        conflicts=[],
        explanation="Feasible schedule certified by CP-SAT solver.",
        blocking_rule_ids=[],
        raw_status=status_code,
    )
