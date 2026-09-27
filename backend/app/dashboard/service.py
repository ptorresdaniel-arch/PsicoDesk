from datetime import datetime, time, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.appointments.enums import AppointmentStatus
from app.appointments.models import Appointment
from app.clinical_sessions.models import ClinicalSession
from app.patients.models import Patient


def get_dashboard(
    db: Session,
    professional_id: UUID,
):

    now = datetime.now(timezone.utc)

    today_start = datetime.combine(
        now.date(),
        time.min,
        tzinfo=timezone.utc,
    )

    today_end = datetime.combine(
        now.date(),
        time.max,
        tzinfo=timezone.utc,
    )

    total_patients = db.scalar(
        select(func.count(Patient.id))
        .where(
            Patient.professional_id == professional_id,
            Patient.is_active.is_(True),
        )
    )

    today_appointments = list(
        db.scalars(
            select(Appointment)
            .options(
                joinedload(Appointment.patient)
            )
            .where(
                Appointment.professional_id == professional_id,
                Appointment.start_time >= today_start,
                Appointment.start_time <= today_end,
            )
            .order_by(
                Appointment.start_time,
            )
        ).all()
    )

    upcoming_appointments = db.scalar(
        select(func.count(Appointment.id))
        .where(
            Appointment.professional_id == professional_id,
            Appointment.start_time >= now,
            Appointment.status.in_(
                [
                    AppointmentStatus.scheduled,
                    AppointmentStatus.confirmed,
                ]
            ),
        )
    )

    recent_sessions = list(
        db.scalars(
            select(ClinicalSession)
            .options(
                joinedload(
                    ClinicalSession.patient
                )
            )
            .where(
                ClinicalSession.patient.has(
                    Patient.professional_id == professional_id
                )
            )
            .order_by(
                ClinicalSession.session_date.desc()
            )
            .limit(5)
        ).all()
    )

    return {
        "total_patients": total_patients or 0,
        "today_appointments": [
            {
                "id": appointment.id,
                "patient_name": (
                    f"{appointment.patient.first_name} "
                    f"{appointment.patient.last_name}"
                ),
                "start_time": appointment.start_time,
                "end_time": appointment.end_time,
                "status": appointment.status,
            }
            for appointment in today_appointments
        ],
        "upcoming_appointments": upcoming_appointments or 0,
        "recent_sessions": [
            {
                "id": session.id,
                "patient_name": (
                    f"{session.patient.first_name} "
                    f"{session.patient.last_name}"
                ),
                "session_date": session.session_date,
            }
            for session in recent_sessions
        ],
    }