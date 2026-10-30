import pytest

from app.schemas.assignment import Assignment, AssignmentSource
from app.schemas.common import (
    CourseLevel,
    DayOfWeek,
    FacultyRank,
    ResourceType,
    RuleType,
)
from app.schemas.constraint import ConstraintRule, ValidationScenario
from app.schemas.course import Course
from app.schemas.faculty import Faculty, FacultyExpertise
from app.schemas.resource import Resource
from app.schemas.section import Section
from app.schemas.timeslot import TimeSlot
from app.services.constraint_engine import ConstraintEngine


@pytest.fixture
def engine():
    return ConstraintEngine()


def make_faculty(
    id="f1",
    name="Dr. Smith",
    rank=FacultyRank.PROFESSOR,
    expertise=None,
    max_weekly_load_hours=12.0,
    max_courses=3,
    min_courses=1,
    max_preparations=2,
    unavailable_slots=None,
    leave_terms=None,
    preferred_course_ids=None,
):
    return Faculty(
        id=id,
        name=name,
        email=f"{id}@univ.edu",
        rank=rank,
        expertise=expertise or [],
        max_weekly_load_hours=max_weekly_load_hours,
        max_courses=max_courses,
        min_courses=min_courses,
        max_preparations=max_preparations,
        unavailable_slots=unavailable_slots or [],
        leave_terms=leave_terms or [],
        preferred_course_ids=preferred_course_ids or [],
    )


def make_course(
    id="c1",
    code="CS101",
    credits=3,
    contact_hours=3.0,
    required_tags=None,
    min_proficiency=3,
    required_resource_ids=None,
):
    return Course(
        id=id,
        code=code,
        title=f"Course {code}",
        credits=credits,
        contact_hours=contact_hours,
        level=CourseLevel.UNDERGRADUATE,
        required_tags=required_tags or [],
        min_proficiency=min_proficiency,
        required_resource_ids=required_resource_ids or [],
    )


def make_section(
    id="s1",
    course_id="c1",
    term="Fall 2026",
    expected_size=30,
    time_slot_id=None,
):
    p50 = expected_size
    p10 = max(0, p50 - 10)
    p90 = p50 + 10
    return Section(
        id=id,
        course_id=course_id,
        term=term,
        section_cap=max(40, p90 + 5),
        expected_size=expected_size,
        size_p10=p10,
        size_p50=p50,
        size_p90=p90,
        time_slot_id=time_slot_id,
    )


def make_assignment(
    id="a1",
    section_id="s1",
    faculty_id="f1",
    fit_score=0.9,
):
    return Assignment(
        id=id,
        section_id=section_id,
        faculty_id=faculty_id,
        source=AssignmentSource.SOLVER,
        fit_score=fit_score,
        run_id="run-1",
    )


# ============================================================================
# HC-01: Faculty Proficiency >= Course Min Proficiency on all required tags
# ============================================================================


def test_hc01_pass_case1_exact_and_higher_proficiency(engine):
    """Pass: Faculty meets or exceeds proficiency on all required tags."""
    f = make_faculty(
        expertise=[
            FacultyExpertise(tag="AI", proficiency=3),
            FacultyExpertise(tag="Python", proficiency=4),
        ]
    )
    c = make_course(required_tags=["AI", "Python"], min_proficiency=3)
    s = make_section(course_id=c.id)
    a = make_assignment(section_id=s.id, faculty_id=f.id)
    rule = engine.get_rule("HC-01")

    violations = engine.check_hc01_proficiency(
        [a], {f.id: f}, {c.id: c}, {s.id: s}, rule
    )
    assert len(violations) == 0


def test_hc01_pass_case2_no_required_tags(engine):
    """Pass: Course has no required tags, any faculty passes."""
    f = make_faculty(expertise=[])
    c = make_course(required_tags=[], min_proficiency=4)
    s = make_section(course_id=c.id)
    a = make_assignment(section_id=s.id, faculty_id=f.id)
    rule = engine.get_rule("HC-01")

    violations = engine.check_hc01_proficiency(
        [a], {f.id: f}, {c.id: c}, {s.id: s}, rule
    )
    assert len(violations) == 0


def test_hc01_fail_case1_proficiency_below_minimum(engine):
    """Fail: Faculty has the tag but proficiency is below min_proficiency."""
    f = make_faculty(expertise=[FacultyExpertise(tag="AI", proficiency=2)])
    c = make_course(required_tags=["AI"], min_proficiency=4)
    s = make_section(course_id=c.id)
    a = make_assignment(section_id=s.id, faculty_id=f.id)
    rule = engine.get_rule("HC-01")

    violations = engine.check_hc01_proficiency(
        [a], {f.id: f}, {c.id: c}, {s.id: s}, rule
    )
    assert len(violations) == 1
    assert violations[0].rule_id == "HC-01"
    assert "proficiency: 2" in violations[0].explanation


