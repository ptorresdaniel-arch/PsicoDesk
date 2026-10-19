import pytest
from unittest.mock import MagicMock

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.auth.models import(
    Permission,
    Role,
    )
from app.roles import service as role_service
from app.roles.schemas import RoleCreate
from app.roles.service import assign_permission_to_role

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
    
def test_assign_permission_to_role(
    db,
):
    role = Role(
        name="permission-test-role",
    )

    permission = Permission(
        code="permission.test",
    )

    db.add_all([
        role,
        permission,
    ])
    db.commit()
    db.refresh(role)
    db.refresh(permission)

    assign_permission_to_role(
        db,
        role,
        permission,
    )

    db.refresh(role)

    assert permission in role.permissions
    
def test_assign_permission_to_role(
    db,
):
    role = Role(
        name="permission-test-role",
    )

    permission = Permission(
        code="permission.test",
    )

    db.add_all([
        role,
        permission,
    ])
    db.commit()
    db.refresh(role)
    db.refresh(permission)

    assign_permission_to_role(
        db,
        role,
        permission,
    )

    db.refresh(role)

    assert permission in role.permissions
    
def test_admin_can_assign_permission_to_role(
    client,
    admin_headers,
    db,
):
    role = Role(
        name="role-permission-api",
    )

    permission = Permission(
        code="api.test.permission",
    )

    db.add_all([
        role,
        permission,
    ])
    db.commit()
    db.refresh(role)
    db.refresh(permission)

    response = client.post(
        f"/roles/{role.id}/permissions/{permission.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    permissions = response.json()

    assert len(permissions) == 1
    assert permissions[0]["id"] == str(permission.id)
    assert permissions[0]["code"] == "api.test.permission"
    
def test_assign_permission_to_nonexistent_role(
    client,
    admin_headers,
    db,
):
    permission = Permission(
        code="permission.missing.role",
    )

    db.add(permission)
    db.commit()
    db.refresh(permission)

    response = client.post(
        f"/roles/00000000-0000-0000-0000-000000000000/"
        f"permissions/{permission.id}",
        headers=admin_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Rol no encontrado."
    }
    
def test_assign_nonexistent_permission_to_role(
    client,
    admin_headers,
    db,
):
    role = Role(
        name="role-missing-permission",
    )

    db.add(role)
    db.commit()
    db.refresh(role)

    response = client.post(
        f"/roles/{role.id}/permissions/"
        "00000000-0000-0000-0000-000000000000",
        headers=admin_headers,
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Permiso no encontrado."
    }
    
def test_user_without_permission_cannot_assign_permission_to_role(
    client,
    auth_headers,
    db,
):
    role = Role(
        name="protected-permission-role",
    )

    permission = Permission(
        code="protected.permission",
    )

    db.add_all([
        role,
        permission,
    ])
    db.commit()
    db.refresh(role)
    db.refresh(permission)

    response = client.post(
        f"/roles/{role.id}/permissions/{permission.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403
    
def test_admin_can_remove_permission_from_role(
    client,
    admin_headers,
    db,
):
    role = Role(
        name="role-remove-permission-api",
    )

    permission = Permission(
        code="api.remove.permission",
    )

    db.add_all([
        role,
        permission,
    ])
    db.commit()
    db.refresh(role)
    db.refresh(permission)

    assign_response = client.post(
        f"/roles/{role.id}/permissions/{permission.id}",
        headers=admin_headers,
    )

    assert assign_response.status_code == 200

    response = client.delete(
        f"/roles/{role.id}/permissions/{permission.id}",
        headers=admin_headers,
    )

    assert response.status_code == 200

    permissions = response.json()

    assert permissions == []

def test_remove_permission_from_nonexistent_role(
    client,
    admin_headers,
    db,
):
    permission = Permission(
        code="remove.permission.missing.role",
    )

    db.add(permission)
    db.commit()
    db.refresh(permission)

    response = client.delete(
        f"/roles/00000000-0000-0000-0000-000000000000/"
        f"permissions/{permission.id}",
        headers=admin_headers,
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Rol no encontrado."
    }
    
def test_remove_nonexistent_permission_from_role(
    client,
    admin_headers,
    db,
):
    role = Role(
        name="role-remove-missing-permission",
    )

    db.add(role)
    db.commit()
    db.refresh(role)

    response = client.delete(
        f"/roles/{role.id}/permissions/"
        "00000000-0000-0000-0000-000000000000",
        headers=admin_headers,
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "Permiso no encontrado."
    }
    
def test_user_without_permission_cannot_remove_permission_from_role(
    client,
    auth_headers,
    db,
):
    role = Role(
        name="protected-remove-permission-role",
    )

    permission = Permission(
        code="protected.remove.permission",
    )

    db.add_all([
        role,
        permission,
    ])
    db.commit()
    db.refresh(role)
    db.refresh(permission)

    response = client.delete(
        f"/roles/{role.id}/permissions/{permission.id}",
        headers=auth_headers,
    )

    assert response.status_code == 403

def test_create_role_rolls_back_when_commit_fails(
    monkeypatch,
):
    db = MagicMock()

    monkeypatch.setattr(
        role_service,
        "get_role_by_name",
        lambda db, name: None,
    )

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    data = RoleCreate(
        name="rollback-role",
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        role_service.create_role(
            db,
            data,
        )

    db.add.assert_called_once()
    db.rollback.assert_called_once_with()
    db.refresh.assert_not_called()


def test_delete_role_rolls_back_when_commit_fails():
    db = MagicMock()
    role = MagicMock(spec=Role)
    role.users = []

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        role_service.delete_role(
            db,
            role,
        )

    db.delete.assert_called_once_with(role)
    db.rollback.assert_called_once_with()


def test_assign_permission_to_role_rolls_back_when_commit_fails():
    db = MagicMock()
    role = MagicMock(spec=Role)
    permission = MagicMock(spec=Permission)

    role.permissions = []

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        role_service.assign_permission_to_role(
            db,
            role,
            permission,
        )

    db.rollback.assert_called_once_with()


def test_remove_permission_from_role_rolls_back_when_commit_fails():
    db = MagicMock()
    role = MagicMock(spec=Role)
    permission = MagicMock(spec=Permission)

    role.permissions = [permission]

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        role_service.remove_permission_from_role(
            db,
            role,
            permission,
        )

    db.rollback.assert_called_once_with()