
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

export interface PatientFilters {
  search?: string
  is_active?: boolean | null
  page?: number
  limit?: number
}
