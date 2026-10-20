import pytest
from unittest.mock import MagicMock
from uuid import uuid4

from sqlalchemy.exc import SQLAlchemyError

from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta

from app.patients import service as patient_service
from app.patients.models import Patient
from app.patients.schemas import PatientCreate, PatientUpdate
from app.users.models import User

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

    assert patients["total"] == 1
    assert len(patients["items"]) == 1
    assert patients["items"][0]["id"] == patient_id
    assert patients["page"] == 1
    assert patients["limit"] == 20

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
    
def test_delete_patient_with_clinical_history(
    client,
    professional_headers,
    db,
):
    # Crear paciente
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Historial",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    # Crear cita
    start = datetime.now(timezone.utc) + timedelta(days=1)
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

    # Completar la cita
    response = client.patch(
        f"/appointments/{appointment_id}",
        headers=professional_headers,
        json={"status": "confirmed"},
    )

    assert response.status_code == 200

    response = client.patch(
        f"/appointments/{appointment_id}",
        headers=professional_headers,
        json={"status": "completed"},
    )

    assert response.status_code == 200

    # Crear sesión clínica
    session_response = client.post(
        f"/appointments/{appointment_id}/clinical-session",
        headers=professional_headers,
    )

    assert session_response.status_code == 201

    session_id = session_response.json()["id"]

    # Crear nota clínica
    note_response = client.post(
        f"/clinical-sessions/{session_id}/notes",
        headers=professional_headers,
        json={
            "content": "Nota clínica de prueba.",
        },
    )

    assert note_response.status_code == 201

    note_id = note_response.json()["id"]

    # Eliminar paciente
    delete_response = client.delete(
        f"/patients/{patient_id}",
        headers=professional_headers,
    )

    assert delete_response.status_code == 204

    # El paciente ya no existe
    patient_check = client.get(
        f"/patients/{patient_id}",
        headers=professional_headers,
    )

    assert patient_check.status_code == 404

    # Verificar directamente que las entidades relacionadas
    # también fueron eliminadas.
    from sqlalchemy import select

    from app.appointments.models import Appointment
    from app.clinical_sessions.models import ClinicalSession
    from app.clinical_sessions.note_models import ClinicalSessionNote

    db.expire_all()

    assert db.scalar(
        select(Appointment).where(
            Appointment.id == appointment_id,
        )
    ) is None

    assert db.scalar(
        select(ClinicalSession).where(
            ClinicalSession.id == session_id,
        )
    ) is None

    assert db.scalar(
        select(ClinicalSessionNote).where(
            ClinicalSessionNote.id == note_id,
        )
    ) is None
    
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
    assert list_response.json()["items"] == []

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

    assert len(patients["items"]) == 1
    assert patients["items"][0]["first_name"] == "Juan"
    
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
    
    assert patients["total"] == 1    
    assert len(patients["items"]) == 1
    assert patients["items"][0]["identification"] == "12345678-9"
    
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

    patients = response.json()["items"]
    print(patients)
    assert len(patients) >= 1
    for patient in patients:
        assert patient["is_active"] is False
        assert all(patient["last_name"] == "Paciente" for patient in patients)
    
def test_patient_profile_summary(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Ana",
            "last_name": "Resumen",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    # Cita realizada
    past_start = datetime.now(timezone.utc) - timedelta(days=3)
    past_end = past_start + timedelta(minutes=50)

    past_appointment_response = client.post(
        "/appointments",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "start_time": past_start.isoformat(),
            "end_time": past_end.isoformat(),
        },
    )

    assert past_appointment_response.status_code == 201

    past_appointment_id = (
        past_appointment_response.json()["id"]
    )

    client.patch(
        f"/appointments/{past_appointment_id}",
        headers=professional_headers,
        json={
            "status": "confirmed",
        },
    )

    client.patch(
        f"/appointments/{past_appointment_id}",
        headers=professional_headers,
        json={
            "status": "completed",
        },
    )

    session_response = client.post(
        f"/appointments/{past_appointment_id}/clinical-session",
        headers=professional_headers,
    )

    assert session_response.status_code == 201

    # Cita futura
    future_start = datetime.now(timezone.utc) + timedelta(days=5)
    future_end = future_start + timedelta(minutes=50)

    future_appointment_response = client.post(
        "/appointments",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "start_time": future_start.isoformat(),
            "end_time": future_end.isoformat(),
        },
    )

    assert future_appointment_response.status_code == 201

    # Consultar perfil
    profile_response = client.get(
        f"/patients/{patient_id}/profile",
        headers=professional_headers,
    )

    assert profile_response.status_code == 200

    profile = profile_response.json()

    summary = profile["summary"]

    assert summary["total_sessions"] == 1
    assert summary["last_session_date"] is not None
    assert summary["next_appointment_date"] is not None

def test_patient_search_requires_minimum_length(
    client,
    professional_headers,
):
    response = client.get(
        "/patients?search=a",
        headers=professional_headers,
    )

    assert response.status_code == 422


def test_patient_list_rejects_invalid_page(
    client,
    professional_headers,
):
    response = client.get(
        "/patients?page=0",
        headers=professional_headers,
    )

    assert response.status_code == 422


