import uuid
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    String, Text, Boolean, Integer, Numeric, Date, DateTime, ForeignKey, ARRAY, JSON,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    company_name: Mapped[Optional[str]] = mapped_column(String(255))
    approval_threshold_routine: Mapped[float] = mapped_column(Numeric(10, 2), default=300.00)
    approval_threshold_capex: Mapped[float] = mapped_column(Numeric(10, 2), default=1500.00)
    preferred_contact_method: Mapped[str] = mapped_column(String(20), default="email")
    reporting_cadence: Mapped[str] = mapped_column(String(20), default="weekly")
    timezone: Mapped[str] = mapped_column(String(50), default="America/New_York")
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    properties: Mapped[List["Property"]] = relationship(back_populates="client")
    tickets: Mapped[List["Ticket"]] = relationship(back_populates="client")


class Property(Base):
    __tablename__ = "properties"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    name: Mapped[str] = mapped_column(String(255))
    address_line1: Mapped[str] = mapped_column(String(255))
    address_line2: Mapped[Optional[str]] = mapped_column(String(255))
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(50))
    zip: Mapped[str] = mapped_column(String(20))
    property_type: Mapped[str] = mapped_column(String(50))
    access_instructions: Mapped[Optional[str]] = mapped_column(Text)
    lockbox_code: Mapped[Optional[str]] = mapped_column(String(50))
    gate_code: Mapped[Optional[str]] = mapped_column(String(50))
    parking_notes: Mapped[Optional[str]] = mapped_column(Text)
    pet_notes: Mapped[Optional[str]] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    client: Mapped["Client"] = relationship(back_populates="properties")
    units: Mapped[List["Unit"]] = relationship(back_populates="property")


class Unit(Base):
    __tablename__ = "units"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    property_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("properties.id"))
    unit_number: Mapped[str] = mapped_column(String(50))
    bedrooms: Mapped[Optional[int]] = mapped_column(Integer)
    bathrooms: Mapped[Optional[float]] = mapped_column(Numeric(3, 1))
    sq_ft: Mapped[Optional[int]] = mapped_column(Integer)
    floor: Mapped[Optional[int]] = mapped_column(Integer)
    access_instructions: Mapped[Optional[str]] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    property: Mapped["Property"] = relationship(back_populates="units")


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("clients.id"))
    property_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("properties.id"))
    unit_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("units.id"))
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[Optional[str]] = mapped_column(String(50))
    role: Mapped[str] = mapped_column(String(50))
    preferred_contact_method: Mapped[str] = mapped_column(String(20), default="sms")
    notification_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class Vendor(Base):
    __tablename__ = "vendors"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_name: Mapped[str] = mapped_column(String(255))
    contact_name: Mapped[Optional[str]] = mapped_column(String(255))
    email: Mapped[Optional[str]] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(50))
    trades: Mapped[list] = mapped_column(ARRAY(String))
    service_area_zips: Mapped[Optional[list]] = mapped_column(ARRAY(String))
    license_number: Mapped[Optional[str]] = mapped_column(String(100))
    insurance_expiry: Mapped[Optional[date]] = mapped_column(Date)
    insurance_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    hourly_rate: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    emergency_available: Mapped[bool] = mapped_column(Boolean, default=False)
    preferred: Mapped[bool] = mapped_column(Boolean, default=False)
    do_not_dispatch: Mapped[bool] = mapped_column(Boolean, default=False)
    do_not_dispatch_reason: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class VendorScore(Base):
    __tablename__ = "vendor_scores"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id"))
    client_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("clients.id"))
    response_time_avg_hours: Mapped[Optional[float]] = mapped_column(Numeric(6, 2))
    completion_rate: Mapped[Optional[float]] = mapped_column(Numeric(5, 2))
    quality_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    price_competitiveness: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    total_jobs: Mapped[int] = mapped_column(Integer, default=0)
    last_job_date: Mapped[Optional[date]] = mapped_column(Date)
    calculated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_number: Mapped[str] = mapped_column(String(20), unique=True)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    property_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("properties.id"))
    unit_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("units.id"))
    requester_contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("contacts.id"))
    status: Mapped[str] = mapped_column(String(30), default="new")
    priority: Mapped[str] = mapped_column(String(20), default="routine")
    trade: Mapped[Optional[str]] = mapped_column(String(50))
    summary: Mapped[str] = mapped_column(Text)
    description: Mapped[Optional[str]] = mapped_column(Text)
    photo_urls: Mapped[Optional[list]] = mapped_column(ARRAY(Text))
    source: Mapped[str] = mapped_column(String(20))
    approved_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    approved_by: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("contacts.id"))
    approved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    closed_reason: Mapped[Optional[str]] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    client: Mapped["Client"] = relationship(back_populates="tickets")
    work_orders: Mapped[List["WorkOrder"]] = relationship(back_populates="ticket")
    quotes: Mapped[List["Quote"]] = relationship(back_populates="ticket")
    messages: Mapped[List["Message"]] = relationship(back_populates="ticket")
    audit_events: Mapped[List["AuditEvent"]] = relationship(back_populates="ticket")


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tickets.id"))
    vendor_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("vendors.id"))
    scope_summary: Mapped[Optional[str]] = mapped_column(Text)
    scope_line_items: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    assumptions: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    completion_evidence_required: Mapped[Optional[dict]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(30), default="draft")
    scheduled_date: Mapped[Optional[date]] = mapped_column(Date)
    scheduled_window: Mapped[Optional[str]] = mapped_column(String(50))
    completion_notes: Mapped[Optional[str]] = mapped_column(Text)
    completion_photos: Mapped[Optional[list]] = mapped_column(ARRAY(Text))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    ticket: Mapped["Ticket"] = relationship(back_populates="work_orders")