def test_hc01_fail_case2_missing_required_tag(engine):
    """Fail: Faculty is completely missing one of the required tags."""
    f = make_faculty(expertise=[FacultyExpertise(tag="Java", proficiency=5)])
    c = make_course(required_tags=["Java", "Security"], min_proficiency=3)
    s = make_section(course_id=c.id)
    a = make_assignment(section_id=s.id, faculty_id=f.id)
    rule = engine.get_rule("HC-01")

    violations = engine.check_hc01_proficiency(
        [a], {f.id: f}, {c.id: c}, {s.id: s}, rule
    )
    assert len(violations) == 1
    assert "Security" in violations[0].explanation


# ============================================================================
# HC-02: Total Weekly Load <= Max Weekly Load Hours
# ============================================================================


def test_hc02_pass_case1_load_strictly_under_limit(engine):
    """Pass: Total contact hours well below max_weekly_load_hours."""
    f = make_faculty(max_weekly_load_hours=12.0)
    c = make_course(contact_hours=4.0)
    s = make_section(course_id=c.id)
    a = make_assignment(section_id=s.id, faculty_id=f.id)
    rule = engine.get_rule("HC-02")

    violations = engine.check_hc02_max_weekly_load(
        [a], {f.id: f}, {c.id: c}, {s.id: s}, rule
    )
    assert len(violations) == 0


def test_hc02_pass_case2_load_exactly_at_limit(engine):
    """Pass: Total contact hours exactly equals max_weekly_load_hours."""
    f = make_faculty(max_weekly_load_hours=9.0)
    c1 = make_course(id="c1", contact_hours=4.5)
    c2 = make_course(id="c2", contact_hours=4.5)
    s1 = make_section(id="s1", course_id="c1")
    s2 = make_section(id="s2", course_id="c2")
    a1 = make_assignment(id="a1", section_id="s1", faculty_id=f.id)
    a2 = make_assignment(id="a2", section_id="s2", faculty_id=f.id)
    rule = engine.get_rule("HC-02")

    violations = engine.check_hc02_max_weekly_load(
        [a1, a2], {f.id: f}, {"c1": c1, "c2": c2}, {"s1": s1, "s2": s2}, rule
    )
    assert len(violations) == 0


def test_hc02_fail_case1_single_section_overload(engine):
    """Fail: A single heavy section exceeds faculty limit."""
    f = make_faculty(name="Dr. Rao", max_weekly_load_hours=12.0)
    c = make_course(contact_hours=14.0)
    s = make_section(course_id=c.id)
    a = make_assignment(section_id=s.id, faculty_id=f.id)
    rule = engine.get_rule("HC-02")

    violations = engine.check_hc02_max_weekly_load(
        [a], {f.id: f}, {c.id: c}, {s.id: s}, rule
    )
    assert len(violations) == 1
    assert (
        "Dr. Rao is assigned 14h/week; the limit is 12h (HC-02)"
        in violations[0].explanation
    )


def test_hc02_fail_case2_cumulative_sections_overload(engine):
    """Fail: Multiple sections sum to exceed faculty limit."""
    f = make_faculty(name="Dr. Alan", max_weekly_load_hours=10.0)
    c = make_course(contact_hours=4.0)
    s1, s2, s3 = make_section("s1"), make_section("s2"), make_section("s3")
    a1, a2, a3 = (
        make_assignment("a1", "s1", f.id),
        make_assignment("a2", "s2", f.id),
        make_assignment("a3", "s3", f.id),
    )
    rule = engine.get_rule("HC-02")

    violations = engine.check_hc02_max_weekly_load(
        [a1, a2, a3], {f.id: f}, {"c1": c}, {"s1": s1, "s2": s2, "s3": s3}, rule
    )
    assert len(violations) == 1
    assert "assigned 12h/week; the limit is 10h" in violations[0].explanation


# ============================================================================
# HC-03: No Overlapping Time Slots for One Faculty
# ============================================================================


def test_hc03_pass_case1_distinct_time_slots(engine):
    """Pass: Sections are in completely different time slots."""
    f = make_faculty()
    s1 = make_section("s1", time_slot_id="TS-MON-0900")
    s2 = make_section("s2", time_slot_id="TS-TUE-1100")
    a1, a2 = make_assignment("a1", "s1", f.id), make_assignment("a2", "s2", f.id)
    rule = engine.get_rule("HC-03")

    violations = engine.check_hc03_time_overlap(
        [a1, a2], {f.id: f}, {"s1": s1, "s2": s2}, {}, rule
    )
    assert len(violations) == 0


