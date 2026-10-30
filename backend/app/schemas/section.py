from pydantic import BaseModel, ConfigDict, Field, model_validator


class Section(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(..., min_length=1, description="Unique section instance identifier")
    course_id: str = Field(..., min_length=1, description="Parent course identifier")
    term: str = Field(
        ..., min_length=1, description="Academic term offering (e.g., Fall 2026)"
    )
    section_cap: int = Field(
        ..., gt=0, le=1000, description="Maximum student enrollment capacity"
    )
    expected_size: int = Field(
        ..., ge=0, description="Baseline expected student enrollment"
    )
    size_p10: int = Field(
        ..., ge=0, description="Conservative 10th percentile demand forecast"
    )
    size_p50: int = Field(
        ..., ge=0, description="Median 50th percentile demand forecast"
    )
    size_p90: int = Field(
        ..., ge=0, description="High-demand 90th percentile demand forecast"
    )
    time_slot_id: str | None = Field(
        default=None, description="Assigned scheduled time slot identifier"
    )

    @model_validator(mode="after")
    def validate_quantile_monotonicity(self) -> "Section":
        if not (self.size_p10 <= self.size_p50 <= self.size_p90):
            raise ValueError(
                f"Quantile demand forecasts must satisfy P10 <= P50 <= P90. "
                f"Got P10={self.size_p10}, P50={self.size_p50}, P90={self.size_p90}"
            )
        return self
