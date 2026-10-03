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
    
def test_update_appointment_status_invalid_transition(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "EstadoInvalido",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    start = datetime.now(timezone.utc) + timedelta(days=4)
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

    # scheduled -> confirmed: válido
    confirm_response = client.patch(
        f"/appointments/{appointment_id}",
        headers=professional_headers,
        json={
            "status": "confirmed",
        },
    )

    assert confirm_response.status_code == 200

    # confirmed -> scheduled: inválido
    invalid_response = client.patch(
        f"/appointments/{appointment_id}",
        headers=professional_headers,
        json={
            "status": "scheduled",
        },
    )

    assert invalid_response.status_code == 400
     
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
    
def test_calendar_returns_patient_data(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Ana",
            "last_name": "Calendario",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    start = datetime.now(timezone.utc) + timedelta(days=2)
    end = start + timedelta(minutes=50)

    appointment_response = client.post(
        "/appointments",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "title": "Sesión inicial",
        },
    )

    assert appointment_response.status_code == 201

    response = client.get(
        "/appointments/calendar",
        headers=professional_headers,
        params={
            "start_date": (
                start.replace(
                    hour=0,
                    minute=0,
                )
                .isoformat()
            ),
            "end_date": (
                start.replace(
                    hour=23,
                    minute=59,
                )
                .isoformat()
            ),
        },
    )

    assert response.status_code == 200

    appointments = response.json()

    assert len(appointments) == 1

    appointment = appointments[0]

    assert appointment["patient_name"] == "Ana Calendario"
    assert appointment["title"] == "Sesión inicial"
    assert appointment["status"] == "scheduled"
    
def test_calendar_excludes_out_of_range_appointments(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Rango",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    outside_start = datetime.now(timezone.utc) + timedelta(days=10)
    outside_end = outside_start + timedelta(minutes=50)

    client.post(
        "/appointments",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "start_time": outside_start.isoformat(),
            "end_time": outside_end.isoformat(),
        },
    )

    target_day = datetime.now(timezone.utc) + timedelta(days=2)

    response = client.get(
        "/appointments/calendar",
        headers=professional_headers,
        params={
            "start_date": (
                target_day.replace(
                    hour=0,
                    minute=0,
                )
                .isoformat()
            ),
            "end_date": (
                target_day.replace(
                    hour=23,
                    minute=59,
                )
                .isoformat()
            ),
        },
    )

    assert response.status_code == 200

    assert response.json() == []
    
def test_appointment_availability_free_slot(
    client,
    professional_headers,
):
    start = datetime.now(timezone.utc) + timedelta(days=5)
    end = start + timedelta(minutes=50)

    response = client.get(
        "/appointments/availability",
        headers=professional_headers,
        params={
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["available"] is True

def test_appointment_availability_conflict(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Disponibilidad",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    start = datetime.now(timezone.utc) + timedelta(days=5)
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

    response = client.get(
        "/appointments/availability",
        headers=professional_headers,
        params={
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["available"] is False

def test_appointment_summary_empty(
    client,
    professional_headers,
):
    response = client.get(
        "/appointments/summary",
        headers=professional_headers,
    )

    assert response.status_code == 200

    summary = response.json()

    assert summary["total"] == 0
    assert summary["scheduled"] == 0
    assert summary["confirmed"] == 0
    assert summary["completed"] == 0
    assert summary["cancelled"] == 0
    assert summary["no_show"] == 0

def test_appointment_summary_with_statuses(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Resumen",
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

    # scheduled inicial
    summary_response = client.get(
        "/appointments/summary",
        headers=professional_headers,
    )

    assert summary_response.json()["scheduled"] == 1

    # confirmed
    client.patch(
        f"/appointments/{appointment_id}",
        headers=professional_headers,
        json={
            "status": "confirmed",
        },
    )

    summary_response = client.get(
        "/appointments/summary",
        headers=professional_headers,
    )

    assert summary_response.json()["confirmed"] == 1
    
def test_cannot_update_appointment_with_invalid_time_range(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "HorarioInvalido",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    start = datetime.now(timezone.utc) + timedelta(days=8)
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

    response = client.patch(
        f"/appointments/{appointment_id}",
        headers=professional_headers,
        json={
            "start_time": end.isoformat(),
            "end_time": start.isoformat(),
        },
    )

    assert response.status_code == 400
    
def test_cannot_update_appointment_into_existing_conflict(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "ConflictoUpdate",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    base = datetime.now(timezone.utc) + timedelta(days=9)

    first_start = base.replace(
        hour=10,
        minute=0,
        second=0,
        microsecond=0,
    )
    first_end = first_start + timedelta(minutes=50)

    second_start = base.replace(
        hour=12,
        minute=0,
        second=0,
        microsecond=0,
    )
    second_end = second_start + timedelta(minutes=50)

    first_response = client.post(
        "/appointments",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "start_time": first_start.isoformat(),
            "end_time": first_end.isoformat(),
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/appointments",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "start_time": second_start.isoformat(),
            "end_time": second_end.isoformat(),
        },
    )

    assert second_response.status_code == 201

    second_id = second_response.json()["id"]

    response = client.patch(
        f"/appointments/{second_id}",
        headers=professional_headers,
        json={
            "start_time": first_start.isoformat(),
            "end_time": first_end.isoformat(),
        },
    )

    assert response.status_code == 400

def test_professional_cannot_create_clinical_session_from_another_professional_appointment(
    client,
    professional_factory,
):
    professional_a = professional_factory()
    professional_b = professional_factory()

    patient_response = client.post(
        "/patients",
        headers=professional_a,
        json={
            "first_name": "Paciente",
            "last_name": "CitaPrivada",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    start = datetime.now(timezone.utc) + timedelta(days=10)
    end = start + timedelta(minutes=60)

    appointment_response = client.post(
        "/appointments",
        headers=professional_a,
        json={
            "patient_id": patient_id,
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
    )

    assert appointment_response.status_code == 201

    appointment_id = appointment_response.json()["id"]

    # La cita debe estar completada antes de crear la sesión.
    confirm_response = client.patch(
        f"/appointments/{appointment_id}",
        headers=professional_a,
        json={
            "status": "confirmed",
        },
    )

    assert confirm_response.status_code == 200

    complete_response = client.patch(
        f"/appointments/{appointment_id}",
        headers=professional_a,
        json={
            "status": "completed",
        },
    )

    assert complete_response.status_code == 200

    response = client.post(
        f"/appointments/{appointment_id}/clinical-session",
        headers=professional_b,
    )

    assert response.status_code == 404