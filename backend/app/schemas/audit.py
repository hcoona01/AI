from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(..., min_length=1, description="Unique audit log entry identifier")
    actor_id: str = Field(
        ...,
        min_length=1,
        description="Identifier of the user or system component performing the action",
    )
    action: str = Field(
        ...,
        min_length=1,
        description="Action code (e.g., ASSIGNMENT_OVERRIDE, SOLVER_OPTIMIZE, CONSTRAINT_UPDATE)",
    )
    entity: str = Field(
        ...,
        min_length=1,
        description="Target entity domain (e.g., assignment, faculty, course)",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Structured change delta, arguments, or event payload",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp of event occurrence",
    )
