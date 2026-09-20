from uuid import UUID, uuid4
from datetime import datetime, timezone

from sqlalchemy import UUID as SQLAlchemyUUID, String, DateTime, Boolean
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
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    
    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )
    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )
    professional_license: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )
    specialty: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    avatar_path: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    
    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc,),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )