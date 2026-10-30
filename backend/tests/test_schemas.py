from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas import (
    Assignment,
    AssignmentSource,
    AuditLogEntry,
    ConstraintRule,
    Course,
    CourseLevel,
    DayOfWeek,
    Faculty,
    FacultyExpertise,
    FacultyRank,
    Override,
    Resource,
    ResourceType,
    RuleType,
    Section,
    TimeSlot,
    User,
    UserRole,
    Violation,
    ViolationSeverity,
)


# --- User Validation Tests ---
def test_valid_user():
    u = User(id="u1", email="admin@univ.edu", role=UserRole.ADMIN)
    assert u.email == "admin@univ.edu"
    assert u.role == UserRole.ADMIN
    assert u.faculty_id is None


def test_user_invalid_email():
    with pytest.raises(ValidationError):
        User(id="u1", email="not-an-email", role=UserRole.ADMIN)


def test_user_empty_faculty_id_when_provided():
    with pytest.raises(ValidationError, match="faculty_id cannot be empty"):
        User(id="u2", email="prof@univ.edu", role=UserRole.FACULTY, faculty_id="   ")


def test_user_extra_fields_forbidden():
    with pytest.raises(ValidationError):
        User(id="u1", email="admin@univ.edu", role=UserRole.ADMIN, extra="unexpected")


# --- Faculty Validation Tests ---
def test_valid_faculty():
    f = Faculty(
        id="f1",
        name="Dr. Alan Turing",
        email="alan@univ.edu",
        rank=FacultyRank.PROFESSOR,
        expertise=[
            FacultyExpertise(tag="Algorithms", proficiency=5),
            FacultyExpertise(tag="Complexity", proficiency=4),
        ],
        max_weekly_load_hours=12.0,
        max_courses=3,
        min_courses=1,
        max_preparations=2,
        unavailable_slots=["TS1"],
        leave_terms=[],
        preferred_course_ids=["C101"],
    )
    assert f.name == "Dr. Alan Turing"
    assert len(f.expertise) == 2


def test_faculty_max_courses_less_than_min_courses():
    with pytest.raises(
        ValidationError,
        match="max_courses.*must be greater than or equal to min_courses",
    ):
        Faculty(
            id="f1",
            name="Dr. Ada",
            email="ada@univ.edu",
            rank=FacultyRank.PROFESSOR,
            max_weekly_load_hours=12.0,
            max_courses=1,
            min_courses=3,
            max_preparations=1,
        )


def test_faculty_max_preparations_exceeds_max_courses():
    with pytest.raises(
        ValidationError, match="max_preparations.*cannot exceed max_courses"
    ):
        Faculty(
            id="f1",
            name="Dr. Ada",
            email="ada@univ.edu",
            rank=FacultyRank.PROFESSOR,
            max_weekly_load_hours=12.0,
            max_courses=2,
            min_courses=1,
            max_preparations=3,
        )


def test_faculty_expertise_proficiency_bounds():
    with pytest.raises(ValidationError):
        FacultyExpertise(tag="AI", proficiency=0)

    with pytest.raises(ValidationError):
        FacultyExpertise(tag="AI", proficiency=6)


def test_faculty_duplicate_expertise_tags():
    with pytest.raises(ValidationError, match="Duplicate expertise tag"):
        Faculty(
            id="f1",
            name="Dr. Ada",
            email="ada@univ.edu",
            rank=FacultyRank.PROFESSOR,
            expertise=[
                FacultyExpertise(tag="Machine Learning", proficiency=4),
                FacultyExpertise(tag="machine learning", proficiency=5),
            ],
            max_weekly_load_hours=12.0,
            max_courses=3,
            min_courses=1,
            max_preparations=2,
        )


def test_faculty_zero_or_negative_load_hours():
    with pytest.raises(ValidationError):
        Faculty(
            id="f1",
            name="Dr. Ada",
            email="ada@univ.edu",
            rank=FacultyRank.PROFESSOR,
            max_weekly_load_hours=0.0,
            max_courses=3,
            min_courses=1,
            max_preparations=2,
        )


# --- Course Validation Tests ---
def test_valid_course():
    c = Course(
        id="c1",
        code="CS101",
        title="Intro to CS",
        description="Foundational computing",
        credits=3,
        contact_hours=3.0,
        level=CourseLevel.UNDERGRADUATE,
        required_tags=["Python"],
        min_proficiency=3,
        is_lab=False,
    )
    assert c.code == "CS101"
    assert c.min_proficiency == 3


def test_course_invalid_credits_or_contact_hours():
    with pytest.raises(ValidationError):
        Course(
            id="c1",
            code="CS101",
            title="Intro to CS",
            credits=0,
            contact_hours=3.0,
            level=CourseLevel.UNDERGRADUATE,
        )

    with pytest.raises(ValidationError):
        Course(
            id="c1",
            code="CS101",
            title="Intro to CS",
            credits=3,
            contact_hours=0.0,
            level=CourseLevel.UNDERGRADUATE,
        )


# --- Section Validation Tests ---
def test_valid_section():
    s = Section(
        id="s1",
        course_id="c1",
        term="Fall 2026",
        section_cap=40,
        expected_size=35,
        size_p10=25,
        size_p50=35,
        size_p90=42,
    )
    assert s.size_p10 <= s.size_p50 <= s.size_p90


