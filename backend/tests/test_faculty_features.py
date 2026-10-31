"""Integration tests verifying faculty self-service features and strict RBAC isolation."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

ADMIN_HEADERS = {"x-user-role": "admin", "x-user-id": "u-admin-test"}
FACULTY_HEADERS_F01 = {
    "x-user-role": "faculty",
    "x-user-id": "u-faculty-test-1",
    "x-faculty-id": "f-01",
}
FACULTY_HEADERS_F02 = {
    "x-user-role": "faculty",
    "x-user-id": "u-faculty-test-2",
    "x-faculty-id": "f-02",
}


def test_faculty_preferences_update_and_rbac():
    """Verify faculty can update their own availability & preferences, but cannot modify others."""
    # 1. Faculty f-01 updates their own preferences -> succeeds
    payload = {
        "unavailable_slots": ["ts-01", "ts-03"],
        "leave_terms": ["Summer 2027"],
        "preferred_course_ids": ["c-01", "c-02"],
    }
    resp = client.put(
        "/api/v1/faculty/f-01/preferences",
        json=payload,
        headers=FACULTY_HEADERS_F01,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["success"] is True
    assert data["pending_optimization"] is True
    assert "pending" in data["message"].lower()
    assert data["faculty"]["unavailable_slots"] == ["ts-01", "ts-03"]
    assert data["faculty"]["leave_terms"] == ["Summer 2027"]

    # 2. Faculty f-01 attempts to modify f-02 preferences -> 403 Forbidden
    unauth_resp = client.put(
        "/api/v1/faculty/f-02/preferences",
        json=payload,
        headers=FACULTY_HEADERS_F01,
    )
    assert unauth_resp.status_code == 403
    assert "restricted" in unauth_resp.json()["message"].lower()

    # 3. Admin can update f-02 preferences
    admin_resp = client.put(
        "/api/v1/faculty/f-02/preferences",
        json=payload,
        headers=ADMIN_HEADERS,
    )
    assert admin_resp.status_code == 200


def test_anonymized_load_comparison_and_privacy():
    """Verify faculty load comparison strictly anonymizes peers (never other faculty names)."""
    # 1. Faculty f-01 queries their own load comparison -> succeeds
    resp = client.get(
        "/api/v1/faculty/f-01/load-comparison?term=Fall 2026",
        headers=FACULTY_HEADERS_F01,
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()

    assert data["faculty_id"] == "f-01"
    assert "my_load" in data
    assert "department_median_load" in data
    assert "anonymized_peers" in data
    assert len(data["anonymized_peers"]) > 0

    # Ensure no peer has a real name or email, and current user is labeled 'You'
    found_you = False
    for peer in data["anonymized_peers"]:
        if peer["is_current_user"]:
            found_you = True
            assert "You" in peer["label"]
        else:
            # Must be strictly anonymized
            assert peer["peer_id"].startswith("peer-")
            assert "name" not in peer
            assert "email" not in peer
            assert "Peer" in peer["label"]

    assert found_you, "Current user must be represented in anonymized peer distribution"

    # 2. Faculty f-01 queries load comparison for f-02 -> 403 Forbidden
    forbidden_resp = client.get(
        "/api/v1/faculty/f-02/load-comparison?term=Fall 2026",
        headers=FACULTY_HEADERS_F01,
    )
    assert forbidden_resp.status_code == 403
    assert "restricted" in forbidden_resp.json()["message"].lower()


def test_change_request_lifecycle_and_isolation():
    """Verify faculty can only submit comments on their own assignments and admin can review."""
    # Find active assignment for f-01 or create one if needed
    assign_resp = client.get("/api/v1/assign?term=Fall 2026", headers=ADMIN_HEADERS)
    assert assign_resp.status_code == 200
    assignments = assign_resp.json()

    f01_asgn = next((a for a in assignments if a["faculty_id"] == "f-01"), None)
    f02_asgn = next((a for a in assignments if a["faculty_id"] == "f-02"), None)

    # If test data has assignments:
    if f01_asgn:
        # 1. Faculty f-01 creates change request on own assignment -> succeeds
        cr_payload = {
            "assignment_id": f01_asgn["id"],
            "comment": "Requesting to swap section due to graduate research conflict on Fridays.",
        }
        cr_resp = client.post(
            "/api/v1/faculty/change-requests",
            json=cr_payload,
            headers=FACULTY_HEADERS_F01,
        )
        assert cr_resp.status_code == 201, cr_resp.text
        cr_data = cr_resp.json()
        assert cr_data["status"] == "pending"
        assert cr_data["faculty_id"] == "f-01"

        # 2. Faculty f-01 listing change requests sees their own request
        my_reqs_resp = client.get(
            "/api/v1/faculty/change-requests",
            headers=FACULTY_HEADERS_F01,
        )
        assert my_reqs_resp.status_code == 200
        req_ids = [r["id"] for r in my_reqs_resp.json()]
        assert cr_data["id"] in req_ids

        # 3. Faculty f-02 listing change requests does NOT see f-01's request
        f02_reqs_resp = client.get(
            "/api/v1/faculty/change-requests",
            headers=FACULTY_HEADERS_F02,
        )
        assert f02_reqs_resp.status_code == 200
        f02_req_ids = [r["id"] for r in f02_reqs_resp.json()]
        assert cr_data["id"] not in f02_req_ids

        # 4. Faculty f-01 attempting to approve/reject own change request -> 403 Forbidden
        status_payload = {"status": "approved", "admin_response": "Self-approved"}
        forbidden_status = client.put(
            f"/api/v1/faculty/change-requests/{cr_data['id']}/status",
            json=status_payload,
            headers=FACULTY_HEADERS_F01,
        )
        assert forbidden_status.status_code == 403

        # 5. Admin can approve change request
        admin_status = client.put(
            f"/api/v1/faculty/change-requests/{cr_data['id']}/status",
            json={"status": "approved", "admin_response": "Approved by dept chair."},
            headers=ADMIN_HEADERS,
        )
        assert admin_status.status_code == 200
        assert admin_status.json()["status"] == "approved"

    if f02_asgn:
        # 6. Faculty f-01 attempts to create change request on f-02 assignment -> 403 Forbidden
        forbidden_cr = client.post(
            "/api/v1/faculty/change-requests",
            json={
                "assignment_id": f02_asgn["id"],
                "comment": "Attempting to request change on colleague's assignment.",
            },
            headers=FACULTY_HEADERS_F01,
        )
        assert forbidden_cr.status_code == 403

