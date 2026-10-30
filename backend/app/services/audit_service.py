"""Audit logging service for tracking system mutations and administrative events."""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime
from typing import Any

from app.core.errors import NotFoundError
from app.repositories import get_audit_repository
from app.repositories.base import Repository
from app.schemas.audit import AuditLogEntry

logger = logging.getLogger("app.services.audit")


class AuditService:
    """Service orchestrating immutable audit trail recording."""

    def __init__(self, repository: Repository[AuditLogEntry] | None = None) -> None:
        self.repository = repository or get_audit_repository()

    async def log_event(
        self,
        actor_id: str,
        action: str,
        entity: str,
        payload: dict[str, Any] | None = None,
    ) -> AuditLogEntry:
        """Create and persist a new immutable audit log event."""
        entry = AuditLogEntry(
            id=f"audit-{uuid.uuid4().hex[:12]}",
            actor_id=actor_id,
            action=action.upper(),
            entity=entity.lower(),
            payload=payload or {},
            timestamp=datetime.now(UTC),
        )
        await self.repository.upsert(entry)
        logger.info(
            f"Audit log recorded: [{entry.action}] {entry.entity} by {entry.actor_id}"
        )
        return entry

    async def get_logs(
        self,
        entity: str | None = None,
        actor_id: str | None = None,
        action: str | None = None,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """Fetch audit history sorted chronologically descending."""
        logs = await self.repository.get_all(force_refresh=True)

        if entity:
            target_entity = entity.lower()
            logs = [entry for entry in logs if entry.entity.lower() == target_entity]
        if actor_id:
            logs = [entry for entry in logs if entry.actor_id == actor_id]
        if action:
            target_action = action.upper()
            logs = [entry for entry in logs if entry.action.upper() == target_action]

        # Sort newest first
        logs.sort(key=lambda x: x.timestamp, reverse=True)
        return logs[:limit]

    async def get_log_by_id(self, log_id: str) -> AuditLogEntry:
        """Retrieve a specific audit entry by its ID."""
        entry = await self.repository.get(log_id)
        if not entry:
            raise NotFoundError(f"Audit entry '{log_id}' not found")
        return entry
