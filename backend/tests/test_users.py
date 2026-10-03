from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.users.models import User


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