def test_hc03_pass_case2_same_day_non_overlapping_hours(engine):
    """Pass: Same day, sequential non-overlapping hours."""
    f = make_faculty()
    ts1 = TimeSlot(id="ts1", day=DayOfWeek.MON, start="09:00", end="10:30")
    ts2 = TimeSlot(id="ts2", day=DayOfWeek.MON, start="11:00", end="12:30")
    s1 = make_section("s1", time_slot_id="ts1")
    s2 = make_section("s2", time_slot_id="ts2")
    a1, a2 = make_assignment("a1", "s1", f.id), make_assignment("a2", "s2", f.id)
    rule = engine.get_rule("HC-03")

    violations = engine.check_hc03_time_overlap(
        [a1, a2], {f.id: f}, {"s1": s1, "s2": s2}, {"ts1": ts1, "ts2": ts2}, rule
    )
    assert len(violations) == 0


def test_hc03_fail_case1_identical_slot_id(engine):
    """Fail: Two assigned sections share identical time_slot_id."""
    f = make_faculty(name="Dr. Hopper")
    s1 = make_section("s1", time_slot_id="TS-WED-1000")
    s2 = make_section("s2", time_slot_id="TS-WED-1000")
    a1, a2 = make_assignment("a1", "s1", f.id), make_assignment("a2", "s2", f.id)
    rule = engine.get_rule("HC-03")

    violations = engine.check_hc03_time_overlap(
        [a1, a2], {f.id: f}, {"s1": s1, "s2": s2}, {}, rule
    )
    assert len(violations) == 1
    assert "overlapping sections s1 and s2" in violations[0].explanation


def test_hc03_fail_case2_overlapping_clock_interval(engine):
    """Fail: Distinct slot IDs but times overlap on the same day."""
    f = make_faculty(name="Dr. Knuth")
    ts1 = TimeSlot(id="ts1", day=DayOfWeek.FRI, start="09:00", end="11:00")
    ts2 = TimeSlot(id="ts2", day=DayOfWeek.FRI, start="10:00", end="12:00")
    s1 = make_section("s1", time_slot_id="ts1")
    s2 = make_section("s2", time_slot_id="ts2")
    a1, a2 = make_assignment("a1", "s1", f.id), make_assignment("a2", "s2", f.id)
    rule = engine.get_rule("HC-03")

    violations = engine.check_hc03_time_overlap(
        [a1, a2], {f.id: f}, {"s1": s1, "s2": s2}, {"ts1": ts1, "ts2": ts2}, rule
    )
    assert len(violations) == 1
    assert "overlapping time intervals" in violations[0].explanation


# ============================================================================
# HC-04: No Assignment in Leave Terms or Unavailable Slots
# ============================================================================


def test_hc04_pass_case1_active_term_available_slot(engine):
    """Pass: Assigned in active term and available time slot."""
    f = make_faculty(leave_terms=["Spring 2026"], unavailable_slots=["TS-NIGHT"])
    s = make_section("s1", term="Fall 2026", time_slot_id="TS-MORNING")
    a = make_assignment("a1", "s1", f.id)
    rule = engine.get_rule("HC-04")

    violations = engine.check_hc04_availability_and_leave(
        [a], {f.id: f}, {"s1": s}, rule
    )
    assert len(violations) == 0


def test_hc04_pass_case2_no_leaves_or_restrictions(engine):
    """Pass: Faculty with empty leave terms and no unavailable slots."""
    f = make_faculty(leave_terms=[], unavailable_slots=[])
    s = make_section("s1", term="Summer 2026", time_slot_id="TS-ANY")
    a = make_assignment("a1", "s1", f.id)
    rule = engine.get_rule("HC-04")

    violations = engine.check_hc04_availability_and_leave(
        [a], {f.id: f}, {"s1": s}, rule
    )
    assert len(violations) == 0


def test_hc04_fail_case1_assigned_during_leave_term(engine):
    """Fail: Assigned section in a term when faculty is on sabbatical."""
    f = make_faculty(name="Dr. Sabbatical", leave_terms=["Fall 2026"])
    s = make_section("s1", term="Fall 2026")
    a = make_assignment("a1", "s1", f.id)
    rule = engine.get_rule("HC-04")

    violations = engine.check_hc04_availability_and_leave(
        [a], {f.id: f}, {"s1": s}, rule
    )
    assert len(violations) == 1
    assert "on approved leave during term Fall 2026" in violations[0].explanation


