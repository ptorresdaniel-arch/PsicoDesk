from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import Permission
from app.permissions.schemas import PermissionCreate


def get_permissions(
    db: Session,
) -> list[Permission]:

    statement = (
        select(Permission)
        .order_by(Permission.code)
    )

    return list(
        db.scalars(statement).all()
    )


def get_permission_by_code(
    db: Session,
    code: str,
) -> Permission | None:

    statement = select(Permission).where(
        Permission.code == code,
    )

    return db.scalar(statement)


def create_permission(
    db: Session,
    data: PermissionCreate,
) -> Permission:

    existing_permission = get_permission_by_code(
        db,
        data.code,
    )

    if existing_permission is not None:
        raise ValueError(
            "Ya existe un permiso con ese código."
        )

    permission = Permission(
        code=data.code,
    )

    db.add(permission)
    try:
        db.commit()
    except Exception:
        db.rollback()
        raise
    db.refresh(permission)

    return permission

def get_permission_by_id(
    db: Session,
    permission_id: UUID,
) -> Permission | None:

    statement = select(Permission).where(
        Permission.id == permission_id,
    )

    return db.scalar(statement)