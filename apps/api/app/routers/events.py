"""Generic event ingestion endpoint for the orchestrator."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.tickets import EventIngest, QuoteCreate, AppointmentCreate, InvoiceCreate
from app.services.orchestrator import handle_event
from app.models import Quote, Appointment, Invoice

import structlog

logger = structlog.get_logger()
router = APIRouter(tags=["events"])


@router.post("/events")
async def ingest_event(payload: EventIngest, db: AsyncSession = Depends(get_db)):
    """Ingest a generic event and route it through the orchestrator."""
    logger.info("Event received", event_type=payload.event_type, ticket_id=payload.ticket_id)
    result = await handle_event(db, payload)
    return result


@router.post("/quotes", tags=["quotes"])
async def create_quote(payload: QuoteCreate, db: AsyncSession = Depends(get_db)):
    """Record a vendor quote."""
    quote = Quote(
        ticket_id=payload.ticket_id,
        vendor_id=payload.vendor_id,
        work_order_id=payload.work_order_id,
        total_amount=payload.total_amount,
        labor_amount=payload.labor_amount,
        materials_amount=payload.materials_amount,
        warranty_terms=payload.warranty_terms,
        exclusions=payload.exclusions,
        notes=payload.notes,
    )
    db.add(quote)
    await db.commit()
    await db.refresh(quote)
    logger.info("Quote recorded", quote_id=str(quote.id), ticket_id=str(payload.ticket_id))
    return {"id": str(quote.id), "status": "received"}


@router.post("/appointments", tags=["appointments"])
async def create_appointment(payload: AppointmentCreate, db: AsyncSession = Depends(get_db)):
    """Create a service appointment."""
    appt = Appointment(
        ticket_id=payload.ticket_id,
        work_order_id=payload.work_order_id,
        vendor_id=payload.vendor_id,
        property_id=payload.property_id,
        unit_id=payload.unit_id,
        scheduled_date=payload.scheduled_date,
        scheduled_window=payload.scheduled_window,
        access_method=payload.access_method,
        access_instructions=payload.access_instructions,
        parking_notes=payload.parking_notes,
        pet_notes=payload.pet_notes,
    )
    db.add(appt)
    await db.commit()
    await db.refresh(appt)
    logger.info("Appointment created", appointment_id=str(appt.id))
    return {"id": str(appt.id), "status": "scheduled"}


@router.post("/invoices", tags=["invoices"])
async def create_invoice(payload: InvoiceCreate, db: AsyncSession = Depends(get_db)):
    """Record a vendor invoice."""
    invoice = Invoice(
        ticket_id=payload.ticket_id,
        vendor_id=payload.vendor_id,
        client_id=payload.client_id,
        work_order_id=payload.work_order_id,
        invoice_number=payload.invoice_number,
        amount=payload.amount,
        notes=payload.notes,
    )
    db.add(invoice)
    await db.commit()
    await db.refresh(invoice)
    logger.info("Invoice recorded", invoice_id=str(invoice.id))
    return {"id": str(invoice.id), "status": "pending"}