def test_hc04_fail_case2_assigned_to_unavailable_slot(engine):
    """Fail: Section scheduled during faculty member's unavailable slot."""
    f = make_faculty(name="Dr. Busy", unavailable_slots=["TS-FRI-1400"])
    s = make_section("s1", time_slot_id="TS-FRI-1400")
    a = make_assignment("a1", "s1", f.id)
    rule = engine.get_rule("HC-04")

    violations = engine.check_hc04_availability_and_leave(
        [a], {f.id: f}, {"s1": s}, rule
    )
    assert len(violations) == 1
    assert (
        "designated time slot 'TS-FRI-1400' as unavailable" in violations[0].explanation
    )


# ============================================================================
# HC-05: Distinct Preparations <= Max Preparations
# ============================================================================


def test_hc05_pass_case1_preparations_below_limit(engine):
    """Pass: Multiple sections of the same course count as 1 prep."""
    f = make_faculty(max_preparations=2)
    s1 = make_section("s1", course_id="c1")
    s2 = make_section("s2", course_id="c1")
    a1, a2 = make_assignment("a1", "s1", f.id), make_assignment("a2", "s2", f.id)
    rule = engine.get_rule("HC-05")

    violations = engine.check_hc05_preparations(
        [a1, a2], {f.id: f}, {"s1": s1, "s2": s2}, rule
    )
    assert len(violations) == 0


def test_hc05_pass_case2_preparations_equal_to_limit(engine):
    """Pass: Distinct courses exactly equals max_preparations."""
    f = make_faculty(max_preparations=2)
    s1 = make_section("s1", course_id="c1")
    s2 = make_section("s2", course_id="c2")
    a1, a2 = make_assignment("a1", "s1", f.id), make_assignment("a2", "s2", f.id)
    rule = engine.get_rule("HC-05")

    violations = engine.check_hc05_preparations(
        [a1, a2], {f.id: f}, {"s1": s1, "s2": s2}, rule
    )
    assert len(violations) == 0


def test_hc05_fail_case1_three_preps_when_max_is_two(engine):
    """Fail: 3 distinct course IDs assigned when max_preparations is 2."""
    f = make_faculty(name="Dr. Overprep", max_preparations=2)
    s1, s2, s3 = (
        make_section("s1", course_id="CS101"),
        make_section("s2", course_id="CS201"),
        make_section("s3", course_id="CS301"),
    )
    a1, a2, a3 = (
        make_assignment("a1", "s1", f.id),
        make_assignment("a2", "s2", f.id),
        make_assignment("a3", "s3", f.id),
    )
    rule = engine.get_rule("HC-05")

    violations = engine.check_hc05_preparations(
        [a1, a2, a3], {f.id: f}, {"s1": s1, "s2": s2, "s3": s3}, rule
    )
    assert len(violations) == 1
    assert "assigned 3 distinct course preparations" in violations[0].explanation


def test_hc05_fail_case2_two_preps_when_max_is_one(engine):
    """Fail: 2 distinct courses assigned when max_preparations is 1."""
    f = make_faculty(name="Dr. Specialist", max_preparations=1)
    s1, s2 = make_section("s1", course_id="c1"), make_section("s2", course_id="c2")
    a1, a2 = make_assignment("a1", "s1", f.id), make_assignment("a2", "s2", f.id)
    rule = engine.get_rule("HC-05")

    violations = engine.check_hc05_preparations(
        [a1, a2], {f.id: f}, {"s1": s1, "s2": s2}, rule
    )
    assert len(violations) == 1
    assert "the limit is 1" in violations[0].explanation


# ============================================================================
# HC-06: Every Section Has Exactly One Faculty Assigned
# ============================================================================


def test_hc06_pass_case1_all_sections_singly_assigned(engine):
    """Pass: 2 sections each assigned to 1 instructor."""
    f1, f2 = make_faculty("f1"), make_faculty("f2")
    s1, s2 = make_section("s1"), make_section("s2")
    c = make_course()
    a1 = make_assignment("a1", "s1", f1.id)
    a2 = make_assignment("a2", "s2", f2.id)
    rule = engine.get_rule("HC-06")

    violations = engine.check_hc06_section_single_assignment(
        [a1, a2], [s1, s2], {"f1": f1, "f2": f2}, {"c1": c}, rule
    )
    assert len(violations) == 0


def test_hc06_pass_case2_one_faculty_two_sections(engine):
    """Pass: Single faculty assigned to two sections (each section has exactly 1 instructor)."""
    f = make_faculty("f1")
    s1, s2 = make_section("s1"), make_section("s2")
    c = make_course()
    a1 = make_assignment("a1", "s1", f.id)
    a2 = make_assignment("a2", "s2", f.id)
    rule = engine.get_rule("HC-06")

    violations = engine.check_hc06_section_single_assignment(
        [a1, a2], [s1, s2], {f.id: f}, {"c1": c}, rule
    )
    assert len(violations) == 0


