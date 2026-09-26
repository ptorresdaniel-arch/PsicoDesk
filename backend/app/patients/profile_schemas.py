from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class PatientProfileAppointment(BaseModel):
    id: UUID
    start_time: datetime
    end_time: datetime
    status: str
    title: str | None

    model_config = {
        "from_attributes": True
    }


class PatientProfileSession(BaseModel):
    id: UUID
    session_date: datetime
    duration_minutes: int | None
    summary: str | None
    notes: str | None

    model_config = {
        "from_attributes": True
    }


class PatientProfileRead(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    email: str | None
    phone: str | None

    upcoming_appointments: list[
        PatientProfileAppointment
    ]

    clinical_sessions: list[
        PatientProfileSession
    ]

    last_session: PatientProfileSession | None