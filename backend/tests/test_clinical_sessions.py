from unittest.mock import MagicMock
from uuid import uuid4
import pytest
from sqlalchemy.exc import SQLAlchemyError

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.clinical_sessions import service as clinical_session_service
from app.clinical_sessions.models import ClinicalSession
from app.clinical_sessions.schemas import(
    ClinicalSessionCreate,
    ClinicalSessionUpdate,
)

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
    
    assert len(sessions["items"]) == 1
    assert sessions["items"][0]["id"] == session_id
    
    assert sessions["total"] == 1
    assert sessions["page"] == 1
    assert sessions["limit"] == 20

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
    
def test_create_clinical_session_note(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Notas",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    session_response = client.post(
        "/clinical-sessions",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "session_date": datetime.now(
                timezone.utc
            ).isoformat(),
            "duration_minutes": 50,
            "summary": "Sesión inicial",
        },
    )

    assert session_response.status_code == 201

    session_id = session_response.json()["id"]

    response = client.post(
        f"/clinical-sessions/{session_id}/notes",
        headers=professional_headers,
        json={
            "content": "Paciente refiere mejoría del ánimo.",
        },
    )

    assert response.status_code == 201

    note = response.json()

    assert note["clinical_session_id"] == session_id
    assert note["content"] == (
        "Paciente refiere mejoría del ánimo."
    )
    assert note["created_by"] is not None
    

def test_create_clinical_session_note_rejects_whitespace_only_content(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "NotaVacia",
        },
    )

    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    session_response = client.post(
        "/clinical-sessions",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "session_date": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )

    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    response = client.post(
        f"/clinical-sessions/{session_id}/notes",
        headers=professional_headers,
        json={
            "content": "   \t\n",
        },
    )

    assert response.status_code == 422

    

def test_list_clinical_session_notes(
    client,
    professional_headers,
):
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

    session_response = client.post(
        "/clinical-sessions",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "session_date": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )

    assert session_response.status_code == 201

    session_id = session_response.json()["id"]

    for content in [
        "Primera observación",
        "Segunda observación",
    ]:
        response = client.post(
            f"/clinical-sessions/{session_id}/notes",
            headers=professional_headers,
            json={
                "content": content,
            },
        )

        assert response.status_code == 201

    response = client.get(
        f"/clinical-sessions/{session_id}/notes",
        headers=professional_headers,
    )

    assert response.status_code == 200

    data = response.json()
    notes = data["items"]

    assert data["total"] == 2
    assert data["page"] == 1
    assert data["limit"] == 20

    assert len(notes) == 2

    assert notes[0]["content"] == "Segunda observación"
    assert notes[1]["content"] == "Primera observación"


def test_professional_cannot_access_another_professionals_notes(
    client,
    professional_headers,
    professional_factory,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Privado",
        },
    )

    patient_id = patient_response.json()["id"]

    session_response = client.post(
        "/clinical-sessions",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "session_date": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )

    session_id = session_response.json()["id"]

    note_response = client.post(
        f"/clinical-sessions/{session_id}/notes",
        headers=professional_headers,
        json={
            "content": "Nota privada",
        },
    )

    assert note_response.status_code == 201

    other_professional_headers = professional_factory()
    
    create_response = client.post(
        f"/clinical-sessions/{session_id}/notes",
        headers=other_professional_headers,
        json={
            "content": "Intento de nota no autorizado",
        },
    )
    
    assert create_response.status_code == 404
    
    response = client.get(
        f"/clinical-sessions/{session_id}/notes",
        headers=other_professional_headers,
    )

    assert response.status_code == 404
    
def test_clinical_session_note_is_immutable(
    client: TestClient,
    professional_headers,
) -> None:
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Inmutable",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    session_response = client.post(
        "/clinical-sessions",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "session_date": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )

    assert session_response.status_code == 201

    session_id = session_response.json()["id"]

    note_response = client.post(
        f"/clinical-sessions/{session_id}/notes",
        headers=professional_headers,
        json={
            "content": "Nota original.",
        },
    )

    assert note_response.status_code == 201

    note_id = note_response.json()["id"]

    update_response = client.patch(
        f"/clinical-sessions/{session_id}/notes/{note_id}",
        headers=professional_headers,
        json={
            "content": "Nota modificada.",
        },
    )

    assert update_response.status_code == 404

    delete_response = client.delete(
        f"/clinical-sessions/{session_id}/notes/{note_id}",
        headers=professional_headers,
    )

    assert delete_response.status_code == 404
    