def test_hc06_fail_case1_unassigned_section(engine):
    """Fail: Section has 0 assignments."""
    s1 = make_section("s1")
    c = make_course()
    rule = engine.get_rule("HC-06")

    violations = engine.check_hc06_section_single_assignment(
        [], [s1], {}, {"c1": c}, rule
    )
    assert len(violations) == 1
    assert "Section s1 (CS101) is unassigned" in violations[0].explanation


def test_hc06_fail_case2_duplicate_assigned_faculty(engine):
    """Fail: Section has 2 instructors assigned."""
    f1, f2 = make_faculty("f1", name="Dr. A"), make_faculty("f2", name="Dr. B")
    s1 = make_section("s1")
    c = make_course()
    a1 = make_assignment("a1", "s1", f1.id)
    a2 = make_assignment("a2", "s1", f2.id)
    rule = engine.get_rule("HC-06")

    violations = engine.check_hc06_section_single_assignment(
        [a1, a2], [s1], {"f1": f1, "f2": f2}, {"c1": c}, rule
    )
    assert len(violations) == 1
    assert "has 2 instructors assigned" in violations[0].explanation


# ============================================================================
# HC-07: Required Resources Available and Capacity >= Expected Size
# ============================================================================


def test_hc07_pass_case1_resource_available_and_ample_capacity(engine):
    """Pass: Resource exists, time slot open, capacity exceeds size."""
    r = Resource(id="LAB-1", type=ResourceType.LAB, capacity=50, unavailable_slots=[])
    c = make_course(required_resource_ids=["LAB-1"])
    s = make_section(course_id=c.id, expected_size=30, time_slot_id="TS1")
    rule = engine.get_rule("HC-07")

    violations = engine.check_hc07_resources([s], {c.id: c}, {r.id: r}, rule)
    assert len(violations) == 0


def test_hc07_pass_case2_no_resource_requirements(engine):
    """Pass: Course has no required resource IDs."""
    c = make_course(required_resource_ids=[])
    s = make_section(course_id=c.id, expected_size=40)
    rule = engine.get_rule("HC-07")

    violations = engine.check_hc07_resources([s], {c.id: c}, {}, rule)
    assert len(violations) == 0


def test_hc07_fail_case1_insufficient_resource_capacity(engine):
    """Fail: Facility capacity is lower than section expected enrollment."""
    r = Resource(
        id="ROOM-10", type=ResourceType.ROOM, capacity=25, unavailable_slots=[]
    )
    c = make_course(required_resource_ids=["ROOM-10"])
    s = make_section(course_id=c.id, expected_size=35)
    rule = engine.get_rule("HC-07")

    violations = engine.check_hc07_resources([s], {c.id: c}, {r.id: r}, rule)
    assert len(violations) == 1
    assert "capacity (25) is insufficient" in violations[0].explanation


def test_hc07_fail_case2_resource_unavailable_slot_conflict(engine):
    """Fail: Facility is marked unavailable during section time slot."""
    r = Resource(
        id="LAB-2",
        type=ResourceType.LAB,
        capacity=40,
        unavailable_slots=["TS-THU-1400"],
    )
    c = make_course(required_resource_ids=["LAB-2"])
    s = make_section(course_id=c.id, expected_size=20, time_slot_id="TS-THU-1400")
    rule = engine.get_rule("HC-07")

    violations = engine.check_hc07_resources([s], {c.id: c}, {r.id: r}, rule)
    assert len(violations) == 1
    assert "is unavailable during time slot 'TS-THU-1400'" in violations[0].explanation


# ============================================================================
# SC-01: Maximize Expertise Fit Score
# ============================================================================


def test_sc01_pass_case1_fit_above_threshold(engine):
    """Pass: Fit score is above default 0.6 threshold."""
    f = make_faculty()
    s = make_section()
    a = make_assignment(fit_score=0.85)
    rule = engine.get_rule("SC-01")

    violations = engine.check_sc01_expertise_fit([a], {f.id: f}, {s.id: s}, {}, rule)
    assert len(violations) == 0


def test_sc01_pass_case2_fit_exactly_at_threshold(engine):
    """Pass: Fit score equals min_acceptable_fit parameter."""
    f = make_faculty()
    s = make_section()
    rule = engine.get_rule("SC-01")
    threshold = float(rule.params.get("min_acceptable_fit", 0.6))
    a = make_assignment(fit_score=threshold)

    violations = engine.check_sc01_expertise_fit([a], {f.id: f}, {s.id: s}, {}, rule)
    assert len(violations) == 0


