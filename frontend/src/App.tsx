
import { useEffect, useState, type FormEvent } from 'react'
import './App.css'

import { getDashboard, login as loginRequest } from './services/api'
import type {
  DashboardAppointment,
  DashboardRead,
} from './types/dashboard'

import PatientsPage from './pages/PatientsPage'

const TOKEN_KEY = 'psicodesk_token'

type ActiveView = 'dashboard' | 'patients'

function formatTime(value: string): string {
  return new Date(value).toLocaleTimeString('es-CL', {
    hour: '2-digit',
    minute: '2-digit',
  })
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
  return 'other'
}

function App() {
  const [token, setToken] = useState<string | null>(
    () => localStorage.getItem(TOKEN_KEY),
  )

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const [dashboard, setDashboard] =
    useState<DashboardRead | null>(null)

  const [loading, setLoading] = useState(
    () => Boolean(localStorage.getItem(TOKEN_KEY)),
  )

  const [loggingIn, setLoggingIn] = useState(false)
  const [error, setError] = useState('')
  const [activeView, setActiveView] =
    useState<ActiveView>('dashboard')

  // Cargar los datos reales del dashboard.
  useEffect(() => {
    if (!token) return

    let cancelled = false

    getDashboard(token)
      .then((data) => {
        if (!cancelled) {
          setDashboard(data)
        }
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(
            err instanceof Error
              ? err.message
              : 'No se pudo cargar el dashboard.',
          )
        }
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [token])

  // Iniciar sesión.
  async function handleLogin(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    setLoggingIn(true)
    setError('')

    try {
      const result = await loginRequest(email, password)

      localStorage.setItem(TOKEN_KEY, result.access_token)

      setLoading(true)
      setDashboard(null)
      setActiveView('dashboard')
      setToken(result.access_token)
      setPassword('')
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : 'No se pudo iniciar sesión.',
      )
    } finally {
      setLoggingIn(false)
    }
  }

  // Cerrar sesión.
  function handleLogout() {
    localStorage.removeItem(TOKEN_KEY)

    setToken(null)
    setDashboard(null)
    setLoading(false)
    setError('')
    setPassword('')
    setActiveView('dashboard')
  }

  // Pantalla de inicio de sesión.
  if (!token) {
    return (
      <main className="login-page">
        <section className="login-card">
          <a className="brand login-brand" href="#inicio">
            <span className="brand-logo">P</span>

            <span className="brand-text">
              <strong>PsicoDesk</strong>
              <small>Gestión clínica</small>
            </span>
          </a>

          <h1>Bienvenido</h1>

          <p>
            Inicia sesión para acceder a tu espacio de trabajo.
          </p>

          <form className="login-form" onSubmit={handleLogin}>
            <label className="form-field">
              Correo electrónico

              <input
                type="email"
                value={email}
                onChange={(event) =>
                  setEmail(event.target.value)
                }
                autoComplete="username"
                required
              />
            </label>

            <label className="form-field">
              Contraseña

              <input
                type="password"
                value={password}
                onChange={(event) =>
                  setPassword(event.target.value)
                }
                autoComplete="current-password"
                required
              />
            </label>

            {error && (
              <p className="error-banner" role="alert">
                {error}
              </p>
            )}

            <button
              className="primary-button login-submit"
              type="submit"
              disabled={loggingIn}
            >
              {loggingIn
                ? 'Iniciando sesión…'
                : 'Iniciar sesión'}
            </button>
          </form>
        </section>
      </main>
    )
  }

  // Indicador de carga inicial.
  if (loading && !dashboard) {
    return (
      <main
        className="loading-page"
        aria-live="polite"
        aria-busy="true"
      >
        <span className="loading-spinner" />

        <h1>PsicoDesk</h1>

        <p>Cargando tu espacio de trabajo…</p>

        <p className="loading-detail">
          Estamos preparando los datos de tu consulta.
        </p>
      </main>
    )
  }

  // Error al cargar el dashboard.
  if (!dashboard) {
    return (
      <main className="state-page">
        <h1>No se pudo cargar PsicoDesk</h1>

        <p className="error-banner" role="alert">
          {error || 'No se recibieron datos del dashboard.'}
        </p>

        <button
          className="primary-button"
          type="button"
          onClick={handleLogout}
        >
          Volver al inicio de sesión
        </button>
      </main>
    )
  }

  // Tarjetas de resumen.
  const stats = [
    {
      label: 'Pacientes activos',
      value: dashboard.total_patients,
      detail: 'Pacientes registrados',
      icon: '♧',
      color: 'purple',
    },
    {
      label: 'Citas de hoy',
      value: dashboard.today_appointments.length,
      detail: 'Citas programadas para hoy',
      icon: '▦',
      color: 'blue',
    },
    {
      label: 'Próximas citas',
      value: dashboard.upcoming_appointments,
      detail: 'Citas futuras programadas o confirmadas',
      icon: '◷',
      color: 'orange',
    },
    {
      label: 'Sesiones recientes',
      value: dashboard.recent_sessions.length,
      detail: 'Últimos registros cargados (máx. 5)',
      icon: '✓',
      color: 'green',
    },
  ]

  // Accesos rápidos.
  const shortcuts = [
    {
      title: 'Pacientes',
      description: 'Consultar y gestionar fichas',
      icon: '♧',
      color: 'purple',
      href: '#pacientes',
    },
    {
      title: 'Agenda',
      description: 'Consultar las citas',
      icon: '▦',
      color: 'blue',
      href: '#agenda',
    },
    {
      title: 'Sesiones clínicas',
      description: 'Consultar las sesiones',
      icon: '✓',
      color: 'green',
      href: '#sesiones',
    },
  ]

  return (
    <div className="app-shell" id="inicio">
      <aside className="sidebar">
        <a
          className="brand"
          href="#inicio"
          onClick={() => setActiveView('dashboard')}
        >
          <span className="brand-logo">P</span>

          <span className="brand-text">
            <strong>PsicoDesk</strong>
            <small>Gestión clínica</small>
          </span>
        </a>

        <div className="nav-label">Menú principal</div>

        <nav
          className="navigation"
          aria-label="Menú principal"
        >
          <a
            className={`nav-link ${
              activeView === 'dashboard' ? 'active' : ''
            }`}
            href="#inicio"
            onClick={(event) => {
              event.preventDefault()
              setActiveView('dashboard')
            }}
          >
            <span className="nav-icon">⌂</span>
            Inicio
          </a>

          <a
            className={`nav-link ${
              activeView === 'patients' ? 'active' : ''
            }`}
            href="#pacientes"
            onClick={(event) => {
              event.preventDefault()
              setActiveView('patients')
            }}
          >
            <span className="nav-icon">♧</span>
            Pacientes
          </a>

          <a className="nav-link" href="#agenda">
            <span className="nav-icon">▦</span>
            Agenda
          </a>

          <a className="nav-link" href="#sesiones">
            <span className="nav-icon">✓</span>
            Sesiones clínicas
          </a>

          <a className="nav-link" href="#configuracion">
            <span className="nav-icon">⚙</span>
            Configuración
          </a>
        </nav>

        <div className="sidebar-profile">
          <div className="avatar">PS</div>

          <div>
            <strong>Profesional</strong>
            <small>Espacio de trabajo</small>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="page-header">
          <div>
            <span className="eyebrow">
              Espacio de trabajo
            </span>

            <h1>
              {activeView === 'patients'
                ? 'Gestión de pacientes'
                : 'Buenos días'}
            </h1>

            <p>
              {activeView === 'patients'
                ? 'Consulta y administra las fichas de tus pacientes.'
                : 'Aquí tienes un resumen de tu consulta.'}
            </p>
          </div>

          <div className="header-actions">
            {activeView === 'dashboard' && (
              <a className="primary-button" href="#agenda">
                Ver agenda
                <span aria-hidden="true">→</span>
              </a>
            )}

            <button
              className="secondary-button"
              type="button"
              onClick={handleLogout}
            >
              Cerrar sesión
            </button>
          </div>
        </header>

        {activeView === 'patients' ? (
          <PatientsPage token={token} />
        ) : (
          <>
            {error && (
              <div className="error-banner" role="alert">
                No se pudo actualizar el dashboard: {error}
              </div>
            )}

            <section
              className="stats-grid"
              aria-label="Resumen de actividad"
            >
              {stats.map((stat) => (
                <article
                  className="stat-card"
                  key={stat.label}
                >
                  <div className="stat-heading">
                    <span
                      className={`icon-box ${stat.color}`}
                    >
                      {stat.icon}
                    </span>

                    <span>{stat.label}</span>
                  </div>

                  <div className="stat-value">
                    {stat.value}
                  </div>

                  <p className="stat-detail">
                    {stat.detail}
                  </p>
                </article>
              ))}
            </section>

            <section className="dashboard-grid">
              <article className="panel" id="agenda">
                <div className="panel-header">
                  <div>
                    <h2>Agenda de hoy</h2>
                    <p>Citas obtenidas de tu consulta</p>
                  </div>
                </div>

                <div className="appointment-list">
                  {dashboard.today_appointments.length ===
                  0 ? (
                    <p className="empty-state">
                      No tienes citas programadas para hoy.
                    </p>
                  ) : (
                    dashboard.today_appointments.map(
                      (appointment: DashboardAppointment) => (
                        <div
                          className="appointment-row"
                          key={appointment.id}
                        >
                          <time className="appointment-time">
                            {formatTime(
                              appointment.start_time,
                            )}
                          </time>

                          <div className="appointment-info">
                            <strong>
                              {appointment.patient_name}
                            </strong>

                            <span>
                              Hasta las{' '}
                              {formatTime(
                                appointment.end_time,
                              )}
                            </span>
                          </div>

                          <span
                            className={`status ${statusClass(
                              appointment.status,
                            )}`}
                          >
                            {statusLabel(appointment.status)}
                          </span>
                        </div>
                      ),
                    )
                  )}
                </div>
              </article>

              <article className="panel" id="accesos">
                <div className="panel-header">
                  <div>
                    <h2>Accesos rápidos</h2>
                    <p>Áreas principales de PsicoDesk</p>
                  </div>
                </div>

                <div className="shortcut-list">
                  {shortcuts.map((shortcut) => (
                    <a
                      className="shortcut-row"
                      href={shortcut.href}
                      key={shortcut.title}
                      onClick={(event) => {
                        if (
                          shortcut.title === 'Pacientes'
                        ) {
                          event.preventDefault()
                          setActiveView('patients')
                        }
                      }}
                    >
                      <span
                        className={`icon-box ${shortcut.color}`}
                      >
                        {shortcut.icon}
                      </span>

                      <span className="shortcut-info">
                        <strong>{shortcut.title}</strong>

                        <small>
                          {shortcut.description}
                        </small>
                      </span>

                      <span
                        className="shortcut-arrow"
                        aria-hidden="true"
                      >
                        →
                      </span>
                    </a>
                  ))}
                </div>
              </article>
            </section>
          </>
        )}

        <footer className="page-footer">
          PsicoDesk <span>·</span> Aplicación en desarrollo
        </footer>
      </main>
    </div>
  )
}

export default App
