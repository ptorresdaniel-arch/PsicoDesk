from fastapi import(
    APIRouter,
    Depends,
    HTTPException,
    status,
    )

from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.core.database import get_db

from app.permissions.schemas import(
    PermissionCreate,
    PermissionRead,
    )
from app.permissions.service import(
    get_permissions,
    create_permission,
    )
from app.users.models import User


router = APIRouter(
    prefix="/permissions",
    tags=["Permisos"],
)


@router.get(
    "",
    response_model=list[PermissionRead],
)
def list_permissions(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("users.read")
    ),
):
    return get_permissions(db)

@router.post(
    "",
    response_model=PermissionRead,
    status_code=status.HTTP_201_CREATED,
)
def create_permission_view(
    data: PermissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("users.update")
    ),
):
    try:
        return create_permission(
            db,
            data,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )