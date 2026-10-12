from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.models import Permission


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
    
