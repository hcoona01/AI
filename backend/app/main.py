import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.errors import register_error_handlers
from app.core.logging import setup_logging

logger = logging.getLogger("app.main")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifecycle events: startup and shutdown."""
    setup_logging(log_level=settings.LOG_LEVEL, environment=settings.ENVIRONMENT)
    logger.info(
        f"Starting {settings.PROJECT_NAME} v{settings.VERSION} "
        f"[env: {settings.ENVIRONMENT}, store: {settings.STORE_BACKEND}, forecast: {settings.FORECAST_MODE}]"
    )
    yield
    logger.info(f"Shutting down {settings.PROJECT_NAME}")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan,
)

# Configure CORS
origins = (
    [str(origin).strip() for origin in settings.ALLOWED_ORIGINS]
    if isinstance(settings.ALLOWED_ORIGINS, list)
    else [settings.ALLOWED_ORIGINS]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register global error handlers
register_error_handlers(app)

# Include API v1 router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/", tags=["Root"])
async def root():
    return {
        "message": f"Welcome to {settings.PROJECT_NAME}",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
        "health": f"{settings.API_V1_STR}/health",
    }
