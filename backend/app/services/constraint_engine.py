import json
import logging
from collections import defaultdict
from datetime import datetime
from pathlib import Path

from app.schemas.assignment import Assignment
from app.schemas.common import RuleType, ViolationSeverity
from app.schemas.constraint import ConstraintRule, ValidationScenario
from app.schemas.course import Course
from app.schemas.faculty import Faculty
from app.schemas.resource import Resource
from app.schemas.section import Section
from app.schemas.timeslot import TimeSlot
from app.schemas.violation import Violation

logger = logging.getLogger("app.services.constraint_engine")

DEFAULT_CONSTRAINTS_FILE = (
    Path(__file__).resolve().parents[3] / "data" / "seed" / "constraints.json"
)


class ConstraintEngine:
    """Constraint reasoning engine for academic course assignments and workload balancing.

    Each hard and soft rule is implemented as an independent checker. Rules can be
    enabled/disabled and reweighted dynamically.
    """

    def __init__(
        self,
        rules_path: Path | str | None = None,
        rules: list[ConstraintRule] | None = None,
    ) -> None:
        self.rules_path = Path(rules_path) if rules_path else DEFAULT_CONSTRAINTS_FILE
        self._rules_by_id: dict[str, ConstraintRule] = {}
        if rules is not None:
            for r in rules:
                self._rules_by_id[r.rule_id] = r
        else:
            self.load_rules()

    def load_rules(self) -> list[ConstraintRule]:
        """Load constraint rules from persistent JSON file."""
        if self.rules_path.exists():
            try:
                data = json.loads(self.rules_path.read_text(encoding="utf-8"))
                rules = [ConstraintRule.model_validate(item) for item in data]
                self._rules_by_id = {r.rule_id: r for r in rules}
                return rules
            except (OSError, json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to load constraints from {self.rules_path}: {e}")
        # Fallback to default in-memory rules if file missing or corrupt
        fallback_rules = self._get_fallback_rules()
        self._rules_by_id = {r.rule_id: r for r in fallback_rules}
        return fallback_rules

    def save_rules(self, rules: list[ConstraintRule]) -> list[ConstraintRule]:
        """Persist updated rules to disk."""
        self._rules_by_id = {r.rule_id: r for r in rules}
        try:
            self.rules_path.parent.mkdir(parents=True, exist_ok=True)
            serialized = [r.model_dump() for r in rules]
            self.rules_path.write_text(
                json.dumps(serialized, indent=2), encoding="utf-8"
            )
        except (OSError, TypeError, ValueError) as e:
            logger.error(f"Failed to save constraints to {self.rules_path}: {e}")
        return rules

    def get_rules(self) -> list[ConstraintRule]:
        """Retrieve all currently registered constraint rules."""
        return list(self._rules_by_id.values())

    def get_rule(self, rule_id: str) -> ConstraintRule | None:
        """Retrieve a specific rule by ID."""
        return self._rules_by_id.get(rule_id)

    def update_rules(self, updated_rules: list[ConstraintRule]) -> list[ConstraintRule]:
        """Update existing rules with new enabled states, weights, or parameters."""
        for updated in updated_rules:
            self._rules_by_id[updated.rule_id] = updated
        return self.save_rules(list(self._rules_by_id.values()))

    def validate(
        self,
        assignments: list[Assignment],
        scenario: ValidationScenario,
        rule_overrides: list[ConstraintRule] | None = None,
    ) -> list[Violation]:
        """Validate course assignments against the scenario using all active rules."""
        active_rules = dict(self._rules_by_id)
        if rule_overrides:
            for override in rule_overrides:
                active_rules[override.rule_id] = override

        # Precompute lookups for fast execution
        faculty_map: dict[str, Faculty] = {f.id: f for f in scenario.faculty}
        course_map: dict[str, Course] = {c.id: c for c in scenario.courses}
        section_map: dict[str, Section] = {s.id: s for s in scenario.sections}
        resource_map: dict[str, Resource] = {r.id: r for r in scenario.resources}
        timeslot_map: dict[str, TimeSlot] = {ts.id: ts for ts in scenario.timeslots}

        violations: list[Violation] = []

        # Hard Constraints
        if self._is_enabled(active_rules, "HC-01"):
            violations.extend(
                self.check_hc01_proficiency(
                    assignments,
                    faculty_map,
                    course_map,
                    section_map,
                    active_rules["HC-01"],
                )
            )

        if self._is_enabled(active_rules, "HC-02"):
            violations.extend(
                self.check_hc02_max_weekly_load(
                    assignments,
                    faculty_map,
                    course_map,
                    section_map,
                    active_rules["HC-02"],
                )
            )

        if self._is_enabled(active_rules, "HC-03"):
            violations.extend(
                self.check_hc03_time_overlap(
                    assignments,
                    faculty_map,
                    section_map,
                    timeslot_map,
                    active_rules["HC-03"],
                )
            )

        if self._is_enabled(active_rules, "HC-04"):
            violations.extend(
                self.check_hc04_availability_and_leave(
                    assignments, faculty_map, section_map, active_rules["HC-04"]
                )
            )

        if self._is_enabled(active_rules, "HC-05"):
            violations.extend(
                self.check_hc05_preparations(
                    assignments, faculty_map, section_map, active_rules["HC-05"]
                )
            )

        if self._is_enabled(active_rules, "HC-06"):
            violations.extend(
                self.check_hc06_section_single_assignment(
                    assignments,
                    scenario.sections,
                    faculty_map,
                    course_map,
                    active_rules["HC-06"],
                )
            )

        if self._is_enabled(active_rules, "HC-07"):
            violations.extend(
                self.check_hc07_resources(
                    scenario.sections, course_map, resource_map, active_rules["HC-07"]
                )
            )

        # Soft Constraints
        if self._is_enabled(active_rules, "SC-01"):
            violations.extend(
                self.check_sc01_expertise_fit(
                    assignments,
                    faculty_map,
                    section_map,
                    course_map,
                    active_rules["SC-01"],
                )
            )

        if self._is_enabled(active_rules, "SC-02"):
            violations.extend(
                self.check_sc02_load_balance(
                    assignments,
                    faculty_map,
                    course_map,
                    section_map,
                    active_rules["SC-02"],
                )
            )

        if self._is_enabled(active_rules, "SC-03"):
            violations.extend(
                self.check_sc03_course_preferences(
                    assignments,
                    faculty_map,
                    section_map,
                    course_map,
                    active_rules["SC-03"],
                )
            )

        if self._is_enabled(active_rules, "SC-04"):
            violations.extend(
                self.check_sc04_continuity(
                    assignments,
                    scenario.previous_assignments,
                    faculty_map,
                    section_map,
                    course_map,
                    active_rules["SC-04"],
                )
            )

        if self._is_enabled(active_rules, "SC-05"):
            violations.extend(
                self.check_sc05_min_courses(
                    assignments, faculty_map, active_rules["SC-05"]
                )
            )

        return violations

    @staticmethod
    def _is_enabled(rules: dict[str, ConstraintRule], rule_id: str) -> bool:
        return rule_id in rules and rules[rule_id].enabled

    # --- INDEPENDENT RULE CHECKERS ---

    def check_hc01_proficiency(
        self,
        assignments: list[Assignment],
        faculty_map: dict[str, Faculty],
        course_map: dict[str, Course],
        section_map: dict[str, Section],
        rule: ConstraintRule,
    ) -> list[Violation]:
        """HC-01: Faculty proficiency >= course min_proficiency on all required syllabus tags."""
        violations: list[Violation] = []
        for a in assignments:
            faculty = faculty_map.get(a.faculty_id)
            section = section_map.get(a.section_id)
            if not faculty or not section:
                continue
            course = course_map.get(section.course_id)
            if not course or not course.required_tags:
                continue

            faculty_skills = {
                e.tag.strip().lower(): e.proficiency for e in faculty.expertise
            }
            missing_or_deficient: list[tuple[str, int, int]] = []

            for tag in course.required_tags:
                tag_norm = tag.strip().lower()
                current_prof = faculty_skills.get(tag_norm, 0)
                if current_prof < course.min_proficiency:
                    missing_or_deficient.append(
                        (tag, current_prof, course.min_proficiency)
                    )

            for tag, curr_p, req_p in missing_or_deficient:
                status_str = f"proficiency: {curr_p}" if curr_p > 0 else "unlisted"
                violations.append(
                    Violation(
                        rule_id=rule.rule_id,
                        severity=ViolationSeverity.ERROR,
                        entity_ids=[section.id, faculty.id, course.id],
                        explanation=(
                            f"{faculty.name} does not meet required min proficiency {req_p} "
                            f"for tag '{tag}' in course {course.code} ({status_str}) ({rule.rule_id})"
                        ),
                        suggested_repairs=[
                            f"Reassign section {section.id} to an instructor with proficiency >= {req_p} in '{tag}'",
                            f"Adjust required proficiency threshold for course {course.code}",
                        ],
                    )
                )
        return violations

    def check_hc02_max_weekly_load(
        self,
        assignments: list[Assignment],
        faculty_map: dict[str, Faculty],
        course_map: dict[str, Course],
        section_map: dict[str, Section],
        rule: ConstraintRule,
    ) -> list[Violation]:
        """HC-02: Total assigned weekly load <= faculty max_weekly_load_hours."""
        violations: list[Violation] = []
        faculty_loads: dict[str, float] = defaultdict(float)
        faculty_sections: dict[str, list[str]] = defaultdict(list)

        for a in assignments:
            section = section_map.get(a.section_id)
            if not section:
                continue
            course = course_map.get(section.course_id)
            hours = course.contact_hours if course else 0.0
            faculty_loads[a.faculty_id] += hours
            faculty_sections[a.faculty_id].append(a.section_id)

        for faculty_id, total_load in faculty_loads.items():
            faculty = faculty_map.get(faculty_id)
            if not faculty:
                continue
            if total_load > faculty.max_weekly_load_hours:
                violations.append(
                    Violation(
                        rule_id=rule.rule_id,
                        severity=ViolationSeverity.ERROR,
                        entity_ids=[faculty.id] + faculty_sections[faculty_id],
                        explanation=(
                            f"{faculty.name} is assigned {total_load:g}h/week; "
                            f"the limit is {faculty.max_weekly_load_hours:g}h ({rule.rule_id})"
                        ),
                        suggested_repairs=[
                            f"Unassign one or more sections from {faculty.name} to reduce load by {total_load - faculty.max_weekly_load_hours:g}h",
                            f"Grant administrative overload exception for {faculty.name}",
                        ],
                    )
                )
        return violations

    def check_hc03_time_overlap(
        self,
        assignments: list[Assignment],
        faculty_map: dict[str, Faculty],
        section_map: dict[str, Section],
        timeslot_map: dict[str, TimeSlot],
        rule: ConstraintRule,
    ) -> list[Violation]:
        """HC-03: No overlapping time slots for the same faculty member."""
        violations: list[Violation] = []
        faculty_sections: dict[str, list[Section]] = defaultdict(list)

        for a in assignments:
            section = section_map.get(a.section_id)
            if section and section.time_slot_id:
                faculty_sections[a.faculty_id].append(section)

        for faculty_id, sec_list in faculty_sections.items():
            faculty = faculty_map.get(faculty_id)
            fac_name = faculty.name if faculty else faculty_id

            for i in range(len(sec_list)):
                for j in range(i + 1, len(sec_list)):
                    s1 = sec_list[i]
                    s2 = sec_list[j]
                    if s1.time_slot_id == s2.time_slot_id:
                        violations.append(
                            Violation(
                                rule_id=rule.rule_id,
                                severity=ViolationSeverity.ERROR,
                                entity_ids=[faculty_id, s1.id, s2.id],
                                explanation=(
                                    f"{fac_name} is assigned overlapping sections {s1.id} and {s2.id} "
                                    f"in time slot {s1.time_slot_id} ({rule.rule_id})"
                                ),
                                suggested_repairs=[
                                    f"Reschedule section {s2.id} to a non-conflicting time slot",
                                    f"Reassign section {s2.id} to another instructor",
                                ],
                            )
                        )
                    else:
                        # Check interval overlap if both timeslots exist
                        ts1 = timeslot_map.get(s1.time_slot_id or "")
                        ts2 = timeslot_map.get(s2.time_slot_id or "")
                        if ts1 and ts2 and ts1.day == ts2.day:
                            t1_start = datetime.strptime(ts1.start, "%H:%M").time()
                            t1_end = datetime.strptime(ts1.end, "%H:%M").time()
                            t2_start = datetime.strptime(ts2.start, "%H:%M").time()
                            t2_end = datetime.strptime(ts2.end, "%H:%M").time()
                            if t1_start < t2_end and t2_start < t1_end:
                                violations.append(
                                    Violation(
                                        rule_id=rule.rule_id,
                                        severity=ViolationSeverity.ERROR,
                                        entity_ids=[faculty_id, s1.id, s2.id],
                                        explanation=(
                                            f"{fac_name} is assigned overlapping time intervals for sections "
                                            f"{s1.id} ({ts1.day} {ts1.start}-{ts1.end}) and {s2.id} ({ts2.day} {ts2.start}-{ts2.end}) ({rule.rule_id})"
                                        ),
                                        suggested_repairs=[
                                            f"Reschedule section {s2.id} to a non-conflicting time slot",
                                            f"Reassign section {s2.id} to another instructor",
                                        ],
                                    )
                                )
        return violations

    def check_hc04_availability_and_leave(
        self,
        assignments: list[Assignment],
        faculty_map: dict[str, Faculty],
        section_map: dict[str, Section],
        rule: ConstraintRule,
    ) -> list[Violation]:
        """HC-04: No assignment in leave terms or unavailable slots."""
        violations: list[Violation] = []
        for a in assignments:
            faculty = faculty_map.get(a.faculty_id)
            section = section_map.get(a.section_id)
            if not faculty or not section:
                continue

            # Check leave terms
            if section.term in faculty.leave_terms:
                violations.append(
                    Violation(
                        rule_id=rule.rule_id,
                        severity=ViolationSeverity.ERROR,
                        entity_ids=[faculty.id, section.id],
                        explanation=(
                            f"{faculty.name} is on approved leave during term {section.term} "
                            f"and cannot be assigned section {section.id} ({rule.rule_id})"
                        ),
                        suggested_repairs=[
                            f"Reassign section {section.id} to an active faculty member",
                            f"Reschedule section {section.id} to an active term",
                        ],
                    )
                )

            # Check unavailable time slots
            if (
                section.time_slot_id
                and section.time_slot_id in faculty.unavailable_slots
            ):
                violations.append(
                    Violation(
                        rule_id=rule.rule_id,
                        severity=ViolationSeverity.ERROR,
                        entity_ids=[faculty.id, section.id],
                        explanation=(
                            f"{faculty.name} has designated time slot '{section.time_slot_id}' "
                            f"as unavailable for section {section.id} ({rule.rule_id})"
                        ),
                        suggested_repairs=[
                            f"Move section {section.id} to an alternative time slot",
                            f"Reassign section {section.id} to an instructor available at {section.time_slot_id}",
                        ],
                    )
                )
        return violations

    def check_hc05_preparations(
        self,
        assignments: list[Assignment],
        faculty_map: dict[str, Faculty],
        section_map: dict[str, Section],
        rule: ConstraintRule,
    ) -> list[Violation]:
        """HC-05: Distinct preparations <= max_preparations."""
        violations: list[Violation] = []
        faculty_courses: dict[str, set[str]] = defaultdict(set)
        faculty_sections: dict[str, list[str]] = defaultdict(list)

        for a in assignments:
            section = section_map.get(a.section_id)
            if section:
                faculty_courses[a.faculty_id].add(section.course_id)
                faculty_sections[a.faculty_id].append(section.id)

        for faculty_id, course_ids in faculty_courses.items():
            faculty = faculty_map.get(faculty_id)
            if not faculty:
                continue
            if len(course_ids) > faculty.max_preparations:
                course_list = ", ".join(sorted(course_ids))
                violations.append(
                    Violation(
                        rule_id=rule.rule_id,
                        severity=ViolationSeverity.ERROR,
                        entity_ids=[faculty.id] + faculty_sections[faculty_id],
                        explanation=(
                            f"{faculty.name} is assigned {len(course_ids)} distinct course preparations "
                            f"({course_list}); the limit is {faculty.max_preparations} ({rule.rule_id})"
                        ),
                        suggested_repairs=[
                            f"Consolidate multiple sections of the same course under {faculty.name}",
                            "Reassign sections of one or more courses to another faculty member",
                        ],
                    )
                )
        return violations

    def check_hc06_section_single_assignment(
        self,
        assignments: list[Assignment],
        sections: list[Section],
        faculty_map: dict[str, Faculty],
        course_map: dict[str, Course],
        rule: ConstraintRule,
    ) -> list[Violation]:
        """HC-06: Every section has exactly one faculty assigned."""
        violations: list[Violation] = []
        assigned_faculty: dict[str, list[str]] = defaultdict(list)

        for a in assignments:
            assigned_faculty[a.section_id].append(a.faculty_id)

        for section in sections:
            fac_ids = assigned_faculty.get(section.id, [])
            course = course_map.get(section.course_id)
            course_code = course.code if course else section.course_id

            if len(fac_ids) == 0:
                violations.append(
                    Violation(
                        rule_id=rule.rule_id,
                        severity=ViolationSeverity.ERROR,
                        entity_ids=[section.id],
                        explanation=f"Section {section.id} ({course_code}) is unassigned ({rule.rule_id})",
                        suggested_repairs=[
                            f"Assign an eligible faculty member to section {section.id}",
                        ],
                    )
                )
            elif len(fac_ids) > 1:
                names = [
                    faculty_map[fid].name if fid in faculty_map else fid
                    for fid in fac_ids
                ]
                violations.append(
                    Violation(
                        rule_id=rule.rule_id,
                        severity=ViolationSeverity.ERROR,
                        entity_ids=[section.id] + fac_ids,
                        explanation=(
                            f"Section {section.id} ({course_code}) has {len(fac_ids)} instructors assigned: "
                            f"{', '.join(names)} ({rule.rule_id})"
                        ),
                        suggested_repairs=[
                            f"Remove duplicate assignment for section {section.id} and retain a single instructor",
                        ],
                    )
                )
        return violations

    def check_hc07_resources(
        self,
        sections: list[Section],
        course_map: dict[str, Course],
        resource_map: dict[str, Resource],
        rule: ConstraintRule,
    ) -> list[Violation]:
        """HC-07: Required resources are available and capacity >= expected_size."""
        violations: list[Violation] = []
        for section in sections:
            course = course_map.get(section.course_id)
            if not course or not course.required_resource_ids:
                continue

            for res_id in course.required_resource_ids:
                resource = resource_map.get(res_id)
                if not resource:
                    violations.append(
                        Violation(
                            rule_id=rule.rule_id,
                            severity=ViolationSeverity.ERROR,
                            entity_ids=[section.id, res_id],
                            explanation=(
                                f"Required resource '{res_id}' for course {course.code} (section {section.id}) "
                                f"is not found in facility records ({rule.rule_id})"
                            ),
                            suggested_repairs=[
                                f"Register facility '{res_id}' in system inventory",
                                f"Update course {course.code} resource requirements",
                            ],
                        )
                    )
                    continue

                # Check resource availability for section time slot
                if (
                    section.time_slot_id
                    and section.time_slot_id in resource.unavailable_slots
                ):
                    violations.append(
                        Violation(
                            rule_id=rule.rule_id,
                            severity=ViolationSeverity.ERROR,
                            entity_ids=[section.id, resource.id],
                            explanation=(
                                f"Facility '{resource.id}' is unavailable during time slot '{section.time_slot_id}' "
                                f"required for section {section.id} ({rule.rule_id})"
                            ),
                            suggested_repairs=[
                                f"Reschedule section {section.id} to a time slot when facility '{resource.id}' is open",
                                f"Assign an alternative available facility of type '{resource.type}'",
                            ],
                        )
                    )

                # Check capacity
                if resource.capacity < section.expected_size:
                    violations.append(
                        Violation(
                            rule_id=rule.rule_id,
                            severity=ViolationSeverity.ERROR,
                            entity_ids=[section.id, resource.id],
                            explanation=(
                                f"Facility '{resource.id}' capacity ({resource.capacity}) is insufficient for section {section.id} "
                                f"expected enrollment ({section.expected_size}) ({rule.rule_id})"
                            ),
                            suggested_repairs=[
                                f"Relocate section {section.id} to a facility with capacity >= {section.expected_size}",
                                f"Split section {section.id} into two smaller cohorts",
                            ],
                        )
                    )
        return violations

    def check_sc01_expertise_fit(
        self,
        assignments: list[Assignment],
        faculty_map: dict[str, Faculty],
        section_map: dict[str, Section],
        course_map: dict[str, Course],
        rule: ConstraintRule,
    ) -> list[Violation]:
        """SC-01: Maximize expertise fit."""
        violations: list[Violation] = []
        min_fit = float(rule.params.get("min_acceptable_fit", 0.6))

        for a in assignments:
            if a.fit_score < min_fit:
                faculty = faculty_map.get(a.faculty_id)
                section = section_map.get(a.section_id)
                fac_name = faculty.name if faculty else a.faculty_id
                course_code = ""
                if section:
                    course = course_map.get(section.course_id)
                    course_code = course.code if course else section.course_id

                violations.append(
                    Violation(
                        rule_id=rule.rule_id,
                        severity=ViolationSeverity.WARNING,
                        entity_ids=[a.id, a.faculty_id, a.section_id],
                        explanation=(
                            f"Assignment of {fac_name} to section {a.section_id} ({course_code}) has sub-optimal "
                            f"expertise fit score {a.fit_score:.2f} < threshold {min_fit:.2f} ({rule.rule_id})"
                        ),
                        suggested_repairs=[
                            f"Assign an instructor with higher domain match to section {a.section_id}",
                        ],
                    )
                )
        return violations

    def check_sc02_load_balance(
        self,
        assignments: list[Assignment],
        faculty_map: dict[str, Faculty],
        course_map: dict[str, Course],
        section_map: dict[str, Section],
        rule: ConstraintRule,
    ) -> list[Violation]:
        """SC-02: Minimize load imbalance across faculty of equal rank."""
        violations: list[Violation] = []
        max_discrepancy = float(rule.params.get("max_discrepancy_hours", 3.0))

        faculty_hours: dict[str, float] = defaultdict(float)
        for a in assignments:
            section = section_map.get(a.section_id)
            if section:
                course = course_map.get(section.course_id)
                if course:
                    faculty_hours[a.faculty_id] += course.contact_hours

        # Group faculty by rank
        rank_groups: dict[str, list[Faculty]] = defaultdict(list)
        for f in faculty_map.values():
            if not f.leave_terms:  # only evaluate active non-leave faculty
                rank_groups[f.rank.value].append(f)

        for rank, members in rank_groups.items():
            if len(members) < 2:
                continue
            loads = [faculty_hours[m.id] for m in members]
            min_load = min(loads)
            max_load = max(loads)
            gap = max_load - min_load

            if gap > max_discrepancy:
                max_fac = next(
                    m.name for m in members if faculty_hours[m.id] == max_load
                )
                min_fac = next(
                    m.name for m in members if faculty_hours[m.id] == min_load
                )
                violations.append(
                    Violation(
                        rule_id=rule.rule_id,
                        severity=ViolationSeverity.WARNING,
                        entity_ids=[m.id for m in members],
                        explanation=(
                            f"Load imbalance of {gap:g}h between {max_fac} ({max_load:g}h) and {min_fac} ({min_load:g}h) "
                            f"exceeds tolerance {max_discrepancy:g}h among {rank} faculty ({rule.rule_id})"
                        ),
                        suggested_repairs=[
                            f"Rebalance sections from {max_fac} to {min_fac} to narrow the teaching load gap",
                        ],
                    )
                )
        return violations

    def check_sc03_course_preferences(
        self,
        assignments: list[Assignment],
        faculty_map: dict[str, Faculty],
        section_map: dict[str, Section],
        course_map: dict[str, Course],
        rule: ConstraintRule,
    ) -> list[Violation]:
        """SC-03: Honor course preferences."""
        violations: list[Violation] = []
        for a in assignments:
            faculty = faculty_map.get(a.faculty_id)
            section = section_map.get(a.section_id)
            if not faculty or not section or not faculty.preferred_course_ids:
                continue
            course = course_map.get(section.course_id)
            course_id = course.id if course else section.course_id
            course_code = course.code if course else course_id

            if course_id not in faculty.preferred_course_ids:
                pref_codes = [
                    course_map[cid].code if cid in course_map else cid
                    for cid in faculty.preferred_course_ids
                ]
                violations.append(
                    Violation(
                        rule_id=rule.rule_id,
                        severity=ViolationSeverity.INFO,
                        entity_ids=[a.id, faculty.id, section.id],
                        explanation=(
                            f"{faculty.name} is assigned section {section.id} ({course_code}), "
                            f"which is outside their preferred courses list ({', '.join(pref_codes)}) ({rule.rule_id})"
                        ),
                        suggested_repairs=[
                            f"Assign {faculty.name} to one of their preferred courses ({', '.join(pref_codes)})",
                        ],
                    )
                )
        return violations

    def check_sc04_continuity(
        self,
        assignments: list[Assignment],
        previous_assignments: list[Assignment],
        faculty_map: dict[str, Faculty],
        section_map: dict[str, Section],
        course_map: dict[str, Course],
        rule: ConstraintRule,
    ) -> list[Violation]:
        """SC-04: Continuity (same faculty as previous term)."""
        violations: list[Violation] = []
        if not previous_assignments:
            return violations

        # Map course_id -> set of previous instructors
        prev_course_faculty: dict[str, set[str]] = defaultdict(set)
        for prev_a in previous_assignments:
            sec = section_map.get(prev_a.section_id)
            if sec:
                prev_course_faculty[sec.course_id].add(prev_a.faculty_id)

        for a in assignments:
            section = section_map.get(a.section_id)
            if not section:
                continue
            course_id = section.course_id
            prev_instructors = prev_course_faculty.get(course_id, set())

            # If there was a previous instructor who is available in scenario but not assigned
            if prev_instructors and a.faculty_id not in prev_instructors:
                curr_faculty = faculty_map.get(a.faculty_id)
                curr_name = curr_faculty.name if curr_faculty else a.faculty_id
                course = course_map.get(course_id)
                course_code = course.code if course else course_id
                prev_names = [
                    faculty_map[pid].name if pid in faculty_map else pid
                    for pid in prev_instructors
                ]

                violations.append(
                    Violation(
                        rule_id=rule.rule_id,
                        severity=ViolationSeverity.INFO,
                        entity_ids=[a.id, section.id, a.faculty_id]
                        + list(prev_instructors),
                        explanation=(
                            f"Course {course_code} (section {section.id}) was previously taught by "
                            f"{', '.join(prev_names)}, but currently assigned to {curr_name} ({rule.rule_id})"
                        ),
                        suggested_repairs=[
                            f"Consider assigning section {section.id} to previous instructor {prev_names[0]} for pedagogical continuity",
                        ],
                    )
                )
        return violations

    def check_sc05_min_courses(
        self,
        assignments: list[Assignment],
        faculty_map: dict[str, Faculty],
        rule: ConstraintRule,
    ) -> list[Violation]:
        """SC-05: Respect min_courses floor."""
        violations: list[Violation] = []
        faculty_counts: dict[str, int] = defaultdict(int)
        for a in assignments:
            faculty_counts[a.faculty_id] += 1

        for faculty in faculty_map.values():
            if faculty.leave_terms:
                continue
            assigned = faculty_counts[faculty.id]
            if assigned < faculty.min_courses:
                violations.append(
                    Violation(
                        rule_id=rule.rule_id,
                        severity=ViolationSeverity.WARNING,
                        entity_ids=[faculty.id],
                        explanation=(
                            f"{faculty.name} is assigned {assigned} courses; "
                            f"contractual minimum is {faculty.min_courses} ({rule.rule_id})"
                        ),
                        suggested_repairs=[
                            f"Assign {faculty.min_courses - assigned} additional course section(s) to {faculty.name}",
                        ],
                    )
                )
        return violations

    @staticmethod
    def _get_fallback_rules() -> list[ConstraintRule]:
        """In-memory default rules if constraints.json is not yet created."""
        return [
            ConstraintRule(
                rule_id="HC-01",
                type=RuleType.HARD,
                description="Faculty proficiency >= course min_proficiency on all required tags",
                weight=1.0,
                enabled=True,
            ),
            ConstraintRule(
                rule_id="HC-02",
                type=RuleType.HARD,
                description="Total assigned weekly contact hours <= faculty max_weekly_load_hours",
                weight=1.0,
                enabled=True,
            ),
            ConstraintRule(
                rule_id="HC-03",
                type=RuleType.HARD,
                description="No overlapping time slots permitted for one faculty member",
                weight=1.0,
                enabled=True,
            ),
            ConstraintRule(
                rule_id="HC-04",
                type=RuleType.HARD,
                description="No assignment in leave terms or unavailable slots",
                weight=1.0,
                enabled=True,
            ),
            ConstraintRule(
                rule_id="HC-05",
                type=RuleType.HARD,
                description="Distinct preparations <= max_preparations",
                weight=1.0,
                enabled=True,
            ),
            ConstraintRule(
                rule_id="HC-06",
                type=RuleType.HARD,
                description="Every active course section must have exactly one faculty assigned",
                weight=1.0,
                enabled=True,
            ),
            ConstraintRule(
                rule_id="HC-07",
                type=RuleType.HARD,
                description="Required resources available and capacity >= expected_size",
                weight=1.0,
                enabled=True,
            ),
            ConstraintRule(
                rule_id="SC-01",
                type=RuleType.SOFT,
                description="Maximize expertise fit score with course content",
                weight=3.0,
                enabled=True,
                params={"min_acceptable_fit": 0.6},
            ),
            ConstraintRule(
                rule_id="SC-02",
                type=RuleType.SOFT,
                description="Minimize teaching load imbalance among faculty of equal rank",
                weight=2.0,
                enabled=True,
                params={"max_discrepancy_hours": 3.0},
            ),
            ConstraintRule(
                rule_id="SC-03",
                type=RuleType.SOFT,
                description="Honor faculty course preferences",
                weight=1.5,
                enabled=True,
            ),
            ConstraintRule(
                rule_id="SC-04",
                type=RuleType.SOFT,
                description="Pedagogical continuity (same faculty as previous term)",
                weight=1.0,
                enabled=True,
            ),
            ConstraintRule(
                rule_id="SC-05",
                type=RuleType.SOFT,
                description="Respect faculty contractual min_courses floor",
                weight=2.5,
                enabled=True,
            ),
        ]
