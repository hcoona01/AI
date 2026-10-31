"""Infeasibility diagnosis and plain-language explanation generation.

Uses assumption literals and pre-filter diagnostics to extract minimal conflicting
rule subsets and entities, producing explainable audit reports for department planners.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ml.optimizer.cpsat import SolveResult, _extract_id, prefilter_eligible_pairs


@dataclass
class ConflictDetail:
    """Detailed record of a conflicting rule and impacted entity."""

    rule_id: str
    entity_type: str  # section, faculty, resource, timeslot
    entity_id: str
    description: str


@dataclass
class ExplanationResult:
    """Structured, explainable diagnostic outcome for infeasible planning scenarios."""

    feasible: bool
    summary: str
    primary_rule_ids: list[str]
    conflicts: list[ConflictDetail]
    detailed_narrative: str
    suggested_actions: list[str] = field(default_factory=list)


def generate_explanation(
    solve_result: SolveResult,
    faculty: list[Any],
    courses: list[Any],
    sections: list[Any],
    resources: list[Any] | None = None,
    timeslots: list[Any] | None = None,
    previous_assignments: list[Any] | None = None,  # accepted, not used
) -> ExplanationResult:
    """Synthesize structured, plain-language explanation of an infeasible solver run."""
    if solve_result.feasible:
        return ExplanationResult(
            feasible=True,
            summary="Schedule is feasible.",
            primary_rule_ids=[],
            conflicts=[],
            detailed_narrative="All hard constraints (HC-01 through HC-07) are satisfied.",
            suggested_actions=[],
        )

    conflicts: list[ConflictDetail] = []
    rule_ids: list[str] = list(solve_result.blocking_rule_ids)

    # 1. Inspect pre-filter conflicts if any section had 0 eligible faculty
    prefilter = prefilter_eligible_pairs(
        faculty=faculty,
        courses=courses,
        sections=sections,
        resources=resources,
    )

    course_map = {_extract_id(c): c for c in courses}
    resource_map = {_extract_id(r): r for r in (resources or [])}

    for sid, fids in prefilter.pairs_by_section.items():
        if not fids:
            blocking = prefilter.blocking_reasons_by_section.get(sid, ["HC-01"])
            for r in blocking:
                if r not in rule_ids:
                    rule_ids.append(r)
                if r == "HC-01":
                    conflicts.append(
                        ConflictDetail(
                            rule_id="HC-01",
                            entity_type="section",
                            entity_id=sid,
                            description=(
                                f"No available faculty member possesses the required domain "
                                f"syllabus tag proficiency (HC-01) for section '{sid}'."
                            ),
                        )
                    )
                elif r == "HC-04":
                    conflicts.append(
                        ConflictDetail(
                            rule_id="HC-04",
                            entity_type="section",
                            entity_id=sid,
                            description=(
                                f"All potential instructors for section '{sid}' are on approved sabbatical "
                                f"leave or unavailable during its scheduled time slot (HC-04)."
                            ),
                        )
                    )
                elif r == "HC-07":
                    conflicts.append(
                        ConflictDetail(
                            rule_id="HC-07",
                            entity_type="section",
                            entity_id=sid,
                            description=(
                                f"Required facility or lab resource for section '{sid}' has insufficient "
                                f"capacity or is unavailable (HC-07)."
                            ),
                        )
                    )

    # 2. Extract conflicts from assumption literals
    for c in solve_result.conflicts:
        r_id = c.get("rule_id", "HC-Unknown")
        e_id = c.get("entity_id", "Unknown")
        desc = c.get("description", c.get("reason", ""))
        if r_id not in rule_ids:
            rule_ids.append(r_id)

        ent_type = "section" if "sec" in e_id.lower() or "s-" in e_id.lower() else "faculty"
        conflicts.append(
            ConflictDetail(
                rule_id=r_id,
                entity_type=ent_type,
                entity_id=e_id,
                description=desc,
            )
        )

    # 3. Formulate plain-language narrative and suggested repairs
    narrative_paragraphs = []
    actions = []

    if "HC-01" in rule_ids:
        narrative_paragraphs.append(
            "Curricular Expertise Deficit (HC-01): One or more course sections require specialized subject "
            "proficiencies exceeding the current departmental faculty competency ratings."
        )
        actions.append("Adjust required course proficiency threshold or hire adjunct faculty.")

    if "HC-02" in rule_ids:
        narrative_paragraphs.append(
            "Contractual Workload Overload (HC-02): Aggregate teaching hours or course section counts "
            "exceed the maximum contractual teaching limits of qualified department faculty."
        )
        actions.append("Authorize administrative load overload exceptions or onboard additional section instructors.")

    if "HC-03" in rule_ids:
        narrative_paragraphs.append(
            "Simultaneous Time Slot Collision (HC-03): A single instructor is required to teach multiple "
            "distinct sections scheduled in overlapping or identical time slots."
        )
        actions.append("Reschedule one or more conflicting sections to alternative non-overlapping time slots.")

    if "HC-04" in rule_ids:
        narrative_paragraphs.append(
            "Availability / Sabbatical Impasse (HC-04): Key qualified instructors are on approved sabbatical "
            "leave during this term or have marked the assigned time slot as strictly unavailable."
        )
        actions.append("Shift section offerings to terms when instructors return, or reassign to active faculty.")

    if "HC-05" in rule_ids:
        narrative_paragraphs.append(
            "Preparation Cap Exceeded (HC-05): A faculty member is assigned too many distinct course preparations, "
            "exceeding pedagogical preparation limits."
        )
        actions.append("Relax maximum preparation limits (HC-05) or consolidate sections of the same course.")

    if "HC-07" in rule_ids:
        narrative_paragraphs.append(
            "Facility / Equipment Constraint (HC-07): Assigned room or specialized lab capacity cannot "
            "accommodate the expected section enrollment."
        )
        actions.append("Move section to a larger room or split enrollment into multiple smaller cohorts.")

    if not narrative_paragraphs:
        narrative_paragraphs.append(solve_result.explanation or "Multiple simultaneous constraints cannot be satisfied.")

    detailed_narrative = "\n\n".join(narrative_paragraphs)
    summary = f"Optimization infeasible due to rule conflicts: {', '.join(rule_ids)}."

    return ExplanationResult(
        feasible=False,
        summary=summary,
        primary_rule_ids=rule_ids,
        conflicts=conflicts,
        detailed_narrative=detailed_narrative,
        suggested_actions=actions,
    )
