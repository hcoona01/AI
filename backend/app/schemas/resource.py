from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import ResourceType


class Resource(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    id: str = Field(
        ...,
        min_length=1,
        description="Unique physical resource identifier (e.g., ROOM-101)",
    )
    type: ResourceType = Field(
        ..., description="Classification of facility/resource (room or lab)"
    )
    capacity: int = Field(
        ..., gt=0, le=2000, description="Maximum seating/station capacity"
    )
    unavailable_slots: list[str] = Field(
        default_factory=list,
        description="TimeSlot IDs when resource is unavailable or reserved",
    )
