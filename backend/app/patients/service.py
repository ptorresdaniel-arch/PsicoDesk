from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.patients.models import Patient
from app.patients.schemas import PatientCreate
from app.users.models import User
from app.patients.schemas import PatientCreate, PatientUpdate


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


def get_patients_by_professional(
    db: Session,
    professional_id: UUID,
) -> list[Patient]:
    statement = (
        select(Patient)
        .where(Patient.professional_id == professional_id)
        .order_by(Patient.last_name, Patient.first_name)
    )

    return list(db.scalars(statement).all())


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