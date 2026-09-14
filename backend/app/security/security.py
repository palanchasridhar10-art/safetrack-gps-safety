"""
Security primitives: password hashing and JWT issuing/verification.

- Passwords are hashed with bcrypt (via passlib) — never stored in plain text.
- Two kinds of JWTs are issued:
    1. "otp_session" tokens — short-lived, issued right after password check,
       only usable against /auth/verify-otp. They do NOT grant API access.
    2. "access" tokens — issued after OTP verification, used as the bearer
       token for all authenticated endpoints.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def hash_otp(otp: str) -> str:
    # OTPs are short-lived and low-entropy (6 digits), but we still never
    # store them in plain text — bcrypt hash, same as passwords.
    return pwd_context.hash(otp)


def verify_otp_hash(otp: str, otp_hash: str) -> bool:
    return pwd_context.verify(otp, otp_hash)


def _create_token(data: dict, expires_delta: timedelta) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire, "iat": datetime.now(timezone.utc)})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def create_otp_session_token(user_id: str) -> str:
    return _create_token(
        {"sub": user_id, "type": "otp_session"},
        timedelta(minutes=settings.OTP_SESSION_TOKEN_EXPIRE_MINUTES),
    )


def create_access_token(user_id: str) -> str:
    return _create_token(
        {"sub": user_id, "type": "access"},
        timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None
