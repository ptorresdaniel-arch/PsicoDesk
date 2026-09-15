from uuid import UUID, uuid4

from sqlalchemy import UUID as SQLAlchemyUUID, String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(
        SQLAlchemyUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        index=True,
        nullable=False,
    )
