"""Change request schemas for faculty assignment modification requests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ChangeRequestCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    assignment_id: str = Field(..., min_length=1, description="Target assignment ID")
    comment: str = Field(..., min_length=3, description="Comment or requested change explanation")


class ChangeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(..., min_length=1, description="Unique change request ID")
    assignment_id: str = Field(..., description="Target assignment ID")
    faculty_id: str = Field(..., description="Faculty member ID submitting the request")
    section_id: str = Field(..., description="Target course section ID")
    course_code: str = Field(default="", description="Human-readable course code")
    comment: str = Field(..., description="Instructor request rationale")
    status: Literal["pending", "approved", "rejected"] = Field(
        default="pending", description="Administrative review status"
    )
    admin_response: str | None = Field(
        default=None, description="Optional administrative response note"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(UTC))

