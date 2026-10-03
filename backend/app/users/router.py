from uuid import UUID
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.users.schemas import(
    UserCreate,
    UserRead,
    UserUpdate,
    UserPasswordUpdate,
    UserStatusUpdate,
    )
from app.users.service import(
    create_user,
    get_user_by_email,
    get_user_by_id,
    update_user,
    change_password,
    update_user_status,
    )

from app.auth.dependencies import(
    require_permission,
    get_current_user,
    )
from app.users.models import User
from app.users.service import update_user


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
    current_user: Annotated[User, Depends(
        require_permission("users.read")
        ),
                            ],
) -> list[User]:
    return list(db.scalars(select(User)).all())

@router.patch(
    "/{user_id}/status",
    response_model=UserRead,
)
def update_user_status_view(
    user_id: UUID,
    data: UserStatusUpdate,
    db: DbSession,
    current_user: Annotated[
        User,
        Depends(require_permission("users.update")),
    ],
) -> User:
    user = get_user_by_id(
        db,
        user_id,
    )

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado.",
        )

    return update_user_status(
        db,
        user,
        data.is_active,
    )

@router.get(
    "/me",
    response_model=UserRead,
)
def get_my_profile(
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    return current_user

@router.post(
    "/me/password",
)
def update_password(
    password_data: UserPasswordUpdate,
    db: DbSession,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> dict[str, str]:

    updated = change_password(
        db,
        current_user,
        password_data,
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="La contraseña actual es incorrecta.",
        )

    return {
        "message": "Contraseña actualizada correctamente.",
    }

@router.patch(
    "/me",
    response_model=UserRead,
)
def update_my_profile(
    user_data: UserUpdate,
    db: DbSession,
    current_user: Annotated[
        User,
        Depends(get_current_user),
    ],
) -> User:
    return update_user(
        db,
        current_user,
        user_data,
    )
    
