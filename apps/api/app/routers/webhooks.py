"""Webhook endpoints for inbound channels (SMS, email, web form)."""
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.ext.asyncio import AsyncSession
from twilio.request_validator import RequestValidator

from app.database import get_db
from app.config import settings
from app.schemas.webhooks import TwilioInboundSMS, EmailInbound, WebFormSubmission
from app.services.intake import process_sms_intake, process_email_intake, process_form_intake
from app.services.audit import log_event

import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/webhooks", tags=["webhooks"])


@router.post("/twilio/inbound", response_class=PlainTextResponse)
async def twilio_inbound_sms(request: Request, db: AsyncSession = Depends(get_db)):
    """Receive inbound SMS/MMS from Twilio."""
    form_data = await request.form()
    data = dict(form_data)

    # Validate Twilio signature in production
    if settings.twilio_auth_token:
        validator = RequestValidator(settings.twilio_auth_token)
        url = str(request.url)
        signature = request.headers.get("X-Twilio-Signature", "")
        if not validator.validate(url, data, signature):
            logger.warning("Invalid Twilio signature", url=url)
            raise HTTPException(status_code=403, detail="Invalid signature")

    sms = TwilioInboundSMS(**data)
    logger.info("Inbound SMS received", from_number=sms.From, body_preview=sms.Body[:100])

    result = await process_sms_intake(db, sms)

    # Return TwiML response
    return f'<?xml version="1.0" encoding="UTF-8"?><Response><Message>{result["reply"]}</Message></Response>'


@router.post("/email/inbound")
async def email_inbound(payload: EmailInbound, db: AsyncSession = Depends(get_db)):
    """Receive inbound email (from SendGrid Inbound Parse or similar)."""
    logger.info("Inbound email received", from_email=payload.from_email, subject=payload.subject)
    result = await process_email_intake(db, payload)
    return {"status": "received", "ticket_id": result.get("ticket_id")}


@router.post("/form/inbound")
async def form_inbound(payload: WebFormSubmission, db: AsyncSession = Depends(get_db)):
    """Receive web form submission from portal or landing page."""
    logger.info("Form submission received", name=payload.name, issue=payload.issue_description[:100])
    result = await process_form_intake(db, payload)
    return {"status": "received", "ticket_id": result.get("ticket_id")}
