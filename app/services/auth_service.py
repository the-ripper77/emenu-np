import datetime
import hashlib
import secrets
from typing import Optional

from app.config import settings


def hash_password(password: str) -> str:
    import bcrypt
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    import bcrypt
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


def generate_reset_token() -> str:
    return secrets.token_urlsafe(32)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def create_access_token(
    subject: str,
    role: str,
    user_type: str,
    expires_delta: Optional[datetime.timedelta] = None,
    expires_minutes: Optional[int] = None,
) -> str:
    from jose import jwt
    if expires_minutes is not None:
        expire = datetime.datetime.now(datetime.UTC) + datetime.timedelta(minutes=expires_minutes)
    else:
        expire = datetime.datetime.now(datetime.UTC) + (
            expires_delta or datetime.timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES)
        )
    payload = {
        "sub": subject,
        "role": role,
        "type": user_type,
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    from jose import JWTError, jwt
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