def test_sc01_fail_case1_low_fit_score(engine):
    """Fail: Fit score 0.35 is below 0.6."""
    f = make_faculty(name="Dr. Taylor")
    s = make_section("s1")
    a = make_assignment("a1", "s1", f.id, fit_score=0.35)
    rule = engine.get_rule("SC-01")

    violations = engine.check_sc01_expertise_fit([a], {f.id: f}, {s.id: s}, {}, rule)
    assert len(violations) == 1
    assert violations[0].severity == "warning"
    assert "sub-optimal expertise fit score 0.35" in violations[0].explanation


def test_sc01_fail_case2_custom_high_threshold_breached(engine):
    """Fail: Custom parameter min_acceptable_fit=0.9 breaches score 0.82."""
    f = make_faculty()
    s = make_section()
    a = make_assignment(fit_score=0.82)
    rule = ConstraintRule(
        rule_id="SC-01",
        type=RuleType.SOFT,
        description="Fit",
        params={"min_acceptable_fit": 0.9},
    )

    violations = engine.check_sc01_expertise_fit([a], {f.id: f}, {s.id: s}, {}, rule)
    assert len(violations) == 1
    assert "threshold 0.90" in violations[0].explanation


# ============================================================================
# SC-02: Minimize Load Imbalance
# ============================================================================


def test_sc02_pass_case1_balanced_loads_same_rank(engine):
    """Pass: Faculty members of same rank have identical loads."""
    f1 = make_faculty("f1", rank=FacultyRank.PROFESSOR)
    f2 = make_faculty("f2", rank=FacultyRank.PROFESSOR)
    c = make_course(contact_hours=3.0)
    s1, s2 = make_section("s1"), make_section("s2")
    a1, a2 = make_assignment("a1", "s1", "f1"), make_assignment("a2", "s2", "f2")
    rule = engine.get_rule("SC-02")

    violations = engine.check_sc02_load_balance(
        [a1, a2], {"f1": f1, "f2": f2}, {"c1": c}, {"s1": s1, "s2": s2}, rule
    )
    assert len(violations) == 0


def test_sc02_pass_case2_imbalance_within_tolerance(engine):
    """Pass: Discrepancy (2.0h) is within 3.0h max_discrepancy_hours."""
    f1 = make_faculty("f1", rank=FacultyRank.LECTURER)
    f2 = make_faculty("f2", rank=FacultyRank.LECTURER)
    c1, c2 = make_course("c1", contact_hours=6.0), make_course("c2", contact_hours=4.0)
    s1, s2 = make_section("s1", "c1"), make_section("s2", "c2")
    a1, a2 = make_assignment("a1", "s1", "f1"), make_assignment("a2", "s2", "f2")
    rule = engine.get_rule("SC-02")

    violations = engine.check_sc02_load_balance(
        [a1, a2], {"f1": f1, "f2": f2}, {"c1": c1, "c2": c2}, {"s1": s1, "s2": s2}, rule
    )
    assert len(violations) == 0


def test_sc02_fail_case1_excessive_gap_same_rank(engine):
    """Fail: 9h load vs 3h load produces 6h gap > 3h tolerance."""
    f1 = make_faculty("f1", name="Dr. High", rank=FacultyRank.PROFESSOR)
    f2 = make_faculty("f2", name="Dr. Low", rank=FacultyRank.PROFESSOR)
    c1 = make_course("c1", contact_hours=9.0)
    c2 = make_course("c2", contact_hours=3.0)
    s1, s2 = make_section("s1", "c1"), make_section("s2", "c2")
    a1, a2 = make_assignment("a1", "s1", "f1"), make_assignment("a2", "s2", "f2")
    rule = engine.get_rule("SC-02")

    violations = engine.check_sc02_load_balance(
        [a1, a2], {"f1": f1, "f2": f2}, {"c1": c1, "c2": c2}, {"s1": s1, "s2": s2}, rule
    )
    assert len(violations) == 1
    assert "Load imbalance of 6h" in violations[0].explanation


def test_sc02_fail_case2_three_faculty_gap_exceeded(engine):
    """Fail: In a trio of professors, max-min gap is 8h."""
    f1 = make_faculty("f1", rank=FacultyRank.ASSOCIATE_PROFESSOR)
    f2 = make_faculty("f2", rank=FacultyRank.ASSOCIATE_PROFESSOR)
    f3 = make_faculty("f3", rank=FacultyRank.ASSOCIATE_PROFESSOR)
    c1, c2, c3 = (
        make_course("c1", contact_hours=12.0),
        make_course("c2", contact_hours=6.0),
        make_course("c3", contact_hours=4.0),
    )
    s1, s2, s3 = (
        make_section("s1", "c1"),
        make_section("s2", "c2"),
        make_section("s3", "c3"),
    )
    a1, a2, a3 = (
        make_assignment("a1", "s1", "f1"),
        make_assignment("a2", "s2", "f2"),
        make_assignment("a3", "s3", "f3"),
    )
    rule = engine.get_rule("SC-02")

    violations = engine.check_sc02_load_balance(
        [a1, a2, a3],
        {"f1": f1, "f2": f2, "f3": f3},
        {"c1": c1, "c2": c2, "c3": c3},
        {"s1": s1, "s2": s2, "s3": s3},
        rule,
    )
    assert len(violations) == 1
    assert "Load imbalance of 8h" in violations[0].explanation


