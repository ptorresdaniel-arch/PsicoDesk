from datetime import datetime, timezone, timedelta
from uuid import UUID

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

from app.core.config import settings

password_hasher = PasswordHasher()

def hash_password(password: str) -> str:
    return password_hasher.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    try:
        return password_hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False
    

def create_access_token(user_id: UUID) -> str:
    expires_at= datetime.now(timezone.utc) + timedelta(
        minutes= settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
    )
    
    payload = {
        "sub": str(user_id),
        "exp": expires_at,
    }
    
    return jwt.encode(
        payload,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )