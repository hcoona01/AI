"""Integration tests for assignment optimization, override, explain, fairness, and RBAC."""

import time
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.repositories import get_assignment_repository, get_override_repository, get_audit_repository
from app.schemas.assignment import Assignment
from app.schemas.common import AssignmentSource

client = TestClient(app)

ADMIN_HEADERS = {"x-user-role": "admin", "x-user-id": "u-admin-test"}
FACULTY_HEADERS_F01 = {
    "x-user-role": "faculty",
    "x-user-id": "u-faculty-test",
    "x-faculty-id": "f-01",
}
FACULTY_HEADERS_F02 = {
    "x-user-role": "faculty",
    "x-user-id": "u-faculty-test-2",
    "x-faculty-id": "f-02",
}


@pytest.fixture(autouse=True)
def reset_jobs_and_assignments():
    """Reset service in-memory job state before each test."""
    from app.services.assignment_service import AssignmentService
    AssignmentService._active_job = None
    AssignmentService._jobs.clear()


def test_single_active_job_enforcement():
    """Verify that only one optimization job can be active at a time (409 Conflict on concurrent)."""
    from app.services.assignment_service import AssignmentService

    # 1. Trigger first job (CPSAT)
    resp1 = client.post(
        "/api/v1/assign/run",
        json={"term": "Fall 2026", "method": "cpsat", "forecast_mode": "p50", "time_limit": 5.0},
        headers=ADMIN_HEADERS,
    )
    assert resp1.status_code == 202
    job_id1 = resp1.json()["job_id"]

    # 2. While an active job is marked as RUNNING in the service, second call returns 409
    AssignmentService._active_job = {"id": job_id1, "status": "RUNNING"}
    resp2 = client.post(
        "/api/v1/assign/run",
        json={"term": "Fall 2026", "method": "greedy", "forecast_mode": "p50"},
        headers=ADMIN_HEADERS,
    )
    assert resp2.status_code == 409
    assert "currently running" in resp2.json()["message"].lower()

    # 3. Check status of job 1
    status_resp = client.get(f"/api/v1/assign/jobs/{job_id1}", headers=ADMIN_HEADERS)
    assert status_resp.status_code == 200
    assert status_resp.json()["id"] == job_id1


