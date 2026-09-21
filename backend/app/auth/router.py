from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.schemas import LoginRequest, LoginResponse
from app.auth.dependencies import get_current_user

from app.core.database import get_db
from app.core.security import verify_password, create_access_token

from app.users.service import get_user_by_email
from app.users.models import User
from app.users.schemas import UserRead



router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)

DbSession = Annotated[Session, Depends(get_db)]


@router.post(
    "/login",
    response_model=LoginResponse,
)
def login(
    login_data: LoginRequest,
    db: DbSession,
) -> LoginResponse:
    user = get_user_by_email(db, login_data.email)

    if user is None or not verify_password(
        login_data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos.",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario está inactivo.",
        )

    access_token = create_access_token(user.id)
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
    )
    
@router.get(
    "/me",
    response_model=UserRead,
)
def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    return current_user
    
    
    
    