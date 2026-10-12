from uuid import UUID

from pydantic import(
    BaseModel,
    ConfigDict,
    Field,
)

class PermissionCreate(BaseModel):
    code: str = Field(
        min_length=3,
        max_length=100,
    )

class PermissionRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    code: str