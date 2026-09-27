from dataclasses import dataclass

from fastapi import Query


@dataclass
class PatientFilters:
    search: str | None = Query(
        default=None,
        min_length=2,
    )

    is_active: bool | None = Query(
        default=None,
    )
    
    page: int = Query(
        default=1,
        ge=1,
    )
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    )