
import { useEffect, useState, type FormEvent } from 'react'
import {
  getPatient,
  getPatientProfile,
  updatePatient,
} from '../services/api'
import type {
  PatientProfileRead,
  PatientRead,
  PatientUpdateInput,
} from '../types/patient'
import { cleanRutInput, formatRut, isValidRut } from '../utils/rut'

interface PatientDetailProps {
  token: string
  patientId: string
  onBack: () => void
  onUpdated: () => void
}

interface PatientForm {
  first_name: string
  last_name: string
  identification: string
  birth_date: string
  email: string
  phone: string
  notes: string
}

const EMPTY_FORM: PatientForm = {
  first_name: '',
  last_name: '',
  identification: '',
  birth_date: '',
  email: '',
  phone: '',
  notes: '',
}

function toForm(patient: PatientRead): PatientForm {
  return {
    first_name: patient.first_name,
    last_name: patient.last_name,
    identification: formatRut(patient.identification),
    birth_date: patient.birth_date?.slice(0, 10) ?? '',
    email: patient.email ?? '',
    phone: patient.phone ?? '',
    notes: patient.notes ?? '',
  }
}

function formatDate(value: string | null | undefined): string {
  if (!value) return '—'

  const date = new Date(`${value.slice(0, 10)}T12:00:00`)
  return date.toLocaleDateString('es-CL')
}

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString('es-CL', {
    dateStyle: 'medium',
    timeStyle: 'short',
  })
}

function appointmentStatus(status: string): string {
  const labels: Record<string, string> = {
    scheduled: 'Programada',
    confirmed: 'Confirmada',
    completed: 'Realizada',
    cancelled: 'Cancelada',
    no_show: 'No asistió',
  }

  return labels[status] ?? status
}

