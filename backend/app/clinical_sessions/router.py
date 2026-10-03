from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import require_permission
from app.users.models import User

from app.clinical_sessions.schemas import (
    ClinicalSessionCreate,
    ClinicalSessionRead,
    ClinicalSessionUpdate,
    ClinicalSessionListRead,
)

from app.clinical_sessions.service import (
    create_clinical_session,
    delete_clinical_session,
    get_session_by_id,
    get_sessions_by_patient,
    update_clinical_session,
)

from app.clinical_sessions.note_schemas import ClinicalSessionNoteCreate, ClinicalSessionNoteRead
from app.clinical_sessions.note_service import create_session_note, get_session_for_professional, get_session_notes

router = APIRouter(
    prefix="/clinical-sessions",
    tags=["Sesiones clínicas"],
)


@router.post(
    "",
    response_model=ClinicalSessionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_session(
    data: ClinicalSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical_sessions.create")),
):
    clinical_session = create_clinical_session(
        db,
        data,
        current_user.id,
    )

    if clinical_session is None:
        raise HTTPException(
            status_code=404,
            detail="Paciente no encontrado.",
        )

    return clinical_session


@router.get(
    "/patient/{patient_id}",
    response_model=ClinicalSessionListRead,
)
def list_patient_sessions(
    patient_id: UUID,
    page: int = Query(
        default=1,
        ge=1,
    ),
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("clinical_sessions.read")
    ),
):
    return get_sessions_by_patient(
        db,
        patient_id,
        current_user.id,
        page,
        limit,
    )


@router.get(
    "/{session_id}",
    response_model=ClinicalSessionRead,
)
def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical_sessions.read")),
):
    clinical_session = get_session_by_id(
        db,
        session_id,
        current_user.id,
    )

    if clinical_session is None:
        raise HTTPException(
            status_code=404,
            detail="Sesión no encontrada.",
        )

    return clinical_session


@router.patch(
    "/{session_id}",
    response_model=ClinicalSessionRead,
)
def update_session(
    session_id: UUID,
    data: ClinicalSessionUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical_sessions.update")),
):
    clinical_session = get_session_by_id(
        db,
        session_id,
        current_user.id,
    )

    if clinical_session is None:
        raise HTTPException(
            status_code=404,
            detail="Sesión no encontrada.",
        )

    return update_clinical_session(
        db,
        clinical_session,
        data,
    )


@router.delete(
    "/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical_sessions.delete")),
):
    clinical_session = get_session_by_id(
        db,
        session_id,
        current_user.id,
    )

    if clinical_session is None:
        raise HTTPException(
            status_code=404,
            detail="Sesión no encontrada.",
        )

    delete_clinical_session(
        db,
        clinical_session,
    )
    
@router.post(
    "/{session_id}/notes",
    response_model=ClinicalSessionNoteRead,
    status_code=status.HTTP_201_CREATED,
)
def create_note(
    session_id: UUID,
    data: ClinicalSessionNoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical_notes.create")),
):
    clinical_session = get_session_for_professional(
        db,
        session_id,
        current_user.id,
    )

    if clinical_session is None:
        raise HTTPException(
            status_code=404,
            detail="Sesión no encontrada.",
        )

    return create_session_note(
        db,
        clinical_session,
        data,
        current_user,
    )


@router.get(
    "/{session_id}/notes",
    response_model=list[ClinicalSessionNoteRead],
)
def list_notes(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission("clinical_notes.read")),
):
    clinical_session = get_session_for_professional(
        db,
        session_id,
        current_user.id,
    )

    if clinical_session is None:
        raise HTTPException(
            status_code=404,
            detail="Sesión no encontrada.",
        )

    return get_session_notes(
        db,
        session_id,
    )