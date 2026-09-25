from app.appointments.enums import AppointmentStatus


ALLOWED_TRANSITIONS = {
    AppointmentStatus.scheduled: {
        AppointmentStatus.confirmed,
        AppointmentStatus.cancelled,
    },
    AppointmentStatus.confirmed: {
        AppointmentStatus.completed,
        AppointmentStatus.no_show,
        AppointmentStatus.cancelled,
    },
    AppointmentStatus.completed: set(),
    AppointmentStatus.cancelled: set(),
    AppointmentStatus.no_show: set(),
}


def can_change_status(
    current_status: AppointmentStatus,
    new_status: AppointmentStatus,
) -> bool:

    return new_status in ALLOWED_TRANSITIONS.get(
        current_status,
        set(),
    )