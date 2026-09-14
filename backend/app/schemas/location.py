from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


class LocationIn(BaseModel):
    latitude: float
    longitude: float
    accuracy: Optional[float] = None

    @field_validator("latitude")
    @classmethod
    def check_lat(cls, v: float) -> float:
        if not (-90.0 <= v <= 90.0):
            raise ValueError("latitude must be between -90 and 90")
        return v

    @field_validator("longitude")
    @classmethod
    def check_lng(cls, v: float) -> float:
        if not (-180.0 <= v <= 180.0):
            raise ValueError("longitude must be between -180 and 180")
        return v


class LocationOut(BaseModel):
    id: str
    latitude: float
    longitude: float
    accuracy: Optional[float] = None
    timestamp: datetime
    map_link: str

    class Config:
        from_attributes = True


class SendLocationResponse(BaseModel):
    location: LocationOut
    whatsapp_links: List[str] = Field(
        description="wa.me click-to-chat links (one per trusted contact) prefilled "
        "with the safety alert message, OR delivery confirmations if the "
        "WhatsApp Business Cloud API is configured."
    )
    delivery_mode: str  # "cloud_api" | "click_to_chat"


class SafetySessionOut(BaseModel):
    id: str
    started_at: datetime
    stopped_at: Optional[datetime] = None
    status: str

    class Config:
        from_attributes = True


class EmergencyEventOut(BaseModel):
    id: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    accuracy: Optional[float] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
