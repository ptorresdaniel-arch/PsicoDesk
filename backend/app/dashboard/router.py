from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.core.database import get_db
from app.dashboard.schemas import DashboardRead
from app.dashboard.service import get_dashboard
from app.users.models import User


router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


DbSession = Annotated[
    Session,
    Depends(get_db),
]


@router.get(
    "",
    response_model=DashboardRead,
)
def dashboard(
    db: DbSession,
    current_user: Annotated[
        User,
        Depends(
            require_permission("patients.read")
            ),
    ],
)-> DashboardRead:
    return get_dashboard(
        db,
        current_user.id,
    )