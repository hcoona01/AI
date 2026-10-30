"""Tests for data generation, determinism, schema adherence, and constraint engine evaluations.

Validates that:
1. Generation is completely deterministic given the same random seed.
2. Different seeds produce distinct outputs.
3. All generated seed files parse cleanly into their respective Pydantic v2 schemas.
4. All 10 evaluation fixtures parse into ValidationScenario and Assignment models.
5. ConstraintEngine evaluates each fixture in exact accordance with its expected_outcome.
"""

import json
import random
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND_DIR = REPO_ROOT / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.schemas.assignment import Assignment
from app.schemas.common import ViolationSeverity
from app.schemas.constraint import ValidationScenario
from app.schemas.course import Course
from app.schemas.faculty import Faculty
from app.schemas.resource import Resource
from app.schemas.section import Section
from app.schemas.timeslot import TimeSlot
from app.schemas.user import User
from app.services.constraint_engine import ConstraintEngine

from ml.datagen import (
    FIXTURES_DIR,
    SEED_DIR,
    generate_courses,
    generate_enrollment_history,
    generate_faculty,
)


def test_datagen_determinism():
    """Verify that datagen is strictly deterministic given the same seed."""
    rng_a = random.Random(42)
    courses_a = generate_courses(rng_a)
    fac_a = generate_faculty(rng_a, courses_a)
    hist_a = generate_enrollment_history(rng_a, courses_a)

    rng_b = random.Random(42)
    courses_b = generate_courses(rng_b)
    fac_b = generate_faculty(rng_b, courses_b)
    hist_b = generate_enrollment_history(rng_b, courses_b)

    assert [c.model_dump() for c in courses_a] == [c.model_dump() for c in courses_b]
    assert [f.model_dump() for f in fac_a] == [f.model_dump() for f in fac_b]
    assert hist_a == hist_b

    # Different seed must produce different distributions
    rng_c = random.Random(999)
    courses_c = generate_courses(rng_c)
    fac_c = generate_faculty(rng_c, courses_c)
    hist_c = generate_enrollment_history(rng_c, courses_c)

    assert hist_c[0]["enrolled_students"] != hist_a[0]["enrolled_students"]
    assert fac_c[0].name == fac_a[0].name
    assert (
        fac_c[0].expertise != fac_a[0].expertise
        or fac_c[0].preferred_course_ids != fac_a[0].preferred_course_ids
    )


def test_seed_files_exist_and_under_size_limit():
    """Verify all base seed files exist on disk and are well under 1 MB."""
    required_files = [
        "users.json",
        "faculty.json",
        "courses.json",
        "sections.json",
        "resources.json",
        "timeslots.json",
        "enrollment_history.json",
    ]
    for filename in required_files:
        filepath = SEED_DIR / filename
        assert filepath.exists(), f"Missing seed file {filename}"
        size_bytes = filepath.stat().st_size
        assert (
            size_bytes < 1_000_000
        ), f"File {filename} is too large: {size_bytes} bytes"


def test_seed_schema_validation():
    """Verify all seed files parse cleanly into Pydantic v2 schemas."""
    # Users
    with open(SEED_DIR / "users.json", "r", encoding="utf-8") as f:
        users_raw = json.load(f)
    users = [User.model_validate(u) for u in users_raw]
    assert len(users) >= 25

    # Faculty
    with open(SEED_DIR / "faculty.json", "r", encoding="utf-8") as f:
        faculty_raw = json.load(f)
    faculty = [Faculty.model_validate(fac) for fac in faculty_raw]
    assert len(faculty) == 25

    # Courses
    with open(SEED_DIR / "courses.json", "r", encoding="utf-8") as f:
        courses_raw = json.load(f)
    courses = [Course.model_validate(c) for c in courses_raw]
    assert len(courses) == 40

    # Sections
    with open(SEED_DIR / "sections.json", "r", encoding="utf-8") as f:
        sections_raw = json.load(f)
    sections = [Section.model_validate(s) for s in sections_raw]
    assert len(sections) == 60
    # Ensure all section quantiles are monotonic
    for s in sections:
        assert s.size_p10 <= s.size_p50 <= s.size_p90

    # Resources
    with open(SEED_DIR / "resources.json", "r", encoding="utf-8") as f:
        resources_raw = json.load(f)
    resources = [Resource.model_validate(r) for r in resources_raw]
    assert len(resources) == 10

    # Timeslots
    with open(SEED_DIR / "timeslots.json", "r", encoding="utf-8") as f:
        timeslots_raw = json.load(f)
    timeslots = [TimeSlot.model_validate(ts) for ts in timeslots_raw]
    assert len(timeslots) == 20

    # Enrollment history
    with open(SEED_DIR / "enrollment_history.json", "r", encoding="utf-8") as f:
        enrollment_raw = json.load(f)
    assert len(enrollment_raw) == 360  # 40 courses * 9 terms
    for row in enrollment_raw:
        assert "course_id" in row
        assert "course_code" in row
        assert "term" in row
        assert "season" in row
        assert "year" in row
        assert "enrolled_students" in row
        assert "avg_section_size" in row
        assert row["enrolled_students"] > 0


