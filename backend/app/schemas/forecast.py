from pydantic import BaseModel, ConfigDict, Field


class ForecastRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    course_id: str = Field(..., description="Unique course identifier")
    course_code: str = Field(..., description="Institutional course code (e.g. CS101)")
    term: str = Field(..., description="Academic term (e.g. Fall 2026)")
    season: str = Field(..., description="Term season (Fall, Spring, Summer)")
    year: int = Field(..., description="Academic year")
    p10: int = Field(..., ge=0, description="Conservative 10th percentile demand")
    p50: int = Field(..., ge=0, description="Median 50th percentile demand")
    p90: int = Field(..., ge=0, description="High-demand 90th percentile demand")
    n_sections: int = Field(
        ..., gt=0, description="Recommended section count based on P50"
    )
    p90_risk_sections: int = Field(
        ..., gt=0, description="Stress-case section count based on P90"
    )


class ForecastRunResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    status: str = Field(default="ok", description="Status code")
    term: str = Field(..., description="Term processed")
    courses_forecasted: int = Field(..., ge=0, description="Number of courses forecasted")
    forecast_mode: str = Field(..., description="Active forecast mode (model or precomputed)")
    message: str | None = Field(default=None, description="Detailed message")