def test_patient_list_rejects_invalid_limit(
    client,
    professional_headers,
):
    response = client.get(
        "/patients?limit=0",
        headers=professional_headers,
    )

    assert response.status_code == 422


def test_patient_list_rejects_limit_above_maximum(
    client,
    professional_headers,
):
    response = client.get(
        "/patients?limit=101",
        headers=professional_headers,
    )

    assert response.status_code == 422

def test_create_patient_rolls_back_when_commit_fails():
    db = MagicMock()
    professional = MagicMock(spec=User)
    professional.id = uuid4()

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    data = PatientCreate(
        first_name="Paciente",
        last_name="Rollback",
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        patient_service.create_patient(
            db,
            data,
            professional,
        )

    db.add.assert_called_once()
    db.rollback.assert_called_once_with()
    db.refresh.assert_not_called()


def test_update_patient_rolls_back_when_commit_fails():
    db = MagicMock()
    patient = MagicMock(spec=Patient)

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    data = PatientUpdate(
        notes="Actualización de prueba",
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        patient_service.update_patient(
            db,
            patient,
            data,
        )

    db.rollback.assert_called_once_with()
    db.refresh.assert_not_called()


def test_delete_patient_rolls_back_when_commit_fails():
    db = MagicMock()
    patient = MagicMock(spec=Patient)

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        patient_service.delete_patient(
            db,
            patient,
        )

    db.delete.assert_called_once_with(patient)
    db.rollback.assert_called_once_with()
    
def test_patient_profile_selects_nearest_valid_upcoming_appointment(
    client,
    professional_headers,
    monkeypatch,
):
    fixed_now = datetime(
        2026, 10, 16, 12, 0,
        tzinfo=timezone.utc,
    )

    class FixedDateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            if tz is None:
                return fixed_now.replace(tzinfo=None)
            return fixed_now.astimezone(tz)

    monkeypatch.setattr(
        "app.patients.service.datetime",
        FixedDateTime,
    )

    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Proxima",
        },
    )

    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    # Cita válida más cercana.
    nearest_start = fixed_now + timedelta(days=1)
    nearest_end = nearest_start + timedelta(minutes=50)

    nearest_response = client.post(
        "/appointments",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "start_time": nearest_start.isoformat(),
            "end_time": nearest_end.isoformat(),
        },
    )

    assert nearest_response.status_code == 201

    # Cita válida posterior.
    later_start = fixed_now + timedelta(days=3)
    later_end = later_start + timedelta(minutes=50)

    later_response = client.post(
        "/appointments",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "start_time": later_start.isoformat(),
            "end_time": later_end.isoformat(),
        },
    )

    assert later_response.status_code == 201

    later_appointment_id = later_response.json()["id"]

    confirmed_response = client.patch(
        f"/appointments/{later_appointment_id}",
        headers=professional_headers,
        json={"status": "confirmed"},
    )

    assert confirmed_response.status_code == 200

    # Cita cancelada: debe ignorarse.
    cancelled_start = fixed_now + timedelta(days=2)
    cancelled_end = cancelled_start + timedelta(minutes=50)

    cancelled_response = client.post(
        "/appointments",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "start_time": cancelled_start.isoformat(),
            "end_time": cancelled_end.isoformat(),
        },
    )

    assert cancelled_response.status_code == 201

    cancelled_id = cancelled_response.json()["id"]

    cancelled_update = client.patch(
        f"/appointments/{cancelled_id}",
        headers=professional_headers,
        json={"status": "cancelled"},
    )

    assert cancelled_update.status_code == 200

    # No-show: debe ignorarse.
    no_show_start = fixed_now + timedelta(days=4)
    no_show_end = no_show_start + timedelta(minutes=50)

    no_show_response = client.post(
        "/appointments",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "start_time": no_show_start.isoformat(),
            "end_time": no_show_end.isoformat(),
        },
    )

    assert no_show_response.status_code == 201

    no_show_id = no_show_response.json()["id"]

    confirmed_response = client.patch(
        f"/appointments/{no_show_id}",
        headers=professional_headers,
        json={"status": "confirmed"},
    )

    assert confirmed_response.status_code == 200

    no_show_update = client.patch(
        f"/appointments/{no_show_id}",
        headers=professional_headers,
        json={"status": "no_show"},
    )

    assert no_show_update.status_code == 200

    profile_response = client.get(
        f"/patients/{patient_id}/profile",
        headers=professional_headers,
    )

    assert profile_response.status_code == 200

    profile = profile_response.json()

    assert profile["summary"]["next_appointment_date"] is not None

    returned_next = datetime.fromisoformat(
        profile["summary"]["next_appointment_date"]
    )

    assert returned_next.astimezone(timezone.utc) == nearest_start

    assert len(profile["upcoming_appointments"]) == 2

    returned_dates = [
        datetime.fromisoformat(
            appointment["start_time"]
        ).astimezone(timezone.utc)
        for appointment in profile["upcoming_appointments"]
    ]

    assert returned_dates == [
        nearest_start,
        later_start,
    ]