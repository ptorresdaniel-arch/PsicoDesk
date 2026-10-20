
export interface PatientRead {
  id: string
  professional_id: string
  first_name: string
  last_name: string
  identification: string | null
  birth_date: string | null
  email: string | null
  phone: string | null
  notes: string | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface PatientListRead {
  items: PatientRead[]
  total: number
  page: number
  limit: number
}

export interface PatientCreateInput {
  first_name: string
  last_name: string
  identification?: string | null
  birth_date?: string | null
  email?: string | null
  phone?: string | null
  notes?: string | null
}

export interface PatientUpdateInput {
  first_name?: string
  last_name?: string
  identification?: string | null
  birth_date?: string | null
  email?: string | null
  phone?: string | null
  notes?: string | null
  is_active?: boolean
}

export interface PatientFilters {
  search?: string
  is_active?: boolean | null
  page?: number
  limit?: number
}

export interface PatientProfileAppointment {
  id: string
  start_time: string
  end_time: string
  status: string
  title: string | null
}

export interface PatientProfileSession {
  id: string
  session_date: string
  duration_minutes: number | null
  summary: string | null
  notes: string | null
}

export interface PatientProfileSummary {
  total_sessions: number
  last_session_date: string | null
  next_appointment_date: string | null
}

export interface PatientProfileRead {
  id: string
  first_name: string
  last_name: string
  email: string | null
  phone: string | null
  summary: PatientProfileSummary
  upcoming_appointments: PatientProfileAppointment[]
  clinical_sessions: PatientProfileSession[]
  last_session: PatientProfileSession | null
}
