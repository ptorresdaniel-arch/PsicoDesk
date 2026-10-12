from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.auth.models import Role


def test_list_roles_with_permission(
    client: TestClient,
    admin_headers,
    db: Session,
):
    role = Role(
        name="test-role",
    )

    db.add(role)
    db.commit()

    response = client.get(
        "/roles",
        headers=admin_headers,
    )

    assert response.status_code == 200

    roles = response.json()

    assert any(
        item["name"] == "test-role"
        for item in roles
    )


def test_list_roles_without_permission(
    client: TestClient,
    auth_headers,
):
    response = client.get(
        "/roles",
        headers=auth_headers,
    )

    assert response.status_code == 403

def test_admin_can_create_role(
    client,
    admin_headers,
):
    response = client.post(
        "/roles",
        headers=admin_headers,
        json={
            "name": "psychologist-manager",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "psychologist-manager"

def test_user_without_permission_cannot_create_role(
    client,
    auth_headers,
):
    response = client.post(
        "/roles",
        headers=auth_headers,
        json={
            "name": "forbidden-role",
        },
    )

    assert response.status_code == 403

def test_create_existing_role_returns_409(
    client,
    admin_headers,
):
    first_response = client.post(
        "/roles",
        headers=admin_headers,
        json={
            "name": "duplicate-role",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/roles",
        headers=admin_headers,
        json={
            "name": "duplicate-role",
        },
    )

    assert second_response.status_code == 409

    assert second_response.json() == {
        "detail": "Ya existe un rol con ese nombre."
    }

def test_admin_can_delete_role(
    client,
    admin_headers,
    db,
):
    role = Role(
        name="role-to-delete",
    )

    db.add(role)
    db.commit()
    db.refresh(role)

    response = client.delete(
        f"/roles/{role.id}",
        headers=admin_headers,
    )

    assert response.status_code == 204

def test_delete_nonexistent_role(
    client,
    admin_headers,
):
    response = client.delete(
        "/roles/00000000-0000-0000-0000-000000000000",
        headers=admin_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Rol no encontrado."
    }

def test_cannot_delete_role_with_users(
    client,
    admin_headers,
    db,
):
    user_response = client.post(
        "/users",
        json={
            "email": "role-owner@example.com",
            "password": "password-test-123",
            "first_name": "Role",
            "last_name": "Owner",
        },
    )

    assert user_response.status_code == 201

    user_id = user_response.json()["id"]

    role = Role(
        name="role-with-user",
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
        f"/roles/{role.id}",
        headers=admin_headers,
    )

    assert response.status_code == 409

def test_user_without_permission_cannot_delete_role(
    client,
    auth_headers,
):
    response = client.delete(
        "/roles/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
    )

    assert response.status_code == 403