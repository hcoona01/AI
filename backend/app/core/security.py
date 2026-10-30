"""Security, JWT token issuance/verification, and RBAC authorization dependencies."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import Depends, Header, HTTPException, Request, status
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
    """Generate a signed HS256 JWT access token (15-minute default validity)."""
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire, "iat": now, "type": "access"})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=ALGORITHM)


def create_refresh_token(
    data: dict[str, Any],
    expires_delta: timedelta | None = None,
) -> str:
    """Generate a signed HS256 JWT refresh token (7-day default validity)."""
    to_encode = data.copy()
    now = datetime.now(UTC)
    expire = now + (expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    to_encode.update({"exp": expire, "iat": now, "type": "refresh"})
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

            # Reject refresh tokens used as bearer access tokens
            token_type = payload.get("type")
            if token_type and token_type != "access":
                raise UnauthorizedError("Invalid token type for access authentication")

            # Lookup in user repository if available
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


def require_faculty(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """RBAC dependency ensuring the current user possesses Faculty privileges."""
    if current_user.role != UserRole.FACULTY:
        logger.warning(
            f"Access denied: User {current_user.id} ({current_user.role}) attempted faculty action"
        )
        raise ForbiddenError("Faculty access required for this operation")
    return current_user


def require_authenticated(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Dependency verifying user is authenticated (either admin or faculty)."""
    return current_user


def verify_faculty_access(target_faculty_id: str, current_user: User) -> None:
    """Ensure faculty users can only access data belonging to their own faculty_id.

    Admins are permitted to access any faculty record.
    Faculty members are restricted strictly to their assigned faculty_id.
    """
    if current_user.role == UserRole.ADMIN:
        return
    if current_user.role == UserRole.FACULTY:
        if not current_user.faculty_id or current_user.faculty_id != target_faculty_id:
            logger.warning(
                f"Access denied: Faculty {current_user.id} (linked to {current_user.faculty_id}) "
                f"attempted to access data for faculty_id '{target_faculty_id}'"
            )
            raise ForbiddenError(
                "Faculty members are restricted to accessing their own data only"
            )
        return
    raise ForbiddenError("Access forbidden: Insufficient permissions")


class FacultyAccessGuard:
    """Dependency helper verifying that the authenticated user can access the target faculty_id."""

    def __init__(self, faculty_id_param: str = "faculty_id") -> None:
        self.faculty_id_param = faculty_id_param

    def __call__(
        self,
        request: Request,
        current_user: Annotated[User, Depends(get_current_user)],
    ) -> User:
        target_id = request.path_params.get(self.faculty_id_param)
        if target_id:
            verify_faculty_access(target_id, current_user)
        return current_user
