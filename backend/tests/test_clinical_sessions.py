from datetime import datetime, timezone

from fastapi.testclient import TestClient


def test_create_clinical_session(
    client: TestClient,
    professional_headers,
) -> None:
    # Crear paciente
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Sesión",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    # Crear sesión clínica
    session_response = client.post(
        "/clinical-sessions",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "session_date": datetime.now(
                timezone.utc
            ).isoformat(),
            "duration_minutes": 50,
            "summary": "Primera entrevista",
            "notes": "Evaluación inicial.",
        },
    )

    assert session_response.status_code == 201

    data = session_response.json()

    assert data["patient_id"] == patient_id
    assert data["duration_minutes"] == 50
    assert data["summary"] == "Primera entrevista"
    assert data["notes"] == "Evaluación inicial."
    
from datetime import datetime, timezone

from fastapi.testclient import TestClient


def test_professional_cannot_access_another_professionals_session(
    client: TestClient,
    professional_factory,
) -> None:
    professional_a = professional_factory()
    professional_b = professional_factory()

    # Profesional A crea paciente
    patient_response = client.post(
        "/patients",
        headers=professional_a,
        json={
            "first_name": "Paciente",
            "last_name": "Privado",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    # Profesional A crea sesión
    session_response = client.post(
        "/clinical-sessions",
        headers=professional_a,
        json={
            "patient_id": patient_id,
            "session_date": datetime.now(
                timezone.utc
            ).isoformat(),
            "duration_minutes": 45,
            "summary": "Sesión privada",
            "notes": "Información confidencial.",
        },
    )

    assert session_response.status_code == 201

    session_id = session_response.json()["id"]

    # Profesional B intenta obtener la sesión
    get_response = client.get(
        f"/clinical-sessions/{session_id}",
        headers=professional_b,
    )

    assert get_response.status_code == 404

    # Profesional B intenta modificarla
    patch_response = client.patch(
        f"/clinical-sessions/{session_id}",
        headers=professional_b,
        json={
            "notes": "Intento de acceso.",
        },
    )

    assert patch_response.status_code == 404

    # Profesional B intenta eliminarla
    delete_response = client.delete(
        f"/clinical-sessions/{session_id}",
        headers=professional_b,
    )

    assert delete_response.status_code == 404

    # Confirmamos que A sigue viendo su sesión
    owner_response = client.get(
        f"/clinical-sessions/{session_id}",
        headers=professional_a,
    )

    assert owner_response.status_code == 200
    
from datetime import datetime, timezone


def test_clinical_session_crud(
    client: TestClient,
    professional_headers,
) -> None:
    # Crear paciente
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "CRUD",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    # Crear sesión
    create_response = client.post(
        "/clinical-sessions",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "session_date": datetime.now(
                timezone.utc
            ).isoformat(),
            "duration_minutes": 60,
            "summary": "Sesión inicial",
            "notes": "Notas iniciales.",
        },
    )

    assert create_response.status_code == 201

    session_id = create_response.json()["id"]

    # Listar sesiones del paciente
    list_response = client.get(
        f"/clinical-sessions/patient/{patient_id}",
        headers=professional_headers,
    )

    assert list_response.status_code == 200

    sessions = list_response.json()

    assert len(sessions) == 1
    assert sessions[0]["id"] == session_id

    # Actualizar
    update_response = client.patch(
        f"/clinical-sessions/{session_id}",
        headers=professional_headers,
        json={
            "duration_minutes": 90,
            "notes": "Notas actualizadas.",
        },
    )

    assert update_response.status_code == 200

    updated = update_response.json()

    assert updated["duration_minutes"] == 90
    assert updated["notes"] == "Notas actualizadas."

    # Eliminar
    delete_response = client.delete(
        f"/clinical-sessions/{session_id}",
        headers=professional_headers,
    )

    assert delete_response.status_code == 204

    # Confirmar eliminación
    get_response = client.get(
        f"/clinical-sessions/{session_id}",
        headers=professional_headers,
    )

    assert get_response.status_code == 404