from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.core.database import get_db
from app.patients.models import Patient
from app.patients.schemas import PatientCreate, PatientRead, PatientUpdate
from app.patients.service import (
    create_patient,
    delete_patient,
    get_patient_by_id,
    get_patients_by_professional,
    update_patient,
    get_patient_profile,
)
from app.patients.profile_schemas import PatientProfileRead
from app.patients.filters import PatientFilters
from app.users.models import User


router = APIRouter(
    prefix="/patients",
    tags=["Pacientes"],
)

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=PatientRead,
    status_code=status.HTTP_201_CREATED,
)
def register_patient(
    patient_data: PatientCreate,
    db: DbSession,
    current_user: Annotated[
        User,
        Depends(require_permission("patients.create")),
    ],
) -> Patient:
    return create_patient(
        db,
        patient_data,
        current_user,
    )


@router.get(
    "",
    response_model=list[PatientRead],
)
def list_patients(
    db: DbSession,
    filters: Annotated[
        PatientFilters,
        Depends(),
    ],
    current_user: Annotated[
        User,
        Depends(require_permission("patients.read")),
    ],
) -> list[Patient]:
    print(
    "SEARCH:",
    filters.search,
    "ACTIVE:",
    filters.is_active,
)
    return get_patients_by_professional(
        db,
        current_user.id,
        filters,
    )

@router.get(
    "/{patient_id}/profile",
    response_model=PatientProfileRead,
)
def get_patient_profile_view(
    patient_id: UUID,
    db: DbSession,
    current_user: Annotated[
        User,
        Depends(require_permission("patients.read")),
    ],
):
    patient = get_patient_by_id(
        db,
        patient_id,
        current_user.id,
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado.",
        )

    return get_patient_profile(
        patient,
    )

@router.get(
    "/{patient_id}",
    response_model=PatientRead,
)
def get_patient(
    patient_id: UUID,
    db: DbSession,
    current_user: Annotated[
        User,
        Depends(require_permission("patients.read")),
    ],
) -> Patient:
    patient = get_patient_by_id(
        db,
        patient_id,
        current_user.id,
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado.",
        )

    return patient

@router.patch(
    "/{patient_id}",
    response_model=PatientRead,
)
def edit_patient(
    patient_id: UUID,
    patient_data: PatientUpdate,
    db: DbSession,
    current_user: Annotated[
        User,
        Depends(require_permission("patients.update")),
    ],
) -> Patient:
    patient = get_patient_by_id(
        db,
        patient_id,
        current_user.id,
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado.",
        )

    return update_patient(
        db,
        patient,
        patient_data,
    )


@router.delete(
    "/{patient_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_patient(
    patient_id: UUID,
    db: DbSession,
    current_user: Annotated[
        User,
        Depends(require_permission("patients.delete")),
    ],
) -> None:
    patient = get_patient_by_id(
        db,
        patient_id,
        current_user.id,
    )

    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paciente no encontrado.",
        )

    delete_patient(
        db,
        patient,
    )