FIXTURE_CASES = [
    ("balanced_baseline", True, None),
    ("tight_capacity", True, None),
    ("infeasible_expertise", False, "HC-01"),
    ("leave_heavy", False, "HC-04"),
    ("single_expert_bottleneck", False, "HC-02"),
    ("lab_resource_shortage", False, "HC-07"),
    ("time_clash_dense", False, "HC-03"),
    ("demand_spike", True, None),
    ("boundary_exact_limit", True, None),
    ("boundary_zero_capacity", False, "HC-07"),
]


@pytest.mark.parametrize(
    "fixture_name,expected_feasible,expected_violation_rule", FIXTURE_CASES
)
def test_evaluation_fixtures(
    fixture_name: str, expected_feasible: bool, expected_violation_rule: str | None
):
    """Test that all 10 fixtures validate against schemas and evaluate properly via ConstraintEngine."""
    fixture_path = FIXTURES_DIR / f"{fixture_name}.json"
    assert fixture_path.exists(), f"Fixture file {fixture_path} does not exist"
    assert (
        fixture_path.stat().st_size < 1_000_000
    ), f"Fixture {fixture_name} exceeds 1MB limit"

    with open(fixture_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Check top-level fixture format
    assert data["name"] == fixture_name
    assert "expected_outcome" in data
    assert data["expected_outcome"]["feasible"] == expected_feasible
    assert isinstance(data["expected_outcome"]["reason"], str)

    # Validate against Pydantic schemas
    scenario = ValidationScenario.model_validate(data["scenario"])
    assignments = [Assignment.model_validate(a) for a in data["assignments"]]

    # Evaluate with constraint engine
    engine = ConstraintEngine()
    violations = engine.validate(assignments, scenario)
    hard_violations = [v for v in violations if v.severity == ViolationSeverity.ERROR]

    if expected_feasible:
        assert len(hard_violations) == 0, (
            f"Expected {fixture_name} to be feasible, but found hard violations: "
            f"{[v.rule_id + ': ' + v.explanation for v in hard_violations]}"
        )
    else:
        assert (
            len(hard_violations) > 0
        ), f"Expected {fixture_name} to be infeasible, but found 0 hard violations"
        if expected_violation_rule:
            violated_rule_ids = {v.rule_id for v in hard_violations}
            assert expected_violation_rule in violated_rule_ids, (
                f"Expected violation of {expected_violation_rule} in {fixture_name}, "
                f"but got {violated_rule_ids}"
            )


def test_scenarios_aggregate_json():
    """Verify scenarios.json aggregates all 10 fixtures properly."""
    scenarios_path = FIXTURES_DIR / "scenarios.json"
    assert scenarios_path.exists()
    assert scenarios_path.stat().st_size < 1_000_000

    with open(scenarios_path, "r", encoding="utf-8") as f:
        all_scenarios = json.load(f)

    assert len(all_scenarios) == 10
    for name, _, _ in FIXTURE_CASES:
        assert name in all_scenarios
        assert all_scenarios[name]["name"] == name
