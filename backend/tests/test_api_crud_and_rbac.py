"""Integration tests verifying role enforcement, administrative CRUD, audit logging, and scenario loading."""

from fastapi.testclient import TestClient

from app.main import app

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


def test_faculty_reads_are_role_aware():
    """Verify faculty can only view their own profile, while admins view all."""
    # 1. Admin gets all faculty
    admin_resp = client.get("/api/v1/faculty", headers=ADMIN_HEADERS)
    assert admin_resp.status_code == 200
    all_fac = admin_resp.json()
    assert len(all_fac) >= 20

    # 2. Faculty member f-01 gets only f-01 in list
    fac_resp = client.get("/api/v1/faculty", headers=FACULTY_HEADERS_F01)
    assert fac_resp.status_code == 200
    my_fac = fac_resp.json()
    assert len(my_fac) == 1
    assert my_fac[0]["id"] == "f-01"

    # 3. Faculty f-01 reading their own ID directly succeeds
    self_resp = client.get("/api/v1/faculty/f-01", headers=FACULTY_HEADERS_F01)
    assert self_resp.status_code == 200
    assert self_resp.json()["id"] == "f-01"

    # 4. Faculty f-01 reading another faculty's profile (f-02) is forbidden (403)
    forbidden_resp = client.get("/api/v1/faculty/f-02", headers=FACULTY_HEADERS_F01)
    assert forbidden_resp.status_code == 403
    assert "restricted" in forbidden_resp.json()["message"].lower()

    # 5. Admin reading f-02 succeeds
    admin_f02 = client.get("/api/v1/faculty/f-02", headers=ADMIN_HEADERS)
    assert admin_f02.status_code == 200
    assert admin_f02.json()["id"] == "f-02"


def test_shared_reference_data_readable_by_all():
    """Verify shared reference data (courses, sections, resources, timeslots) is accessible by faculty."""
    for endpoint in [
        "/api/v1/courses",
        "/api/v1/sections",
        "/api/v1/resources",
        "/api/v1/timeslots",
    ]:
        resp = client.get(endpoint, headers=FACULTY_HEADERS_F01)
        assert resp.status_code == 200, f"Failed accessing {endpoint} as faculty"
        assert isinstance(resp.json(), list)
        assert len(resp.json()) > 0


def test_writes_are_strictly_admin_only():
    """Verify write attempts by faculty members return 403 Forbidden across all entities."""
    # 1. Course write
    course_payload = {
        "id": "c-unauthorized",
        "code": "UNAUTH101",
        "title": "Unauthorized Course",
        "credits": 3,
        "contact_hours": 3.0,
        "level": "undergraduate",
        "required_tags": ["Algorithms"],
        "min_proficiency": 2,
        "is_lab": False,
        "required_resource_ids": [],
    }
    resp = client.post(
        "/api/v1/courses", json=course_payload, headers=FACULTY_HEADERS_F01
    )
    assert resp.status_code == 403

    # 2. Faculty write
    fac_payload = {
        "id": "f-unauth",
        "name": "Dr. Unauth",
        "email": "unauth@univ.edu",
        "rank": "Assistant Professor",
        "expertise": [{"tag": "Algorithms", "proficiency": 3}],
        "max_weekly_load_hours": 12.0,
        "max_courses": 3,
        "min_courses": 1,
        "max_preparations": 2,
    }
    resp = client.post("/api/v1/faculty", json=fac_payload, headers=FACULTY_HEADERS_F01)
    assert resp.status_code == 403

    # 3. Section write
    section_payload = {
        "id": "s-unauth-01",
        "course_id": "c-cs101",
        "term": "Fall 2026",
        "section_cap": 30,
        "expected_size": 25,
        "size_p10": 20,
        "size_p50": 25,
        "size_p90": 28,
        "time_slot_id": "TS-MON-0900",
    }
    resp = client.post(
        "/api/v1/sections", json=section_payload, headers=FACULTY_HEADERS_F01
    )
    assert resp.status_code == 403

    # 4. Resource write
    res_payload = {
        "id": "ROOM-UNAUTH",
        "type": "room",
        "capacity": 50,
        "unavailable_slots": [],
    }
    resp = client.post(
        "/api/v1/resources", json=res_payload, headers=FACULTY_HEADERS_F01
    )
    assert resp.status_code == 403

    # 5. Timeslot write
    slot_payload = {
        "id": "TS-UNAUTH",
        "day": "Monday",
        "start": "08:00",
        "end": "09:15",
    }
    resp = client.post(
        "/api/v1/timeslots", json=slot_payload, headers=FACULTY_HEADERS_F01
    )
    assert resp.status_code == 403


