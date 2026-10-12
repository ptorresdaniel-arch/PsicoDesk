from uuid import UUID

from fastapi import(
    APIRouter,
    Depends,
    HTTPException,
    status,
)
    
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission

from app.core.database import get_db

from app.roles.schemas import(
    RoleCreate,
    RoleRead,
    )

from app.roles.service import(
    get_roles,
    create_role,
    delete_role
    )
from app.auth.service import get_role_by_id

from app.users.models import User


router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)


@router.get(
    "",
    response_model=list[RoleRead],
)
def list_roles(
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("users.read")
    ),
):
    return get_roles(db)

@router.post(
    "",
    response_model=RoleRead,
    status_code=status.HTTP_201_CREATED,
)
def create_role_view(
    data: RoleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("users.update")
    ),
):
    try:
        return create_role(
            db,
            data,
        )
    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )

@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def remove_role(
    role_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_permission("users.update")
    ),
):
    role = get_role_by_id(
        db,
        role_id,
    )

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Rol no encontrado.",
        )

    try:
        delete_role(
            db,
            role,
        )

    except ValueError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        )