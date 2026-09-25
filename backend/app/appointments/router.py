from uuid import UUID

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.core.database import get_db
from app.users.models import User

from app.appointments.schemas import (
    AppointmentCreate,
    AppointmentRead,
    AppointmentUpdate,
)

from app.appointments.service import (
    create_appointment,
    delete_appointment,
    get_appointment_by_id,
    get_professional_appointments,
    update_appointment,
    get_appointments_by_date_range
)


router = APIRouter(
    prefix="/appointments",
    tags=["Agenda"],
)


@router.post(
    "",
    response_model=AppointmentRead,
    status_code=status.HTTP_201_CREATED,
)
def create(
    data: AppointmentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    try:
        appointment = create_appointment(
            db,
            data,
            current_user.id,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Paciente no encontrado.",
        )

    return appointment


@router.get(
    "",
    response_model=list[AppointmentRead],
)
def list_my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return get_professional_appointments(
        db,
        current_user.id,
    )

@router.get(
    "/calendar",
    response_model=list[AppointmentRead],
)
def calendar(
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    return get_appointments_by_date_range(
        db,
        current_user.id,
        start_date,
        end_date,
    )


@router.get(
    "/{appointment_id}",
    response_model=AppointmentRead,
)
def get_one(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    appointment = get_appointment_by_id(
        db,
        appointment_id,
        current_user.id,
    )

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Cita no encontrada.",
        )

    return appointment


@router.patch(
    "/{appointment_id}",
    response_model=AppointmentRead,
)
def update(
    appointment_id: UUID,
    data: AppointmentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    appointment = get_appointment_by_id(
        db,
        appointment_id,
        current_user.id,
    )

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Cita no encontrada.",
        )

    return update_appointment(
        db,
        appointment,
        data,
    )


@router.delete(
    "/{appointment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete(
    appointment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    appointment = get_appointment_by_id(
        db,
        appointment_id,
        current_user.id,
    )

    if appointment is None:
        raise HTTPException(
            status_code=404,
            detail="Cita no encontrada.",
        )

    delete_appointment(
        db,
        appointment,
    )
    
