from datetime import datetime, timedelta, timezone


def test_dashboard_with_data(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Ana",
            "last_name": "Dashboard",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    start = datetime.now(timezone.utc) + timedelta(
        hours=1,
    )

    end = start + timedelta(
        minutes=50,
    )

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

    dashboard_response = client.get(
        "/dashboard",
        headers=professional_headers,
    )

    assert dashboard_response.status_code == 200

    dashboard = dashboard_response.json()

    assert dashboard["total_patients"] == 1

    assert len(
        dashboard["today_appointments"]
    ) == 1

    assert (
        dashboard["today_appointments"][0]["patient_name"]
        == "Ana Dashboard"
    )

    assert dashboard["upcoming_appointments"] == 1

def test_dashboard_empty(
    client,
    professional_headers,
):
    response = client.get(
        "/dashboard",
        headers=professional_headers,
    )

    assert response.status_code == 200

    dashboard = response.json()

    assert dashboard["total_patients"] == 0
    assert dashboard["today_appointments"] == []
    assert dashboard["upcoming_appointments"] == 0
    assert dashboard["recent_sessions"] == []

def test_dashboard_does_not_include_another_professional_data(
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
            "last_name": "Privado",
        },
    )

    assert patient_response.status_code == 201

    start = datetime.now(timezone.utc) + timedelta(
        hours=1,
    )

    end = start + timedelta(
        minutes=45,
    )

    appointment_response = client.post(
        "/appointments",
        headers=professional_a,
        json={
            "patient_id": patient_response.json()["id"],
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
        },
    )

    assert appointment_response.status_code == 201

    dashboard_response = client.get(
        "/dashboard",
        headers=professional_b,
    )

    assert dashboard_response.status_code == 200

    dashboard = dashboard_response.json()

    assert dashboard["total_patients"] == 0
    assert dashboard["today_appointments"] == []
    assert dashboard["upcoming_appointments"] == 0
    assert dashboard["recent_sessions"] == []

def test_dashboard_requires_permission(
    client,
    auth_headers,
):
    response = client.get(
        "/dashboard",
        headers=auth_headers,
    )

    assert response.status_code == 403

def test_dashboard_includes_recent_session(
    client,
    professional_headers,
):
    patient_response = client.post(
        "/patients",
        headers=professional_headers,
        json={
            "first_name": "Paciente",
            "last_name": "Sesion",
        },
    )

    assert patient_response.status_code == 201

    patient_id = patient_response.json()["id"]

    session_date = datetime.now(timezone.utc)

    session_response = client.post(
        "/clinical-sessions",
        headers=professional_headers,
        json={
            "patient_id": patient_id,
            "session_date": session_date.isoformat(),
            "duration_minutes": 50,
            "summary": "Sesión de prueba",
            "notes": "Notas de prueba.",
        },
    )

    assert session_response.status_code == 201

    dashboard_response = client.get(
        "/dashboard",
        headers=professional_headers,
    )

    assert dashboard_response.status_code == 200

    dashboard = dashboard_response.json()

    assert len(dashboard["recent_sessions"]) == 1

    recent_session = dashboard["recent_sessions"][0]

    assert recent_session["id"] == session_response.json()["id"]
    assert recent_session["patient_name"] == "Paciente Sesion"

    returned_session_date = datetime.fromisoformat(
        recent_session["session_date"]
    )

    assert (
        returned_session_date.astimezone(timezone.utc)
        == session_date
    )