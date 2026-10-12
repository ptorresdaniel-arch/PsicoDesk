from uuid import UUID

from fastapi import(
    APIRouter,
    Depends,
    HTTPException,
    status,
)
    
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.permissions.service import get_permission_by_id
from app.core.database import get_db
from app.permissions.schemas import PermissionRead
from app.roles.schemas import(
    RoleCreate,
    RoleRead,
    )

from app.roles.service import(
    assign_permission_to_role,
    remove_permission_from_role,
    get_roles,
    create_role,
    delete_role,
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
        
@router.post(
    "/{role_id}/permissions/{permission_id}",
    response_model=list[PermissionRead],
    status_code=status.HTTP_200_OK,
)
def assign_role_permission(
    role_id: UUID,
    permission_id: UUID,
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

    permission = get_permission_by_id(
        db,
        permission_id,
    )

    if permission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso no encontrado.",
        )

    assign_permission_to_role(
        db,
        role,
        permission,
    )

    return role.permissions

@router.delete(
    "/{role_id}/permissions/{permission_id}",
    response_model=list[PermissionRead],
)
def remove_role_permission(
    role_id: UUID,
    permission_id: UUID,
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

    permission = get_permission_by_id(
        db,
        permission_id,
    )

    if permission is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permiso no encontrado.",
        )

    remove_permission_from_role(
        db,
        role,
        permission,
    )

    return role.permissions