"""
OTP lifecycle: generation, hashed storage, verification, expiry and
attempt-limiting. OTP plaintext values are NEVER logged or persisted —
only their bcrypt hash is stored, mirroring how passwords are handled.
"""
import secrets
from datetime import datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.config import settings
from app.models.models import OTPRecord
from app.security.security import hash_otp, verify_otp_hash


def generate_otp() -> str:
    digits = "0123456789"
    return "".join(secrets.choice(digits) for _ in range(settings.OTP_LENGTH))


def create_otp_record(db: Session, user_id: str) -> tuple[OTPRecord, str]:
    """Creates a new OTP record for the user and returns (record, plaintext_otp)."""
    otp_plain = generate_otp()
    record = OTPRecord(
        user_id=user_id,
        otp_hash=hash_otp(otp_plain),
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
        attempts=0,
        verified=False,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record, otp_plain


def get_latest_unverified_otp(db: Session, user_id: str) -> OTPRecord | None:
    return (
        db.query(OTPRecord)
        .filter(OTPRecord.user_id == user_id, OTPRecord.verified.is_(False))
        .order_by(OTPRecord.created_at.desc())
        .first()
    )


class OTPResult:
    OK = "ok"
    EXPIRED = "expired"
    TOO_MANY_ATTEMPTS = "too_many_attempts"
    INVALID = "invalid"
    NOT_FOUND = "not_found"


def verify_otp(db: Session, user_id: str, otp_plain: str) -> str:
    record = get_latest_unverified_otp(db, user_id)
    if record is None:
        return OTPResult.NOT_FOUND

    now = datetime.now(timezone.utc)
    expires_at = record.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)

    if now > expires_at:
        return OTPResult.EXPIRED

    if record.attempts >= settings.OTP_MAX_ATTEMPTS:
        return OTPResult.TOO_MANY_ATTEMPTS

    if not verify_otp_hash(otp_plain, record.otp_hash):
        record.attempts += 1
        db.commit()
        return OTPResult.INVALID

    record.verified = True
    db.commit()
    return OTPResult.OK
