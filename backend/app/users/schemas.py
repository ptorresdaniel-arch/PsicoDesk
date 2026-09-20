from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    
    phone: str | None = Field(
        default=None,
        max_length=30,
    )
    professional_license: str | None = Field(
        default=None,
        max_length=50,
        )
    specialty: str | None = Field(
        default=None,
        max_length=100,
        )
    
class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id:UUID
    email: EmailStr
    first_name: str
    last_name: str
    
    phone: str | None
    professional_license: str | None
    specialty: str | None
    avatar_path: str | None
    
    is_active: bool
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime
    