def test_section_non_monotonic_quantiles():
    with pytest.raises(ValidationError, match="P10 <= P50 <= P90"):
        Section(
            id="s1",
            course_id="c1",
            term="Fall 2026",
            section_cap=40,
            expected_size=35,
            size_p10=38,
            size_p50=30,  # P10 > P50!
            size_p90=45,
        )

    with pytest.raises(ValidationError, match="P10 <= P50 <= P90"):
        Section(
            id="s1",
            course_id="c1",
            term="Fall 2026",
            section_cap=40,
            expected_size=35,
            size_p10=20,
            size_p50=45,
            size_p90=40,  # P50 > P90!
        )


def test_section_invalid_cap():
    with pytest.raises(ValidationError):
        Section(
            id="s1",
            course_id="c1",
            term="Fall 2026",
            section_cap=0,
            expected_size=0,
            size_p10=0,
            size_p50=0,
            size_p90=0,
        )


# --- Resource Validation Tests ---
def test_valid_resource():
    r = Resource(id="r1", type=ResourceType.LAB, capacity=30, unavailable_slots=["TS1"])
    assert r.type == ResourceType.LAB
    assert r.capacity == 30


def test_resource_invalid_capacity():
    with pytest.raises(ValidationError):
        Resource(id="r1", type=ResourceType.ROOM, capacity=0)


# --- TimeSlot Validation Tests ---
def test_valid_timeslot():
    ts = TimeSlot(id="ts1", day=DayOfWeek.MON, start="09:00", end="10:30")
    assert ts.start == "09:00"
    assert ts.end == "10:30"


def test_timeslot_invalid_format():
    with pytest.raises(ValidationError, match="24-hour HH:MM format"):
        TimeSlot(id="ts1", day=DayOfWeek.MON, start="9:00", end="10:30")

    with pytest.raises(ValidationError, match="24-hour HH:MM format"):
        TimeSlot(id="ts1", day=DayOfWeek.MON, start="25:00", end="10:30")


def test_timeslot_non_chronological():
    with pytest.raises(ValidationError, match="Start time.*must precede end time"):
        TimeSlot(id="ts1", day=DayOfWeek.MON, start="11:00", end="10:00")

    with pytest.raises(ValidationError, match="Start time.*must precede end time"):
        TimeSlot(id="ts1", day=DayOfWeek.MON, start="10:00", end="10:00")


# --- ConstraintRule Validation Tests ---
def test_valid_constraint_rule():
    rule = ConstraintRule(
        rule_id="HC-01_MAX_LOAD",
        type=RuleType.HARD,
        description="Faculty cannot exceed max load hours",
        weight=1.0,
        enabled=True,
        params={"buffer": 0.0},
    )
    assert rule.rule_id == "HC-01_MAX_LOAD"


def test_constraint_negative_weight():
    with pytest.raises(ValidationError):
        ConstraintRule(
            rule_id="SC-01",
            type=RuleType.SOFT,
            description="Test",
            weight=-0.5,
        )


# --- Assignment Validation Tests ---
def test_valid_assignment():
    a = Assignment(
        id="a1",
        section_id="s1",
        faculty_id="f1",
        source=AssignmentSource.SOLVER,
        fit_score=0.92,
        fit_breakdown={"expertise": 0.95, "history": 0.89},
        rule_ids_satisfied=["HC-01", "SC-01"],
        rule_ids_violated=[],
        run_id="run-101",
    )
    assert a.fit_score == 0.92


def test_assignment_fit_score_bounds():
    with pytest.raises(ValidationError):
        Assignment(
            id="a1",
            section_id="s1",
            faculty_id="f1",
            source=AssignmentSource.SOLVER,
            fit_score=1.5,
            run_id="run-101",
        )

    with pytest.raises(ValidationError):
        Assignment(
            id="a1",
            section_id="s1",
            faculty_id="f1",
            source=AssignmentSource.SOLVER,
            fit_score=-0.1,
            run_id="run-101",
        )


# --- Violation Validation Tests ---
def test_valid_violation():
    v = Violation(
        rule_id="HC-02_TIME_CONFLICT",
        severity=ViolationSeverity.ERROR,
        entity_ids=["s1", "f1"],
        explanation="Faculty f1 assigned to overlapping time slots",
        suggested_repairs=["Reassign s1 to alternative instructor f2"],
    )
    assert v.severity == ViolationSeverity.ERROR


# --- Override Validation Tests ---
def test_valid_override():
    o = Override(
        id="o1",
        assignment_id="a1",
        admin_id="adm-1",
        reason="Emergency sabbatical cover approved by Dean",
        previous_faculty_id="f1",
        new_faculty_id="f2",
        constraint_evidence_snapshot={"fit_score": 0.75},
        acknowledged_violations=["SC-01_EXPERTISE_MATCH"],
    )
    assert o.new_faculty_id == "f2"


def test_override_same_faculty_error():
    with pytest.raises(ValidationError, match="cannot be identical"):
        Override(
            id="o1",
            assignment_id="a1",
            admin_id="adm-1",
            reason="Legitimate adjustment rationale",
            previous_faculty_id="f1",
            new_faculty_id="f1",
        )


def test_override_reason_too_short():
    with pytest.raises(ValidationError):
        Override(
            id="o1",
            assignment_id="a1",
            admin_id="adm-1",
            reason="no",  # min_length=5
            previous_faculty_id="f1",
            new_faculty_id="f2",
        )


# --- AuditLogEntry Validation Tests ---
def test_valid_audit_log_entry():
    entry = AuditLogEntry(
        id="aud-1",
        actor_id="admin-42",
        action="ASSIGNMENT_OVERRIDE",
        entity="assignment",
        payload={"assignment_id": "a1", "new_faculty_id": "f2"},
        timestamp=datetime.now(UTC),
    )
    assert entry.actor_id == "admin-42"
