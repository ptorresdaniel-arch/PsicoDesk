from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ClinicalSessionNoteCreate(BaseModel):
    content: str = Field(
        min_length=1,
    )


class ClinicalSessionNoteRead(BaseModel):
    id: UUID

    clinical_session_id: UUID

    content: str

    created_by: UUID

    created_at: datetime

    model_config = {
        "from_attributes": True
    }