def test_admin_crud_and_audit_trail_logging():
    """Verify admin CRUD creates audit entries for create, update, and delete operations."""
    test_code = "CS999"
    test_id = f"c-{test_code.lower()}"

    # 1. CREATE
    create_payload = {
        "id": test_id,
        "code": test_code,
        "title": "Advanced Experimental Testing",
        "description": "Testing CRUD and audit trail",
        "credits": 4,
        "contact_hours": 4.0,
        "level": "graduate",
        "required_tags": ["Algorithms"],
        "min_proficiency": 4,
        "is_lab": False,
        "required_resource_ids": ["ROOM-101"],
    }
    create_resp = client.post(
        "/api/v1/courses", json=create_payload, headers=ADMIN_HEADERS
    )
    assert create_resp.status_code == 201
    created_course = create_resp.json()
    assert created_course["code"] == test_code

    # 2. UPDATE
    update_payload = dict(create_payload)
    update_payload["title"] = "Updated Experimental Testing Title"
    update_resp = client.put(
        f"/api/v1/courses/{test_id}", json=update_payload, headers=ADMIN_HEADERS
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["title"] == "Updated Experimental Testing Title"

    # 3. DELETE
    delete_resp = client.delete(f"/api/v1/courses/{test_id}", headers=ADMIN_HEADERS)
    assert delete_resp.status_code == 204

    # Verify not found after delete
    get_resp = client.get(f"/api/v1/courses/{test_id}", headers=ADMIN_HEADERS)
    assert get_resp.status_code == 404

    # 4. Check audit log for COURSE_CREATED, COURSE_UPDATED, COURSE_DELETED
    audit_resp = client.get("/api/v1/audit?entity=course", headers=ADMIN_HEADERS)
    assert audit_resp.status_code == 200
    logs = audit_resp.json()
    actions = {log["action"] for log in logs}
    assert "COURSE_CREATED" in actions
    assert "COURSE_UPDATED" in actions
    assert "COURSE_DELETED" in actions

    # Non-admin access to audit is forbidden
    fac_audit_resp = client.get("/api/v1/audit", headers=FACULTY_HEADERS_F01)
    assert fac_audit_resp.status_code == 403


def test_scenario_loading_and_audit():
    """Verify loading evaluation fixtures replaces store state and records audit log."""
    scenario_name = "infeasible_expertise"

    # 1. Faculty cannot load scenarios
    fac_resp = client.post(
        f"/api/v1/scenarios/load/{scenario_name}", headers=FACULTY_HEADERS_F01
    )
    assert fac_resp.status_code == 403

    # 2. Non-existent fixture returns 404
    missing_resp = client.post(
        "/api/v1/scenarios/load/non_existent_fixture_123", headers=ADMIN_HEADERS
    )
    assert missing_resp.status_code == 404

    # 3. Admin loads valid fixture
    load_resp = client.post(
        f"/api/v1/scenarios/load/{scenario_name}", headers=ADMIN_HEADERS
    )
    assert load_resp.status_code == 200
    data = load_resp.json()
    assert data["scenario_name"] == scenario_name
    assert data["expected_outcome"]["feasible"] is False
    assert "HC-01" in data["expected_outcome"]["reason"]
    assert data["loaded_counts"]["courses"] >= 1

    # 4. Confirm audit log recorded
    audit_resp = client.get(
        "/api/v1/audit?action=SCENARIO_LOADED", headers=ADMIN_HEADERS
    )
    assert audit_resp.status_code == 200
    logs = audit_resp.json()
    assert len(logs) >= 1
    latest_scenario_log = logs[0]
    assert latest_scenario_log["payload"]["scenario_name"] == scenario_name
    assert latest_scenario_log["payload"]["feasible"] is False

    # 5. Restore full seed state after test
    import asyncio

    from scripts.seed_store import seed_data

    asyncio.run(seed_data(reset=True))
