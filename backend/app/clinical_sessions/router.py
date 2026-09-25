from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.auth.dependencies import get_current_user
from app.users.models import User

from app.clinical_sessions.schemas import (
    ClinicalSessionCreate,
    ClinicalSessionRead,
    ClinicalSessionUpdate,
)

from app.clinical_sessions.service import (
    create_clinical_session,
    delete_clinical_session,
    get_session_by_id,
    get_sessions_by_patient,
    update_clinical_session,
)


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
    current_user: User = Depends(get_current_user),
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
    response_model=list[ClinicalSessionRead],
)
def list_patient_sessions(
    patient_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return get_sessions_by_patient(
        db,
        patient_id,
        current_user.id,
    )


@router.get(
    "/{session_id}",
    response_model=ClinicalSessionRead,
)
def get_session(
    session_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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
    current_user: User = Depends(get_current_user),
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