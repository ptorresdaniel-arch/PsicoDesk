from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.models import Permission, Role
from app.users.models import User


def get_role_by_name(db: Session, name: str) -> Role | None:
    statement = select(Role).where(Role.name == name)
    return db.scalar(statement)


def get_permission_by_code(
    db: Session,
    code: str,
) -> Permission | None:
    statement = select(Permission).where(Permission.code == code)
    return db.scalar(statement)


def create_role(db: Session, name: str) -> Role:
    role = Role(name=name)

    db.add(role)
    db.commit()
    db.refresh(role)

    return role


def create_permission(
    db: Session,
    code: str,
) -> Permission:
    permission = Permission(code=code)

    db.add(permission)
    db.commit()
    db.refresh(permission)

    return permission


def assign_permission_to_role(
    db: Session,
    role: Role,
    permission: Permission,
) -> None:
    if permission not in role.permissions:
        role.permissions.append(permission)
        db.commit()


def assign_role_to_user(
    db: Session,
    user: User,
    role: Role,
) -> None:
    if role not in user.roles:
        user.roles.append(role)
        db.commit()