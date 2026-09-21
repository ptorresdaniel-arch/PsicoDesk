from app.auth.service import (
    assign_permission_to_role,
    assign_role_to_user,
    create_permission,
    create_role,
    get_permission_by_code,
    get_role_by_name,
)
from app.core.database import SessionLocal
from app.patients import models as patient_models
from app.users.service import get_user_by_email


INITIAL_PERMISSIONS = [
    "users.read",
    "users.create",
    "users.update",
    "users.delete",
    "patients.read",
    "patients.create",
    "patients.update",
    "patients.delete",
]

ADMIN_ROLE = "admin"
PROFESSIONAL_ROLE = "professional"

PROFESSIONAL_PERMISSIONS = [
    "patients.read",
    "patients.create",
    "patients.update",
    "patients.delete",
]


def seed() -> None:
    db = SessionLocal()

    try:
        # -------------------------------------------------
        # 1. Crear/obtener roles
        # -------------------------------------------------

        admin_role = get_role_by_name(
            db,
            ADMIN_ROLE,
        )

        if admin_role is None:
            admin_role = create_role(
                db,
                ADMIN_ROLE,
            )

        professional_role = get_role_by_name(
            db,
            PROFESSIONAL_ROLE,
        )

        if professional_role is None:
            professional_role = create_role(
                db,
                PROFESSIONAL_ROLE,
            )

        # -------------------------------------------------
        # 2. Crear permisos y asignarlos al administrador
        # -------------------------------------------------

        for code in INITIAL_PERMISSIONS:
            permission = get_permission_by_code(
                db,
                code,
            )

            if permission is None:
                permission = create_permission(
                    db,
                    code,
                )

            assign_permission_to_role(
                db,
                admin_role,
                permission,
            )

        # -------------------------------------------------
        # 3. Asignar permisos de pacientes al profesional
        # -------------------------------------------------

        for code in PROFESSIONAL_PERMISSIONS:
            permission = get_permission_by_code(
                db,
                code,
            )

            if permission is not None:
                assign_permission_to_role(
                    db,
                    professional_role,
                    permission,
                )

        # -------------------------------------------------
        # 4. Asignar rol admin
        # -------------------------------------------------

        admin_user = get_user_by_email(
            db,
            "daniel.api@example.com",
        )

        if admin_user is not None:
            assign_role_to_user(
                db,
                admin_user,
                admin_role,
            )

        # -------------------------------------------------
        # 5. Asignar rol professional
        # -------------------------------------------------

        professional_user = get_user_by_email(
            db,
            "daniel.prueba@example.com",
        )

        if professional_user is not None:
            assign_role_to_user(
                db,
                professional_user,
                professional_role,
            )

    finally:
        db.close()


if __name__ == "__main__":
    seed()