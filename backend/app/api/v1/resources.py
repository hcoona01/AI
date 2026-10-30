"""Resources API router for managing campus rooms and laboratories."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.core.security import require_admin, require_authenticated
from app.schemas.resource import Resource
from app.schemas.user import User
from app.services.resource_service import ResourceService

router = APIRouter(prefix="/resources", tags=["Resources"])


def get_resource_service() -> ResourceService:
    return ResourceService()


@router.get("", response_model=list[Resource])
async def list_resources(
    _: Annotated[User, Depends(require_authenticated)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
) -> list[Resource]:
    """Retrieve all campus physical rooms and laboratories (shared reference data)."""
    return await service.get_all()


@router.get("/{resource_id}", response_model=Resource)
async def get_resource(
    resource_id: str,
    _: Annotated[User, Depends(require_authenticated)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
) -> Resource:
    """Retrieve facility parameters by ID."""
    return await service.get_by_id(resource_id=resource_id)


@router.post("", response_model=Resource, status_code=status.HTTP_201_CREATED)
async def create_resource(
    resource: Resource,
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
) -> Resource:
    """Admin-only: Register a new campus facility and record an audit log."""
    return await service.create(resource=resource, actor_id=admin_user.id)


@router.put("/{resource_id}", response_model=Resource)
async def update_resource(
    resource_id: str,
    resource: Resource,
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
) -> Resource:
    """Admin-only: Update facility parameters and record an audit log."""
    return await service.update(
        resource_id=resource_id, resource=resource, actor_id=admin_user.id
    )


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_resource(
    resource_id: str,
    admin_user: Annotated[User, Depends(require_admin)],
    service: Annotated[ResourceService, Depends(get_resource_service)],
) -> None:
    """Admin-only: Remove a campus facility and record an audit log."""
    await service.delete(resource_id=resource_id, actor_id=admin_user.id)
