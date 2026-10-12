from uuid import UUID
from pydantic import(
    BaseModel,
    ConfigDict,
    Field,
    )

class RoleCreate(BaseModel):
    name: str = Field(
        min_length=2,
        max_length=50,
    )

class RoleRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )
    id: UUID
    name: str