class Quote(Base):
    __tablename__ = "quotes"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tickets.id"))
    work_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("work_orders.id"))
    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id"))
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    labor_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    materials_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    warranty_terms: Mapped[Optional[str]] = mapped_column(Text)
    earliest_availability: Mapped[Optional[date]] = mapped_column(Date)
    exclusions: Mapped[Optional[str]] = mapped_column(Text)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    quote_document_url: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="received")
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    ticket: Mapped["Ticket"] = relationship(back_populates="quotes")


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tickets.id"))
    work_order_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("work_orders.id"))
    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id"))
    property_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("properties.id"))
    unit_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("units.id"))
    scheduled_date: Mapped[date] = mapped_column(Date)
    scheduled_window: Mapped[str] = mapped_column(String(50))
    access_method: Mapped[Optional[str]] = mapped_column(String(50))
    access_instructions: Mapped[Optional[str]] = mapped_column(Text)
    parking_notes: Mapped[Optional[str]] = mapped_column(Text)
    pet_notes: Mapped[Optional[str]] = mapped_column(Text)
    tenant_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    vendor_confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_notified: Mapped[bool] = mapped_column(Boolean, default=False)
    status: Mapped[str] = mapped_column(String(20), default="scheduled")
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tickets.id"))
    work_order_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("work_orders.id"))
    vendor_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("vendors.id"))
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id"))
    invoice_number: Mapped[Optional[str]] = mapped_column(String(50))
    amount: Mapped[float] = mapped_column(Numeric(10, 2))
    approved_amount: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String(20), default="pending")
    invoice_document_url: Mapped[Optional[str]] = mapped_column(Text)
    payment_link: Mapped[Optional[str]] = mapped_column(Text)
    stripe_payment_intent_id: Mapped[Optional[str]] = mapped_column(String(255))
    due_date: Mapped[Optional[date]] = mapped_column(Date)
    paid_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    notes: Mapped[Optional[str]] = mapped_column(Text)
    is_change_order: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("tickets.id"))
    contact_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("contacts.id"))
    vendor_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("vendors.id"))
    direction: Mapped[str] = mapped_column(String(10))
    channel: Mapped[str] = mapped_column(String(20))
    from_address: Mapped[Optional[str]] = mapped_column(String(255))
    to_address: Mapped[Optional[str]] = mapped_column(String(255))
    subject: Mapped[Optional[str]] = mapped_column(String(500))
    body: Mapped[str] = mapped_column(Text)
    media_urls: Mapped[Optional[list]] = mapped_column(ARRAY(Text))
    external_id: Mapped[Optional[str]] = mapped_column(String(255))
    sentiment_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 2))
    agent_name: Mapped[Optional[str]] = mapped_column(String(50))
    status: Mapped[str] = mapped_column(String(20), default="sent")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    ticket: Mapped[Optional["Ticket"]] = relationship(back_populates="messages")


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    ticket_id: Mapped[Optional[uuid.UUID]] = mapped_column(ForeignKey("tickets.id"))
    event_type: Mapped[str] = mapped_column(String(100))
    agent_name: Mapped[Optional[str]] = mapped_column(String(50))
    actor_type: Mapped[Optional[str]] = mapped_column(String(20))
    actor_id: Mapped[Optional[str]] = mapped_column(String(255))
    detail: Mapped[str] = mapped_column(Text)
    metadata: Mapped[Optional[dict]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    ticket: Mapped[Optional["Ticket"]] = relationship(back_populates="audit_events")
