from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user, limiter
from app.models.models import User
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    UserPublic,
    VerifyOTPRequest,
    VerifyOTPResponse,
)
from app.security.security import (
    create_access_token,
    create_otp_session_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.services.email_service import send_otp_email
from app.services.otp_service import OTPResult, create_otp_record, verify_otp

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="An account with this email already exists.")

    user = User(
        name=payload.name,
        email=payload.email,
        password_hash=hash_password(payload.password),
        phone=payload.phone,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return RegisterResponse(id=user.id, name=user.name, email=user.email)


@router.post("/login", response_model=LoginResponse)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()

    # Constant-shape response whether or not the user exists / password
    # matches, to avoid user-enumeration — but we still must not proceed
    # with OTP issuance unless credentials are valid.
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password.")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This account is disabled.")

    _, otp_plain = create_otp_record(db, user.id)
    send_otp_email(user.email, otp_plain, settings.OTP_EXPIRE_MINUTES)

    otp_session_token = create_otp_session_token(user.id)

    dev_preview = otp_plain if not settings.SMTP_HOST and settings.ENVIRONMENT != "production" else None

    return LoginResponse(otp_session_token=otp_session_token, dev_otp_preview=dev_preview)


@router.post("/verify-otp", response_model=VerifyOTPResponse)
@limiter.limit(settings.RATE_LIMIT_OTP)
def verify_otp_endpoint(request: Request, payload: VerifyOTPRequest, db: Session = Depends(get_db)):
    token_data = decode_token(payload.otp_session_token)
    if token_data is None or token_data.get("type") != "otp_session":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="OTP session expired. Please log in again.")

    user_id = token_data["sub"]
    result = verify_otp(db, user_id, payload.otp)

    if result == OTPResult.OK:
        user = db.query(User).filter(User.id == user_id).first()
        access_token = create_access_token(user.id)
        return VerifyOTPResponse(access_token=access_token, user=UserPublic.model_validate(user))

    error_map = {
        OTPResult.EXPIRED: "OTP has expired. Please log in again to request a new one.",
        OTPResult.TOO_MANY_ATTEMPTS: "Too many incorrect attempts. Please log in again.",
        OTPResult.INVALID: "Incorrect OTP. Please try again.",
        OTPResult.NOT_FOUND: "No pending OTP found. Please log in again.",
    }
    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=error_map[result])


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    # Stateless JWT: logout is enforced client-side by discarding the token.
    # (For hard server-side revocation, add a token-blocklist table keyed by
    # jti + expiry, checked in get_current_user.)
    return {"message": "Logged out."}


@router.get("/me", response_model=UserPublic)
def me(current_user: User = Depends(get_current_user)):
    return current_user
