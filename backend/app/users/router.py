from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.users.schemas import UserCreate, UserRead
from app.users.service import create_user, get_user_by_email

from app.auth.dependencies import require_permission
from app.users.models import User


router = APIRouter(
    prefix="/users",
    tags=["Usuarios"],
)

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "",
    response_model=UserRead,
    status_code=status.HTTP_201_CREATED,
)
def register_user(
    user_data: UserCreate,
    db: DbSession,
) -> UserRead:
    existing_user = get_user_by_email(db, user_data.email)

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un usuario con ese email.",
        )

    return create_user(db, user_data)

@router.get(
    "/",
    response_model=list[UserRead],
)
def list_users(
    db: DbSession,
    current_user: Annotated[User, Depends(require_permission("users.read")),],
) -> list[User]:
    return list(db.scalars(select(User)).all())