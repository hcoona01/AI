"""API v1 router aggregating all modular domain route endpoints."""

from fastapi import APIRouter

from app.api.v1 import (
    audit,
    constraints,
    courses,
    faculty,
    health,
    resources,
    scenarios,
    sections,
    timeslots,
)

api_router = APIRouter()

# Register domain subrouters
api_router.include_router(health.router)
api_router.include_router(constraints.router)
api_router.include_router(faculty.router)
api_router.include_router(courses.router)
api_router.include_router(sections.router)
api_router.include_router(resources.router)
api_router.include_router(timeslots.router)
api_router.include_router(scenarios.router)
api_router.include_router(audit.router)
