from fastapi.testclient import TestClient

from app.main import app
from app.schemas.assignment import Assignment, AssignmentSource
from app.schemas.common import CourseLevel, FacultyRank
from app.schemas.course import Course
from app.schemas.faculty import Faculty
from app.schemas.section import Section

client = TestClient(app)


def test_get_constraints_returns_all_rules():
    response = client.get("/api/v1/constraints")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 12
    rule_ids = {r["rule_id"] for r in data}
    assert "HC-01" in rule_ids
    assert "HC-02" in rule_ids
    assert "SC-01" in rule_ids


def test_put_constraints_admin_allowed():
    payload = {
        "rules": [
            {
                "rule_id": "SC-01",
                "type": "soft",
                "description": "Custom updated description",
                "weight": 4.5,
                "enabled": True,
                "params": {"min_acceptable_fit": 0.75},
            }
        ]
    }
    response = client.put(
        "/api/v1/constraints",
        json=payload,
        headers={"x-user-role": "admin"},
    )
    assert response.status_code == 200
    data = response.json()
    sc01 = next(r for r in data if r["rule_id"] == "SC-01")
    assert sc01["weight"] == 4.5
    assert sc01["params"]["min_acceptable_fit"] == 0.75

    # Restore default SC-01
    restore_payload = {
        "rules": [
            {
                "rule_id": "SC-01",
                "type": "soft",
                "description": "Maximize faculty expertise fit score with assigned course content",
                "weight": 3.0,
                "enabled": True,
                "params": {"min_acceptable_fit": 0.6},
            }
        ]
    }
    client.put(
        "/api/v1/constraints", json=restore_payload, headers={"x-user-role": "admin"}
    )


def test_put_constraints_faculty_forbidden():
    payload = {
        "rules": [
            {
                "rule_id": "HC-01",
                "type": "hard",
                "description": "Attempted faculty update",
                "weight": 1.0,
                "enabled": False,
                "params": {},
            }
        ]
    }
    response = client.put(
        "/api/v1/constraints",
        json=payload,
        headers={"x-user-role": "faculty"},
    )
    assert response.status_code == 403
    assert "Admin role required" in response.json()["detail"]


def test_post_constraints_validate_endpoint():
    f = Faculty(
        id="f1",
        name="Dr. Curie",
        email="curie@univ.edu",
        rank=FacultyRank.PROFESSOR,
        max_weekly_load_hours=12.0,
        max_courses=3,
        min_courses=1,
        max_preparations=2,
    )
    c = Course(
        id="c1",
        code="PHYS101",
        title="Physics I",
        credits=3,
        contact_hours=15.0,  # exceeds 12.0h -> triggers HC-02!
        level=CourseLevel.UNDERGRADUATE,
    )
    s = Section(
        id="s1",
        course_id="c1",
        term="Fall 2026",
        section_cap=30,
        expected_size=25,
        size_p10=15,
        size_p50=25,
        size_p90=28,
    )
    a = Assignment(
        id="a1",
        section_id="s1",
        faculty_id="f1",
        source=AssignmentSource.SOLVER,
        fit_score=0.85,
        run_id="run-test",
    )

    request_payload = {
        "assignments": [a.model_dump(mode="json")],
        "scenario": {
            "faculty": [f.model_dump(mode="json")],
            "courses": [c.model_dump(mode="json")],
            "sections": [s.model_dump(mode="json")],
            "resources": [],
            "timeslots": [],
            "previous_assignments": [],
        },
    }

    response = client.post("/api/v1/constraints/validate", json=request_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["is_valid"] is False
    assert data["hard_violation_count"] >= 1
    hc02_violations = [v for v in data["violations"] if v["rule_id"] == "HC-02"]
    assert len(hc02_violations) == 1
    assert "the limit is 12h" in hc02_violations[0]["explanation"]