def test_list_clinical_session_notes_pagination(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Paginacion",
        },
    )

    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    session_response = client.post(
        "/clinical-sessions",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "session_date": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )

    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    created_note_ids = set()

    for content in [
        "Primera observación",
        "Segunda observación",
    ]:
        note_response = client.post(
            f"/clinical-sessions/{session_id}/notes",
            headers=professional_headers,
            json={
                "content": content,
            },
        )

        assert note_response.status_code == 201

        created_note_ids.add(
            note_response.json()["id"]
        )

    first_response = client.get(
        f"/clinical-sessions/{session_id}/notes",
        headers=professional_headers,
        params={
            "page": 1,
            "limit": 1,
        },
    )

    second_response = client.get(
        f"/clinical-sessions/{session_id}/notes",
        headers=professional_headers,
        params={
            "page": 2,
            "limit": 1,
        },
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 200

    first_page = first_response.json()
    second_page = second_response.json()

    assert first_page["total"] == 2
    assert second_page["total"] == 2

    assert first_page["page"] == 1
    assert second_page["page"] == 2

    assert first_page["limit"] == 1
    assert second_page["limit"] == 1

    assert len(first_page["items"]) == 1
    assert len(second_page["items"]) == 1

    first_note_id = first_page["items"][0]["id"]
    second_note_id = second_page["items"][0]["id"]

    assert first_note_id != second_note_id

    returned_note_ids = {
        first_note_id,
        second_note_id,
    }

    assert returned_note_ids == created_note_ids

    third_response = client.get(
        f"/clinical-sessions/{session_id}/notes",
        headers=professional_headers,
        params={
            "page": 3,
            "limit": 1,
        },
    )

    assert third_response.status_code == 200

    third_page = third_response.json()

    assert third_page["items"] == []
    assert third_page["total"] == 2
    assert third_page["page"] == 3
    assert third_page["limit"] == 1



def test_list_clinical_session_notes_rejects_invalid_pagination_params(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Limites",
        },
    )

    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    session_response = client.post(
        "/clinical-sessions",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "session_date": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )

    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    invalid_params = [
        {"page": 0},
        {"limit": 0},
        {"limit": 101},
    ]

    for params in invalid_params:
        response = client.get(
            f"/clinical-sessions/{session_id}/notes",
            headers=professional_headers,
            params=params,
        )

        assert response.status_code == 422, (
            f"Se esperaban parámetros inválidos: {params}"
        )


def test_list_clinical_session_notes_empty(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "SinNotas",
        },
    )

    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    session_response = client.post(
        "/clinical-sessions",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "session_date": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )

    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    response = client.get(
        f"/clinical-sessions/{session_id}/notes",
        headers=professional_headers,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["limit"] == 20


def test_create_clinical_session_note_rolls_back_when_commit_fails(
    client,
    professional_headers,
    db,
    monkeypatch,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Rollback",
        },
    )

    assert patient_response.status_code == 201
    patient_id = patient_response.json()["id"]

    session_response = client.post(
        "/clinical-sessions",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "session_date": datetime.now(
                timezone.utc
            ).isoformat(),
        },
    )

    assert session_response.status_code == 201
    session_id = session_response.json()["id"]

    rollback_calls = []
    
    def failing_commit():
        raise SQLAlchemyError(
            "Fallo simulado durante el commit"
        )
    
    def tracking_rollback():
        rollback_calls.append(True)

    with monkeypatch.context() as patch:
        patch.setattr(db, "commit", failing_commit)
        patch.setattr(db, "rollback", tracking_rollback)

        with pytest.raises(
            SQLAlchemyError,
            match="Fallo simulado durante el commit",
        ):
            client.post(
                f"/clinical-sessions/{session_id}/notes",
                headers=professional_headers,
                json={
                    "content": "Nota de prueba.",
                },
            )

    assert rollback_calls == [True]


def test_create_clinical_session_rolls_back_when_commit_fails(
    monkeypatch,
):
    db = MagicMock()
    patient = MagicMock()
    patient.id = uuid4()

    monkeypatch.setattr(
        clinical_session_service,
        "get_patient_for_professional",
        lambda db, patient_id, professional_id: patient,
    )

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    data = ClinicalSessionCreate(
        patient_id=patient.id,
        session_date=datetime.now(timezone.utc),
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        clinical_session_service.create_clinical_session(
            db,
            data,
            uuid4(),
        )

    db.add.assert_called_once()
    db.rollback.assert_called_once_with()
    db.refresh.assert_not_called()


def test_update_clinical_session_rolls_back_when_commit_fails():
    db = MagicMock()
    clinical_session = MagicMock(spec=ClinicalSession)

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    data = ClinicalSessionUpdate(
        summary="Resumen actualizado",
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        clinical_session_service.update_clinical_session(
            db,
            clinical_session,
            data,
        )

    db.rollback.assert_called_once_with()
    db.refresh.assert_not_called()


def test_delete_clinical_session_rolls_back_when_commit_fails():
    db = MagicMock()
    clinical_session = MagicMock(spec=ClinicalSession)

    db.commit.side_effect = SQLAlchemyError(
        "Fallo simulado durante el commit"
    )

    with pytest.raises(
        SQLAlchemyError,
        match="Fallo simulado durante el commit",
    ):
        clinical_session_service.delete_clinical_session(
            db,
            clinical_session,
        )

    db.delete.assert_called_once_with(clinical_session)
    db.rollback.assert_called_once_with()

def test_professional_cannot_list_another_professionals_sessions(
    client: TestClient,
    professional_factory,
) -> None:
    professional_a = professional_factory()
    professional_b = professional_factory()

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

    response = client.get(
        f"/clinical-sessions/patient/{patient_id}",
        headers=professional_b,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["items"] == []
    assert data["total"] == 0
    assert data["page"] == 1
    assert data["limit"] == 20