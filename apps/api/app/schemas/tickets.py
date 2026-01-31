from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class TicketCreate(BaseModel):
    client_id: UUID
    property_id: UUID
    unit_id: Optional[UUID] = None
    requester_contact_id: Optional[UUID] = None
    priority: str = "routine"
    trade: Optional[str] = None
    summary: str
    description: Optional[str] = None
    photo_urls: Optional[List[str]] = None
    source: str = "web_form"


class TicketUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    trade: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    photo_urls: Optional[List[str]] = None
    approved_amount: Optional[float] = None
    approved_by: Optional[UUID] = None
    closed_reason: Optional[str] = None


class TicketResponse(BaseModel):
    id: UUID
    ticket_number: str
    client_id: UUID
    property_id: UUID
    unit_id: Optional[UUID]
    requester_contact_id: Optional[UUID]
    status: str
    priority: str
    trade: Optional[str]
    summary: str
    description: Optional[str]
    photo_urls: Optional[List[str]]
    source: str
    approved_amount: Optional[float]
    approved_at: Optional[datetime]
    closed_at: Optional[datetime]
    closed_reason: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class QuoteCreate(BaseModel):
    ticket_id: UUID
    vendor_id: UUID
    work_order_id: Optional[UUID] = None
    total_amount: float
    labor_amount: Optional[float] = None
    materials_amount: Optional[float] = None
    warranty_terms: Optional[str] = None
    earliest_availability: Optional[str] = None
    exclusions: Optional[str] = None
    notes: Optional[str] = None


class AppointmentCreate(BaseModel):
    ticket_id: UUID
    work_order_id: UUID
    vendor_id: UUID
    property_id: UUID
    unit_id: Optional[UUID] = None
    scheduled_date: str
    scheduled_window: str
    access_method: Optional[str] = None
    access_instructions: Optional[str] = None
    parking_notes: Optional[str] = None
    pet_notes: Optional[str] = None


class InvoiceCreate(BaseModel):
    ticket_id: UUID
    vendor_id: UUID
    client_id: UUID
    work_order_id: Optional[UUID] = None
    invoice_number: Optional[str] = None
    amount: float
    due_date: Optional[str] = None
    notes: Optional[str] = None


class EventIngest(BaseModel):
    event_type: str = Field(
        ...,
        description="One of: inbound_message, quote_received, owner_approved, "
                    "appointment_completed, invoice_received, timer_fired"
    )
    ticket_id: Optional[str] = None
    payload: dict = Field(default_factory=dict)
    policies: Optional[dict] = None
