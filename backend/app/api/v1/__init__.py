"""API v1 router aggregating all modular domain route endpoints."""

from fastapi import APIRouter

from app.api.v1 import (
    assign,
    audit,
    auth,
    constraints,
    courses,
    faculty,
    forecast,
    health,
    me,
    resources,
    scenarios,
    sections,
    timeslots,
)

api_router = APIRouter()

# Register domain subrouters
api_router.include_router(auth.router)
api_router.include_router(me.router)
api_router.include_router(health.router)
api_router.include_router(constraints.router)
api_router.include_router(faculty.router)
api_router.include_router(courses.router)
api_router.include_router(sections.router)
api_router.include_router(resources.router)
api_router.include_router(timeslots.router)
api_router.include_router(scenarios.router)
api_router.include_router(audit.router)
api_router.include_router(forecast.router)
api_router.include_router(assign.router)
