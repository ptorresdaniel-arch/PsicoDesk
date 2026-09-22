from fastapi.testclient import TestClient


def test_create_patient_without_permission(
    client: TestClient,
    auth_headers: dict[str, str],
) -> None:
    response = client.post(
        "/patients",
        headers=auth_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Sin Permiso",
        },
    )

    assert response.status_code == 403
    assert response.json() == {
        "detail": "No tienes permiso para realizar esta acción."
    }

def test_create_patient(
    client: TestClient,
    professional_headers: dict[str, str],
) -> None:
    response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Automatizado",
            "identification": "PYTEST-001",
            "birth_date": "1990-05-15",
            "email": "patient@example.com",
            "phone": "+56912345678",
            "notes": "Creado por pytest.",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["first_name"] == "Paciente"
    assert data["last_name"] == "Automatizado"
    assert data["identification"] == "PYTEST-001"
    assert data["is_active"] is True

    assert "id" in data
    assert "professional_id" in data
    assert "created_at" in data
    assert "updated_at" in data
    
def test_patient_crud(
    client: TestClient,
    professional_headers: dict[str, str],
) -> None:
    # CREATE
    create_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Ana",
            "last_name": "Prueba",
            "phone": "+56911111111",
        },
    )

    assert create_response.status_code == 201

    patient = create_response.json()
    patient_id = patient["id"]

    # LIST
    list_response = client.get(
        "/patients",
        headers=professional_headers,
    )

    assert list_response.status_code == 200

    patients = list_response.json()

    assert len(patients) == 1
    assert patients[0]["id"] == patient_id

    # GET
    get_response = client.get(
        f"/patients/{patient_id}",
        headers=professional_headers,
    )

    assert get_response.status_code == 200
    assert get_response.json()["id"] == patient_id

    # PATCH
    patch_response = client.patch(
        f"/patients/{patient_id}",
        headers=professional_headers,
        json={
            "phone": "+56922222222",
            "notes": "Actualizado por pytest.",
        },
    )

    assert patch_response.status_code == 200

    updated_patient = patch_response.json()

    assert updated_patient["phone"] == "+56922222222"
    assert updated_patient["notes"] == "Actualizado por pytest."
    assert updated_patient["first_name"] == "Ana"
    assert updated_patient["last_name"] == "Prueba"

    # DELETE
    delete_response = client.delete(
        f"/patients/{patient_id}",
        headers=professional_headers,
    )

    assert delete_response.status_code == 204

    # El recurso ya no debe existir.
    get_deleted_response = client.get(
        f"/patients/{patient_id}",
        headers=professional_headers,
    )

    assert get_deleted_response.status_code == 404
    
def test_professional_cannot_access_another_professionals_patient(
    client: TestClient,
    professional_factory,
) -> None:
    professional_a = professional_factory()
    professional_b = professional_factory()

    create_response = client.post(
        "/patients",
        headers=professional_a,
        json={
            "first_name": "Paciente",
            "last_name": "Privado",
        },
    )

    assert create_response.status_code == 201

    patient_id = create_response.json()["id"]

    # B no debe ver el paciente de A en su listado.
    list_response = client.get(
        "/patients",
        headers=professional_b,
    )

    assert list_response.status_code == 200
    assert list_response.json() == []

    # B tampoco debe poder obtenerlo directamente.
    get_response = client.get(
        f"/patients/{patient_id}",
        headers=professional_b,
    )

    assert get_response.status_code == 404

    # Ni modificarlo.
    patch_response = client.patch(
        f"/patients/{patient_id}",
        headers=professional_b,
        json={
            "notes": "Intento de modificación ajena."
        },
    )

    assert patch_response.status_code == 404

    # Ni eliminarlo.
    delete_response = client.delete(
        f"/patients/{patient_id}",
        headers=professional_b,
    )

    assert delete_response.status_code == 404

    # Y comprobamos que el paciente sigue existiendo para A.
    owner_response = client.get(
        f"/patients/{patient_id}",
        headers=professional_a,
    )

    assert owner_response.status_code == 200