"""In-memory OTP generation, salted-hash persistence, rate-limiting, and dispatch."""

from __future__ import annotations

import hashlib
import logging
import secrets
import smtplib
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from email.message import EmailMessage

from fastapi import status

from app.core.config import settings
from app.core.errors import RateLimitError, UnauthorizedError

logger = logging.getLogger("app.services.otp")


@dataclass
class OTPRecord:
    email: str
    salted_hash: str
    salt: str
    expires_at: datetime
    attempts: int = 0
    max_attempts: int = 5


class OTPService:
    """Short-TTL in-memory OTP lifecycle manager with rate limiting and salted hashing."""

    def __init__(self) -> None:
        # In-memory store: email -> OTPRecord (never written to disk or Gist)
        self._store: dict[str, OTPRecord] = {}
        # Sliding rate limit windows (last 10 minutes)
        self._rate_limits_email: dict[str, list[datetime]] = {}
        self._rate_limits_ip: dict[str, list[datetime]] = {}
        # Testing aid when OTP_DEV_MODE is active
        self._dev_last_otp: dict[str, str] = {}

    def _normalize_email(self, email: str) -> str:
        return email.strip().lower()

    def check_and_record_rate_limit(self, email: str, client_ip: str) -> None:
        """Enforce strict rate limits: 3 OTP requests per email and per IP per 10 minutes."""
        now = datetime.now(UTC)
        window = timedelta(minutes=10)
        max_requests = 3

        norm_email = self._normalize_email(email)
        norm_ip = client_ip.strip()

        # Evict timestamps older than 10 minutes for this email
        email_history = [
            ts
            for ts in self._rate_limits_email.get(norm_email, [])
            if now - ts < window
        ]
        self._rate_limits_email[norm_email] = email_history

        # Evict timestamps older than 10 minutes for this IP
        ip_history = [
            ts for ts in self._rate_limits_ip.get(norm_ip, []) if now - ts < window
        ]
        self._rate_limits_ip[norm_ip] = ip_history

        if len(email_history) >= max_requests:
            logger.warning(
                f"Rate limit exceeded: 3 OTP requests per 10m reached for email {norm_email}"
            )
            raise RateLimitError(
                message="Rate limit exceeded: Maximum 3 OTP requests per 10 minutes for this email.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        if len(ip_history) >= max_requests:
            logger.warning(
                f"Rate limit exceeded: 3 OTP requests per 10m reached for IP {norm_ip}"
            )
            raise RateLimitError(
                message="Rate limit exceeded: Maximum 3 OTP requests per 10 minutes for this IP address.",
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        # Record this attempt
        self._rate_limits_email[norm_email].append(now)
        self._rate_limits_ip[norm_ip].append(now)

    def generate_and_store_otp(self, email: str) -> str:
        """Generate a cryptographically secure 6-digit OTP, store salted hash, and dispatch."""
        norm_email = self._normalize_email(email)

        # 6-digit numeric OTP using Python secrets module
        otp_int = secrets.randbelow(1_000_000)
        otp = f"{otp_int:06d}"

        # 16-byte random salt and SHA-256 salted hash
        salt = secrets.token_hex(16)
        salted_hash = hashlib.sha256(f"{salt}:{otp}".encode()).hexdigest()

        # 5-minute lifespan
        expires_at = datetime.now(UTC) + timedelta(
            minutes=settings.OTP_CODE_TTL_MINUTES
        )

        # Store ONLY the salted hash and attempt metadata in memory
        self._store[norm_email] = OTPRecord(
            email=norm_email,
            salted_hash=salted_hash,
            salt=salt,
            expires_at=expires_at,
            attempts=0,
            max_attempts=5,
        )

        # Dispatch
        if settings.OTP_DEV_MODE:
            self._dev_last_otp[norm_email] = otp
            logger.info(
                f"[OTP_DEV_MODE] Passcode generated for {norm_email}: {otp} (expires in {settings.OTP_CODE_TTL_MINUTES}m)"
            )
            print(f"[OTP_DEV_MODE] {norm_email} -> {otp}", flush=True)
        else:
            self._send_smtp_email(norm_email, otp)

        return otp

    def verify_otp(self, email: str, otp: str) -> bool:
        """Validate an OTP code against stored salted hash with max 5 attempts, constant-time compare, and single use."""
        norm_email = self._normalize_email(email)
        now = datetime.now(UTC)

        record = self._store.get(norm_email)
        if record is None:
            raise UnauthorizedError("Invalid or expired OTP code")

        if now > record.expires_at:
            self._store.pop(norm_email, None)
            self._dev_last_otp.pop(norm_email, None)
            raise UnauthorizedError("OTP code has expired. Please request a new one.")

        record.attempts += 1

        if record.attempts > record.max_attempts:
            self._store.pop(norm_email, None)
            self._dev_last_otp.pop(norm_email, None)
            raise UnauthorizedError(
                "Maximum verification attempts exceeded. Account locked out for this code. Please request a new OTP."
            )

        # Constant-time comparison
        candidate_hash = hashlib.sha256(
            f"{record.salt}:{otp.strip()}".encode()
        ).hexdigest()
        is_match = secrets.compare_digest(candidate_hash, record.salted_hash)

        if not is_match:
            if record.attempts >= record.max_attempts:
                self._store.pop(norm_email, None)
                self._dev_last_otp.pop(norm_email, None)
                raise UnauthorizedError(
                    "Maximum verification attempts exceeded. Account locked out for this code. Please request a new OTP."
                )
            remaining = record.max_attempts - record.attempts
            raise UnauthorizedError(
                f"Invalid OTP code. {remaining} attempt(s) remaining."
            )

        # Successful verification -> Single-use invalidation
        self._store.pop(norm_email, None)
        self._dev_last_otp.pop(norm_email, None)
        return True

    def get_dev_otp(self, email: str) -> str | None:
        """Retrieve last generated OTP code for test assertions when in dev mode."""
        return self._dev_last_otp.get(self._normalize_email(email))

    def clear_all(self) -> None:
        """Reset all in-memory store and rate-limit state (useful for test isolation)."""
        self._store.clear()
        self._rate_limits_email.clear()
        self._rate_limits_ip.clear()
        self._dev_last_otp.clear()

    def _send_smtp_email(self, email: str, otp: str) -> None:
        """Dispatch OTP email via configured SMTP server."""
        msg = EmailMessage()
        msg["Subject"] = "Faculty Workload Balancing - One-Time Passcode"
        msg["From"] = f"no-reply@{settings.SMTP_HOST}"
        msg["To"] = email
        msg.set_content(
            f"Hello,\n\n"
            f"Your one-time passcode to sign in to the University Faculty Workload System is:\n\n"
            f"    {otp}\n\n"
            f"This code will expire in {settings.OTP_CODE_TTL_MINUTES} minutes.\n"
            f"If you did not request this verification code, please ignore this email.\n"
        )

        try:
            with smtplib.SMTP(
                settings.SMTP_HOST, settings.SMTP_PORT, timeout=10
            ) as server:
                if settings.SMTP_USER and settings.SMTP_PASS:
                    server.login(settings.SMTP_USER, settings.SMTP_PASS)
                server.send_message(msg)
        except (smtplib.SMTPException, OSError) as exc:
            logger.error(f"Failed to dispatch OTP email to {email} via SMTP: {exc}")


_OTP_SERVICE_INSTANCE: OTPService | None = None


def get_otp_service() -> OTPService:
    """Singleton provider for in-memory OTP lifecycle manager."""
    global _OTP_SERVICE_INSTANCE
    if _OTP_SERVICE_INSTANCE is None:
        _OTP_SERVICE_INSTANCE = OTPService()
    return _OTP_SERVICE_INSTANCE
