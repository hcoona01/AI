"""Authentication router handling passwordless Email OTP verification, refresh, and logout."""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, Request, Response, status

from app.core.config import settings
from app.core.errors import UnauthorizedError
from app.repositories import get_user_repository
from app.repositories.base import Repository
from app.schemas.auth import (
    MessageResponse,
    OTPRequest,
    OTPResponse,
    OTPVerifyRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.schemas.user import User
from app.services.auth_service import AuthService
from app.services.otp_service import OTPService, get_otp_service

logger = logging.getLogger("app.api.auth")

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_client_ip(request: Request) -> str:
    """Extract client IP honoring X-Forwarded-For headers when behind reverse proxies."""
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "127.0.0.1"


def get_auth_service(
    user_repo: Annotated[Repository[User], Depends(get_user_repository)],
    otp_service: Annotated[OTPService, Depends(get_otp_service)],
) -> AuthService:
    return AuthService(user_repo=user_repo, otp_service=otp_service)


@router.post(
    "/request-otp",
    response_model=OTPResponse,
    status_code=status.HTTP_200_OK,
)
async def request_otp(
    payload: OTPRequest,
    request: Request,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> OTPResponse:
    """Request a 6-digit one-time passcode. Always returns a generic confirmation message."""
    client_ip = get_client_ip(request)
    result = await auth_service.request_otp(email=payload.email, client_ip=client_ip)
    return OTPResponse(message=result["message"], status=result["status"])


@router.get("/dev-otp")
async def get_dev_otp(
    email: str,
    otp_service: Annotated[OTPService, Depends(get_otp_service)],
) -> dict[str, str | None]:
    """Retrieve in-memory dev OTP for automated testing in non-production environments."""
    if not settings.OTP_DEV_MODE:
        return {"email": email, "otp": None}
    return {"email": email, "otp": otp_service.get_dev_otp(email)}


@router.post(
    "/verify-otp",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def verify_otp(
    payload: OTPVerifyRequest,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
) -> TokenResponse:
    """Verify 6-digit OTP code. On success, issues 15-min JWT access token and httpOnly refresh cookie."""
    user, access_token, refresh_token = await auth_service.verify_otp(
        email=payload.email, otp=payload.otp
    )

    # Set refresh token in httpOnly, SameSite cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        secure=(settings.ENVIRONMENT in ("production", "staging")),
        path="/",
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user.model_dump(),
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_token(
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    body: RefreshTokenRequest | None = None,
    refresh_token_cookie: Annotated[str | None, Cookie(alias="refresh_token")] = None,
) -> TokenResponse:
    """Renew session using refresh token from httpOnly cookie (or optional fallback body)."""
    token_str = refresh_token_cookie or (body.refresh_token if body else None)
    if not token_str:
        raise UnauthorizedError("Missing refresh token cookie")

    user, new_access_token, new_refresh_token = await auth_service.refresh_session(
        refresh_token=token_str
    )

    # Rotate refresh token cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        samesite="lax",
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 3600,
        secure=(settings.ENVIRONMENT in ("production", "staging")),
        path="/",
    )

    return TokenResponse(
        access_token=new_access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=user.model_dump(),
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    status_code=status.HTTP_200_OK,
)
async def logout(response: Response) -> MessageResponse:
    """Terminate session by clearing the httpOnly refresh token cookie."""
    response.delete_cookie(key="refresh_token", path="/")
    return MessageResponse(message="Successfully logged out")
