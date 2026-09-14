from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field, field_validator

import phonenumbers


class ContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    phone: str
    relationship_label: Optional[str] = Field(default=None, max_length=60)
    email: Optional[EmailStr] = None

    @field_validator("phone")
    @classmethod
    def validate_and_normalize_phone(cls, v: str) -> str:
        try:
            parsed = phonenumbers.parse(v, None)
        except phonenumbers.NumberParseException:
            raise ValueError(
                "Invalid phone number. Include the country code, e.g. +91XXXXXXXXXX"
            )
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid phone number for the given country code.")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


class ContactUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    phone: Optional[str] = None
    relationship_label: Optional[str] = None
    email: Optional[EmailStr] = None

    @field_validator("phone")
    @classmethod
    def validate_and_normalize_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        try:
            parsed = phonenumbers.parse(v, None)
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid phone number. Include the country code.")
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid phone number for the given country code.")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)


class ContactPublic(BaseModel):
    id: str
    name: str
    phone: str
    relationship_label: Optional[str] = None
    email: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
