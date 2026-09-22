from fastapi.testclient import TestClient


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