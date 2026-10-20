
import type { DashboardRead } from '../types/dashboard'
import type {
  PatientCreateInput,
  PatientFilters,
  PatientListRead,
  PatientRead,
  PatientUpdateInput,
  PatientProfileRead,
} from '../types/patient'

const API_URL =
  import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000'

export interface LoginResponse {
  access_token: string
  token_type: string
}

export interface UserProfile {
  id: string
  email: string
  first_name: string
  last_name: string
}

async function apiRequest<T>(
  path: string,
  options: RequestInit = {},
  token?: string,
): Promise<T> {
  const headers = new Headers(options.headers)

  if (options.body && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    headers,
  })

  if (!response.ok) {
    let message = `Error HTTP ${response.status}`

    try {
      const data = await response.json()
      message =
        typeof data.detail === 'string'
          ? data.detail
          : message
    } catch {
      // La respuesta no contiene JSON.
    }

    throw new Error(message)
  }

  return response.json() as Promise<T>
}

export function login(
  email: string,
  password: string,
): Promise<LoginResponse> {
  return apiRequest<LoginResponse>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  })
}

export function getDashboard(
  token: string,
): Promise<DashboardRead> {
  return apiRequest<DashboardRead>(
    '/dashboard',
    {},
    token,
  )
}

export function getCurrentUser(
  token: string,
): Promise<UserProfile> {
  return apiRequest<UserProfile>('/auth/me', {}, token)
}


export async function getPatients(
  token: string,
  filters: PatientFilters = {},
): Promise<PatientListRead> {
  const params = new URLSearchParams()

  const search = filters.search?.trim()

  // El backend exige un mínimo de dos caracteres.
  if (search && search.length >= 2) {
    params.set('search', search)
  }

  if (filters.is_active !== undefined &&
      filters.is_active !== null) {
    params.set('is_active', String(filters.is_active))
  }

  params.set('page', String(filters.page ?? 1))
  params.set('limit', String(filters.limit ?? 20))

  return apiRequest<PatientListRead>(
    `/patients?${params.toString()}`,
    {},
    token,
  )
}

export function createPatient(
  token: string,
  data: PatientCreateInput,
): Promise<PatientRead> {
  return apiRequest<PatientRead>(
    '/patients',
    {
      method: 'POST',
      body: JSON.stringify(data),
    },
    token,
  )
}


export function getPatient(
  token: string,
  patientId: string,
): Promise<PatientRead> {
  return apiRequest<PatientRead>(
    `/patients/${encodeURIComponent(patientId)}`,
    {},
    token,
  )
}

export function getPatientProfile(
  token: string,
  patientId: string,
): Promise<PatientProfileRead> {
  return apiRequest<PatientProfileRead>(
    `/patients/${encodeURIComponent(patientId)}/profile`,
    {},
    token,
  )
}

export function updatePatient(
  token: string,
  patientId: string,
  data: PatientUpdateInput,
): Promise<PatientRead> {
  return apiRequest<PatientRead>(
    `/patients/${encodeURIComponent(patientId)}`,
    {
      method: 'PATCH',
      body: JSON.stringify(data),
    },
    token,
  )
}
