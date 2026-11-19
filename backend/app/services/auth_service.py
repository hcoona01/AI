"""Authentication service handling OTP verification, session refresh, and token issuance."""

from __future__ import annotations

import logging
from typing import Any

from app.core.errors import UnauthorizedError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
)
from app.repositories import get_faculty_repository, get_user_repository
from app.repositories.base import Repository
from app.schemas.common import UserRole
from app.schemas.faculty import Faculty
from app.schemas.user import User
from app.services.otp_service import OTPService, get_otp_service

logger = logging.getLogger("app.services.auth")

_FACULTY_USER_ID_PREFIX = "u-"


class AuthService:
    """Service layer coordinating passwordless authentication and token sessions."""

    def __init__(
        self,
        user_repo: Repository[User] | None = None,
        faculty_repo: Repository[Faculty] | None = None,
        otp_service: OTPService | None = None,
    ) -> None:
        self.user_repo = user_repo or get_user_repository()
        self.faculty_repo = faculty_repo or get_faculty_repository()
        self.otp_service = otp_service or get_otp_service()

    async def get_user_by_email(self, email: str) -> User | None:
        """Query user collection case-insensitively by email address.

        If a matching user is not found in users.json, check faculty.json and
        auto-provision / self-heal the missing user record so registered faculty
        members can always authenticate without manual intervention.
        """
        norm_email = email.strip().lower()
        all_users = await self.user_repo.get_all()
        for u in all_users:
            if u.email.strip().lower() == norm_email:
                return u

        # Fallback & self-heal: Check if this email belongs to any registered Faculty
        all_faculty = await self.faculty_repo.get_all()
        for f in all_faculty:
            if f.email.strip().lower() == norm_email:
                user_id = f"{_FACULTY_USER_ID_PREFIX}{f.id}"
                existing_user = await self.user_repo.get(user_id)
                if existing_user:
                    existing_user.email = f.email
                    existing_user.faculty_id = f.id
                    existing_user.role = UserRole.FACULTY
                    await self.user_repo.upsert(existing_user)
                    logger.info(
                        f"Synchronized existing user '{user_id}' with faculty email '{f.email}' during auth lookup"
                    )
                    return existing_user

                new_user = User(
                    id=user_id,
                    email=f.email,
                    role=UserRole.FACULTY,
                    faculty_id=f.id,
                )
                await self.user_repo.upsert(new_user)
                logger.info(
                    f"Auto-provisioned missing user record '{user_id}' for registered faculty '{f.id}' ({f.email}) during auth lookup"
                )
                return new_user

        return None

    async def request_otp(self, email: str, client_ip: str) -> dict[str, Any]:
        """Process OTP request with rate limiting and generic response to prevent user enumeration."""
        # 1. Rate limiting checked regardless of user existence (up to 8 per email/IP per 10m)
        self.otp_service.check_and_record_rate_limit(email=email, client_ip=client_ip)

        # 2. Check if user exists
        user = await self.get_user_by_email(email)
        dev_code: str | None = None
        if user is not None:
            generated_otp = self.otp_service.generate_and_store_otp(email)
            from app.core.config import settings

            if settings.OTP_DEV_MODE:
                dev_code = generated_otp
        else:
            logger.info(
                f"OTP requested for non-existent email '{email}'. Silently omitted code generation."
            )

        # 3. Always return generic message, attaching dev_code if in dev mode
        resp: dict[str, Any] = {
            "message": "If the provided email is registered, a one-time passcode has been sent.",
            "status": "sent",
        }
        if dev_code is not None:
            resp["dev_code"] = dev_code
        return resp

    async def verify_otp(self, email: str, otp: str) -> tuple[User, str, str]:
        """Verify OTP with attempt limits, constant-time compare, and issue access & refresh tokens."""
        # 1. Validate OTP against in-memory store
        self.otp_service.verify_otp(email=email, otp=otp)

        # 2. Retrieve user
        user = await self.get_user_by_email(email)
        if user is None:
            raise UnauthorizedError("User profile not found")

        # 3. Create 15-minute access token and refresh token
        token_data: dict[str, Any] = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "faculty_id": user.faculty_id,
        }
        access_token = create_access_token(data=token_data)
        refresh_token = create_refresh_token(data={"sub": user.id})

        logger.info(f"User {user.id} ({user.email}) successfully authenticated via OTP")
        return user, access_token, refresh_token

    async def refresh_session(self, refresh_token: str) -> tuple[User, str, str]:
        """Validate refresh token and issue a fresh access token pair."""
        payload = decode_access_token(refresh_token)

        token_type = payload.get("type")
        if token_type != "refresh":
            raise UnauthorizedError("Invalid token type: Expected refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise UnauthorizedError(
                "Invalid refresh token payload: Missing subject claim"
            )

        user = await self.user_repo.get(user_id)
        if user is None:
            raise UnauthorizedError("Authenticated user record no longer exists")

        token_data: dict[str, Any] = {
            "sub": user.id,
            "email": user.email,
            "role": user.role.value,
            "faculty_id": user.faculty_id,
        }
        new_access_token = create_access_token(data=token_data)
        new_refresh_token = create_refresh_token(data={"sub": user.id})

        return user, new_access_token, new_refresh_token
