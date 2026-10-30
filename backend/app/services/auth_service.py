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
from app.repositories import get_user_repository
from app.repositories.base import Repository
from app.schemas.user import User
from app.services.otp_service import OTPService, get_otp_service

logger = logging.getLogger("app.services.auth")


class AuthService:
    """Service layer coordinating passwordless authentication and token sessions."""

    def __init__(
        self,
        user_repo: Repository[User] | None = None,
        otp_service: OTPService | None = None,
    ) -> None:
        self.user_repo = user_repo or get_user_repository()
        self.otp_service = otp_service or get_otp_service()

    async def get_user_by_email(self, email: str) -> User | None:
        """Query user collection case-insensitively by email address."""
        norm_email = email.strip().lower()
        all_users = await self.user_repo.get_all()
        for u in all_users:
            if u.email.strip().lower() == norm_email:
                return u
        return None

    async def request_otp(self, email: str, client_ip: str) -> dict[str, str]:
        """Process OTP request with rate limiting and generic response to prevent user enumeration."""
        # 1. Rate limiting checked regardless of user existence (3 per email/IP per 10m)
        self.otp_service.check_and_record_rate_limit(email=email, client_ip=client_ip)

        # 2. Check if user exists
        user = await self.get_user_by_email(email)
        if user is not None:
            self.otp_service.generate_and_store_otp(email)
        else:
            logger.info(
                f"OTP requested for non-existent email '{email}'. Silently omitted code generation."
            )

        # 3. Always return identical generic message
        return {
            "message": "If the provided email is registered, a one-time passcode has been sent.",
            "status": "sent",
        }

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
