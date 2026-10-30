"""Audit log API router for querying system mutation events."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from app.core.security import require_admin
from app.schemas.audit import AuditLogEntry
from app.schemas.user import User
from app.services.audit_service import AuditService

router = APIRouter(prefix="/audit", tags=["Audit"])


def get_audit_service() -> AuditService:
    return AuditService()


@router.get("", response_model=list[AuditLogEntry])
async def list_audit_logs(
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[AuditService, Depends(get_audit_service)],
    entity: Annotated[
        str | None, Query(description="Filter by target entity domain")
    ] = None,
    actor_id: Annotated[str | None, Query(description="Filter by actor ID")] = None,
    action: Annotated[str | None, Query(description="Filter by action code")] = None,
    limit: Annotated[
        int, Query(ge=1, le=500, description="Max entries to return")
    ] = 100,
) -> list[AuditLogEntry]:
    """Admin-only: Retrieve immutable audit trail history."""
    return await service.get_logs(
        entity=entity, actor_id=actor_id, action=action, limit=limit
    )


@router.get("/{log_id}", response_model=AuditLogEntry)
async def get_audit_log(
    log_id: str,
    _: Annotated[User, Depends(require_admin)],
    service: Annotated[AuditService, Depends(get_audit_service)],
) -> AuditLogEntry:
    """Admin-only: Retrieve a single audit event entry by ID."""
    return await service.get_log_by_id(log_id=log_id)
