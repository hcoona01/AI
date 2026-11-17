"""Tests for passwordless Email OTP authentication, session lifecycle, and RBAC enforcement."""

from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.errors import ForbiddenError
from app.core.security import decode_access_token, verify_faculty_access
from app.main import app
from app.schemas.common import UserRole
from app.schemas.user import User
from app.services.otp_service import get_otp_service

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_otp_store():
    """Ensure in-memory OTP store and rate-limit tracking are fresh for each test."""
    otp_svc = get_otp_service()
    otp_svc.clear_all()
    yield
    otp_svc.clear_all()


def test_generic_response_for_existing_and_nonexistent_email():
    """Verify that OTP request returns the exact same generic response regardless of user existence."""
    # 1. Existing admin user
    resp_existing = client.post(
        "/auth/request-otp",
        json={"email": "admin@university.edu"},
    )
    assert resp_existing.status_code == 200
    data_existing = resp_existing.json()
    assert "one-time passcode" in data_existing["message"]
    assert data_existing["status"] == "sent"

    # 2. Non-existent email
    resp_nonexistent = client.post(
        "/auth/request-otp",
        json={"email": "unknown-ghost-user@university.edu"},
    )
    assert resp_nonexistent.status_code == 200
    data_nonexistent = resp_nonexistent.json()

    # Generic messages must match exactly to prevent account enumeration
    assert data_existing == data_nonexistent

    # Confirm OTP was only generated for existing user
    otp_svc = get_otp_service()
    assert otp_svc.get_dev_otp("admin@university.edu") is not None
    assert otp_svc.get_dev_otp("unknown-ghost-user@university.edu") is None


def test_otp_rate_limiting_per_email():
    """Verify that more than 8 OTP requests for the same email within 10 minutes returns 429."""
    email = "alan.turing@university.edu"

    # 8 allowed requests
    for i in range(8):
        resp = client.post("/auth/request-otp", json={"email": email})
        assert resp.status_code == 200, f"Request {i+1} should succeed"

    # 9th request must be rate-limited (HTTP 429)
    resp_blocked = client.post("/auth/request-otp", json={"email": email})
    assert resp_blocked.status_code == 429
    assert "Rate limit exceeded" in resp_blocked.json()["message"]


def test_otp_rate_limiting_per_ip():
    """Verify that more than 8 OTP requests from the same IP address within 10 minutes returns 429."""
    client_ip = "192.168.1.100"
    headers = {"x-forwarded-for": client_ip}

    # 8 allowed requests with different emails from the same IP
    emails = [
        "admin@university.edu",
        "chair@university.edu",
        "ada.lovelace@university.edu",
        "john.von.neumann@university.edu",
        "claude.shannon@university.edu",
        "marvin.minsky@university.edu",
        "tim.berners-lee@university.edu",
        "donald.knuth@university.edu",
    ]
    for email in emails:
        resp = client.post("/auth/request-otp", json={"email": email}, headers=headers)
        assert resp.status_code == 200

    # 9th request from same IP must be rejected with 429
    resp_blocked = client.post(
        "/auth/request-otp",
        json={"email": "grace.hopper@university.edu"},
        headers=headers,
    )
    assert resp_blocked.status_code == 429
    assert "Rate limit exceeded" in resp_blocked.json()["message"]


def test_otp_verification_success_and_tokens():
    """Verify successful OTP verification yields 15-minute access token and httpOnly refresh cookie."""
    email = "admin@university.edu"
    client.post("/auth/request-otp", json={"email": email})

    otp_svc = get_otp_service()
    otp_code = otp_svc.get_dev_otp(email)
    assert otp_code is not None
    assert len(otp_code) == 6

    # Verify OTP
    verify_resp = client.post(
        "/auth/verify-otp",
        json={"email": email, "otp": otp_code},
    )
    assert verify_resp.status_code == 200
    data = verify_resp.json()

    # Access token payload validation
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["expires_in"] == 900  # 15 minutes
    assert data["user"]["email"] == email
    assert data["user"]["role"] == "admin"

    # Validate decoded claims
    claims = decode_access_token(data["access_token"])
    assert claims["email"] == email
    assert claims["role"] == "admin"
    assert claims["type"] == "access"

    # Refresh token cookie validation
    assert "refresh_token" in verify_resp.cookies
    cookie = verify_resp.cookies["refresh_token"]
    assert cookie is not None


