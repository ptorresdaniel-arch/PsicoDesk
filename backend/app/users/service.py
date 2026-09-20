from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.users.models import User
from app.users.schemas import UserCreate

def get_user_by_email(db: Session, email: str) -> User | None:
    statement = select(User).where(User.email == email)
    return db.scalar(statement)

def create_user(db: Session, user_data: UserCreate) -> User:
    user = User(
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        phone=user_data.phone,
        professional_license=user_data.professional_license,
        specialty=user_data.specialty,
)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return user