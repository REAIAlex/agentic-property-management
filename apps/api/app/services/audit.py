"""Audit logging service - every decision, every action."""
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AuditEvent

import structlog

logger = structlog.get_logger()


async def log_event(
    db: AsyncSession,
    ticket_id: Optional[UUID],
    event_type: str,
    detail: str,
    agent_name: str = "system",
    actor_type: str = "system",
    actor_id: str = "",
    metadata: Optional[dict] = None,
) -> AuditEvent:
    """Log an audit event."""
    event = AuditEvent(
        ticket_id=ticket_id,
        event_type=event_type,
        agent_name=agent_name,
        actor_type=actor_type,
        actor_id=actor_id,
        detail=detail,
        metadata=metadata or {},
    )
    db.add(event)
    logger.info(
        "Audit event logged",
        event_type=event_type,
        ticket_id=str(ticket_id) if ticket_id else None,
        detail=detail[:200],
    )
    return event
