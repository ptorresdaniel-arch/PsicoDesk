from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.clinical_sessions.models import ClinicalSession
from app.clinical_sessions.note_models import ClinicalSessionNote
from app.clinical_sessions.note_schemas import ClinicalSessionNoteCreate
from app.patients.models import Patient
from app.users.models import User


def get_session_for_professional(
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


def create_session_note(
    db: Session,
    clinical_session: ClinicalSession,
    data: ClinicalSessionNoteCreate,
    user: User,
) -> ClinicalSessionNote:

    note = ClinicalSessionNote(
        clinical_session_id=clinical_session.id,
        content=data.content,
        created_by=user.id,
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    return note


def get_session_notes(
    db: Session,
    clinical_session_id: UUID,
) -> list[ClinicalSessionNote]:

    statement = (
        select(ClinicalSessionNote)
        .where(
            ClinicalSessionNote.clinical_session_id
            == clinical_session_id
        )
        .order_by(
            ClinicalSessionNote.created_at.desc()
        )
    )

    return list(
        db.scalars(statement).all()
    )