export default function PatientDetail({
  token,
  patientId,
  onBack,
  onUpdated,
}: PatientDetailProps) {
  const [patient, setPatient] = useState<PatientRead | null>(null)
  const [profile, setProfile] = useState<PatientProfileRead | null>(null)
  const [form, setForm] = useState<PatientForm>(EMPTY_FORM)

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [updatingStatus, setUpdatingStatus] = useState(false)
  const [editing, setEditing] = useState(false)

  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    let cancelled = false

    Promise.all([
      getPatient(token, patientId),
      getPatientProfile(token, patientId),
    ])
      .then(([patientData, profileData]) => {
        if (cancelled) return

        setPatient(patientData)
        setProfile(profileData)
        setForm(toForm(patientData))
      })
      .catch((err: unknown) => {
        if (cancelled) return

        setError(
          err instanceof Error
            ? err.message
            : 'No se pudo cargar la ficha del paciente.',
        )
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [token, patientId])

  async function handleSave(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    if (!patient) return

    setSaving(true)
    setError('')
    setSuccess('')

    const rut = form.identification.trim()

    if(rut && !isValidRut(rut)){
        setError(
            'El RUT ingresado no es válido. Revisa el número y el dígito verificador.'
        )
        setSuccess('')
        return
    }

    const data: PatientUpdateInput = {
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      identification: formatRut(form.identification) || null,
      birth_date: form.birth_date || null,
      email: form.email.trim() || null,
      phone: form.phone.trim() || null,
      notes: form.notes.trim() || null,
    }

    try {
      const updated = await updatePatient(token, patient.id, data)

      setPatient(updated)
      setForm(toForm(updated))
      setEditing(false)
      setSuccess(
        'Los datos del paciente se actualizaron correctamente.',
      )
      onUpdated()
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : 'No se pudieron guardar los cambios.',
      )
    } finally {
      setSaving(false)
    }
  }

  async function handleToggleStatus() {
    if (!patient) return

    const nextStatus = !patient.is_active
    const action = nextStatus ? 'activar' : 'desactivar'

    if (
      !window.confirm(
        `¿Quieres ${action} a ${patient.first_name} ${patient.last_name}?`,
      )
    ) {
      return
    }

    setUpdatingStatus(true)
    setError('')
    setSuccess('')

    try {
      const updated = await updatePatient(token, patient.id, {
        is_active: nextStatus,
      })

      setPatient(updated)

      setSuccess(
        nextStatus
          ? 'Paciente activado correctamente.'
          : 'Paciente desactivado correctamente.',
      )

      onUpdated()
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : 'No se pudo cambiar el estado del paciente.',
      )
    } finally {
      setUpdatingStatus(false)
    }
  }

  function cancelEditing() {
    if (patient) {
      setForm(toForm(patient))
    }

    setEditing(false)
    setError('')
    setSuccess('')
  }

  if (loading) {
    return (
      <section className="patients-page">
        <button
          className="secondary-button"
          type="button"
          onClick={onBack}
        >
          ← Volver al directorio
        </button>

        <div className="patients-loading" role="status">
          <span className="loading-spinner" />
          <p>Cargando ficha del paciente…</p>
        </div>
      </section>
    )
  }

  if (!patient) {
    return (
      <section className="patients-page">
        <button
          className="secondary-button"
          type="button"
          onClick={onBack}
        >
          ← Volver al directorio
        </button>

        <div className="error-banner" role="alert">
          {error || 'No se encontró el paciente.'}
        </div>
      </section>
    )
  }

  const initials = (
    patient.first_name.charAt(0) +
    patient.last_name.charAt(0)
  ).toUpperCase()

  return (
    <section className="patients-page patient-detail-page">
      <div className="patient-detail-toolbar">
        <button
          className="secondary-button"
          type="button"
          onClick={onBack}
        >
          ← Volver al directorio
        </button>

        <span className="eyebrow">Ficha del paciente</span>
      </div>

      <section className="panel patient-detail-heading">
        <div className="patient-detail-identity">
          <span className="patient-avatar patient-detail-avatar">
            {initials}
          </span>

          <div>
            <h2>
              {patient.first_name} {patient.last_name}
            </h2>

            <p>
              {formatRut(patient.identification) ||
                'Sin RUT registrado'}
            </p>

            <span
              className={`patient-state ${
                patient.is_active ? 'active' : 'inactive'
              }`}
            >
              {patient.is_active ? 'Activo' : 'Inactivo'}
            </span>
          </div>
        </div>

        <div className="patient-detail-actions">
          <button
            className="secondary-button"
            type="button"
            onClick={() => {
              if (editing) {
                cancelEditing()
              } else {
                setError('')
                setSuccess('')
                setEditing(true)
              }
            }}
          >
            {editing ? 'Cancelar edición' : 'Editar datos'}
          </button>

          <button
            className="secondary-button"
            type="button"
            disabled={updatingStatus}
            onClick={handleToggleStatus}
          >
            {updatingStatus
              ? 'Actualizando…'
              : patient.is_active
                ? 'Desactivar paciente'
                : 'Activar paciente'}
          </button>
        </div>
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

      {profile && (
        <section
          className="patient-detail-summary"
          aria-label="Resumen clínico"
        >
          <article className="panel patient-detail-summary-card">
            <span>Total de sesiones</span>
            <strong>{profile.summary.total_sessions}</strong>
          </article>

          <article className="panel patient-detail-summary-card">
            <span>Última sesión</span>
            <strong>
              {formatDate(profile.summary.last_session_date)}
            </strong>
          </article>

          <article className="panel patient-detail-summary-card">
            <span>Próxima cita</span>
            <strong>
              {formatDate(profile.summary.next_appointment_date)}
            </strong>
          </article>
        </section>
      )}

      {editing && (
        <form className="panel patient-form" onSubmit={handleSave}>
          <div className="panel-header">
            <div>
              <h2>Editar datos personales</h2>
              <p>Modifica los datos y guarda los cambios.</p>
            </div>
          </div>

          <div className="patient-form-grid">
            <label className="form-field">
              Nombre *
              <input
                required
                maxLength={100}
                value={form.first_name}
                onChange={(event) =>
                  setForm({
                    ...form,
                    first_name: event.target.value,
                  })
                }
              />
            </label>

            <label className="form-field">
              Apellidos *
              <input
                required
                maxLength={100}
                value={form.last_name}
                onChange={(event) =>
                  setForm({
                    ...form,
                    last_name: event.target.value,
                  })
                }
              />
            </label>

            <label className="form-field">
              RUT
              <input
                type="text"
                inputMode="text"
                autoCapitalize="characters"
                maxLength={12}
                placeholder="12.345.678-5"
                value={form.identification}
                onChange={(event) =>
                  setForm({
                    ...form,
                    identification: cleanRutInput(
                      event.target.value,
                    ),
                  })
                }
                onBlur={() =>
                  setForm((current) => ({
                    ...current,
                    identification: formatRut(
                      current.identification,
                    ),
                  }))
                }
              />
            </label>

            <label className="form-field">
              Fecha de nacimiento
              <input
                type="date"
                value={form.birth_date}
                onChange={(event) =>
                  setForm({
                    ...form,
                    birth_date: event.target.value,
                  })
                }
              />
            </label>

            <label className="form-field">
              Correo electrónico
              <input
                type="email"
                value={form.email}
                onChange={(event) =>
                  setForm({
                    ...form,
                    email: event.target.value,
                  })
                }
              />
            </label>

            <label className="form-field">
              Teléfono
              <input
                type="tel"
                maxLength={30}
                value={form.phone}
                onChange={(event) =>
                  setForm({
                    ...form,
                    phone: event.target.value,
                  })
                }
              />
            </label>

            <label className="form-field patient-notes-field">
              Notas generales
              <textarea
                rows={4}
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

          <div className="patient-form-actions">
            <button
              className="secondary-button"
              type="button"
              disabled={saving}
              onClick={cancelEditing}
            >
              Cancelar
            </button>

            <button
              className="primary-button"
              type="submit"
              disabled={saving}
            >
              {saving ? 'Guardando…' : 'Guardar cambios'}
            </button>
          </div>
        </form>
      )}

      <div className="patient-detail-grid">
        <section className="panel patient-detail-section">
          <div className="panel-header">
            <div>
              <h2>Datos personales</h2>
              <p>Información registrada del paciente.</p>
            </div>
          </div>

          <dl className="patient-detail-fields">
            <div>
              <dt>RUT</dt>
              <dd>
                {formatRut(patient.identification) ||
                  'No registrado'}
              </dd>
            </div>

            <div>
              <dt>Fecha de nacimiento</dt>
              <dd>{formatDate(patient.birth_date)}</dd>
            </div>

            <div>
              <dt>Correo electrónico</dt>
              <dd>{patient.email || 'No registrado'}</dd>
            </div>

            <div>
              <dt>Teléfono</dt>
              <dd>{patient.phone || 'No registrado'}</dd>
            </div>

            <div>
              <dt>Fecha de registro</dt>
              <dd>{formatDate(patient.created_at)}</dd>
            </div>

            <div>
              <dt>Notas generales</dt>
              <dd className="patient-detail-notes">
                {patient.notes || 'Sin notas generales.'}
              </dd>
            </div>
          </dl>
        </section>

        <section className="panel patient-detail-section">
          <div className="panel-header">
            <div>
              <h2>Próximas citas</h2>
              <p>Agenda asociada a este paciente.</p>
            </div>
          </div>

          {!profile ||
          profile.upcoming_appointments.length === 0 ? (
            <p className="patient-detail-empty">
              No hay próximas citas registradas.
            </p>
          ) : (
            <div className="patient-detail-list">
              {profile.upcoming_appointments.map((appointment) => (
                <article
                  className="patient-detail-item"
                  key={appointment.id}
                >
                  <div>
                    <strong>
                      {appointment.title || 'Cita psicológica'}
                    </strong>

                    <p>
                      {formatDateTime(appointment.start_time)}
                    </p>

                    <small>
                      Hasta {formatDateTime(appointment.end_time)}
                    </small>
                  </div>

                  <span className="status scheduled">
                    {appointmentStatus(appointment.status)}
                  </span>
                </article>
              ))}
            </div>
          )}
        </section>

        <section className="panel patient-detail-section patient-detail-history">
          <div className="panel-header">
            <div>
              <h2>Historial de sesiones</h2>
              <p>Sesiones clínicas disponibles en el sistema.</p>
            </div>
          </div>

          {!profile || profile.clinical_sessions.length === 0 ? (
            <p className="patient-detail-empty">
              Todavía no hay sesiones clínicas registradas.
            </p>
          ) : (
            <div className="patient-detail-list">
              {profile.clinical_sessions.map((session) => (
                <article
                  className="patient-detail-item patient-detail-session"
                  key={session.id}
                >
                  <div>
                    <strong>
                      {formatDateTime(session.session_date)}
                    </strong>

                    {session.duration_minutes !== null && (
                      <p>
                        Duración: {session.duration_minutes} minutos
                      </p>
                    )}

                    <p>
                      {session.summary || 'Sin resumen registrado.'}
                    </p>

                    {session.notes && (
                      <details>
                        <summary>Ver notas de la sesión</summary>
                        <p className="patient-detail-notes">
                          {session.notes}
                        </p>
                      </details>
                    )}
                  </div>
                </article>
              ))}
            </div>
          )}
        </section>
      </div>
    </section>
  )
}
