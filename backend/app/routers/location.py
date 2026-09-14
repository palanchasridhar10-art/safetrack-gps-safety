from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models.models import LocationRecord, TrustedContact, User
from app.schemas.location import LocationIn, LocationOut, SendLocationResponse
from app.services.whatsapp_service import build_map_link, send_location_alert

router = APIRouter(prefix="/api/location", tags=["location"])


def _require_two_contacts(db: Session, user_id: str) -> list[TrustedContact]:
    contacts = db.query(TrustedContact).filter(TrustedContact.user_id == user_id).all()
    if len(contacts) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please add two trusted contacts before using safety sharing.",
        )
    return contacts


def _to_out(record: LocationRecord) -> LocationOut:
    return LocationOut(
        id=record.id,
        latitude=record.latitude,
        longitude=record.longitude,
        accuracy=record.accuracy,
        timestamp=record.timestamp,
        map_link=build_map_link(record.latitude, record.longitude),
    )


@router.post("/current", response_model=SendLocationResponse)
def send_current_location(
    payload: LocationIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contacts = _require_two_contacts(db, current_user.id)

    record = LocationRecord(
        user_id=current_user.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy=payload.accuracy,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    links, mode = send_location_alert(
        contact_phones=[c.phone for c in contacts],
        user_name=current_user.name,
        latitude=record.latitude,
        longitude=record.longitude,
        accuracy=record.accuracy,
        timestamp_str=record.timestamp.strftime("%d %B %Y, %I:%M %p UTC"),
    )

    return SendLocationResponse(location=_to_out(record), whatsapp_links=links, delivery_mode=mode)


@router.get("/latest", response_model=LocationOut)
def get_latest_location(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    record = (
        db.query(LocationRecord)
        .filter(LocationRecord.user_id == current_user.id)
        .order_by(LocationRecord.timestamp.desc())
        .first()
    )
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No location shared yet.")
    return _to_out(record)
