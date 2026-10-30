from fastapi import APIRouter

from app.api.v1 import constraints, health

api_router = APIRouter()

# Include subrouters
api_router.include_router(health.router)
api_router.include_router(constraints.router)
