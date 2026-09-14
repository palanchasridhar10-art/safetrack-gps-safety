import logging
from typing import Optional

import phonenumbers
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

from app.config import settings
from app.deps import get_current_user
from app.models.models import User
from app.services import whatsapp_service

logger = logging.getLogger("safetrack.whatsapp_router")

router = APIRouter(prefix="/api/whatsapp", tags=["whatsapp"])


class TestWhatsAppRequest(BaseModel):
    phone_number: str


class WhatsAppConfigUpdate(BaseModel):
    access_token: Optional[str] = None
    phone_number_id: Optional[str] = None
    business_account_id: Optional[str] = None
    webhook_verify_token: Optional[str] = None


@router.get("/status")
def get_whatsapp_status(user: User = Depends(get_current_user)):
    """Returns the current operational status of the WhatsApp API server."""
    is_configured = whatsapp_service._is_cloud_api_configured()
    masked_phone_id = None
    if settings.WHATSAPP_PHONE_NUMBER_ID:
        raw = settings.WHATSAPP_PHONE_NUMBER_ID
        masked_phone_id = raw[:3] + "..." + raw[-4:] if len(raw) > 7 else "***"

    return {
        "status": "online",
        "mode": "cloud_api" if is_configured else "click_to_chat",
        "is_configured": is_configured,
        "phone_number_id": masked_phone_id,
        "api_version": settings.WHATSAPP_API_VERSION,
        "webhook_endpoint": "/api/whatsapp/webhook",
        "webhook_verify_token": settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN,
    }


@router.post("/test")
def test_whatsapp(payload: TestWhatsAppRequest, user: User = Depends(get_current_user)):
    """Sends a test WhatsApp alert to a phone number to test connectivity."""
    try:
        parsed = phonenumbers.parse(payload.phone_number, None)
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid phone number. Include country code, e.g. +91XXXXXXXXXX")
        normalized_phone = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    except phonenumbers.NumberParseException:
        raise HTTPException(status_code=400, detail="Invalid phone number. Include country code, e.g. +91XXXXXXXXXX")
    except ValueError as err:
        raise HTTPException(status_code=400, detail=str(err))

    success, message, link = whatsapp_service.send_test_message(normalized_phone)
    return {
        "success": success,
        "message": message,
        "phone_number": normalized_phone,
        "mode": "cloud_api" if whatsapp_service._is_cloud_api_configured() else "click_to_chat",
        "link": link,
    }


@router.post("/config")
def update_whatsapp_config(payload: WhatsAppConfigUpdate, user: User = Depends(get_current_user)):
    """Allows updating WhatsApp API credentials directly from the web interface."""
    if payload.access_token is not None:
        settings.WHATSAPP_ACCESS_TOKEN = payload.access_token.strip()
    if payload.phone_number_id is not None:
        settings.WHATSAPP_PHONE_NUMBER_ID = payload.phone_number_id.strip()
    if payload.business_account_id is not None:
        settings.WHATSAPP_BUSINESS_ACCOUNT_ID = payload.business_account_id.strip()
    if payload.webhook_verify_token is not None:
        settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN = payload.webhook_verify_token.strip()

    return {
        "message": "WhatsApp API server settings updated successfully.",
        "is_configured": whatsapp_service._is_cloud_api_configured(),
        "mode": "cloud_api" if whatsapp_service._is_cloud_api_configured() else "click_to_chat",
    }


@router.get("/webhook")
def verify_meta_webhook(
    hub_mode: Optional[str] = Query(None, alias="hub.mode"),
    hub_challenge: Optional[str] = Query(None, alias="hub.challenge"),
    hub_verify_token: Optional[str] = Query(None, alias="hub.verify_token"),
):
    """Meta WhatsApp Cloud API Webhook verification endpoint."""
    if hub_mode == "subscribe" and hub_verify_token == settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified successfully by Meta.")
        return PlainTextResponse(content=hub_challenge, status_code=200)

    logger.warning("WhatsApp webhook verification rejected: token mismatch.")
    raise HTTPException(status_code=403, detail="Verification token mismatch")


@router.post("/webhook")
async def receive_meta_webhook(request: Request):
    """Receives incoming message callbacks and status updates from Meta."""
    try:
        data = await request.json()
        logger.info("Received WhatsApp Webhook event: %s", data)
        # Process message statuses or delivery confirmations here
        return {"status": "received"}
    except Exception as e:
        logger.error("Failed to parse WhatsApp Webhook payload: %s", e)
        return {"status": "error", "detail": str(e)}
