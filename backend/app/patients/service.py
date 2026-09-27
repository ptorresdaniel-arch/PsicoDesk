from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import select, or_, func
from sqlalchemy.orm import Session

from app.patients.models import Patient
from app.patients.schemas import PatientCreate, PatientUpdate
from app.patients.filters import PatientFilters

from app.users.models import User

from app.appointments.enums import AppointmentStatus



def create_patient(
    db: Session,
    patient_data: PatientCreate,
    professional: User,
) -> Patient:
    patient = Patient(
        professional_id=professional.id,
        **patient_data.model_dump(),
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    return patient

def update_patient(
    db: Session,
    patient: Patient,
    patient_data: PatientUpdate,
    ) -> Patient:
    update_data = patient_data.model_dump(
        exclude_unset=True,
    )
    for field, value in update_data.items():
        setattr(patient, field, value)
        
    db.commit()
    db.refresh(patient)
    
    return patient

def delete_patient(
    db:Session,
    patient: Patient,
) -> None:
    db.delete(patient)
    db.commit()

def apply_patient_filters(
    statement,
    professional_id: UUID,
    filters: PatientFilters,
):
    statement = statement.where(
        Patient.professional_id == professional_id,
    )

    if filters.search:
        search = f"%{filters.search}%"

        statement = statement.where(
            or_(
                Patient.first_name.ilike(search),
                Patient.last_name.ilike(search),
                Patient.identification.ilike(search),
            )
        )

    if filters.is_active is not None:
        statement = statement.where(
            Patient.is_active == filters.is_active,
        )

    return statement

def get_patients_by_professional(
    db: Session,
    professional_id: UUID,
    filters: PatientFilters,
):
    base_statement = select(Patient)

    filtered_statement = apply_patient_filters(
        base_statement,
        professional_id,
        filters,
    )

    total = db.scalar(
        select(func.count())
        .select_from(filtered_statement.subquery()
        )
    )

    statement = (
        filtered_statement
        .order_by(
            Patient.last_name,
            Patient.first_name,
        )
        .offset(
            (filters.page - 1) * filters.limit
        )
        .limit(
            filters.limit,
        )
    )

    items = list(
        db.scalars(statement).all()
    )

    return {
        "items": items,
        "total": total,
        "page": filters.page,
        "limit": filters.limit,
    }


def get_patient_by_id(
    db: Session,
    patient_id: UUID,
    professional_id: UUID,
) -> Patient | None:
    statement = select(Patient).where(
        Patient.id == patient_id,
        Patient.professional_id == professional_id,
    )

    return db.scalar(statement)

def get_patient_profile(
    patient: Patient,
) -> dict:

    now = datetime.now(timezone.utc)

    upcoming = [
        appointment
        for appointment in patient.appointments
        if(
            appointment.start_time >= now
            and appointment.status not in [
                AppointmentStatus.completed,
                AppointmentStatus.cancelled,
                AppointmentStatus.no_show,
            ]
        )
    ]

    sessions = sorted(
        patient.clinical_sessions,
        key=lambda x: x.session_date,
        reverse=True,
    )

    return {
        "id": patient.id,
        "first_name": patient.first_name,
        "last_name": patient.last_name,
        "email": patient.email,
        "phone": patient.phone,
        "upcoming_appointments": sorted(
            upcoming,
            key=lambda x: x.start_time,
        ),
        "clinical_sessions": sessions,
        "last_session": (
            sessions[0]
            if sessions
            else None
        ),
    }