def test_otp_no_reuse_single_use():
    """Verify that an OTP code is strictly single-use and cannot be used twice."""
    email = "alan.turing@university.edu"
    client.post("/auth/request-otp", json={"email": email})

    otp_svc = get_otp_service()
    otp_code = otp_svc.get_dev_otp(email)
    assert otp_code is not None

    # First verification succeeds
    first_resp = client.post("/auth/verify-otp", json={"email": email, "otp": otp_code})
    assert first_resp.status_code == 200

    # Immediate second verification attempt with same code fails
    second_resp = client.post(
        "/auth/verify-otp", json={"email": email, "otp": otp_code}
    )
    assert second_resp.status_code == 401
    assert "invalid or expired" in second_resp.json()["message"].lower()


def test_otp_expiry():
    """Verify that an expired OTP cannot be verified."""
    email = "ada.lovelace@university.edu"
    client.post("/auth/request-otp", json={"email": email})

    otp_svc = get_otp_service()
    otp_code = otp_svc.get_dev_otp(email)
    assert otp_code is not None

    # Artificially expire the record
    norm_email = email.lower()
    record = otp_svc._store[norm_email]
    record.expires_at = datetime.now(UTC) - timedelta(seconds=1)

    # Verification must fail due to expiry
    resp = client.post(
        "/auth/verify-otp",
        json={"email": email, "otp": otp_code},
    )
    assert resp.status_code == 401
    assert "expired" in resp.json()["message"].lower()


def test_lockout_after_wrong_attempts():
    """Verify that after 5 wrong OTP attempts, the user is locked out and record is purged."""
    email = "grace.hopper@university.edu"
    client.post("/auth/request-otp", json={"email": email})

    otp_svc = get_otp_service()
    correct_otp = otp_svc.get_dev_otp(email)
    wrong_otp = "000000" if correct_otp != "000000" else "111111"

    # Attempts 1 through 4 should fail with attempt warning
    for i in range(1, 5):
        resp = client.post(
            "/auth/verify-otp",
            json={"email": email, "otp": wrong_otp},
        )
        assert resp.status_code == 401
        assert f"{5 - i} attempt(s) remaining" in resp.json()["message"]

    # 5th failed attempt triggers lockout
    resp_5 = client.post(
        "/auth/verify-otp",
        json={"email": email, "otp": wrong_otp},
    )
    assert resp_5.status_code == 401
    assert "maximum verification attempts exceeded" in resp_5.json()["message"].lower()

    # 6th attempt with CORRECT code still fails because OTP was purged on lockout
    resp_correct = client.post(
        "/auth/verify-otp",
        json={"email": email, "otp": correct_otp},
    )
    assert resp_correct.status_code == 401
    assert "invalid or expired" in resp_correct.json()["message"].lower()


def test_session_refresh_and_logout():
    """Verify POST /auth/refresh with cookie and POST /auth/logout cookie termination."""
    email = "chair@university.edu"
    client.post("/auth/request-otp", json={"email": email})

    otp_svc = get_otp_service()
    otp_code = otp_svc.get_dev_otp(email)

    login_resp = client.post(
        "/auth/verify-otp",
        json={"email": email, "otp": otp_code},
    )
    assert login_resp.status_code == 200
    refresh_cookie = login_resp.cookies["refresh_token"]

    # Refresh session using cookie
    refresh_resp = client.post(
        "/auth/refresh",
        cookies={"refresh_token": refresh_cookie},
    )
    assert refresh_resp.status_code == 200
    new_data = refresh_resp.json()
    assert "access_token" in new_data
    assert new_data["expires_in"] == 900
    assert "refresh_token" in refresh_resp.cookies

    # Logout clears the cookie
    logout_resp = client.post("/auth/logout")
    assert logout_resp.status_code == 200
    assert logout_resp.json()["message"] == "Successfully logged out"

    # Attempting refresh without cookie fails
    fail_refresh = client.post("/auth/refresh")
    assert fail_refresh.status_code == 401


