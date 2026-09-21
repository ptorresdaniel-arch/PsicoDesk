from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PatientCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)

    identification: str | None = Field(default=None, max_length=50)
    birth_date: date | None = None
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    notes: str | None = None

class PatientUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    
    identification: str | None = Field(default=None, max_length=50)
    birth_date: date | None = None
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=30)
    notes: str | None = None
    is_active: bool | None = None


class PatientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    professional_id: UUID

    first_name: str
    last_name: str
    identification: str | None
    birth_date: date | None
    email: EmailStr | None
    phone: str | None
    notes: str | None

    is_active: bool
    created_at: datetime
    updated_at: datetime