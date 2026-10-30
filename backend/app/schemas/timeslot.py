import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.common import DayOfWeek

TIME_REGEX = re.compile(r"^([01]\d|2[0-3]):([0-5]\d)$")


class TimeSlot(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(
        ..., min_length=1, description="Unique time slot identifier (e.g., TS-MON-0900)"
    )
    day: DayOfWeek = Field(..., description="Day of the week (e.g., MON, TUE)")
    start: str = Field(
        ..., description="Start time in 24-hour HH:MM format (e.g., 09:00)"
    )
    end: str = Field(..., description="End time in 24-hour HH:MM format (e.g., 10:30)")

    @field_validator("start", "end")
    @classmethod
    def validate_time_format(cls, v: str) -> str:
        if not TIME_REGEX.match(v):
            raise ValueError(
                f"Time '{v}' must be in 24-hour HH:MM format (00:00 to 23:59)"
            )
        return v

    @model_validator(mode="after")
    def validate_chronological_order(self) -> "TimeSlot":
        t_start = datetime.strptime(self.start, "%H:%M").time()
        t_end = datetime.strptime(self.end, "%H:%M").time()
        if t_start >= t_end:
            raise ValueError(
                f"Start time ({self.start}) must precede end time ({self.end})"
            )
        return self
