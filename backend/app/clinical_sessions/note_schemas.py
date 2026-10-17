from datetime import datetime
from uuid import UUID

from pydantic import(
    BaseModel,
    Field,
    field_validator,
)



class ClinicalSessionNoteCreate(BaseModel):
    content: str = Field(
        min_length=1,
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        if not value.strip():
            raise ValueError(
                "El contenido de la nota no puede estar vacío."
            )

        return value


class ClinicalSessionNoteRead(BaseModel):
    id: UUID

    clinical_session_id: UUID

    content: str

    created_by: UUID

    created_at: datetime

    model_config = {
        "from_attributes": True
    }