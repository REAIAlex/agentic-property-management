"""Orchestrator state machine - the air traffic controller for ticket lifecycle."""
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Ticket, AuditEvent
from app.schemas.tickets import EventIngest
from app.config import settings

import structlog

logger = structlog.get_logger()

# Valid state transitions
VALID_TRANSITIONS = {
    "new": ["qualifying", "closed"],
    "qualifying": ["dispatching", "closed"],
    "dispatching": ["quotes_pending", "closed"],
    "quotes_pending": ["awaiting_approval", "dispatching", "closed"],
    "awaiting_approval": ["scheduled", "dispatching", "closed"],
    "scheduled": ["in_progress", "closed"],
    "in_progress": ["awaiting_invoice", "closed"],
    "awaiting_invoice": ["awaiting_payment", "closed"],
    "awaiting_payment": ["closed"],
    "closed": [],  # terminal state
}

EMERGENCY_KEYWORDS = settings.emergency_keyword_list


def is_emergency(text: str) -> bool:
    """Check if text contains emergency indicators."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in EMERGENCY_KEYWORDS)


async def transition_ticket(
    db: AsyncSession,
    ticket: Ticket,
    new_status: str,
    actor_type: str = "system",
    actor_id: str = "",
    detail: str = "",
) -> Ticket:
    """Transition a ticket to a new status with validation and audit logging."""
    old_status = ticket.status

    if new_status not in VALID_TRANSITIONS.get(old_status, []):
        raise ValueError(
            f"Invalid transition: {old_status} -> {new_status}. "
            f"Valid targets: {VALID_TRANSITIONS.get(old_status, [])}"
        )

    ticket.status = new_status

    if new_status == "closed":
        ticket.closed_at = datetime.utcnow()

    audit = AuditEvent(
        ticket_id=ticket.id,
        event_type="status_changed",
        agent_name="orchestrator",
        actor_type=actor_type,
        actor_id=actor_id,
        detail=detail or f"Status changed from {old_status} to {new_status}",
        metadata={"from_status": old_status, "to_status": new_status},
    )
    db.add(audit)

    logger.info(
        "Ticket status transition",
        ticket_id=str(ticket.id),
        from_status=old_status,
        to_status=new_status,
    )

    return ticket


async def handle_event(db: AsyncSession, event: EventIngest) -> dict:
    """Process an inbound event and determine next actions."""
    result = {
        "decision_summary": "",
        "next_actions": [],
        "escalation_required": False,
        "escalation_reason": "",
        "audit_events": [],
    }

    ticket = None
    if event.ticket_id:
        q = await db.execute(select(Ticket).where(Ticket.id == event.ticket_id))
        ticket = q.scalar_one_or_none()

    if event.event_type == "inbound_message":
        body = event.payload.get("body", "")
        if is_emergency(body):
            result["escalation_required"] = True
            result["escalation_reason"] = "Emergency keywords detected in message"
            result["next_actions"] = [
                {"action": "notify_owner_emergency", "owner": "comms_agent"},
                {"action": "trigger_emergency_dispatch", "owner": "dispatch_agent"},
            ]
            result["decision_summary"] = "Emergency detected. Notifying owner and triggering emergency dispatch."
        else:
            result["next_actions"] = [
                {"action": "run_intake_triage", "owner": "intake_agent"},
            ]
            result["decision_summary"] = "Standard inbound message routed to intake triage."

    elif event.event_type == "quote_received":
        if ticket and ticket.status == "quotes_pending":
            result["next_actions"] = [
                {"action": "normalize_quote", "owner": "quote_analyst"},
                {"action": "check_all_quotes_received", "owner": "orchestrator"},
            ]
            result["decision_summary"] = "Quote received, routing to analysis."

    elif event.event_type == "owner_approved":
        approved_amount = event.payload.get("approved_amount", 0)
        policies = event.policies or {}
        capex_threshold = policies.get("approval_thresholds", {}).get(
            "capex", settings.approval_threshold_capex
        )

        if approved_amount > capex_threshold:
            result["escalation_required"] = True
            result["escalation_reason"] = f"Approved amount ${approved_amount} exceeds capex threshold ${capex_threshold}"

        if ticket:
            await transition_ticket(
                db, ticket, "scheduled",
                actor_type="owner",
                detail=f"Owner approved ${approved_amount}",
            )
        result["next_actions"] = [
            {"action": "schedule_work", "owner": "scheduling_agent"},
            {"action": "notify_tenant_vendor", "owner": "comms_agent"},
        ]
        result["decision_summary"] = f"Owner approved ${approved_amount}. Scheduling work."

    elif event.event_type == "appointment_completed":
        if ticket:
            await transition_ticket(
                db, ticket, "awaiting_invoice",
                actor_type="system",
                detail="Work completed, awaiting vendor invoice.",
            )
        result["next_actions"] = [
            {"action": "request_invoice", "owner": "billing_agent"},
            {"action": "notify_completion", "owner": "comms_agent"},
        ]
        result["decision_summary"] = "Work completed. Requesting invoice and notifying parties."

    elif event.event_type == "invoice_received":
        invoice_amount = event.payload.get("amount", 0)
        approved = ticket.approved_amount if ticket else 0

        if approved and invoice_amount > float(approved) * 1.1:
            result["escalation_required"] = True
            result["escalation_reason"] = (
                f"Invoice ${invoice_amount} exceeds approved ${approved} by >10%"
            )
            result["next_actions"] = [
                {"action": "flag_change_order", "owner": "billing_agent"},
            ]
        else:
            if ticket:
                await transition_ticket(
                    db, ticket, "awaiting_payment",
                    actor_type="system",
                    detail=f"Invoice ${invoice_amount} received and within approved amount.",
                )
            result["next_actions"] = [
                {"action": "generate_payment_link", "owner": "billing_agent"},
                {"action": "send_invoice_summary", "owner": "comms_agent"},
            ]
        result["decision_summary"] = f"Invoice ${invoice_amount} received and processed."

    elif event.event_type == "timer_fired":
        timer_name = event.payload.get("timer_name", "")
        if timer_name == "quote_deadline":
            result["next_actions"] = [
                {"action": "check_quote_status", "owner": "orchestrator"},
                {"action": "send_vendor_reminder", "owner": "dispatch_agent"},
            ]
            result["decision_summary"] = "Quote deadline reached. Checking status and sending reminders."

    # Log audit events
    if ticket:
        audit = AuditEvent(
            ticket_id=ticket.id,
            event_type=f"event_processed_{event.event_type}",
            agent_name="orchestrator",
            actor_type="system",
            detail=result["decision_summary"],
            metadata={"next_actions": result["next_actions"]},
        )
        db.add(audit)
        await db.commit()

    return result