# ============================================================================
# SC-03: Honor Course Preferences
# ============================================================================


def test_sc03_pass_case1_assigned_preferred_course(engine):
    """Pass: Faculty assigned to course in preferred_course_ids."""
    f = make_faculty(preferred_course_ids=["c1", "c2"])
    c = make_course(id="c1")
    s = make_section("s1", course_id="c1")
    a = make_assignment("a1", "s1", f.id)
    rule = engine.get_rule("SC-03")

    violations = engine.check_sc03_course_preferences(
        [a], {f.id: f}, {"s1": s}, {"c1": c}, rule
    )
    assert len(violations) == 0


def test_sc03_pass_case2_no_preferences_declared(engine):
    """Pass: Faculty has not set preferred_course_ids, no penalty."""
    f = make_faculty(preferred_course_ids=[])
    c = make_course(id="c9")
    s = make_section("s1", course_id="c9")
    a = make_assignment("a1", "s1", f.id)
    rule = engine.get_rule("SC-03")

    violations = engine.check_sc03_course_preferences(
        [a], {f.id: f}, {"s1": s}, {"c9": c}, rule
    )
    assert len(violations) == 0


def test_sc03_fail_case1_assigned_unpreferred_course(engine):
    """Fail: Faculty assigned to course not in their preference list."""
    f = make_faculty(name="Dr. Preferred", preferred_course_ids=["CS100"])
    c = make_course(id="CS200", code="CS200")
    s = make_section("s1", course_id="CS200")
    a = make_assignment("a1", "s1", f.id)
    rule = engine.get_rule("SC-03")

    violations = engine.check_sc03_course_preferences(
        [a], {f.id: f}, {"s1": s}, {"CS200": c}, rule
    )
    assert len(violations) == 1
    assert "outside their preferred courses list" in violations[0].explanation


def test_sc03_fail_case2_multiple_unpreferred_assignments(engine):
    """Fail: Faculty assigned two separate courses outside preferences."""
    f = make_faculty(preferred_course_ids=["c1"])
    c2, c3 = make_course("c2"), make_course("c3")
    s2, s3 = make_section("s2", "c2"), make_section("s3", "c3")
    a2, a3 = make_assignment("a2", "s2", f.id), make_assignment("a3", "s3", f.id)
    rule = engine.get_rule("SC-03")

    violations = engine.check_sc03_course_preferences(
        [a2, a3], {f.id: f}, {"s2": s2, "s3": s3}, {"c2": c2, "c3": c3}, rule
    )
    assert len(violations) == 2


# ============================================================================
# SC-04: Continuity (Same Faculty as Previous Term)
# ============================================================================


def test_sc04_pass_case1_same_instructor_reassigned(engine):
    """Pass: Course assigned to previous term instructor."""
    f = make_faculty("f1")
    c = make_course("c1")
    s_curr = make_section("s_curr", "c1")
    s_prev = make_section("s_prev", "c1")
    prev_a = make_assignment("p1", "s_prev", "f1")
    curr_a = make_assignment("c1", "s_curr", "f1")
    rule = engine.get_rule("SC-04")

    violations = engine.check_sc04_continuity(
        [curr_a],
        [prev_a],
        {"f1": f},
        {"s_curr": s_curr, "s_prev": s_prev},
        {"c1": c},
        rule,
    )
    assert len(violations) == 0


def test_sc04_pass_case2_no_historical_precedent(engine):
    """Pass: Course has no previous assignments in historical records."""
    f = make_faculty("f1")
    c = make_course("c_new")
    s_curr = make_section("s_curr", "c_new")
    curr_a = make_assignment("c1", "s_curr", "f1")
    rule = engine.get_rule("SC-04")

    violations = engine.check_sc04_continuity(
        [curr_a], [], {"f1": f}, {"s_curr": s_curr}, {"c_new": c}, rule
    )
    assert len(violations) == 0


