"""Automated schedule repair alternatives generation for infeasible planning scenarios.

Generates structured repair interventions:
1. Relax HC-05 (expand course preparation limits)
2. Add qualified adjunct capacity
3. Relocate / move conflicting time slots (resolve HC-03)
4. Facility upgrade / capacity expansion (resolve HC-07)

Re-solves each candidate repair under a short 5-second time limit and scores
its impact on fairness, expertise fit, and constraint violations.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any

from ml.optimizer.cpsat import SolveResult, _extract_id, solve_cpsat


@dataclass
class RepairAlternative:
    """Actionable repair alternative with re-solved feasibility and quality metrics."""

    repair_type: str  # relax_hc05, add_adjunct, move_timeslot, expand_facility
    title: str
    description: str
    changes: list[dict[str, Any]]
    feasible_after_repair: bool
    solve_result: SolveResult
    fairness_gini: float
    mean_fit: float
    new_violations: list[str] = field(default_factory=list)
    rule_relaxed: str | None = None


def generate_repairs(
    faculty: list[Any],
    courses: list[Any],
    sections: list[Any],
    resources: list[Any] | None = None,
    timeslots: list[Any] | None = None,
    previous_assignments: list[Any] | None = None,
    solve_result: SolveResult | None = None,
    demand_profile: str = "P50",
    max_repairs: int = 3,
    re_solve_time_limit: float = 5.0,
    seed: int = 42,
) -> list[RepairAlternative]:
    """Generate 2-3 automated repair candidates for an infeasible assignment problem."""
    # If initial result was not provided or feasible, check feasibility first
    if solve_result is None:
        solve_result = solve_cpsat(
            faculty=faculty,
            courses=courses,
            sections=sections,
            resources=resources,
            timeslots=timeslots,
            previous_assignments=previous_assignments,
            demand_profile=demand_profile,
            time_limit_seconds=re_solve_time_limit,
            seed=seed,
        )

    if solve_result.feasible:
        return []

    blocking_rules = set(solve_result.blocking_rule_ids)
    repairs: list[RepairAlternative] = []

    # -------------------------------------------------------------------------
    # Alternative 1: Relax HC-05 (Increase Max Course Preparations)
    # -------------------------------------------------------------------------
    faculty_hc05 = copy.deepcopy(faculty)
    for f in faculty_hc05:
        curr = f.get("max_preparations", 2) if isinstance(f, dict) else getattr(f, "max_preparations", 2)
        if isinstance(f, dict):
            f["max_preparations"] = curr + 3
            # Also increase max_weekly_load if tight
            f["max_weekly_load_hours"] = f.get("max_weekly_load_hours", 12.0) + 6.0
            f["max_courses"] = f.get("max_courses", 3) + 3
        else:
            setattr(f, "max_preparations", curr + 3)
            setattr(f, "max_weekly_load_hours", getattr(f, "max_weekly_load_hours", 12.0) + 6.0)
            setattr(f, "max_courses", getattr(f, "max_courses", 3) + 3)

    res_hc05 = solve_cpsat(
        faculty=faculty_hc05,
        courses=courses,
        sections=sections,
        resources=resources,
        timeslots=timeslots,
        previous_assignments=previous_assignments,
        demand_profile=demand_profile,
        time_limit_seconds=re_solve_time_limit,
        seed=seed,
    )

    repairs.append(
        RepairAlternative(
            repair_type="relax_hc05",
            title="Relax Course Preparation Limits (HC-05)",
            description="Temporarily expand maximum distinct course preparations per faculty member by +3.",
            changes=[{"action": "increase_max_preparations", "delta": 3}],
            feasible_after_repair=res_hc05.feasible,
            solve_result=res_hc05,
            fairness_gini=res_hc05.fairness.get("gini", 0.0),
            mean_fit=res_hc05.fit_summary.get("mean_fit", 0.0),
            new_violations=["HC-05 (Relaxed)"] if res_hc05.feasible else [],
            rule_relaxed="HC-05",
        )
    )

    # -------------------------------------------------------------------------
    # Alternative 2: Add Adjunct / Visiting Capacity
    # -------------------------------------------------------------------------
    faculty_adjunct = copy.deepcopy(faculty)
    # Collect all course required tags to give adjunct broad competency
    all_tags = []
    for c in courses:
        tags = c.get("required_tags", []) if isinstance(c, dict) else getattr(c, "required_tags", [])
        all_tags.extend(tags)
    unique_tags = list(set(all_tags))

    adjunct_instructor = {
        "id": "f-adjunct-support",
        "name": "Adjunct Instructor",
        "email": "adjunct@university.edu",
        "rank": "Adjunct",
        "expertise": [{"tag": t, "proficiency": 5} for t in unique_tags],
        "max_weekly_load_hours": 15.0,
        "max_courses": 4,
        "min_courses": 0,
        "max_preparations": 4,
        "unavailable_slots": [],
        "leave_terms": [],
        "preferred_course_ids": [],
    }
    faculty_adjunct.append(adjunct_instructor)

    res_adjunct = solve_cpsat(
        faculty=faculty_adjunct,
        courses=courses,
        sections=sections,
        resources=resources,
        timeslots=timeslots,
        previous_assignments=previous_assignments,
        demand_profile=demand_profile,
        time_limit_seconds=re_solve_time_limit,
        seed=seed,
    )

    repairs.append(
        RepairAlternative(
            repair_type="add_adjunct",
            title="Onboard Qualified Adjunct Instructor",
            description="Introduce a temporary adjunct instructor with expertise across required syllabus tags.",
            changes=[{"action": "add_faculty", "faculty_id": "f-adjunct-support", "capacity_hours": 15.0}],
            feasible_after_repair=res_adjunct.feasible,
            solve_result=res_adjunct,
            fairness_gini=res_adjunct.fairness.get("gini", 0.0),
            mean_fit=res_adjunct.fit_summary.get("mean_fit", 0.0),
            new_violations=[],
            rule_relaxed=None,
        )
    )

    # -------------------------------------------------------------------------
    # Alternative 3: Move Conflicting Time Slot (HC-03)
    # -------------------------------------------------------------------------
    sections_rescheduled = copy.deepcopy(sections)
    # If sections share a time slot, shift the second one to an alternative slot
    slots_seen: set[str] = set()
    slot_changed = False
    for s in sections_rescheduled:
        slot = s.get("time_slot_id", None) if isinstance(s, dict) else getattr(s, "time_slot_id", None)
        if slot and slot in slots_seen:
            new_slot = "TS-WED-1430" if slot != "TS-WED-1430" else "TS-THU-0900"
            if isinstance(s, dict):
                s["time_slot_id"] = new_slot
            else:
                setattr(s, "time_slot_id", new_slot)
            slot_changed = True
            break
        elif slot:
            slots_seen.add(slot)

    if not slot_changed and len(sections_rescheduled) >= 2:
        # Move first section to a non-conflicting default
        s0 = sections_rescheduled[0]
        if isinstance(s0, dict):
            s0["time_slot_id"] = "TS-THU-1030"
        else:
            setattr(s0, "time_slot_id", "TS-THU-1030")

    res_timeslot = solve_cpsat(
        faculty=faculty,
        courses=courses,
        sections=sections_rescheduled,
        resources=resources,
        timeslots=timeslots,
        previous_assignments=previous_assignments,
        demand_profile=demand_profile,
        time_limit_seconds=re_solve_time_limit,
        seed=seed,
    )

    repairs.append(
        RepairAlternative(
            repair_type="move_timeslot",
            title="Reschedule Colliding Time Slots (HC-03)",
            description="Shift one or more overlapping sections to an open departmental teaching time slot.",
            changes=[{"action": "change_timeslot", "new_slot": "TS-WED-1430"}],
            feasible_after_repair=res_timeslot.feasible,
            solve_result=res_timeslot,
            fairness_gini=res_timeslot.fairness.get("gini", 0.0),
            mean_fit=res_timeslot.fit_summary.get("mean_fit", 0.0),
            new_violations=[],
            rule_relaxed="HC-03",
        )
    )

    # -------------------------------------------------------------------------
    # Alternative 4 (if HC-07): Upgrade Facility Capacity
    # -------------------------------------------------------------------------
    if "HC-07" in blocking_rules or any(
        isinstance(r, dict) and r.get("capacity", 0) < 30 for r in (resources or [])
    ):
        resources_upgraded = copy.deepcopy(resources or [])
        for r in resources_upgraded:
            if isinstance(r, dict):
                r["capacity"] = max(r.get("capacity", 0), 100)
                r["unavailable_slots"] = []
            else:
                setattr(r, "capacity", max(getattr(r, "capacity", 0), 100))
                setattr(r, "unavailable_slots", [])

        res_facility = solve_cpsat(
            faculty=faculty,
            courses=courses,
            sections=sections,
            resources=resources_upgraded,
            timeslots=timeslots,
            previous_assignments=previous_assignments,
            demand_profile=demand_profile,
            time_limit_seconds=re_solve_time_limit,
            seed=seed,
        )

        repairs.append(
            RepairAlternative(
                repair_type="expand_facility",
                title="Relocate to High-Capacity Auditorium/Lab (HC-07)",
                description="Reassign sections to an available auditorium or expanded laboratory facility.",
                changes=[{"action": "expand_capacity", "minimum_capacity": 100}],
                feasible_after_repair=res_facility.feasible,
                solve_result=res_facility,
                fairness_gini=res_facility.fairness.get("gini", 0.0),
                mean_fit=res_facility.fit_summary.get("mean_fit", 0.0),
                new_violations=[],
                rule_relaxed="HC-07",
            )
        )

    # Prioritize repairs that restore feasibility, then by fairness / fit
    repairs.sort(
        key=lambda r: (
            1 if r.feasible_after_repair else 0,
            r.mean_fit,
            -r.fairness_gini,
        ),
        reverse=True,
    )

    return repairs[:max_repairs]
