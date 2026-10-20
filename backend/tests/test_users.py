import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.users import service as user_service
from app.users.models import User
from app.users.schemas import(
    UserCreate,
    UserUpdate,
    UserPasswordUpdate,
)
from app.auth.models import Role


def test_register_user(
    client: TestClient,
    db: Session,
) -> None:
    response = client.post(
        "/users",
        json={
            "email": "pytest@example.com",
            "password": "password-test-123",
            "first_name": "Pytest",
            "last_name": "Usuario",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "pytest@example.com"
    assert data["first_name"] == "Pytest"
    assert data["last_name"] == "Usuario"
    assert data["is_active"] is True

    assert "password" not in data
    assert "password_hash" not in data

    user = db.scalar(
        select(User).where(
            User.email == "pytest@example.com"
        )
    )

    assert user is not None
    assert user.email == "pytest@example.com"
    assert user.password_hash != "password-test-123"
    
def test_register_user_with_existing_email(
    client: TestClient,
) -> None:
    payload = {
        "email": "duplicate@example.com",
        "password": "password-test-123",
        "first_name": "Usuario",
        "last_name": "Duplicado",
    }

    first_response = client.post(
        "/users",
        json=payload,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/users",
        json=payload,
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Ya existe un usuario con ese email."
    )

def test_list_users_without_permission(
    client: TestClient,
    professional_headers,
) -> None:
    response = client.get(
        "/users/",
        headers=professional_headers,
    )

    assert response.status_code == 403

def test_list_users_with_permission(
    client: TestClient,
    admin_headers,
) -> None:
    response = client.get(
        "/users/",
        headers=admin_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

def test_get_my_profile(
    client,
    auth_headers,
):
    response = client.get(
        "/users/me",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "authenticated@example.com"
    assert data["first_name"] == "Authenticated"

    assert "password_hash" not in data

def test_update_my_profile(
    client,
    auth_headers,
):
    response = client.patch(
        "/users/me",
        headers=auth_headers,
        json={
            "first_name": "Updated",
            "phone": "123456789",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["first_name"] == "Updated"
    assert data["phone"] == "123456789"

def test_change_password_success(
    client,
    auth_headers,
):
    response = client.post(
        "/users/me/password",
        headers=auth_headers,
        json={
            "current_password": "password-test-123",
            "new_password": "new-password-123",
        },
    )

    assert response.status_code == 200

def test_change_password_wrong_current_password(
    client,
    auth_headers,
):
    response = client.post(
        "/users/me/password",
        headers=auth_headers,
        json={
            "current_password": "wrong-password",
            "new_password": "new-password-123",
        },
    )

    assert response.status_code == 401

def test_login_with_new_password(
    client,
    auth_headers,
):
    client.post(
        "/users/me/password",
        headers=auth_headers,
        json={
            "current_password": "password-test-123",
            "new_password": "new-password-123",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "authenticated@example.com",
            "password": "new-password-123",
        },
    )

    assert response.status_code == 200
    
def test_admin_can_disable_user(
    client,
    admin_headers,
):
    user_response = client.post(
        "/users",
        json={
            "email": "disable@example.com",
            "password": "password-test-123",
            "first_name": "Disable",
            "last_name": "User",
        },
    )

    assert user_response.status_code == 201

    user_id = user_response.json()["id"]

    response = client.patch(
        f"/users/{user_id}/status",
        headers=admin_headers,
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False

def test_user_cannot_update_user_status(
    client,
    auth_headers,
):
    response = client.patch(
        "/users/00000000-0000-0000-0000-000000000000/status",
        headers=auth_headers,
        json={
            "is_active": False,
        },
    )

    assert response.status_code == 403
    
def test_get_user_roles_with_permission(
    client,
    admin_headers,
    db,
):
    response = client.get(
        "/users/",
        headers=admin_headers,
    )

    assert response.status_code == 200

    users = response.json()

    user_id = users[0]["id"]

    roles_response = client.get(
        f"/users/{user_id}/roles",
        headers=admin_headers,
    )

    assert roles_response.status_code == 200

    assert isinstance(
        roles_response.json(),
        list,
    )

def test_get_user_roles_without_permission(
    client,
    auth_headers,
):
    response = client.get(
        "/users/00000000-0000-0000-0000-000000000000/roles",
        headers=auth_headers,
    )

    assert response.status_code == 403

def test_get_roles_of_nonexistent_user(
    client,
    admin_headers,
):
    response = client.get(
        "/users/00000000-0000-0000-0000-000000000000/roles",
        headers=admin_headers,
    )

    assert response.status_code == 404

def test_admin_can_assign_role(
    client,
    admin_headers,
    db,
):
    user_response = client.post(
        "/users",
        json={
            "email": "role-user@example.com",
            "password": "password-test-123",
            "first_name": "Role",
            "last_name": "User",
        },
    )

    assert user_response.status_code == 201

    user_id = user_response.json()["id"]

    role = Role(
        name="professional-test-role",
    )

    db.add(role)
    db.commit()
    db.refresh(role)

    response = client.post(
        f"/users/{user_id}/roles",
        headers=admin_headers,
        json={
            "role_id": str(role.id),
        },
    )

    assert response.status_code == 200

    roles = response.json()

    assert len(roles) == 1
    assert roles[0]["name"] == "professional-test-role"

def test_assign_role_to_nonexistent_user(
    client,
    admin_headers,
    db,
):
    role = Role(
        name="role-nonexistent-user",
    )

    db.add(role)
    db.commit()
    db.refresh(role)

    response = client.post(
        "/users/00000000-0000-0000-0000-000000000000/roles",
        headers=admin_headers,
        json={
            "role_id": str(role.id),
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Usuario no encontrado."
    )

def test_assign_nonexistent_role(
    client,
    admin_headers,
):
    user_response = client.post(
        "/users",
        json={
            "email": "missing-role@example.com",
            "password": "password-test-123",
            "first_name": "Missing",
            "last_name": "Role",
        },
    )

    assert user_response.status_code == 201

    user_id = user_response.json()["id"]

    response = client.post(
        f"/users/{user_id}/roles",
        headers=admin_headers,
        json={
            "role_id": (
                "00000000-0000-0000-0000-000000000000"
            ),
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Rol no encontrado."
    )

def test_user_without_permission_cannot_assign_role(
    client,
    auth_headers,
    db,
):
    role = Role(
        name="restricted-role",
    )

    db.add(role)
    db.commit()
    db.refresh(role)

    response = client.post(
        "/users/00000000-0000-0000-0000-000000000000/roles",
        headers=auth_headers,
        json={
            "role_id": str(role.id),
        },
    )

    assert response.status_code == 403

def test_admin_can_remove_role(
    client,
    admin_headers,
    db,
):
    user_response = client.post(
        "/users",
        json={
            "email": "remove-role@example.com",
            "password": "password-test-123",
            "first_name": "Remove",
            "last_name": "Role",
        },
    )

    assert user_response.status_code == 201

    user_id = user_response.json()["id"]

    role = Role(
        name="role-to-remove",
    )

    db.add(role)
    db.commit()
    db.refresh(role)

    assign_response = client.post(
        f"/users/{user_id}/roles",
        headers=admin_headers,
        json={
            "role_id": str(role.id),
        },
    )

    assert assign_response.status_code == 200

    response = client.delete(
        f"/users/{user_id}/roles/{role.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200
    assert response.json() == []

def test_user_without_permission_cannot_remove_role(
    client,
    auth_headers,
):
    response = client.delete(
        "/users/00000000-0000-0000-0000-000000000000/"
        "roles/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )

    assert response.status_code == 403

def test_user_without_permission_cannot_remove_role_from_existing_user(
    client,
    auth_headers,
    db,
):
    user_response = client.post(
        "/users",
        json={
            "email": "target-remove-role@example.com",
            "password": "password-test-123",
            "first_name": "Target",
            "last_name": "Role",
        },
    )

    assert user_response.status_code == 201

    user_id = user_response.json()["id"]

    role = Role(
        name="protected-role",
    )

    db.add(role)
    db.commit()
    db.refresh(role)

    response = client.delete(
        f"/users/{user_id}/roles/{role.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403

def test_create_user_rolls_back_when_commit_fails():
    db = MagicMock()

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    data = UserCreate(
        email="rollback@example.com",
        password="password-test-123",
        first_name="Rollback",
        last_name="User",
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        user_service.create_user(
            db,
            data,
        )

    db.add.assert_called_once()
    db.rollback.assert_called_once_with()
    db.refresh.assert_not_called()


def test_update_last_login_rolls_back_when_commit_fails():
    db = MagicMock()
    user = MagicMock(spec=User)

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        user_service.update_last_login(
            db,
            user,
        )

    db.rollback.assert_called_once_with()
    db.refresh.assert_not_called()


def test_update_user_rolls_back_when_commit_fails():
    db = MagicMock()
    user = MagicMock(spec=User)

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    data = UserUpdate(
        first_name="Actualizado",
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        user_service.update_user(
            db,
            user,
            data,
        )

    db.rollback.assert_called_once_with()
    db.refresh.assert_not_called()


def test_change_password_rolls_back_when_commit_fails(
    monkeypatch,
):
    db = MagicMock()
    user = MagicMock(spec=User)
    user.password_hash = "hash-anterior"

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    monkeypatch.setattr(
        user_service,
        "verify_password",
        lambda password, password_hash: True,
    )

    monkeypatch.setattr(
        user_service,
        "hash_password",
        lambda password: "hash-nuevo",
    )

    data = UserPasswordUpdate(
        current_password="password-anterior",
        new_password="password-nuevo",
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        user_service.change_password(
            db,
            user,
            data,
        )

    db.rollback.assert_called_once_with()
    db.refresh.assert_not_called()


def test_update_user_status_rolls_back_when_commit_fails():
    db = MagicMock()
    user = MagicMock(spec=User)

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        user_service.update_user_status(
            db,
            user,
            False,
        )

    db.rollback.assert_called_once_with()
    db.refresh.assert_not_called()


def test_assign_role_to_user_rolls_back_when_commit_fails():
    db = MagicMock()
    user = MagicMock(spec=User)
    role = MagicMock(spec=Role)

    user.roles = []

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        user_service.assign_role_to_user(
            db,
            user,
            role,
        )

    db.rollback.assert_called_once_with()


def test_remove_role_from_user_rolls_back_when_commit_fails():
    db = MagicMock()
    user = MagicMock(spec=User)
    role = MagicMock(spec=Role)

    user.roles = [role]

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        user_service.remove_role_from_user(
            db,
            user,
            role,
        )

    db.rollback.assert_called_once_with()