def test_greedy_job_run_and_status():
    """Verify running greedy optimization finishes and updates job status and audit log."""
    from app.schemas.course import Course
    from app.schemas.section import Section
    from app.repositories import get_course_repository, get_section_repository
    import asyncio

    # Seed a cleanly feasible course & section in a dedicated test term
    c = Course.model_validate({
        "id": "c-test-greedy",
        "code": "TG101",
        "title": "Test Greedy Course",
        "credits": 3,
        "contact_hours": 3.0,
        "level": "undergraduate",
        "required_tags": ["Algorithms"],
        "min_proficiency": 2,
        "is_lab": False,
        "required_resource_ids": [],
    })
    s = Section.model_validate({
        "id": "s-test-greedy-1",
        "course_id": "c-test-greedy",
        "term": "TermGreedyFeasible",
        "section_cap": 30,
        "expected_size": 20,
        "size_p10": 15,
        "size_p50": 20,
        "size_p90": 25,
        "time_slot_id": None,
    })

    asyncio.run(get_course_repository().upsert(c))
    asyncio.run(get_section_repository().upsert(s))

    resp = client.post(
        "/api/v1/assign/run",
        json={"term": "TermGreedyFeasible", "method": "greedy", "forecast_mode": "p50"},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    # Poll for completion (greedy finishes in under 2 seconds)
    status_resp = None
    for _ in range(30):
        time.sleep(0.3)
        status_resp = client.get(f"/api/v1/assign/jobs/{job_id}", headers=ADMIN_HEADERS)
        if status_resp.json()["status"] in ["COMPLETED", "FAILED"]:
            break

    assert status_resp is not None
    job_data = status_resp.json()
    assert job_data["status"] == "COMPLETED"
    assert job_data["result"] is not None
    assert job_data["result"]["feasible"] is True
    assert job_data["result"]["assignments_count"] > 0

    # Verify audit logs captured job events
    audit_resp = client.get("/api/v1/audit?action=OPTIMIZE_JOB_START", headers=ADMIN_HEADERS)
    assert audit_resp.status_code == 200
    assert len(audit_resp.json()) > 0


def test_infeasible_path():
    """Verify that an infeasible scenario records infeasibility and provides explanation/blocking rules."""
    from app.services.assignment_service import AssignmentService
    from app.schemas.course import Course
    from app.schemas.section import Section
    from app.repositories import get_course_repository, get_section_repository

    # Inject impossible course and section into store with term 'ImpossibleTerm'
    imp_course = Course.model_validate({
        "id": "c-impossible",
        "code": "IMP999",
        "title": "Quantum Impossible",
        "credits": 4,
        "contact_hours": 4.0,
        "level": "undergraduate",
        "required_tags": ["AlienTechSuperSpecialty"],
        "min_proficiency": 5,
        "is_lab": False,
        "required_resource_ids": [],
    })
    imp_section = Section.model_validate({
        "id": "s-impossible-1",
        "course_id": "c-impossible",
        "term": "ImpossibleTerm",
        "section_cap": 30,
        "expected_size": 25,
        "size_p10": 20,
        "size_p50": 25,
        "size_p90": 30,
        "time_slot_id": None,
    })

    course_repo = get_course_repository()
    section_repo = get_section_repository()

    import asyncio
    asyncio.run(course_repo.upsert(imp_course))
    asyncio.run(section_repo.upsert(imp_section))

    # Run optimization on ImpossibleTerm
    resp = client.post(
        "/api/v1/assign/run",
        json={"term": "ImpossibleTerm", "method": "cpsat", "forecast_mode": "p50", "time_limit": 5.0},
        headers=ADMIN_HEADERS,
    )
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    status_resp = None
    for _ in range(30):
        time.sleep(0.3)
        status_resp = client.get(f"/api/v1/assign/jobs/{job_id}", headers=ADMIN_HEADERS)
        if status_resp.json()["status"] in ["COMPLETED", "FAILED"]:
            break

    assert status_resp is not None
    job_data = status_resp.json()
    assert job_data["status"] == "COMPLETED"
    res = job_data["result"]
    assert res["feasible"] is False
    assert "HC-01" in res["blocking_rule_ids"]
    assert "zero eligible instructors" in res["explanation"].lower()


def test_explain_assignment_and_faculty_isolation():
    """Verify GET /assign/explain/{id} shows chosen rationale + top 3 alternatives, and enforces role access."""
    # Seed an assignment with existing section SEC-FA26-CS580-01
    import asyncio
    asgn_repo = get_assignment_repository()
    test_asgn = Assignment(
        id="asgn-test-explain",
        section_id="SEC-FA26-CS580-01",
        faculty_id="f-01",
        source=AssignmentSource.SOLVER,
        fit_score=0.85,
        fit_breakdown={"tag_overlap": 0.9, "tfidf_syllabus": 0.8},
        rule_ids_satisfied=["HC-01", "HC-02", "HC-03", "HC-06"],
        rule_ids_violated=[],
        run_id="run-test",
    )
    asyncio.run(asgn_repo.upsert(test_asgn))

    # Admin can explain any assignment
    admin_resp = client.get(f"/api/v1/assign/explain/{test_asgn.id}", headers=ADMIN_HEADERS)
    assert admin_resp.status_code == 200
    data = admin_resp.json()
    assert data["assignment_id"] == test_asgn.id
    assert data["chosen_faculty"]["faculty_id"] == "f-01"
    assert len(data["top_alternatives"]) <= 3
    assert data["total_candidates_evaluated"] >= 20

    # Faculty f-01 can explain their own assignment
    fac1_resp = client.get(f"/api/v1/assign/explain/{test_asgn.id}", headers=FACULTY_HEADERS_F01)
    assert fac1_resp.status_code == 200

    # Faculty f-02 CANNOT explain f-01's assignment (403 Forbidden)
    fac2_resp = client.get(f"/api/v1/assign/explain/{test_asgn.id}", headers=FACULTY_HEADERS_F02)
    assert fac2_resp.status_code == 403
    assert "restricted" in fac2_resp.json()["message"].lower()


def test_faculty_assignment_listing_restricted():
    """Verify GET /assign restricts faculty to seeing only their own assignments."""
    import asyncio
    asgn_repo = get_assignment_repository()
    asgn_f01 = Assignment(
        id="asgn-f01-list-test",
        section_id="SEC-FA26-CS580-01",
        faculty_id="f-01",
        source=AssignmentSource.SOLVER,
        fit_score=0.9,
        run_id="run-1",
    )
    asgn_f02 = Assignment(
        id="asgn-f02-list-test",
        section_id="SEC-FA26-CS580-01",
        faculty_id="f-02",
        source=AssignmentSource.SOLVER,
        fit_score=0.85,
        run_id="run-1",
    )
    asyncio.run(asgn_repo.upsert(asgn_f01))
    asyncio.run(asgn_repo.upsert(asgn_f02))

    # Admin gets all
    admin_resp = client.get("/api/v1/assign", headers=ADMIN_HEADERS)
    assert admin_resp.status_code == 200
    all_asgns = admin_resp.json()
    ids = {a["id"] for a in all_asgns}
    assert asgn_f01.id in ids and asgn_f02.id in ids

    # Faculty f-01 gets ONLY f-01
    fac1_resp = client.get("/api/v1/assign", headers=FACULTY_HEADERS_F01)
    assert fac1_resp.status_code == 200
    my_asgns = fac1_resp.json()
    assert all(a["faculty_id"] == "f-01" for a in my_asgns)
    assert any(a["id"] == asgn_f01.id for a in my_asgns)
    assert not any(a["id"] == asgn_f02.id for a in my_asgns)

    # Faculty f-01 querying ?faculty_id=f-02 gets 403
    forbidden_resp = client.get("/api/v1/assign?faculty_id=f-02", headers=FACULTY_HEADERS_F01)
    assert forbidden_resp.status_code == 403


def test_fairness_and_conflicts_endpoints():
    """Verify GET /assign/fairness and GET /assign/conflicts endpoints."""
    # Fairness
    f_resp = client.get("/api/v1/assign/fairness?term=Fall 2026", headers=ADMIN_HEADERS)
    assert f_resp.status_code == 200
    fairness = f_resp.json()
    for k in ["gini", "std_dev", "max_min_gap", "faculty_loads"]:
        assert k in fairness

    # Conflicts
    c_resp = client.get("/api/v1/assign/conflicts?term=Fall 2026", headers=ADMIN_HEADERS)
    assert c_resp.status_code == 200
    conflicts = c_resp.json()
    assert "violations" in conflicts
    assert "has_hard_violations" in conflicts
    assert "repair_alternatives" in conflicts


def test_override_flow_with_and_without_hard_violations():
    """Verify POST /assign/override requires acknowledge_violations when hard violations occur,
    preserves recommendation in snapshot, and logs audit trail.
    """
    import asyncio
    asgn_repo = get_assignment_repository()

    # Seed an initial assignment on SEC-FA26-CS580-01
    asgn = Assignment(
        id="asgn-override-flow-test",
        section_id="SEC-FA26-CS580-01",
        faculty_id="f-01",
        source=AssignmentSource.SOLVER,
        fit_score=0.92,
        run_id="run-flow",
    )
    asyncio.run(asgn_repo.upsert(asgn))

    # 1. First test same-faculty error (400)
    same_resp = client.post(
        "/api/v1/assign/override",
        json={
            "assignment_id": asgn.id,
            "new_faculty_id": "f-01",
            "reason": "Redundant assignment test",
        },
        headers=ADMIN_HEADERS,
    )
    assert same_resp.status_code == 400

    # 2. Assign to an instructor (f-20)
    # Test without acknowledge_violations:
    ovr_resp = client.post(
        "/api/v1/assign/override",
        json={
            "assignment_id": asgn.id,
            "new_faculty_id": "f-20",
            "reason": "Department chair urgent staffing override",
            "acknowledge_violations": False,
        },
        headers=ADMIN_HEADERS,
    )
    assert ovr_resp.status_code == 200
    ovr_data = ovr_resp.json()

    if ovr_data.get("requires_acknowledgement"):
        # Rejected because hard violations were detected!
        assert ovr_data["success"] is False
        assert len(ovr_data["hard_violations"]) > 0

        # Now re-attempt with acknowledge_violations=True
        ack_resp = client.post(
            "/api/v1/assign/override",
            json={
                "assignment_id": asgn.id,
                "new_faculty_id": "f-20",
                "reason": "Department chair urgent staffing override",
                "acknowledge_violations": True,
            },
            headers=ADMIN_HEADERS,
        )
        assert ack_resp.status_code == 200
        ack_data = ack_resp.json()
        assert ack_data["success"] is True
        assert "override_id" in ack_data
        assert ack_data["snapshot"]["previous_faculty_id"] == "f-01"
        assert ack_data["assignment"]["faculty_id"] == "f-20"
        assert ack_data["assignment"]["source"] == "override"
    else:
        # Override succeeded cleanly
        assert ovr_data["success"] is True
        assert ovr_data["snapshot"]["previous_faculty_id"] == "f-01"

    # 3. Faculty user cannot perform overrides (403 Forbidden)
    forbidden_resp = client.post(
        "/api/v1/assign/override",
        json={
            "assignment_id": asgn.id,
            "new_faculty_id": "f-02",
            "reason": "Unauthorized faculty override",
        },
        headers=FACULTY_HEADERS_F01,
    )
    assert forbidden_resp.status_code == 403

    # 4. Verify audit log entry was written
    audit_resp = client.get("/api/v1/audit?action=ASSIGNMENT_OVERRIDE", headers=ADMIN_HEADERS)
    assert audit_resp.status_code == 200
    assert len(audit_resp.json()) > 0


def test_repair_apply_endpoint():
    """Verify POST /assign/repair/apply applies repair, triggers re-solve, and audits action."""
    repair_resp = client.post(
        "/api/v1/assign/repair/apply",
        json={
            "repair_type": "relax_hc05",
            "term": "Fall 2026",
        },
        headers=ADMIN_HEADERS,
    )
    assert repair_resp.status_code == 200
    data = repair_resp.json()
    assert data["success"] is True
    assert "triggered_job_id" in data

    # Faculty cannot apply repairs (403)
    faculty_resp = client.post(
        "/api/v1/assign/repair/apply",
        json={"repair_type": "relax_hc05", "term": "Fall 2026"},
        headers=FACULTY_HEADERS_F01,
    )
    assert faculty_resp.status_code == 403
