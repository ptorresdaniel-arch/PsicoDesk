from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class DashboardAppointmentRead(BaseModel):
    id: UUID
    patient_name: str
    start_time: datetime
    end_time: datetime
    status: str


class DashboardSessionRead(BaseModel):
    id: UUID
    patient_name: str
    session_date: datetime


class DashboardRead(BaseModel):
    total_patients: int

    today_appointments: list[
        DashboardAppointmentRead
    ]

    upcoming_appointments: int

    recent_sessions: list[
        DashboardSessionRead
    ]