def test_me_profile_retrieval():
    """Verify GET /me returns current user profile for authenticated tokens, 401 for anonymous."""
    # 1. Unauthenticated request returns 401
    unauth_resp = client.get("/me")
    assert unauth_resp.status_code == 401

    # 2. Authenticated Faculty member (Alan Turing, f-01)
    email = "alan.turing@university.edu"
    client.post("/auth/request-otp", json={"email": email})
    otp_code = get_otp_service().get_dev_otp(email)
    login_resp = client.post("/auth/verify-otp", json={"email": email, "otp": otp_code})
    token = login_resp.json()["access_token"]

    fac_me = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert fac_me.status_code == 200
    data = fac_me.json()
    assert data["email"] == email
    assert data["role"] == "faculty"
    assert data["faculty_id"] == "f-01"

    # Also test /api/v1/me alias
    v1_me = client.get("/api/v1/me", headers={"Authorization": f"Bearer {token}"})
    assert v1_me.status_code == 200
    assert v1_me.json()["id"] == data["id"]


def test_faculty_user_receives_403_on_admin_routes():
    """Verify that a faculty user (with valid JWT token) is forbidden (403) from admin-only routes."""
    # Login as faculty member f-01
    email = "alan.turing@university.edu"
    client.post("/auth/request-otp", json={"email": email})
    otp_code = get_otp_service().get_dev_otp(email)
    login_resp = client.post("/auth/verify-otp", json={"email": email, "otp": otp_code})
    fac_token = login_resp.json()["access_token"]
    fac_headers = {"Authorization": f"Bearer {fac_token}"}

    # 1. Course creation requires admin
    course_payload = {
        "id": "c-unauth-test",
        "code": "CS999",
        "title": "Unauthorized Test Course",
        "credits": 3,
        "contact_hours": 3.0,
        "level": "undergraduate",
        "required_tags": ["Algorithms"],
        "min_proficiency": 2,
        "is_lab": False,
        "required_resource_ids": [],
    }
    resp_course = client.post(
        "/api/v1/courses", json=course_payload, headers=fac_headers
    )
    assert resp_course.status_code == 403

    # 2. Scenario load requires admin
    resp_scenario = client.post(
        "/api/v1/scenarios/load/infeasible_expertise", headers=fac_headers
    )
    assert resp_scenario.status_code == 403

    # 3. Faculty deletion requires admin
    resp_del_fac = client.delete("/api/v1/faculty/f-02", headers=fac_headers)
    assert resp_del_fac.status_code == 403


def test_faculty_access_control_helper():
    """Verify that verify_faculty_access allows admins for all, and restricts faculty to their own ID."""
    admin_user = User(id="u-admin-1", email="admin@university.edu", role=UserRole.ADMIN)
    faculty_user_01 = User(
        id="u-f-01",
        email="alan.turing@university.edu",
        role=UserRole.FACULTY,
        faculty_id="f-01",
    )

    # Admin accessing f-01 and f-02 succeeds without exception
    verify_faculty_access("f-01", admin_user)
    verify_faculty_access("f-02", admin_user)

    # Faculty 01 accessing f-01 succeeds
    verify_faculty_access("f-01", faculty_user_01)

    # Faculty 01 accessing f-02 raises ForbiddenError
    with pytest.raises(ForbiddenError) as exc_info:
        verify_faculty_access("f-02", faculty_user_01)
    assert "restricted to accessing their own data" in str(exc_info.value)


