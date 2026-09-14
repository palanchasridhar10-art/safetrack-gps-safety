from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.deps import get_current_user, limiter
from app.models.models import EmergencyEvent, TrustedContact, User
from app.schemas.location import EmergencyEventOut, SendLocationResponse
from app.schemas.location import LocationOut
from app.services.whatsapp_service import build_map_link, send_location_alert

router = APIRouter(prefix="/api/emergency", tags=["emergency"])


class SOSRequest(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None


@router.post("/sos", response_model=SendLocationResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(settings.RATE_LIMIT_SOS)
def trigger_sos(
    request: Request,
    payload: SOSRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    contacts = db.query(TrustedContact).filter(TrustedContact.user_id == current_user.id).all()
    if len(contacts) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please add two trusted contacts before using SOS.",
        )

    event = EmergencyEvent(
        user_id=current_user.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy=payload.accuracy,
        status="triggered",
    )
    db.add(event)
    db.commit()
    db.refresh(event)

    if payload.latitude is None or payload.longitude is None:
        # Still record the event, but there is nothing to send without
        # coordinates — the frontend should retry once GPS resolves.
        location_out = LocationOut(
            id=event.id,
            latitude=0.0,
            longitude=0.0,
            accuracy=None,
            timestamp=event.created_at,
            map_link="",
        )
        return SendLocationResponse(location=location_out, whatsapp_links=[], delivery_mode="no_location")

    links, mode = send_location_alert(
        contact_phones=[c.phone for c in contacts],
        user_name=current_user.name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy=payload.accuracy,
        timestamp_str=event.created_at.strftime("%d %B %Y, %I:%M %p UTC"),
        is_emergency=True,
    )
    event.status = "sent" if mode == "cloud_api" else "link_generated"
    db.commit()

    location_out = LocationOut(
        id=event.id,
        latitude=payload.latitude,
        longitude=payload.longitude,
        accuracy=payload.accuracy,
        timestamp=event.created_at,
        map_link=build_map_link(payload.latitude, payload.longitude),
    )
    return SendLocationResponse(location=location_out, whatsapp_links=links, delivery_mode=mode)


@router.get("/history", response_model=List[EmergencyEventOut])
def emergency_history(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return (
        db.query(EmergencyEvent)
        .filter(EmergencyEvent.user_id == current_user.id)
        .order_by(EmergencyEvent.created_at.desc())
        .all()
    )
