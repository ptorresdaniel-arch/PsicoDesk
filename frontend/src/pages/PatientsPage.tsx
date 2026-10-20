
import { useEffect, useState, type FormEvent } from 'react'
import { createPatient, getPatients } from '../services/api'
import type {
  PatientCreateInput,
  PatientListRead,
} from '../types/patient'

interface PatientsPageProps {
  token: string
}

type ActiveFilter = 'all' | 'active' | 'inactive'

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

const EMPTY_LIST: PatientListRead = {
  items: [],
  total: 0,
  page: 1,
  limit: 20,
}

function formatDate(value: string | null): string {
  if (!value) return '—'

  const date = new Date(`${value.slice(0, 10)}T12:00:00`)

  return date.toLocaleDateString('es-CL')
}

export default function PatientsPage({
  token,
}: PatientsPageProps) {
  const [result, setResult] = useState(EMPTY_LIST)
  const [search, setSearch] = useState('')
  const [appliedSearch, setAppliedSearch] = useState('')
  const [activeFilter, setActiveFilter] =
    useState<ActiveFilter>('all')
  const [page, setPage] = useState(1)
  const [reloadKey, setReloadKey] = useState(0)

  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState<PatientForm>(EMPTY_FORM)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')

  useEffect(() => {
    let cancelled = false

    getPatients(token, {
      search: appliedSearch,
      is_active:
        activeFilter === 'all'
          ? null
          : activeFilter === 'active',
      page,
      limit: 20,
    })
      .then((data) => {
        if (cancelled) return

        setResult(data)
        setError('')
      })
      .catch((err: unknown) => {
        if (cancelled) return

        setError(
          err instanceof Error
            ? err.message
            : 'No se pudieron cargar los pacientes.',
        )
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [token, appliedSearch, activeFilter, page, reloadKey])

  function handleSearch(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    setLoading(true)
    setError('')
    setSuccess('')
    setPage(1)
    setAppliedSearch(search.trim())
    setReloadKey((current) => current + 1)
  }

  function handleFilterChange(value: ActiveFilter) {
    setLoading(true)
    setError('')
    setSuccess('')
    setPage(1)
    setActiveFilter(value)
    setReloadKey((current) => current + 1)
  }

  async function handleCreatePatient(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    setSaving(true)
    setError('')
    setSuccess('')

    const data: PatientCreateInput = {
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      identification: form.identification.trim() || null,
      birth_date: form.birth_date || null,
      email: form.email.trim() || null,
      phone: form.phone.trim() || null,
      notes: form.notes.trim() || null,
    }

    try {
      await createPatient(token, data)

      setForm(EMPTY_FORM)
      setShowForm(false)
      setSuccess('Paciente registrado correctamente.')
      setLoading(true)
      setPage(1)
      setReloadKey((current) => current + 1)
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : 'No se pudo registrar el paciente.',
      )
    } finally {
      setSaving(false)
    }
  }

  const totalPages = Math.max(
    1,
    Math.ceil(result.total / result.limit),
  )

  return (
    <section className="patients-page">
      <div className="patients-toolbar">
        <div>
          <span className="eyebrow">Gestión clínica</span>
          <h2>Directorio de pacientes</h2>
          <p>
            Consulta y administra los pacientes de tu consulta.
          </p>
        </div>

        <button
          className="primary-button"
          type="button"
          onClick={() => {
            setShowForm((current) => !current)
            setError('')
            setSuccess('')
          }}
        >
          {showForm ? 'Cancelar' : '+ Nuevo paciente'}
        </button>
      </div>

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
          className="panel patient-form"
          onSubmit={handleCreatePatient}
        >
          <div className="panel-header">
            <div>
              <h2>Registrar paciente</h2>
              <p>
                Los campos marcados con * son obligatorios.
              </p>
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
              Identificación
              <input
                maxLength={50}
                value={form.identification}
                onChange={(event) =>
                  setForm({
                    ...form,
                    identification: event.target.value,
                  })
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

          <div className="patient-form-actions">
            <button
              className="secondary-button"
              type="button"
              disabled={saving}
              onClick={() => {
                setShowForm(false)
                setForm(EMPTY_FORM)
                setError('')
              }}
            >
              Cancelar
            </button>

            <button
              className="primary-button"
              type="submit"
              disabled={saving}
            >
              {saving ? 'Guardando…' : 'Guardar paciente'}
            </button>
          </div>
        </form>
      )}

      <section className="panel patient-directory">
        <form
          className="patient-filters"
          onSubmit={handleSearch}
        >
          <label className="patient-search">
            <span>Buscar paciente</span>
            <input
              type="search"
              placeholder="Nombre, apellido o identificación"
              value={search}
              onChange={(event) =>
                setSearch(event.target.value)
              }
            />
          </label>

          <label className="patient-status-filter">
            <span>Estado</span>
            <select
              value={activeFilter}
              onChange={(event) =>
                handleFilterChange(
                  event.target.value as ActiveFilter,
                )
              }
            >
              <option value="all">Todos</option>
              <option value="active">Activos</option>
              <option value="inactive">Inactivos</option>
            </select>
          </label>

          <button
            className="secondary-button"
            type="submit"
          >
            Buscar
          </button>
        </form>

        <div className="patient-results-heading">
          <div>
            <h2>Pacientes registrados</h2>
            <p>
              {result.total}{' '}
              {result.total === 1 ? 'resultado' : 'resultados'}
            </p>
          </div>
        </div>

        {loading ? (
          <div className="patients-loading" role="status">
            <span className="loading-spinner" />
            <p>Cargando pacientes…</p>
          </div>
        ) : result.items.length === 0 ? (
          <div className="patients-empty">
            <div className="patients-empty-icon" aria-hidden="true">
              ♧
            </div>
            <h3>No se encontraron pacientes</h3>
            <p>
              Prueba otra búsqueda o registra un nuevo paciente.
            </p>
            <button
              className="primary-button"
              type="button"
              onClick={() => setShowForm(true)}
            >
              + Nuevo paciente
            </button>
          </div>
        ) : (
          <>
            <div className="patient-table-wrap">
              <table className="patient-table">
                <thead>
                  <tr>
                    <th>Paciente</th>
                    <th>Identificación</th>
                    <th>Contacto</th>
                    <th>Fecha de nacimiento</th>
                    <th>Estado</th>
                  </tr>
                </thead>

                <tbody>
                  {result.items.map((patient) => (
                    <tr key={patient.id}>
                      <td>
                        <div className="patient-name-cell">
                          <span className="patient-avatar">
                            {patient.first_name
                              .charAt(0)
                              .toUpperCase()}
                            {patient.last_name
                              .charAt(0)
                              .toUpperCase()}
                          </span>
                          <div>
                            <strong>
                              {patient.first_name}{' '}
                              {patient.last_name}
                            </strong>
                            <small>{patient.email || 'Sin correo'}</small>
                          </div>
                        </div>
                      </td>

                      <td>{patient.identification || '—'}</td>

                      <td>{patient.phone || '—'}</td>

                      <td>{formatDate(patient.birth_date)}</td>

                      <td>
                        <span
                          className={`patient-state ${
                            patient.is_active ? 'active' : 'inactive'
                          }`}
                        >
                          {patient.is_active ? 'Activo' : 'Inactivo'}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div className="patient-pagination">
              <span>
                Página {result.page} de {totalPages}
              </span>

              <div>
                <button
                  className="secondary-button"
                  type="button"
                  disabled={page <= 1 || loading}
                  onClick={() => {
                    setLoading(true)
                    setPage((current) => current - 1)
                  }}
                >
                  Anterior
                </button>

                <button
                  className="secondary-button"
                  type="button"
                  disabled={page >= totalPages || loading}
                  onClick={() => {
                    setLoading(true)
                    setPage((current) => current + 1)
                  }}
                >
                  Siguiente
                </button>
              </div>
            </div>
          </>
        )}
      </section>
    </section>
  )
}
