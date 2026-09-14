from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator


class RegisterRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    phone: Optional[str] = None

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        if not any(c.isalpha() for c in v):
            raise ValueError("Password must contain at least one letter")
        return v


class RegisterResponse(BaseModel):
    id: str
    name: str
    email: EmailStr
    message: str = "Account created. Please log in."


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    otp_session_token: str
    message: str = "OTP sent to your registered email."
    # Included ONLY in development mode (no SMTP configured) so the flow is
    # testable end-to-end without a real mail server. Never populated in
    # production — see otp_service.py.
    dev_otp_preview: Optional[str] = None


class VerifyOTPRequest(BaseModel):
    otp_session_token: str
    otp: str = Field(min_length=4, max_length=8)


class VerifyOTPResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserPublic"


class UserPublic(BaseModel):
    id: str
    name: str
    email: EmailStr
    phone: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


VerifyOTPResponse.model_rebuild()
