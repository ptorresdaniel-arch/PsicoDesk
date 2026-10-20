
export interface DashboardAppointment {
  id: string
  patient_name: string
  start_time: string
  end_time: string
  status: string
}

export interface DashboardSession {
  id: string
  patient_name: string
  session_date: string
}

export interface DashboardRead {
  total_patients: number
  today_appointments: DashboardAppointment[]
  upcoming_appointments: number
  recent_sessions: DashboardSession[]
}
