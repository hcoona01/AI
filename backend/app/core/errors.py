import logging
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.errors")


class AppException(Exception):
    """Base exception for application errors."""

    def __init__(
        self,
        message: str,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        rule_id: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.rule_id = rule_id
        self.details = details or {}


class NotFoundError(AppException):
    def __init__(self, message: str = "Resource not found", rule_id: str | None = None):
        super().__init__(
            message=message, status_code=status.HTTP_404_NOT_FOUND, rule_id=rule_id
        )


class ConflictError(AppException):
    def __init__(
        self, message: str = "Constraint conflict occurred", rule_id: str | None = None
    ):
        super().__init__(
            message=message, status_code=status.HTTP_409_CONFLICT, rule_id=rule_id
        )


class UnauthorizedError(AppException):
    def __init__(self, message: str = "Unauthorized access"):
        super().__init__(message=message, status_code=status.HTTP_401_UNAUTHORIZED)


class ForbiddenError(AppException):
    def __init__(self, message: str = "Forbidden access"):
        super().__init__(message=message, status_code=status.HTTP_403_FORBIDDEN)


def register_error_handlers(app: FastAPI) -> None:
    """Register global error and exception handlers on the FastAPI app."""

    @app.exception_handler(AppException)
    async def app_exception_handler(
        request: Request, exc: AppException
    ) -> JSONResponse:
        logger.warning(
            f"AppException: {exc.message} | Path: {request.url.path} | Rule: {exc.rule_id}"
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": exc.message,
                "rule_id": exc.rule_id,
                "details": exc.details,
                "path": request.url.path,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        logger.warning(f"Validation error: {exc.errors()} | Path: {request.url.path}")
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": True,
                "message": "Validation failed",
                "details": exc.errors(),
                "path": request.url.path,
            },
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        logger.exception(f"Unhandled exception at {request.url.path}: {exc!s}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": True,
                "message": "Internal server error",
                "path": request.url.path,
            },
        )