def test_faculty_email_without_prior_user_record_auto_heals_and_generates_otp():
    """Verify that a faculty profile in faculty.json whose User record was never created
    auto-heals into users.json on authentication request, receives an OTP, and can log in.
    """
    import asyncio

    from app.repositories import get_faculty_repository, get_user_repository
    from app.schemas.faculty import Faculty

    faculty_repo = get_faculty_repository()
    user_repo = get_user_repository()
    otp_svc = get_otp_service()

    test_faculty_id = "f-test-om-999"
    test_faculty_email = "om.newfaculty@university.edu"

    # Clean up prior test residues
    asyncio.run(faculty_repo.delete(test_faculty_id))
    asyncio.run(user_repo.delete(f"u-{test_faculty_id}"))

    try:
        # 1. Insert faculty profile directly into faculty.json (simulating pre-existing record)
        test_fac = Faculty(
            id=test_faculty_id,
            name="Om Professor",
            email=test_faculty_email,
            rank="Assistant Professor",
            expertise=[],
            max_weekly_load_hours=12.0,
            min_courses=1,
            max_courses=3,
            max_preparations=2,
            unavailable_slots=[],
            leave_terms=[],
            preferred_course_ids=[],
        )
        asyncio.run(faculty_repo.upsert(test_fac))

        # Confirm user record does NOT exist yet in users.json
        user_before = asyncio.run(user_repo.get(f"u-{test_faculty_id}"))
        assert user_before is None

        # 2. Request OTP via public auth endpoint
        resp = client.post(
            "/auth/request-otp",
            json={"email": test_faculty_email},
        )
        assert resp.status_code == 200
        assert "one-time passcode" in resp.json()["message"]

        # 3. Verify OTP was generated and dev code is available
        code = otp_svc.get_dev_otp(test_faculty_email)
        assert code is not None
        assert len(code) == 6

        # 4. Verify user record was auto-provisioned in users.json
        user_after = asyncio.run(user_repo.get(f"u-{test_faculty_id}"))
        assert user_after is not None
        assert user_after.email == test_faculty_email
        assert user_after.role == UserRole.FACULTY
        assert user_after.faculty_id == test_faculty_id

        # 5. Verify user can successfully verify OTP and obtain JWT tokens
        resp_verify = client.post(
            "/auth/verify-otp",
            json={"email": test_faculty_email, "otp": code},
        )
        assert resp_verify.status_code == 200
        token_data = resp_verify.json()
        assert "access_token" in token_data
        assert token_data["user"]["faculty_id"] == test_faculty_id
        assert token_data["user"]["role"] == "faculty"

    finally:
        asyncio.run(faculty_repo.delete(test_faculty_id))
        asyncio.run(user_repo.delete(f"u-{test_faculty_id}"))


def test_sync_faculty_user_accounts_startup_helper():
    """Verify sync_faculty_user_accounts scans faculty.json and creates missing User entries."""
    import asyncio

    from app.repositories import get_faculty_repository, get_user_repository
    from app.schemas.faculty import Faculty
    from app.services.faculty_service import sync_faculty_user_accounts

    faculty_repo = get_faculty_repository()
    user_repo = get_user_repository()

    f_id = "f-sync-test-888"
    f_email = "sync.tester@university.edu"

    asyncio.run(faculty_repo.delete(f_id))
    asyncio.run(user_repo.delete(f"u-{f_id}"))

    try:
        fac = Faculty(
            id=f_id,
            name="Sync Tester",
            email=f_email,
            rank="Lecturer",
            expertise=[],
            max_weekly_load_hours=9.0,
            min_courses=1,
            max_courses=2,
            max_preparations=1,
            unavailable_slots=[],
            leave_terms=[],
            preferred_course_ids=[],
        )
        asyncio.run(faculty_repo.upsert(fac))

        # Run sync function
        synced = asyncio.run(
            sync_faculty_user_accounts(faculty_repo=faculty_repo, user_repo=user_repo)
        )
        assert synced >= 1

        # Confirm user was created
        u = asyncio.run(user_repo.get(f"u-{f_id}"))
        assert u is not None
        assert u.email == f_email
        assert u.faculty_id == f_id
    finally:
        asyncio.run(faculty_repo.delete(f_id))
        asyncio.run(user_repo.delete(f"u-{f_id}"))
