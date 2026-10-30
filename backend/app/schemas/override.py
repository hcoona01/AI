from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class Override(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(..., min_length=1, description="Unique override record identifier")
    assignment_id: str = Field(
        ..., min_length=1, description="Target assignment record being modified"
    )
    admin_id: str = Field(
        ..., min_length=1, description="ID of administrator executing override"
    )
    reason: str = Field(
        ...,
        min_length=5,
        description="Mandatory administrative justification explaining why assignment was manually changed",
    )
    previous_faculty_id: str | None = Field(
        default=None, description="Faculty ID previously assigned to section, if any"
    )
    new_faculty_id: str = Field(
        ..., min_length=1, description="Newly assigned faculty member identifier"
    )
    constraint_evidence_snapshot: dict[str, Any] = Field(
        default_factory=dict,
        description="Immutable snapshot of optimizer fit scores and rule states prior to override",
    )
    acknowledged_violations: list[str] = Field(
        default_factory=list,
        description="List of rule_ids that the administrator explicitly acknowledged violating",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(UTC),
        description="Timestamp when override was executed",
    )

    @model_validator(mode="after")
    def validate_faculty_change(self) -> "Override":
        if (
            self.previous_faculty_id is not None
            and self.previous_faculty_id == self.new_faculty_id
        ):
            raise ValueError(
                f"new_faculty_id '{self.new_faculty_id}' cannot be identical to previous_faculty_id"
            )
        return self
