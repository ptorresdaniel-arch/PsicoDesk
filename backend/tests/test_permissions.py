import pytest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.auth.models import Permission
from app.permissions import service as permission_service
from app.permissions.schemas import PermissionCreate


def test_list_permissions_with_permission(
    client: TestClient,
    admin_headers,
    db: Session,
):
    permission = Permission(
        code="test.permission",
    )

    db.add(permission)
    db.commit()

    response = client.get(
        "/permissions",
        headers=admin_headers,
    )

    assert response.status_code == 200

    permissions = response.json()

    assert any(
        item["code"] == "test.permission"
        for item in permissions
    )


def test_list_permissions_without_permission(
    client: TestClient,
    auth_headers,
):
    response = client.get(
        "/permissions",
        headers=auth_headers,
    )

    assert response.status_code == 403

def test_admin_can_create_permission(
    client,
    admin_headers,
):
    response = client.post(
        "/permissions",
        headers=admin_headers,
        json={
            "code": "reports.read",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["code"] == "reports.read"
    assert "id" in data
    
def test_create_existing_permission_returns_409(
    client,
    admin_headers,
):
    first_response = client.post(
        "/permissions",
        headers=admin_headers,
        json={
            "code": "reports.create",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/permissions",
        headers=admin_headers,
        json={
            "code": "reports.create",
        },
    )

    assert second_response.status_code == 409

    assert second_response.json() == {
        "detail": "Ya existe un permiso con ese código."
    }

def test_user_without_permission_cannot_create_permission(
    client,
    auth_headers,
):
    response = client.post(
        "/permissions",
        headers=auth_headers,
        json={
            "code": "forbidden.permission",
        },
    )

    assert response.status_code == 403
    
def test_create_permission_rolls_back_when_commit_fails(
    monkeypatch,
):
    db = MagicMock()

    monkeypatch.setattr(
        permission_service,
        "get_permission_by_code",
        lambda db, code: None,
    )

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    data = PermissionCreate(
        code="rollback.permission",
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        permission_service.create_permission(
            db,
            data,
        )

    db.add.assert_called_once()
    db.rollback.assert_called_once_with()
    db.refresh.assert_not_called()