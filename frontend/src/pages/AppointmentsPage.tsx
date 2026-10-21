
import { useEffect, useState, type FormEvent } from 'react'
import {
  createAppointment,
  getCalendarAppointments,
  getPatients,
} from '../services/api'
import type { AppointmentCalendarRead } from '../types/appointment'
import type { PatientListRead } from '../types/patient'

interface AppointmentsPageProps {
  token: string
}

interface AppointmentForm {
  patient_id: string
  start_time: string
  end_time: string
  title: string
  reason: string
  notes: string
}

const SESSION_DURATION_MINUTES = 45
const START_HOUR = 8
const END_HOUR = 20
const SLOT_MINUTES = 30
const PIXELS_PER_MINUTE = 1

const EMPTY_FORM: AppointmentForm = {
  patient_id: '',
  start_time: '09:00',
  end_time: '09:45',
  title: '',
  reason: '',
  notes: '',
}

function getLocalDate(): string {
  const now = new Date()

  return [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0'),
  ].join('-')
}

function dateKey(date: Date): string {
  return [
    date.getFullYear(),
    String(date.getMonth() + 1).padStart(2, '0'),
    String(date.getDate()).padStart(2, '0'),
  ].join('-')
}

function getWeekStartDate(value: string): Date {
  const date = new Date(`${value}T12:00:00`)
  const day = date.getDay()
  const offset = day === 0 ? -6 : 1 - day

  date.setDate(date.getDate() + offset)
  date.setHours(0, 0, 0, 0)

  return date
}

function getWeekStartKey(value: string): string {
  return dateKey(getWeekStartDate(value))
}

function getWeekDates(value: string): string[] {
  const monday = getWeekStartDate(value)

  return Array.from({ length: 7 }, (_, index) => {
    const date = new Date(monday)
    date.setDate(monday.getDate() + index)

    return dateKey(date)
  })
}

function getWeekRange(value: string) {
  const monday = getWeekStartDate(value)
  const nextMonday = new Date(monday)

  nextMonday.setDate(monday.getDate() + 7)

  return {
    start: monday.toISOString(),
    end: nextMonday.toISOString(),
  }
}

function getDateParts(value: string): Record<string, string> {
  const parts = new Intl.DateTimeFormat('en-CA', {
    timeZone: 'America/Santiago',
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  }).formatToParts(new Date(value))

  return Object.fromEntries(
    parts.map((part) => [part.type, part.value]),
  )
}

function getAppointmentDate(value: string): string {
  const parts = getDateParts(value)

  return `${parts.year}-${parts.month}-${parts.day}`
}

function getMinutesOfDay(value: string): number {
  const parts = getDateParts(value)

  return Number(parts.hour) * 60 + Number(parts.minute)
}

function formatTime(value: string): string {
  return new Date(value).toLocaleTimeString('es-CL', {
    timeZone: 'America/Santiago',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  })
}

function formatDate(value: string): string {
  return new Date(`${value}T12:00:00`).toLocaleDateString(
    'es-CL',
    {
      timeZone: 'America/Santiago',
      weekday: 'long',
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    },
  )
}

function formatDayName(value: string): string {
  const name = new Date(`${value}T12:00:00`).toLocaleDateString(
    'es-CL',
    {
      weekday: 'short',
      timeZone: 'America/Santiago',
    },
  )

  return name.replace('.', '').toUpperCase()
}

function formatDayNumber(value: string): string {
  return new Date(`${value}T12:00:00`).toLocaleDateString(
    'es-CL',
    {
      day: '2-digit',
      timeZone: 'America/Santiago',
    },
  )
}

function addMinutesToTime(
  time: string,
  minutesToAdd: number,
): string {
  const [hours, minutes] = time.split(':').map(Number)
  const totalMinutes = hours * 60 + minutes + minutesToAdd

  const resultHours = Math.floor(totalMinutes / 60)
  const resultMinutes = totalMinutes % 60

  return (
    `${String(resultHours).padStart(2, '0')}:` +
    String(resultMinutes).padStart(2, '0')
  )
}

