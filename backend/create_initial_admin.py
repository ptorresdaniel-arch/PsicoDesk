
from getpass import getpass

from sqlalchemy import select

# Registra los modelos de la aplicación en SQLAlchemy.
import app.main  # noqa: F401

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.auth.models import Permission, Role
from app.users.models import User


PERMISSION_CODES = [
    "users.read",
    "users.create",
    "users.update",
    "users.delete",
    "patients.read",
    "patients.create",
    "patients.update",
    "patients.delete",
    "appointments.read",
    "appointments.create",
    "appointments.update",
    "appointments.delete",
    "clinical_sessions.read",
    "clinical_sessions.create",
    "clinical_sessions.update",
    "clinical_sessions.delete",
    "clinical_notes.read",
    "clinical_notes.create",
]

ROLE_NAME = "administrador-inicial"


def main() -> None:
    email = input("Email del administrador: ").strip().lower()
    first_name = input("Nombre: ").strip()
    last_name = input("Apellido: ").strip()

    if not email or not first_name or not last_name:
        raise ValueError(
            "El email, nombre y apellido son obligatorios."
        )

    password = getpass("Contraseña (mínimo 12 caracteres): ")
    confirmation = getpass("Confirma la contraseña: ")

    if len(password) < 12:
        raise ValueError(
            "La contraseña debe tener al menos 12 caracteres."
        )

    if password != confirmation:
        raise ValueError("Las contraseñas no coinciden.")

    db = SessionLocal()

    try:
        existing_user = db.scalar(
            select(User).where(User.email == email)
        )

        if existing_user is not None:
            raise ValueError(
                "Ese email ya existe. No se modificó el usuario."
            )

        role = db.scalar(
            select(Role).where(Role.name == ROLE_NAME)
        )

        if role is not None and role.users:
            raise ValueError(
                "El rol ya está asignado a usuarios. "
                "No se modificará para evitar cambios de permisos "
                "a otros usuarios."
            )

        if role is None:
            role = Role(name=ROLE_NAME)
            db.add(role)
            db.flush()

        for code in PERMISSION_CODES:
            permission = db.scalar(
                select(Permission).where(
                    Permission.code == code
                )
            )

            if permission is None:
                permission = Permission(code=code)
                db.add(permission)
                db.flush()

            if permission not in role.permissions:
                role.permissions.append(permission)

        user = User(
            email=email,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
            is_active=True,
            roles=[role],
        )

        db.add(user)
        db.commit()

        print("\nAdministrador creado correctamente.")
        print(f"Email: {email}")
        print(f"Rol: {ROLE_NAME}")
        print(f"Permisos asignados: {len(PERMISSION_CODES)}")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
