"""Tests to ensure >=80% test coverage on security, auth, and access guards."""

import asyncio
import pytest
from fastapi import HTTPException
from app.core.security import (
    decode_access_token,
    create_access_token,
    get_current_user,
    require_faculty,
    require_authenticated,
    verify_faculty_access,
    FacultyAccessGuard,
    UnauthorizedError,
    ForbiddenError,
)
from app.schemas.user import User
from app.schemas.common import UserRole
from starlette.requests import Request


def test_security_decode_invalid_token():
    with pytest.raises(UnauthorizedError):
        decode_access_token("not-a-valid-token")


def test_security_get_current_user_invalid_role_header():
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_current_user(x_user_role="invalid_role"))
    assert exc_info.value.status_code == 400


def test_security_get_current_user_token_missing_sub():
    from jose import jwt
    from app.core.config import settings

    token = jwt.encode({"role": "faculty"}, settings.JWT_SECRET, algorithm="HS256")
    with pytest.raises(UnauthorizedError, match="missing subject"):
        asyncio.run(get_current_user(authorization=f"Bearer {token}"))


def test_security_get_current_user_token_invalid_type():
    from jose import jwt
    from app.core.config import settings

    token = jwt.encode(
        {"sub": "u-123", "role": "faculty", "type": "refresh"},
        settings.JWT_SECRET,
        algorithm="HS256",
    )
    with pytest.raises(UnauthorizedError, match="Invalid token type"):
        asyncio.run(get_current_user(authorization=f"Bearer {token}"))


def test_security_get_current_user_token_payload_fallback():
    token = create_access_token({"sub": "u-custom", "role": "faculty", "email": "custom@univ.edu", "faculty_id": "fac-1"})
    user = asyncio.run(get_current_user(authorization=f"Bearer {token}", user_repo=None))
    assert user.id == "u-custom"
    assert user.faculty_id == "fac-1"
    assert user.role == UserRole.FACULTY


def test_security_require_faculty():
    faculty_user = User(id="f1", email="f1@univ.edu", role=UserRole.FACULTY, faculty_id="fac-1")
    assert require_faculty(faculty_user) == faculty_user

    admin_user = User(id="a1", email="a1@univ.edu", role=UserRole.ADMIN)
    with pytest.raises(ForbiddenError):
        require_faculty(admin_user)


def test_security_require_authenticated():
    user = User(id="u1", email="u1@univ.edu", role=UserRole.FACULTY)
    assert require_authenticated(user) == user


def test_verify_faculty_access_edges():
    weird_user = User(id="u2", email="u2@univ.edu", role=UserRole.FACULTY, faculty_id="fac-2")
    # Admin allowed
    admin = User(id="a1", email="a1@univ.edu", role=UserRole.ADMIN)
    verify_faculty_access("fac-99", admin)

    # Own faculty allowed
    verify_faculty_access("fac-2", weird_user)

    # Different faculty raises ForbiddenError
    with pytest.raises(ForbiddenError):
        verify_faculty_access("fac-3", weird_user)


def test_faculty_access_guard():
    guard = FacultyAccessGuard(faculty_id_param="faculty_id")
    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/faculty/fac-1/profile",
        "path_params": {"faculty_id": "fac-1"},
    }
    req = Request(scope)
    user = User(id="u1", email="u1@univ.edu", role=UserRole.FACULTY, faculty_id="fac-1")
    res = guard(req, user)
    assert res == user
