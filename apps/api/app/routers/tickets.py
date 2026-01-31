"""Ticket CRUD and lifecycle endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional, List
from uuid import UUID

from app.database import get_db
from app.models import Ticket, AuditEvent
from app.schemas.tickets import TicketCreate, TicketUpdate, TicketResponse
from app.services.orchestrator import transition_ticket

import structlog

logger = structlog.get_logger()
router = APIRouter(prefix="/tickets", tags=["tickets"])


@router.post("", response_model=TicketResponse)
async def create_ticket(payload: TicketCreate, db: AsyncSession = Depends(get_db)):
    """Create a new maintenance ticket."""
    ticket = Ticket(
        ticket_number="",  # trigger generates this
        client_id=payload.client_id,
        property_id=payload.property_id,
        unit_id=payload.unit_id,
        requester_contact_id=payload.requester_contact_id,
        priority=payload.priority,
        trade=payload.trade,
        summary=payload.summary,
        description=payload.description,
        photo_urls=payload.photo_urls,
        source=payload.source,
    )
    db.add(ticket)
    await db.flush()

    audit = AuditEvent(
        ticket_id=ticket.id,
        event_type="ticket_created",
        agent_name="api",
        actor_type="system",
        detail=f"Ticket created via {payload.source}: {payload.summary[:200]}",
        metadata={"priority": payload.priority, "trade": payload.trade},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(ticket)

    logger.info("Ticket created", ticket_id=str(ticket.id), number=ticket.ticket_number)
    return ticket


@router.get("", response_model=List[TicketResponse])
async def list_tickets(
    client_id: Optional[UUID] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
):
    """List tickets with optional filters."""
    query = select(Ticket).order_by(Ticket.created_at.desc())
    if client_id:
        query = query.where(Ticket.client_id == client_id)
    if status:
        query = query.where(Ticket.status == status)
    if priority:
        query = query.where(Ticket.priority == priority)
    query = query.limit(limit).offset(offset)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get a single ticket by ID."""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.patch("/{ticket_id}", response_model=TicketResponse)
async def update_ticket(
    ticket_id: UUID, payload: TicketUpdate, db: AsyncSession = Depends(get_db)
):
    """Update ticket fields. Status transitions go through the orchestrator."""
    result = await db.execute(select(Ticket).where(Ticket.id == ticket_id))
    ticket = result.scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    update_data = payload.model_dump(exclude_unset=True)

    # If status change requested, route through orchestrator
    if "status" in update_data:
        new_status = update_data.pop("status")
        await transition_ticket(db, ticket, new_status, actor_type="api")

    for field, value in update_data.items():
        setattr(ticket, field, value)

    await db.commit()
    await db.refresh(ticket)
    return ticket


@router.get("/{ticket_id}/timeline")
async def get_ticket_timeline(ticket_id: UUID, db: AsyncSession = Depends(get_db)):
    """Get the full audit trail / event timeline for a ticket."""
    result = await db.execute(
        select(AuditEvent)
        .where(AuditEvent.ticket_id == ticket_id)
        .order_by(AuditEvent.created_at.asc())
    )
    events = result.scalars().all()
    return [
        {
            "id": str(e.id),
            "event_type": e.event_type,
            "agent_name": e.agent_name,
            "actor_type": e.actor_type,
            "detail": e.detail,
            "metadata": e.metadata,
            "created_at": e.created_at.isoformat(),
        }
        for e in events
    ]
