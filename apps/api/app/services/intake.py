"""Intake service - processes inbound messages from all channels."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Contact, Ticket, Message, AuditEvent
from app.schemas.webhooks import TwilioInboundSMS, EmailInbound, WebFormSubmission
from app.services.orchestrator import is_emergency

import structlog

logger = structlog.get_logger()


async def find_contact_by_phone(db: AsyncSession, phone: str) -> Contact | None:
    """Look up a contact by phone number."""
    # Normalize phone: strip spaces, ensure +1 prefix
    normalized = phone.strip().replace(" ", "").replace("-", "")
    result = await db.execute(
        select(Contact).where(Contact.phone == normalized, Contact.active == True)
    )
    return result.scalar_one_or_none()


async def find_contact_by_email(db: AsyncSession, email: str) -> Contact | None:
    """Look up a contact by email."""
    result = await db.execute(
        select(Contact).where(Contact.email == email.lower().strip(), Contact.active == True)
    )
    return result.scalar_one_or_none()


async def process_sms_intake(db: AsyncSession, sms: TwilioInboundSMS) -> dict:
    """Process an inbound SMS and create/update a ticket."""
    contact = await find_contact_by_phone(db, sms.From)

    # Log the inbound message
    message = Message(
        contact_id=contact.id if contact else None,
        direction="inbound",
        channel="sms",
        from_address=sms.From,
        to_address=sms.To,
        body=sms.Body,
        media_urls=sms.media_urls or None,
        external_id=sms.MessageSid,
        agent_name="intake",
    )
    db.add(message)

    emergency = is_emergency(sms.Body)

    if contact and contact.property_id and contact.client_id:
        # Known contact - create ticket directly
        ticket = Ticket(
            ticket_number="",
            client_id=contact.client_id,
            property_id=contact.property_id,
            unit_id=contact.unit_id,
            requester_contact_id=contact.id,
            priority="emergency" if emergency else "routine",
            summary=sms.Body[:500],
            description=sms.Body,
            photo_urls=sms.media_urls or None,
            source="sms",
        )
        db.add(ticket)
        await db.flush()

        message.ticket_id = ticket.id

        audit = AuditEvent(
            ticket_id=ticket.id,
            event_type="ticket_created",
            agent_name="intake",
            actor_type="tenant",
            actor_id=str(contact.id),
            detail=f"Ticket created from SMS by {contact.first_name} {contact.last_name}",
        )
        db.add(audit)
        await db.commit()

        if emergency:
            reply = (
                f"We received your EMERGENCY maintenance request and are treating it as urgent. "
                f"Your ticket number is {ticket.ticket_number}. "
                f"We are notifying your property manager immediately."
            )
        else:
            reply = (
                f"Thanks {contact.first_name}! We received your maintenance request. "
                f"Your ticket number is {ticket.ticket_number}. "
                f"Can you send a photo of the issue? We'll get back to you shortly."
            )

        return {"ticket_id": str(ticket.id), "reply": reply}
    else:
        # Unknown contact
        await db.commit()
        reply = (
            "Thanks for reaching out! We received your message. "
            "To create a maintenance request, please reply with your full name "
            "and property address, and we'll get started."
        )
        return {"ticket_id": None, "reply": reply}


async def process_email_intake(db: AsyncSession, email: EmailInbound) -> dict:
    """Process inbound email and create a ticket."""
    contact = await find_contact_by_email(db, email.from_email)

    message = Message(
        contact_id=contact.id if contact else None,
        direction="inbound",
        channel="email",
        from_address=email.from_email,
        to_address=email.to_email,
        subject=email.subject,
        body=email.body_plain,
        external_id=email.message_id,
        agent_name="intake",
    )
    db.add(message)

    if contact and contact.property_id and contact.client_id:
        full_text = f"{email.subject} {email.body_plain}"
        emergency = is_emergency(full_text)

        ticket = Ticket(
            ticket_number="",
            client_id=contact.client_id,
            property_id=contact.property_id,
            unit_id=contact.unit_id,
            requester_contact_id=contact.id,
            priority="emergency" if emergency else "routine",
            summary=email.subject[:500] or email.body_plain[:500],
            description=email.body_plain,
            source="email",
        )
        db.add(ticket)
        await db.flush()
        message.ticket_id = ticket.id

        audit = AuditEvent(
            ticket_id=ticket.id,
            event_type="ticket_created",
            agent_name="intake",
            actor_type="tenant",
            actor_id=str(contact.id),
            detail=f"Ticket created from email: {email.subject}",
        )
        db.add(audit)
        await db.commit()

        return {"ticket_id": str(ticket.id)}
    else:
        await db.commit()
        return {"ticket_id": None, "note": "Unknown sender, needs manual triage"}


async def process_form_intake(db: AsyncSession, form: WebFormSubmission) -> dict:
    """Process web form submission and create a ticket."""
    contact = None
    if form.phone:
        contact = await find_contact_by_phone(db, form.phone)
    if not contact and form.email:
        contact = await find_contact_by_email(db, form.email)

    message = Message(
        contact_id=contact.id if contact else None,
        direction="inbound",
        channel="web",
        from_address=form.email or form.phone or form.name,
        body=f"Name: {form.name}\nAddress: {form.property_address}\nUnit: {form.unit_number}\nIssue: {form.issue_description}",
        media_urls=form.photo_urls,
        agent_name="intake",
    )
    db.add(message)

    if contact and contact.property_id and contact.client_id:
        emergency = is_emergency(form.issue_description)
        priority = "emergency" if emergency else (form.urgency or "routine")

        ticket = Ticket(
            ticket_number="",
            client_id=contact.client_id,
            property_id=contact.property_id,
            unit_id=contact.unit_id,
            requester_contact_id=contact.id,
            priority=priority,
            summary=form.issue_description[:500],
            description=form.issue_description,
            photo_urls=form.photo_urls,
            source="web_form",
        )
        db.add(ticket)
        await db.flush()
        message.ticket_id = ticket.id

        audit = AuditEvent(
            ticket_id=ticket.id,
            event_type="ticket_created",
            agent_name="intake",
            actor_type="tenant",
            detail=f"Ticket created from web form by {form.name}",
        )
        db.add(audit)
        await db.commit()

        return {"ticket_id": str(ticket.id)}
    else:
        await db.commit()
        return {"ticket_id": None, "note": "Contact not found, needs manual match"}
