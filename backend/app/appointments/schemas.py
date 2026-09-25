from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


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


class AppointmentUpdate(BaseModel):
    start_time: datetime | None = None
    end_time: datetime | None = None

    status: str | None = None

    title: str | None = Field(
        default=None,
        max_length=150,
    )

    reason: str | None = Field(
        default=None,
        max_length=255,
    )

    notes: str | None = None


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