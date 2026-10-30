"""Resource management service for campus lecture halls and specialized labs."""

from __future__ import annotations

import logging

from app.core.errors import ConflictError, NotFoundError
from app.repositories import get_resource_repository
from app.repositories.base import Repository
from app.schemas.resource import Resource
from app.services.audit_service import AuditService

logger = logging.getLogger("app.services.resource")


class ResourceService:
    """Service managing campus physical lecture rooms and computing laboratories."""

    def __init__(
        self,
        repository: Repository[Resource] | None = None,
        audit_service: AuditService | None = None,
    ) -> None:
        self.repository = repository or get_resource_repository()
        self.audit_service = audit_service or AuditService()

    async def get_all(self) -> list[Resource]:
        """Fetch all physical campus facilities."""
        return await self.repository.get_all()

    async def get_by_id(self, resource_id: str) -> Resource:
        """Fetch a specific facility by ID."""
        resource = await self.repository.get(resource_id)
        if not resource:
            raise NotFoundError(f"Resource facility '{resource_id}' not found")
        return resource

    async def create(self, resource: Resource, actor_id: str) -> Resource:
        """Register a new campus facility (Admin only) and record audit log."""
        existing = await self.repository.get(resource.id)
        if existing:
            raise ConflictError(f"Resource with ID '{resource.id}' already exists")

        created = await self.repository.upsert(resource)
        await self.audit_service.log_event(
            actor_id=actor_id,
            action="RESOURCE_CREATED",
            entity="resource",
            payload=resource.model_dump(mode="json"),
        )
        return created

    async def update(
        self, resource_id: str, resource: Resource, actor_id: str
    ) -> Resource:
        """Update facility configuration (Admin only) and record audit log."""
        existing = await self.repository.get(resource_id)
        if not existing:
            raise NotFoundError(f"Cannot update non-existent resource '{resource_id}'")

        resource.id = resource_id
        updated = await self.repository.upsert(resource)
        await self.audit_service.log_event(
            actor_id=actor_id,
            action="RESOURCE_UPDATED",
            entity="resource",
            payload={"id": resource_id, "updated": resource.model_dump(mode="json")},
        )
        return updated

    async def delete(self, resource_id: str, actor_id: str) -> bool:
        """Remove a facility (Admin only) and record audit log."""
        existing = await self.repository.get(resource_id)
        if not existing:
            raise NotFoundError(f"Cannot delete non-existent resource '{resource_id}'")

        success = await self.repository.delete(resource_id)
        if success:
            await self.audit_service.log_event(
                actor_id=actor_id,
                action="RESOURCE_DELETED",
                entity="resource",
                payload={"id": resource_id, "type": existing.type.value},
            )
        return success
