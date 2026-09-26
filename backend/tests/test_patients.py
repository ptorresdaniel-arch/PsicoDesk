from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta

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
    
def test_patient_profile(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Perfil",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    response = client.get(
        f"/patients/{patient_id}/profile",
        headers=professional_headers,
    )

    assert response.status_code == 200

    profile = response.json()

    assert profile["id"] == patient_id
    assert profile["first_name"] == "Paciente"
    assert profile["last_name"] == "Perfil"
    assert "upcoming_appointments" in profile
    assert "clinical_sessions" in profile
    assert "last_session" in profile
    
def test_patient_profile_with_related_data(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Completo",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    start = datetime.now(timezone.utc) + timedelta(days=3)
    end = start + timedelta(minutes=50)

    appointment_response = client.post(
        "/appointments",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
    )

    assert appointment_response.status_code == 201

    appointment_id = appointment_response.json()["id"]

    client.patch(
        f"/appointments/{appointment_id}",
        headers=professional_headers,
        json={"status": "confirmed"},
    )

    client.patch(
        f"/appointments/{appointment_id}",
        headers=professional_headers,
        json={"status": "completed"},
    )

    session_response = client.post(
        f"/appointments/{appointment_id}/clinical-session",
        headers=professional_headers,
    )

    assert session_response.status_code == 201

    profile_response = client.get(
        f"/patients/{patient_id}/profile",
        headers=professional_headers,
    )

    assert profile_response.status_code == 200

    profile = profile_response.json()

    assert len(profile["clinical_sessions"]) == 1
    assert profile["last_session"] is not None

    assert len(profile["upcoming_appointments"]) == 0
    
def test_search_patient_by_name(
    client,
    professional_headers,
):
    create_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Juan",
            "last_name": "Pérez",
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        "/patients?search=Juan",
        headers=professional_headers,
    )

    assert response.status_code == 200

    patients = response.json()

    assert len(patients) == 1
    assert patients[0]["first_name"] == "Juan"
    
def test_search_patient_by_identification(
    client,
    professional_headers,
):
    create_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Ana",
            "last_name": "Gómez",
            "identification": "12345678-9",
        },
    )

    assert create_response.status_code == 201

    response = client.get(
        "/patients?search=12345678",
        headers=professional_headers,
    )

    assert response.status_code == 200

    patients = response.json()

    assert len(patients) == 1
    assert patients[0]["identification"] == "12345678-9"
    
def test_filter_patients_by_active_status(
    client,
    professional_headers,
):
    active_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Activo",
            "last_name": "Paciente",
        },
    )

    assert active_response.status_code == 201

    inactive_id = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Inactivo",
            "last_name": "Paciente",
        },
    ).json()["id"]

    update_response = client.patch(
        f"/patients/{inactive_id}",
        headers=professional_headers,
        json={
            "is_active": False,
        },
    )

    assert update_response.status_code == 200

    response = client.get(
        "/patients?is_active=false",
        headers=professional_headers,
    )

    assert response.status_code == 200

    patients = response.json()
    print(patients)
    assert len(patients) >= 1
    for patient in patients:
        assert patient["is_active"] is False
        assert all(patient["last_name"] == "Paciente" for patient in patients)