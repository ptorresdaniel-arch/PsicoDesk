from uuid import UUID
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import(
    Permission,
    Role,
)

from app.roles.schemas import RoleCreate


def get_roles(
    db: Session,
) -> list[Role]:

    statement = (
        select(Role)
        .order_by(Role.name)
    )

    return list(
        db.scalars(statement).all()
    )
    
def create_role(
    db: Session,
    data: RoleCreate,
) -> Role:
    
    existing_role = get_role_by_name(
        db,
        data.name,
    )
    if existing_role is not None:
        raise ValueError(
            "Ya existe un rol con ese nombre."
        )
    role = Role(
        name=data.name,
    )
    
    db.add(role)
    db.commit()
    db.refresh(role)
    
    return role

def get_role_by_name(
    db: Session,
    name: str,
) -> Role | None:

    statement = select(Role).where(
        Role.name == name,
    )

    return db.scalar(statement)

def get_role_by_id(
    db: Session,
    role_id: UUID,
)-> Role | None:
    statement = select(Role).where(
        Role.id == role_id,
    )
    return db.scalar(statement)

def delete_role(
    db: Session,
    role: Role,
) -> None:

    if role.users:
        raise ValueError(
            "No se puede eliminar un rol asignado a usuarios."
        )

    db.delete(role)
    db.commit()

def assign_permission_to_role(
    db: Session,
    role: Role,
    permission: Permission,
) -> None:

    if permission not in role.permissions:
        role.permissions.append(permission)
        db.commit()
        
def remove_permission_from_role(
    db: Session,
    role: Role,
    permission: Permission,
) -> None:

    if permission in role.permissions:
        role.permissions.remove(permission)
        db.commit()