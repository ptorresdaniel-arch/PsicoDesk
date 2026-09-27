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