def test_sc04_fail_case1_different_instructor_replaces_incumbent(engine):
    """Fail: Previous instructor f1 is available, but course is given to f2."""
    f1, f2 = make_faculty("f1", name="Dr. Incumbent"), make_faculty(
        "f2", name="Dr. Newbie"
    )
    c = make_course("c1", code="CS300")
    s_prev, s_curr = make_section("s_prev", "c1"), make_section("s_curr", "c1")
    prev_a = make_assignment("p1", "s_prev", "f1")
    curr_a = make_assignment("c1", "s_curr", "f2")
    rule = engine.get_rule("SC-04")

    violations = engine.check_sc04_continuity(
        [curr_a],
        [prev_a],
        {"f1": f1, "f2": f2},
        {"s_curr": s_curr, "s_prev": s_prev},
        {"c1": c},
        rule,
    )
    assert len(violations) == 1
    assert (
        "previously taught by Dr. Incumbent, but currently assigned to Dr. Newbie"
        in violations[0].explanation
    )


def test_sc04_fail_case2_continuity_broken_multiple_sections(engine):
    """Fail: Two different courses both have broken instructor continuity."""
    f1, f2 = make_faculty("f1"), make_faculty("f2")
    c1, c2 = make_course("c1"), make_course("c2")
    sp1, sp2 = make_section("sp1", "c1"), make_section("sp2", "c2")
    sc1, sc2 = make_section("sc1", "c1"), make_section("sc2", "c2")
    prev = [make_assignment("p1", "sp1", "f1"), make_assignment("p2", "sp2", "f1")]
    curr = [make_assignment("a1", "sc1", "f2"), make_assignment("a2", "sc2", "f2")]
    rule = engine.get_rule("SC-04")

    violations = engine.check_sc04_continuity(
        curr,
        prev,
        {"f1": f1, "f2": f2},
        {"sp1": sp1, "sp2": sp2, "sc1": sc1, "sc2": sc2},
        {"c1": c1, "c2": c2},
        rule,
    )
    assert len(violations) == 2


# ============================================================================
# SC-05: Respect Min Courses Floor
# ============================================================================


def test_sc05_pass_case1_assigned_greater_than_min_courses(engine):
    """Pass: Assigned courses exceeds contractual minimum."""
    f = make_faculty("f1", min_courses=2)
    a1, a2, a3 = (
        make_assignment("a1", "s1", f.id),
        make_assignment("a2", "s2", f.id),
        make_assignment("a3", "s3", f.id),
    )
    rule = engine.get_rule("SC-05")

    violations = engine.check_sc05_min_courses([a1, a2, a3], {f.id: f}, rule)
    assert len(violations) == 0


def test_sc05_pass_case2_assigned_exactly_min_courses(engine):
    """Pass: Assigned courses exactly equals min_courses."""
    f = make_faculty("f1", min_courses=1)
    a1 = make_assignment("a1", "s1", f.id)
    rule = engine.get_rule("SC-05")

    violations = engine.check_sc05_min_courses([a1], {f.id: f}, rule)
    assert len(violations) == 0


def test_sc05_fail_case1_zero_courses_assigned(engine):
    """Fail: Faculty with min_courses=2 is assigned 0 courses."""
    f = make_faculty("f1", name="Dr. Underloaded", min_courses=2)
    rule = engine.get_rule("SC-05")

    violations = engine.check_sc05_min_courses([], {f.id: f}, rule)
    assert len(violations) == 1
    assert "assigned 0 courses; contractual minimum is 2" in violations[0].explanation


def test_sc05_fail_case2_one_course_when_min_is_three(engine):
    """Fail: Faculty with min_courses=3 is assigned 1 course."""
    f = make_faculty("f1", name="Dr. Partial", min_courses=3)
    a = make_assignment("a1", "s1", f.id)
    rule = engine.get_rule("SC-05")

    violations = engine.check_sc05_min_courses([a], {f.id: f}, rule)
    assert len(violations) == 1
    assert "assigned 1 courses; contractual minimum is 3" in violations[0].explanation


# ============================================================================
# Engine Dynamic Toggling & Full Scenario Integration
# ============================================================================


def test_engine_rule_disabled_skips_checker(engine):
    """Verify that disabled rules are skipped in validate()."""
    f = make_faculty(max_weekly_load_hours=5.0)
    c = make_course(contact_hours=10.0)
    s = make_section(course_id=c.id)
    a = make_assignment(section_id=s.id, faculty_id=f.id)
    scenario = ValidationScenario(faculty=[f], courses=[c], sections=[s])

    # Rule HC-02 enabled: violation detected
    violations_on = engine.validate([a], scenario)
    assert any(v.rule_id == "HC-02" for v in violations_on)

    # Disable HC-02 via override
    disabled_rule = ConstraintRule(
        rule_id="HC-02",
        type=RuleType.HARD,
        description="Disabled load rule",
        enabled=False,
    )
    violations_off = engine.validate([a], scenario, rule_overrides=[disabled_rule])
    assert not any(v.rule_id == "HC-02" for v in violations_off)
