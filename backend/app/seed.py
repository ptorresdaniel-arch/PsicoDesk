from app.auth.service import (
    assign_permission_to_role,
    assign_role_to_user,
    create_permission,
    create_role,
    get_permission_by_code,
    get_role_by_name,
)
from app.core.database import SessionLocal
from app.users.service import get_user_by_email


INITIAL_PERMISSIONS = [
    "users.read",
    "users.create",
    "users.update",
    "users.delete",
]

ADMIN_ROLE = "admin"


def seed() -> None:
    db = SessionLocal()

    try:
        admin_role = get_role_by_name(db, ADMIN_ROLE)

        if admin_role is None:
            admin_role = create_role(db, ADMIN_ROLE)

        for code in INITIAL_PERMISSIONS:
            permission = get_permission_by_code(db, code)

            if permission is None:
                permission = create_permission(db, code)

            assign_permission_to_role(
                db,
                admin_role,
                permission,
            )

        user = get_user_by_email(
            db,
            "daniel.api@example.com",
        )

        if user is not None:
            assign_role_to_user(
                db,
                user,
                admin_role,
            )

    finally:
        db.close()


if __name__ == "__main__":
    seed()