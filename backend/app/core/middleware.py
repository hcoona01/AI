"""Production security headers and lightweight rate-limiting middlewares."""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from typing import Callable

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings

logger = logging.getLogger("app.core.middleware")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Enforce strict HTTP security headers across all API responses."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response: Response = await call_next(request)

        # Defense against MIME sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # Defense against clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Defense against legacy XSS
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Strict Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Restrict permissions
        response.headers["Permissions-Policy"] = "accelerometer=(), camera=(), geolocation=(), gyroscope=(), magnetometer=(), microphone=(), payment=(), usb=()"

        # HSTS in production or staging environments
        if settings.ENVIRONMENT in ("production", "staging"):
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Lightweight in-memory sliding-window rate limiter per client IP.

    Ensures the CPU and single-threaded runtime are protected against traffic spikes.
    """

    def __init__(self, app, requests_per_minute: int = 180) -> None:
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_seconds = 60.0
        self._access_log: dict[str, list[float]] = defaultdict(list)

    def _get_client_ip(self, request: Request) -> str:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            return forwarded.split(",")[0].strip()
        if request.client:
            return request.client.host
        return "127.0.0.1"

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Exempt health check and documentation endpoints from rate limits
        path = request.url.path
        if (
            path in ("/health", "/api/v1/health", "/docs", "/redoc", "/api/v1/docs", "/api/v1/redoc")
            or path.startswith("/api/v1/openapi.json")
            or settings.ENVIRONMENT == "test"
            or self.requests_per_minute <= 0
        ):
            return await call_next(request)

        client_ip = self._get_client_ip(request)
        now = time.time()
        window_start = now - self.window_seconds

        # Prune older timestamps for this IP
        timestamps = [ts for ts in self._access_log[client_ip] if ts > window_start]
        self._access_log[client_ip] = timestamps

        if len(timestamps) >= self.requests_per_minute:
            logger.warning(
                f"Global rate limit exceeded for IP {client_ip}: "
                f"{len(timestamps)} requests in last {self.window_seconds}s"
            )
            retry_after = int(self.window_seconds - (now - timestamps[0])) + 1
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "detail": "Too many requests. Please slow down and try again.",
                    "code": "RATE_LIMIT_EXCEEDED",
                    "retry_after_seconds": max(1, retry_after),
                },
                headers={
                    "Retry-After": str(max(1, retry_after)),
                    "X-RateLimit-Limit": str(self.requests_per_minute),
                    "X-RateLimit-Remaining": "0",
                },
            )

        self._access_log[client_ip].append(now)
        response: Response = await call_next(request)

        remaining = max(0, self.requests_per_minute - len(self._access_log[client_ip]))
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        return response

