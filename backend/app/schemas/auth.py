from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OTPRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr = Field(..., description="Institutional email address")


class OTPVerifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    email: EmailStr = Field(..., description="Institutional email address")
    otp: str = Field(
        ...,
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        description="6-digit verification code",
    )


class OTPResponse(BaseModel):
    message: str = Field(
        default="If the provided email is registered, a one-time passcode has been sent."
    )
    status: str = Field(default="sent")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="Signed JWT Bearer access token")
    token_type: str = Field(default="bearer", description="Token type specification")
    expires_in: int = Field(
        default=900, description="Validity lifespan in seconds (15 minutes)"
    )
    user: dict[str, Any] | None = Field(
        default=None, description="Authenticated user profile summary"
    )
    refresh_token: str | None = Field(
        default=None, description="Rotated or issued refresh token payload"
    )


class RefreshTokenRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    refresh_token: str | None = Field(
        default=None, description="Optional fallback refresh token payload"
    )


class MessageResponse(BaseModel):
    message: str = Field(..., description="Informational response status message")

