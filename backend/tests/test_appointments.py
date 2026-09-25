from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient


def test_create_appointment(
    client: TestClient,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Agenda",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    start = datetime.now(timezone.utc) + timedelta(days=1)
    end = start + timedelta(minutes=50)

    response = client.post(
        "/appointments",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "title": "Primera consulta",
            "reason": "Evaluación inicial",
            "notes": "Paciente nuevo",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["patient_id"] == patient_id
    assert data["status"] == "scheduled"
    assert data["title"] == "Primera consulta"
    
from datetime import datetime, timedelta, timezone


def test_professional_cannot_create_appointment_for_other_professional_patient(
    client,
    professional_factory,
):
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

    start = datetime.now(timezone.utc) + timedelta(days=1)
    end = start + timedelta(minutes=50)

    # Profesional B intenta agendarlo
    response = client.post(
        "/appointments",
        headers=professional_b,
        json={
            "patient_id": patient_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "title": "Intento inválido",
        },
    )

    assert response.status_code == 404
def test_cannot_create_overlapping_appointment(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Horario",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    start = datetime.now(timezone.utc) + timedelta(days=1)
    end = start + timedelta(hours=1)

    first = client.post(
        "/appointments",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "title": "Primera cita",
        },
    )

    assert first.status_code == 201

    conflict_start = start + timedelta(minutes=30)
    conflict_end = end + timedelta(minutes=30)

    second = client.post(
        "/appointments",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "start_time": conflict_start.isoformat(),
            "end_time": conflict_end.isoformat(),
            "title": "Cita conflictiva",
        },
    )

    assert second.status_code == 400

def test_appointment_crud(
    client,
    professional_headers,
):
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

    start = datetime.now(timezone.utc) + timedelta(days=2)
    end = start + timedelta(minutes=45)

    create_response = client.post(
        "/appointments",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "title": "Cita CRUD",
            "reason": "Prueba",
        },
    )

    assert create_response.status_code == 201

    appointment_id = create_response.json()["id"]

    # Obtener
    get_response = client.get(
        f"/appointments/{appointment_id}",
        headers=professional_headers,
    )

    assert get_response.status_code == 200

    # Listar
    list_response = client.get(
        "/appointments",
        headers=professional_headers,
    )

    assert list_response.status_code == 200

    assert any(
        item["id"] == appointment_id
        for item in list_response.json()
    )

    # Actualizar
    update_response = client.patch(
        f"/appointments/{appointment_id}",
        headers=professional_headers,
        json={
            "status": "confirmed",
            "notes": "Paciente confirmado.",
        },
    )

    assert update_response.status_code == 200

    updated = update_response.json()

    assert updated["status"] == "confirmed"
    assert updated["notes"] == "Paciente confirmado."

    # Eliminar
    delete_response = client.delete(
        f"/appointments/{appointment_id}",
        headers=professional_headers,
    )

    assert delete_response.status_code == 204

    # Confirmar eliminación
    final_response = client.get(
        f"/appointments/{appointment_id}",
        headers=professional_headers,
    )

    assert final_response.status_code == 404

def test_get_appointments_by_date_range(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Calendario",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    base_date = datetime.now(timezone.utc) + timedelta(days=10)

    # Cita dentro del rango
    inside_start = base_date.replace(
        hour=10,
        minute=0,
    )
    inside_end = inside_start + timedelta(
        minutes=50
    )

    inside_response = client.post(
        "/appointments",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "start_time": inside_start.isoformat(),
            "end_time": inside_end.isoformat(),
            "title": "Dentro del rango",
        },
    )

    assert inside_response.status_code == 201

    # Consulta del día
    response = client.get(
        "/appointments/calendar",
        headers=professional_headers,
        params={
            "start_date": (
                base_date.replace(
                    hour=0,
                    minute=0,
                )
                .isoformat().replace("+00:00", "Z")
            ),
            "end_date": (
                base_date.replace(
                    hour=23,
                    minute=59,
                )
                .isoformat().replace("+00:00", "Z")
            ),
        },
    )
    
    print(response.json())
    assert response.status_code == 200

    appointments = response.json()

    assert len(appointments) == 1
    assert appointments[0]["title"] == "Dentro del rango"
    
def test_update_appointment_status_allowed(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Estado",
        },
    )

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

    appointment_id = appointment_response.json()["id"]

    response = client.patch(
        f"/appointments/{appointment_id}",
        headers=professional_headers,
        json={
            "status": "confirmed",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"
    
def test_update_appointment_status_allowed(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Estado",
        },
    )

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

    appointment_id = appointment_response.json()["id"]

    response = client.patch(
        f"/appointments/{appointment_id}",
        headers=professional_headers,
        json={
            "status": "confirmed",
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "confirmed"
    
def test_create_clinical_session_from_completed_appointment(
    client,
    professional_headers,
):
    # Crear paciente
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Integracion",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    # Crear cita
    start = datetime.now(timezone.utc) + timedelta(days=5)
    end = start + timedelta(minutes=50)

    appointment_response = client.post(
        "/appointments",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "title": "Sesión integración",
        },
    )

    assert appointment_response.status_code == 201

    appointment_id = appointment_response.json()["id"]

    # Pasar a confirmada
    confirm_response = client.patch(
        f"/appointments/{appointment_id}",
        headers=professional_headers,
        json={
            "status": "confirmed",
        },
    )

    assert confirm_response.status_code == 200

    # Pasar a realizada
    complete_response = client.patch(
        f"/appointments/{appointment_id}",
        headers=professional_headers,
        json={
            "status": "completed",
        },
    )

    assert complete_response.status_code == 200

    # Crear sesión clínica
    session_response = client.post(
        f"/appointments/{appointment_id}/clinical-session",
        headers=professional_headers,
    )

    assert session_response.status_code == 201

    session = session_response.json()

    assert session["patient_id"] == patient_id
    assert session["appointment_id"] == appointment_id
    assert session["duration_minutes"] == 50

def test_cannot_create_clinical_session_from_pending_appointment(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Pendiente",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    start = datetime.now(timezone.utc) + timedelta(days=6)
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

    response = client.post(
        f"/appointments/{appointment_id}/clinical-session",
        headers=professional_headers,
    )

    assert response.status_code == 400
    
def test_cannot_create_second_clinical_session_for_same_appointment(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Duplicado",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    start = datetime.now(timezone.utc) + timedelta(days=7)
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

    first_response = client.post(
        f"/appointments/{appointment_id}/clinical-session",
        headers=professional_headers,
    )

    assert first_response.status_code == 201

    second_response = client.post(
        f"/appointments/{appointment_id}/clinical-session",
        headers=professional_headers,
    )

    assert second_response.status_code == 400