"""
Password hashing and JWT token utilities.
"""
from datetime import datetime, timedelta, timezone
from typing import Any, Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
# passlib's legacy `crypt` fallback backend triggers a Python 3.13 deprecation
# warning on import; bcrypt is used exclusively above so this is inert, but we
# avoid importing the fallback path at all where possible.


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, extra_claims: Optional[dict[str, Any]] = None) -> str:
    return _create_token(
        subject,
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        token_type="access",
        extra_claims=extra_claims,
    )


def create_refresh_token(subject: str) -> str:
    return _create_token(
        subject,
        expires_delta=timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES),
        token_type="refresh",
    )


def _create_token(
    subject: str,
    expires_delta: timedelta,
    token_type: str,
    extra_claims: Optional[dict[str, Any]] = None,
) -> str:
    now = datetime.now(timezone.utc)
    to_encode: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + expires_delta,
        "type": token_type,
    }
    if extra_claims:
        to_encode.update(extra_claims)
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc
