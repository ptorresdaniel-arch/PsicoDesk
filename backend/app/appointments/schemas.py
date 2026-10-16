from datetime import datetime
from uuid import UUID

from app.appointments.enums import AppointmentStatus

from pydantic import(
    BaseModel,
    Field,
    field_validator,
    )


class AppointmentCreate(BaseModel):
    patient_id: UUID

    start_time: datetime
    end_time: datetime

    title: str | None = Field(
        default=None,
        max_length=150,
    )

    reason: str | None = Field(
        default=None,
        max_length=255,
    )

    notes: str | None = None

    timezone: str = "America/Santiago"
    
    @field_validator("start_time", "end_time")
    @classmethod
    def validate_timezone(
        cls,
        value: datetime,
    )-> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "La fecha debe incluir información de zona horaria."
            )
        return value


class AppointmentUpdate(BaseModel):
    start_time: datetime = Field(default=None)
    end_time: datetime = Field(default=None)

    status: AppointmentStatus = Field(default=None)

    title: str | None = Field(
        default=None,
        max_length=150,
    )

    reason: str | None = Field(
        default=None,
        max_length=255,
    )

    notes: str | None = None
    
    @field_validator("start_time", "end_time")
    @classmethod
    def validate_timezone(
        cls,
        value: datetime,
    )-> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError(
                "La fecha debe incluir información de zona horaria."
            )
        return value


class AppointmentRead(BaseModel):
    id: UUID

    professional_id: UUID
    patient_id: UUID

    start_time: datetime
    end_time: datetime

    status: str

    title: str | None
    reason: str | None
    notes: str | None

    timezone: str

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }

class AppointmentCalendarRead(BaseModel):
    id: UUID

    patient_name: str

    start_time: datetime
    end_time: datetime

    status: str
    
    title: str | None

    model_config = {
        "from_attributes": True
    }
    
class AppointmentAvailabilityRead(BaseModel):
    available: bool
    
class AppointmentSummaryRead(BaseModel):
    total: int

    scheduled: int
    confirmed: int
    completed: int
    cancelled: int
    no_show: int