from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clinical_sessions.models import ClinicalSession
from app.clinical_sessions.schemas import (
    ClinicalSessionCreate,
    ClinicalSessionUpdate,
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


def create_clinical_session(
    db: Session,
    session_data: ClinicalSessionCreate,
    professional_id: UUID,
) -> ClinicalSession | None:

    patient = get_patient_for_professional(
        db,
        session_data.patient_id,
        professional_id,
    )

    if patient is None:
        return None

    clinical_session = ClinicalSession(
        patient_id=patient.id,
        session_date=session_data.session_date,
        duration_minutes=session_data.duration_minutes,
        summary=session_data.summary,
        notes=session_data.notes,
    )

    db.add(clinical_session)
    db.commit()
    db.refresh(clinical_session)

    return clinical_session


def get_sessions_by_patient(
    db: Session,
    patient_id: UUID,
    professional_id: UUID,
) -> list[ClinicalSession]:

    patient = get_patient_for_professional(
        db,
        patient_id,
        professional_id,
    )

    if patient is None:
        return []

    statement = (
        select(ClinicalSession)
        .where(
            ClinicalSession.patient_id == patient_id
        )
        .order_by(
            ClinicalSession.session_date.desc()
        )
    )

    return list(db.scalars(statement).all())


def get_session_by_id(
    db: Session,
    session_id: UUID,
    professional_id: UUID,
) -> ClinicalSession | None:

    statement = (
        select(ClinicalSession)
        .join(Patient)
        .where(
            ClinicalSession.id == session_id,
            Patient.professional_id == professional_id,
        )
    )

    return db.scalar(statement)


def update_clinical_session(
    db: Session,
    clinical_session: ClinicalSession,
    session_data: ClinicalSessionUpdate,
) -> ClinicalSession:

    update_data = session_data.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        setattr(
            clinical_session,
            field,
            value,
        )

    db.commit()
    db.refresh(clinical_session)

    return clinical_session


def delete_clinical_session(
    db: Session,
    clinical_session: ClinicalSession,
) -> None:

    db.delete(clinical_session)
    db.commit()