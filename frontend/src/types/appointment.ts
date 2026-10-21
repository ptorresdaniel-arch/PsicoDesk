
export type AppointmentStatus =
  | 'scheduled'
  | 'confirmed'
  | 'completed'
  | 'cancelled'
  | 'no_show'

export interface AppointmentCalendarRead {
  id: string
  patient_name: string
  start_time: string
  end_time: string
  status: AppointmentStatus
  title: string | null
}

export interface AppointmentCreateInput {
  patient_id: string
  start_time: string
  end_time: string
  title?: string | null
  reason?: string | null
  notes?: string | null
  timezone?: string
}

export interface AppointmentRead {
  id: string
  professional_id: string
  patient_id: string
  start_time: string
  end_time: string
  status: AppointmentStatus
  title: string | null
  reason: string | null
  notes: string | null
  timezone: string
  created_at: string
  updated_at: string
}

export interface AppointmentUpdateInput {
  start_time?: string
  end_time?: string
  status?: AppointmentStatus
  title?: string | null
  reason?: string | null
  notes?: string | null
}
