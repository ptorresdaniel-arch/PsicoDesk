from uuid import uuid4
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.users.models import User
from app.core.security import create_access_token

def test_login_success(
    client: TestClient,
) -> None:
    # Arrange: crear un usuario para esta prueba
    register_response = client.post(
        "/users",
        json={
            "email": "login@example.com",
            "password": "password-test-123",
            "first_name": "Login",
            "last_name": "Test",
        },
    )

    assert register_response.status_code == 201

    # Act: iniciar sesión
    response = client.post(
        "/auth/login",
        json={
            "email": "login@example.com",
            "password": "password-test-123",
        },
    )

    # Assert
    assert response.status_code == 200

    data = response.json()

    assert isinstance(data["access_token"], str)
    assert data["access_token"]
    assert data["token_type"] == "bearer"


def test_login_wrong_password(
    client: TestClient,
) -> None:
    client.post(
        "/users",
        json={
            "email": "wrong-password@example.com",
            "password": "password-test-123",
            "first_name": "Wrong",
            "last_name": "Password",
        },
    )

    response = client.post(
        "/auth/login",
        json={
            "email": "wrong-password@example.com",
            "password": "incorrect-password",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Email o contraseña incorrectos."
    }


def test_login_nonexistent_user(
    client: TestClient,
) -> None:
    response = client.post(
        "/auth/login",
        json={
            "email": "does-not-exist@example.com",
            "password": "password-test-123",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "Email o contraseña incorrectos."
    }

def test_get_current_user(
    client: TestClient,
    auth_headers,
) -> None:
    response = client.get(
        "/auth/me",
        headers=auth_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["email"] == "authenticated@example.com"
    assert data["first_name"] == "Authenticated"
    assert data["last_name"] == "User"

    assert "password" not in data
    assert "password_hash" not in data

def test_get_current_user_without_authentication(
    client: TestClient,
) -> None:
    response = client.get("/auth/me")

    assert response.status_code == 401

def test_login_inactive_user(
    client: TestClient,
    db: Session,
) -> None:
    email = "inactive@example.com"
    password = "password-test-123"

    register_response = client.post(
        "/users",
        json={
            "email": email,
            "password": password,
            "first_name": "Inactive",
            "last_name": "User",
        },
    )

    assert register_response.status_code == 201

    user = db.scalar(
        select(User).where(
            User.email == email,
        )
    )

    assert user is not None

    user.is_active = False
    db.commit()

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == (
        "El usuario está inactivo."
    )

def test_login_updates_last_login(
    client: TestClient,
    db: Session,
) -> None:
    email = "last-login@example.com"
    password = "password-test-123"

    register_response = client.post(
        "/users",
        json={
            "email": email,
            "password": password,
            "first_name": "Last",
            "last_name": "Login",
        },
    )

    assert register_response.status_code == 201

    user = db.scalar(
        select(User).where(
            User.email == email,
        )
    )

    assert user is not None
    assert user.last_login_at is None

    response = client.post(
        "/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )

    assert response.status_code == 200

    db.refresh(user)

    assert user.last_login_at is not None

def test_get_current_user_with_invalid_token(
    client: TestClient,
) -> None:
    response = client.get(
        "/auth/me",
        headers={
            "Authorization": "Bearer token-invalido",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "No se pudo validar la autenticación.",
    }

def test_get_current_user_with_nonexistent_user(
    client: TestClient,
) -> None:
    token = create_access_token(uuid4())

    response = client.get(
        "/auth/me",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401
    assert response.json() == {
        "detail": "No se pudo validar la autenticación.",
    }