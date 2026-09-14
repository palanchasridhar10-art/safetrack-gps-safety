from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.models import LocationRecord, SafetySession, SafetySessionStatus, TrustedContact, User
from app.schemas.location import LocationIn, LocationOut, SafetySessionOut, SendLocationResponse
from app.services.whatsapp_service import build_map_link, send_location_alert

router = APIRouter(prefix="/api/safety", tags=["safety"])


def _require_two_contacts(db: Session, user_id: str) -> list[TrustedContact]:
    contacts = db.query(TrustedContact).filter(TrustedContact.user_id == user_id).all()
    if len(contacts) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please add two trusted contacts before starting safety tracking.",
        )
    return contacts


@router.post("/start", response_model=SafetySessionOut, status_code=status.HTTP_201_CREATED)
def start_tracking(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    _require_two_contacts(db, current_user.id)

    active = (
        db.query(SafetySession)
        .filter(SafetySession.user_id == current_user.id, SafetySession.status == SafetySessionStatus.ACTIVE)
        .first()
    )
    if active:
        return active

    session = SafetySession(user_id=current_user.id, status=SafetySessionStatus.ACTIVE)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.post("/update-location", response_model=SendLocationResponse)
def update_location(
    payload: LocationIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Called periodically by the frontend while Mode B tracking is active.

    Every update still goes through the same trusted-contact requirement and
    is persisted, but does NOT re-send a WhatsApp alert on every ping (that
    would spam the contacts) — only the location log and 'latest' pointer
    are updated. Use /location/current or /emergency/sos to actually notify.
    """
    session = (
        db.query(SafetySession)
        .filter(SafetySession.user_id == current_user.id, SafetySession.status == SafetySessionStatus.ACTIVE)
        .order_by(SafetySession.started_at.desc())
        .first()
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active safety session. Start tracking first.")

    record = LocationRecord(
        user_id=current_user.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy=payload.accuracy,
        session_id=session.id,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    location_out = LocationOut(
        id=record.id,
        latitude=record.latitude,
        longitude=record.longitude,
        accuracy=record.accuracy,
        timestamp=record.timestamp,
        map_link=build_map_link(record.latitude, record.longitude),
    )
    return SendLocationResponse(location=location_out, whatsapp_links=[], delivery_mode="logged_only")


@router.post("/stop", response_model=SafetySessionOut)
def stop_tracking(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = (
        db.query(SafetySession)
        .filter(SafetySession.user_id == current_user.id, SafetySession.status == SafetySessionStatus.ACTIVE)
        .order_by(SafetySession.started_at.desc())
        .first()
    )
    if session is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No active safety session.")

    session.status = SafetySessionStatus.STOPPED
    session.stopped_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(session)
    return session


@router.get("/status", response_model=SafetySessionOut | None)
def tracking_status(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    session = (
        db.query(SafetySession)
        .filter(SafetySession.user_id == current_user.id, SafetySession.status == SafetySessionStatus.ACTIVE)
        .order_by(SafetySession.started_at.desc())
        .first()
    )
    return session
