"""Security, JWT token issuance/verification, and RBAC authorization dependencies."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt

from app.core.config import settings
from app.core.errors import ForbiddenError, UnauthorizedError
from app.repositories import get_user_repository
from app.repositories.base import Repository
from app.schemas.common import UserRole
from app.schemas.user import User

logger = logging.getLogger("app.security")

ALGORITHM = "HS256"


def create_access_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Generate a signed HS256 JWT access token."""
    to_encode = data.copy()
    now = datetime.now(UTC)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire, "iat": now})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Validate signature and decode JWT payload."""
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[ALGORITHM])
        return payload
    except JWTError as exc:
        logger.warning(f"Failed JWT token verification: {exc}")
        raise UnauthorizedError("Invalid or expired authentication token") from exc


async def get_current_user(
    authorization: Annotated[str | None, Header(description="Bearer JWT token")] = None,
    x_user_id: Annotated[str | None, Header(description="Testing user ID")] = None,
    x_user_role: Annotated[
        str | None, Header(description="Testing role (admin|faculty)")
    ] = None,
    x_user_email: Annotated[
        str | None, Header(description="Testing institutional email")
    ] = None,
    x_faculty_id: Annotated[
        str | None, Header(description="Testing linked faculty ID")
    ] = None,
    user_repo: Annotated[Repository[User], Depends(get_user_repository)] = None,  # type: ignore[assignment]
) -> User:
    """Retrieve and authenticate the active user via JWT Bearer token or test headers."""
    # 1. Check direct test headers (facilitates testing & rapid dev)
    if x_user_role:
        try:
            role = UserRole(x_user_role.lower())
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid X-User-Role: {x_user_role}",
            ) from exc

        return User(
            id=x_user_id or f"u-{role.value}-test",
            email=x_user_email or f"{role.value}@university.edu",
            role=role,
            faculty_id=x_faculty_id if role == UserRole.FACULTY else None,
        )

    # 2. Check Bearer Authorization token
    if authorization:
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() == "bearer" and token:
            payload = decode_access_token(token)
            user_id = payload.get("sub")
            if not user_id:
                raise UnauthorizedError("JWT token missing subject ('sub') claim")

            # Attempt lookup in user repository if available
            if user_repo is not None:
                try:
                    found_user = await user_repo.get(user_id)
                    if found_user:
                        return found_user
                except (KeyError, ValueError, AttributeError, OSError) as exc:
                    logger.debug(f"User repository lookup error: {exc}")

            # Construct user from token payload claims
            role_str = payload.get("role", "faculty")
            return User(
                id=user_id,
                email=payload.get("email", f"{user_id}@university.edu"),
                role=UserRole(role_str),
                faculty_id=payload.get("faculty_id"),
            )

    # 3. Development Fallback: If OTP_DEV_MODE is True and no auth provided, default to admin
    if settings.OTP_DEV_MODE:
        return User(
            id="u-admin-default",
            email="admin@university.edu",
            role=UserRole.ADMIN,
            faculty_id=None,
        )

    raise UnauthorizedError("Missing authentication credentials")


def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """RBAC dependency ensuring the current user possesses Administrator privileges."""
    if current_user.role != UserRole.ADMIN:
        logger.warning(
            f"Access denied: User {current_user.id} ({current_user.role}) attempted admin action"
        )
        raise ForbiddenError("Administrator access required for this operation")
    return current_user


def require_authenticated(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency verifying user is authenticated (either admin or faculty)."""
    return current_user
