from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ClinicalSessionCreate(BaseModel):
    patient_id: UUID

    session_date: datetime

    duration_minutes: int | None = Field(
        default=None,
        ge=1,
        le=480,
    )

    summary: str | None = Field(
        default=None,
        max_length=255,
    )

    notes: str | None = None


class ClinicalSessionUpdate(BaseModel):
    session_date: datetime | None = None

    duration_minutes: int | None = Field(
        default=None,
        ge=1,
        le=480,
    )

    summary: str | None = Field(
        default=None,
        max_length=255,
    )

    notes: str | None = None


class ClinicalSessionRead(BaseModel):
    id: UUID
    patient_id: UUID
    appointment_id: UUID | None

    session_date: datetime

    duration_minutes: int | None

    summary: str | None

    notes: str | None

    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True
    }