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