function statusLabel(status: string): string {
  const labels: Record<string, string> = {
    scheduled: 'Programada',
    confirmed: 'Confirmada',
    completed: 'Realizada',
    cancelled: 'Cancelada',
    no_show: 'No asistió',
  }

  return labels[status] ?? status
}

function statusClass(status: string): string {
  if (status === 'confirmed') return 'confirmed'
  if (status === 'scheduled') return 'scheduled'
  if (status === 'completed') return 'completed'
  if (status === 'cancelled') return 'cancelled'

  return 'other'
}

function AppointmentsPage({ token }: AppointmentsPageProps) {
  const [selectedDate, setSelectedDate] = useState(getLocalDate)
  const [appointments, setAppointments] = useState<
    AppointmentCalendarRead[]
  >([])
  const [patients, setPatients] = useState<
    PatientListRead['items']
  >([])
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [showWeeklyCalendar, setShowWeeklyCalendar] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [reloadKey, setReloadKey] = useState(0)
  const [form, setForm] = useState<AppointmentForm>(EMPTY_FORM)

  const weekDates = getWeekDates(selectedDate)
  const range = getWeekRange(selectedDate)

  const weekLabel = (
    <>
      {formatDate(weekDates[0])} — {formatDate(weekDates[6])}
    </>
  )

  useEffect(() => {
    let cancelled = false

    Promise.all([
      getCalendarAppointments(token, range.start, range.end),
      getPatients(token, {
        is_active: true,
        page: 1,
        limit: 100,
      }),
    ])
      .then(([appointmentData, patientData]) => {
        if (cancelled) return

        setAppointments(appointmentData)
        setPatients(patientData.items)
        setError('')
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : 'No se pudo cargar la agenda.',
          )
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [token, range.start, range.end, reloadKey])

  useEffect(() => {
    if (!showWeeklyCalendar) return

    const previousOverflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setShowWeeklyCalendar(false)
      }
    }

    window.addEventListener('keydown', handleKeyDown)

    return () => {
      document.body.style.overflow = previousOverflow
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [showWeeklyCalendar])

  function navigateDay(offset: number) {
    const next = new Date(`${selectedDate}T12:00:00`)
    next.setDate(next.getDate() + offset)
    selectDate(dateKey(next))
  }

  function navigateWeek(offset: number) {
    const next = new Date(`${selectedDate}T12:00:00`)
    next.setDate(next.getDate() + offset * 7)

    const nextDate = dateKey(next)

    setLoading(true)
    setError('')
    setSuccess('')
    setSelectedDate(nextDate)
  }

  function selectDate(value: string) {
    if (!value) return

    if (getWeekStartKey(value) !== getWeekStartKey(selectedDate)) {
      setLoading(true)
    }

    setError('')
    setSuccess('')
    setSelectedDate(value)
  }

  function handleStartTimeChange(startTime: string) {
    setForm((current) => ({
      ...current,
      start_time: startTime,
      end_time: startTime
        ? addMinutesToTime(startTime, SESSION_DURATION_MINUTES)
        : current.end_time,
    }))
  }

  async function handleCreateAppointment(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    setError('')
    setSuccess('')

    if (!form.patient_id) {
      setError('Selecciona un paciente.')
      return
    }

    if (form.end_time <= form.start_time) {
      setError('La hora de término debe ser posterior al inicio.')
      return
    }

    const startDateTime = new Date(
      `${selectedDate}T${form.start_time}:00`,
    )
    const endDateTime = new Date(
      `${selectedDate}T${form.end_time}:00`,
    )

    if (
      Number.isNaN(startDateTime.getTime()) ||
      Number.isNaN(endDateTime.getTime())
    ) {
      setError('La fecha o la hora no son válidas.')
      return
    }

    setSaving(true)

    try {
      await createAppointment(token, {
        patient_id: form.patient_id,
        start_time: startDateTime.toISOString(),
        end_time: endDateTime.toISOString(),
        title: form.title.trim() || null,
        reason: form.reason.trim() || null,
        notes: form.notes.trim() || null,
        timezone: 'America/Santiago',
      })

      setForm(EMPTY_FORM)
      setShowForm(false)
      setSuccess('La cita se registró correctamente.')
      setLoading(true)
      setReloadKey((current) => current + 1)
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : 'No se pudo registrar la cita.',
      )
    } finally {
      setSaving(false)
    }
  }

  const selectedDayAppointments = appointments
    .filter(
      (appointment) =>
        getAppointmentDate(appointment.start_time) === selectedDate,
    )
    .sort(
      (a, b) =>
        new Date(a.start_time).getTime() -
        new Date(b.start_time).getTime(),
    )

  return (
    <section className="appointments-page">
      <div className="appointments-toolbar">
        <div>
          <span className="eyebrow">Organización de la consulta</span>
          <h2>Agenda diaria</h2>
          <p>Consulta y organiza las citas de tus pacientes.</p>
        </div>

        <div className="appointments-toolbar-actions">
          <button
            className="secondary-button"
            type="button"
            onClick={() => setShowWeeklyCalendar(true)}
          >
            Ver calendario semanal
          </button>
          <button
            className="primary-button"
            type="button"
            onClick={() => {
              setError('')
              setSuccess('')
              setShowForm((current) => !current)
            }}
          >
            {showForm ? 'Cerrar formulario' : '+ Nueva cita'}
          </button>
        </div>
      </div>

      <section className="panel agenda-date-panel agenda-day-panel">
        <button
          className="secondary-button"
          type="button"
          onClick={() => navigateDay(-1)}
        >
          ← Día anterior
        </button>

        <div className="agenda-week-label agenda-day-label">
          <span>Día seleccionado</span>
          <strong>{formatDate(selectedDate)}</strong>
        </div>

        <label className="agenda-date-picker">
          Ir a una fecha
          <input
            type="date"
            value={selectedDate}
            onChange={(event) => selectDate(event.target.value)}
          />
        </label>

        <button
          className="secondary-button"
          type="button"
          onClick={() => navigateDay(1)}
        >
          Día siguiente →
        </button>

        <button
          className="secondary-button"
          type="button"
          onClick={() => selectDate(getLocalDate())}
        >
          Hoy
        </button>
      </section>

      {error && (
        <div className="error-banner" role="alert">
          {error}
        </div>
      )}

      {success && (
        <div className="success-banner" role="status">
          {success}
        </div>
      )}

      {showForm && (
        <form
          className="panel appointment-form"
          onSubmit={handleCreateAppointment}
        >
          <div className="panel-header">
            <div>
              <h2>Registrar cita</h2>
              <p>{formatDate(selectedDate)}</p>
            </div>
          </div>

          <div className="appointment-form-grid">
            <label className="form-field">
              Paciente *
              <select
                required
                value={form.patient_id}
                onChange={(event) =>
                  setForm({
                    ...form,
                    patient_id: event.target.value,
                  })
                }
              >
                <option value="">Seleccionar paciente</option>
                {patients.map((patient) => (
                  <option key={patient.id} value={patient.id}>
                    {patient.first_name} {patient.last_name}
                  </option>
                ))}
              </select>
            </label>

            <label className="form-field">
              Hora de inicio *
              <input
                type="time"
                required
                value={form.start_time}
                onChange={(event) =>
                  handleStartTimeChange(event.target.value)
                }
              />
            </label>

            <label className="form-field">
              Hora de término *
              <input
                type="time"
                required
                value={form.end_time}
                onChange={(event) =>
                  setForm({
                    ...form,
                    end_time: event.target.value,
                  })
                }
              />
              <small>Se calculan inicialmente 45 minutos.</small>
            </label>

            <label className="form-field">
              Título
              <input
                type="text"
                maxLength={150}
                value={form.title}
                placeholder="Ej. Sesión de seguimiento"
                onChange={(event) =>
                  setForm({
                    ...form,
                    title: event.target.value,
                  })
                }
              />
            </label>

            <label className="form-field">
              Motivo de consulta
              <input
                type="text"
                maxLength={255}
                value={form.reason}
                onChange={(event) =>
                  setForm({
                    ...form,
                    reason: event.target.value,
                  })
                }
              />
            </label>

            <label className="form-field appointment-notes">
              Notas
              <textarea
                rows={3}
                value={form.notes}
                onChange={(event) =>
                  setForm({
                    ...form,
                    notes: event.target.value,
                  })
                }
              />
            </label>
          </div>

          {patients.length === 0 && (
            <p className="empty-state">
              No hay pacientes activos disponibles. Registra o
              activa un paciente antes de crear una cita.
            </p>
          )}

          <div className="appointment-form-actions">
            <button
              className="secondary-button"
              type="button"
              onClick={() => setShowForm(false)}
            >
              Cancelar
            </button>

            <button
              className="primary-button"
              type="submit"
              disabled={saving || patients.length === 0}
            >
              {saving ? 'Guardando…' : 'Guardar cita'}
            </button>
          </div>
        </form>
      )}

      <section className="panel agenda-list-panel agenda-day-list-panel">
        <div className="panel-header">
          <div>
            <h2>Citas del día</h2>
            <p>{formatDate(selectedDate)}</p>
          </div>
        </div>

        {loading ? (
          <div className="patients-loading" aria-live="polite">
            <span className="loading-spinner" />
            <p>Cargando agenda…</p>
          </div>
        ) : selectedDayAppointments.length === 0 ? (
          <div className="patients-empty">
            <div className="patients-empty-icon">▦</div>
            <h3>No hay citas para este día</h3>
            <p>
              Puedes elegir otra fecha o registrar una nueva cita.
            </p>
          </div>
        ) : (
          <div className="appointment-list">
            {selectedDayAppointments.map((appointment) => (
              <div className="appointment-row" key={appointment.id}>
                <time className="appointment-time">
                  {formatTime(appointment.start_time)}
                </time>
                <div className="appointment-info">
                  <strong>{appointment.patient_name}</strong>
                  <span>
                    {appointment.title || 'Sesión clínica'}
                    {' · '}
                    Hasta las {formatTime(appointment.end_time)}
                  </span>
                </div>
                <span
                  className={`status ${statusClass(appointment.status)}`}
                >
                  {statusLabel(appointment.status)}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>

      {showWeeklyCalendar && (
        <div
          className="weekly-calendar-modal-overlay"
          role="presentation"
          onMouseDown={(event) => {
            if (event.target === event.currentTarget) {
              setShowWeeklyCalendar(false)
            }
          }}
        >
          <section
            className="weekly-calendar-modal"
            role="dialog"
            aria-modal="true"
            aria-labelledby="weekly-calendar-title"
          >
            <div className="weekly-calendar-modal-header">
              <div>
                <span className="eyebrow">Organización de la consulta</span>
                <h2 id="weekly-calendar-title">Calendario semanal</h2>
                <p>Selecciona un día para ver sus citas en la agenda diaria.</p>
              </div>
              <button
                className="secondary-button weekly-calendar-close"
                type="button"
                aria-label="Cerrar calendario semanal"
                onClick={() => setShowWeeklyCalendar(false)}
              >
                Cerrar ✕
              </button>
            </div>

            <section className="panel agenda-date-panel weekly-modal-date-panel">
              <button
                className="secondary-button"
                type="button"
                onClick={() => navigateWeek(-1)}
              >
                ← Semana anterior
              </button>

              <div className="agenda-week-label">
                <span>Semana seleccionada</span>
                <strong>{weekLabel}</strong>
              </div>

              <button
                className="secondary-button"
                type="button"
                onClick={() => navigateWeek(1)}
              >
                Semana siguiente →
              </button>

              <button
                className="secondary-button"
                type="button"
                onClick={() => selectDate(getLocalDate())}
              >
                Hoy
              </button>
            </section>

            {loading && (
              <div className="patients-loading" aria-live="polite">
                <span className="loading-spinner" />
                <p>Cargando agenda…</p>
              </div>
            )}

        <div className="weekly-calendar-scroll">
          <div className="weekly-calendar">
            <div className="weekly-calendar-header">
              <div className="weekly-time-gutter">Hora</div>

              {weekDates.map((day) => (
                <button
                  className={`weekly-day-heading ${
                    day === selectedDate ? 'selected' : ''
                  }`}
                  type="button"
                  key={day}
                  onClick={() => {
                    selectDate(day)
                    setShowWeeklyCalendar(false)
                  }}
                  aria-pressed={day === selectedDate}
                >
                  <span>{formatDayName(day)}</span>
                  <strong>{formatDayNumber(day)}</strong>
                </button>
              ))}
            </div>

            <div className="weekly-calendar-body">
              <div className="weekly-time-column">
                {Array.from(
                  {
                    length:
                      ((END_HOUR - START_HOUR) * 60) /
                      SLOT_MINUTES,
                  },
                  (_, index) => {
                    const minutes =
                      START_HOUR * 60 + index * SLOT_MINUTES

                    const hour = Math.floor(minutes / 60)
                    const minute = minutes % 60

                    return (
                      <div className="weekly-time-slot" key={minutes}>
                        {minute === 0
                          ? `${String(hour).padStart(2, '0')}:00`
                          : ''}
                      </div>
                    )
                  },
                )}
              </div>

              <div className="weekly-days-grid">
                {weekDates.map((day) => {
                  const dayAppointments = appointments.filter(
                    (appointment) =>
                      getAppointmentDate(appointment.start_time) === day,
                  )

                  return (
                    <div
                      className={`weekly-day-column ${
                        day === selectedDate ? 'selected' : ''
                      }`}
                      key={day}
                    >
                      <div className="weekly-day-track">
                        {Array.from(
                          {
                            length:
                              ((END_HOUR - START_HOUR) * 60) /
                              SLOT_MINUTES,
                          },
                          (_, index) => (
                            <div
                              className="weekly-slot"
                              key={index}
                            />
                          ),
                        )}

                        {dayAppointments.map((appointment) => {
                          const startMinutes =
                            getMinutesOfDay(appointment.start_time) -
                            START_HOUR * 60

                          const endMinutes =
                            getMinutesOfDay(appointment.end_time) -
                            START_HOUR * 60

                          const visibleStart = Math.max(0, startMinutes)
                          const visibleEnd = Math.min(
                            (END_HOUR - START_HOUR) * 60,
                            endMinutes,
                          )

                          if (
                            visibleEnd <= visibleStart ||
                            startMinutes >=
                              (END_HOUR - START_HOUR) * 60 ||
                            endMinutes <= 0
                          ) {
                            return null
                          }

                          const top =
                            visibleStart * PIXELS_PER_MINUTE
                          const height = Math.max(
                            32,
                            (visibleEnd - visibleStart) *
                              PIXELS_PER_MINUTE,
                          )

                          return (
                            <article
                              className={`weekly-event ${statusClass(
                                appointment.status,
                              )}`}
                              key={appointment.id}
                              style={{ top, height }}
                              title={`${appointment.patient_name}: ${formatTime(
                                appointment.start_time,
                              )}–${formatTime(appointment.end_time)} · ${
                                appointment.title || 'Sesión clínica'
                              } · ${statusLabel(appointment.status)}`}
                            >
                              <strong>{appointment.patient_name}</strong>
                              <span>
                                {formatTime(appointment.start_time)}–
                                {formatTime(appointment.end_time)}
                              </span>
                            </article>
                          )
                        })}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          </div>
        </div>

            {!loading && appointments.length === 0 && (
              <div className="patients-empty">
                <div className="patients-empty-icon">▦</div>
                <h3>No hay citas esta semana</h3>
                <p>
                  Selecciona otro período o registra una nueva cita.
                </p>
              </div>
            )}

        <div className="agenda-legend">
          <span><i className="legend-dot scheduled" /> Programada</span>
          <span><i className="legend-dot confirmed" /> Confirmada</span>
          <span><i className="legend-dot completed" /> Realizada</span>
          <span><i className="legend-dot other" /> Otro estado</span>
        </div>
          </section>
        </div>
      )}
    </section>
  )
}

export default AppointmentsPage
