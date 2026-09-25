from uuid import UUID

from sqlalchemy import select, or_
from sqlalchemy.orm import Session

from app.appointments.models import Appointment
from app.appointments.schemas import (
    AppointmentCreate,
    AppointmentUpdate,
)
from app.patients.models import Patient


def get_patient_for_professional(
    db: Session,
    patient_id: UUID,
    professional_id: UUID,
) -> Patient | None:

    statement = select(Patient).where(
        Patient.id == patient_id,
        Patient.professional_id == professional_id,
    )

    return db.scalar(statement)


def has_schedule_conflict(
    db: Session,
    professional_id: UUID,
    start_time,
    end_time,
) -> bool:

    statement = select(Appointment).where(
        Appointment.professional_id == professional_id,
        Appointment.start_time < end_time,
        Appointment.end_time > start_time,
    )

    return db.scalar(statement) is not None


def create_appointment(
    db: Session,
    appointment_data: AppointmentCreate,
    professional_id: UUID,
) -> Appointment | None:

    if appointment_data.end_time <= appointment_data.start_time:
        raise ValueError(
            "La hora de término debe ser posterior al inicio."
        )

    patient = get_patient_for_professional(
        db,
        appointment_data.patient_id,
        professional_id,
    )

    if patient is None:
        return None

    if has_schedule_conflict(
        db,
        professional_id,
        appointment_data.start_time,
        appointment_data.end_time,
    ):
        raise ValueError(
            "Existe una cita que se cruza con ese horario."
        )

    appointment = Appointment(
        professional_id=professional_id,
        patient_id=patient.id,
        start_time=appointment_data.start_time,
        end_time=appointment_data.end_time,
        title=appointment_data.title,
        reason=appointment_data.reason,
        notes=appointment_data.notes,
        timezone=appointment_data.timezone,
    )

    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return appointment


def get_appointment_by_id(
    db: Session,
    appointment_id: UUID,
    professional_id: UUID,
) -> Appointment | None:

    statement = select(Appointment).where(
        Appointment.id == appointment_id,
        Appointment.professional_id == professional_id,
    )

    return db.scalar(statement)


def get_professional_appointments(
    db: Session,
    professional_id: UUID,
):

    statement = (
        select(Appointment)
        .where(
            Appointment.professional_id == professional_id,
        )
        .order_by(
            Appointment.start_time,
        )
    )

    return list(db.scalars(statement).all())


def update_appointment(
    db: Session,
    appointment: Appointment,
    data: AppointmentUpdate,
):

    update_data = data.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        setattr(
            appointment,
            field,
            value,
        )

    db.commit()
    db.refresh(appointment)

    return appointment


def delete_appointment(
    db: Session,
    appointment: Appointment,
):

    db.delete(appointment)
    db.commit()