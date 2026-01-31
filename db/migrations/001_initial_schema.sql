-- =============================================
-- Agentic Property Management - Initial Schema
-- =============================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- =============================================
-- L3: Data Layer - System of Record
-- =============================================

-- Clients (landlords / property managers)
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    company_name VARCHAR(255),
    approval_threshold_routine NUMERIC(10,2) DEFAULT 300.00,
    approval_threshold_capex NUMERIC(10,2) DEFAULT 1500.00,
    preferred_contact_method VARCHAR(20) DEFAULT 'email',
    reporting_cadence VARCHAR(20) DEFAULT 'weekly',
    timezone VARCHAR(50) DEFAULT 'America/New_York',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Properties
CREATE TABLE properties (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID NOT NULL REFERENCES clients(id),
    name VARCHAR(255) NOT NULL,
    address_line1 VARCHAR(255) NOT NULL,
    address_line2 VARCHAR(255),
    city VARCHAR(100) NOT NULL,
    state VARCHAR(50) NOT NULL,
    zip VARCHAR(20) NOT NULL,
    property_type VARCHAR(50) NOT NULL, -- single_family, multi_family, commercial
    access_instructions TEXT,
    lockbox_code VARCHAR(50),
    gate_code VARCHAR(50),
    parking_notes TEXT,
    pet_notes TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Units (for multi-family)
CREATE TABLE units (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    property_id UUID NOT NULL REFERENCES properties(id),
    unit_number VARCHAR(50) NOT NULL,
    bedrooms INTEGER,
    bathrooms NUMERIC(3,1),
    sq_ft INTEGER,
    floor INTEGER,
    access_instructions TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(property_id, unit_number)
);

-- Contacts (tenants, owners, property managers)
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    client_id UUID REFERENCES clients(id),
    property_id UUID REFERENCES properties(id),
    unit_id UUID REFERENCES units(id),
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    role VARCHAR(50) NOT NULL, -- tenant, owner, property_manager, emergency_contact
    preferred_contact_method VARCHAR(20) DEFAULT 'sms',
    notification_enabled BOOLEAN DEFAULT TRUE,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vendors
CREATE TABLE vendors (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    company_name VARCHAR(255) NOT NULL,
    contact_name VARCHAR(255),
    email VARCHAR(255),
    phone VARCHAR(50) NOT NULL,
    trades VARCHAR(255)[] NOT NULL, -- plumbing, electrical, hvac, general, roofing, etc
    service_area_zips VARCHAR(20)[],
    license_number VARCHAR(100),
    insurance_expiry DATE,
    insurance_verified BOOLEAN DEFAULT FALSE,
    hourly_rate NUMERIC(10,2),
    emergency_available BOOLEAN DEFAULT FALSE,
    preferred BOOLEAN DEFAULT FALSE,
    do_not_dispatch BOOLEAN DEFAULT FALSE,
    do_not_dispatch_reason TEXT,
    notes TEXT,
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Vendor performance scores
CREATE TABLE vendor_scores (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    vendor_id UUID NOT NULL REFERENCES vendors(id),
    client_id UUID REFERENCES clients(id),
    response_time_avg_hours NUMERIC(6,2),
    completion_rate NUMERIC(5,2),
    quality_score NUMERIC(3,2), -- 1.00 to 5.00
    price_competitiveness NUMERIC(3,2), -- 1.00 to 5.00
    total_jobs INTEGER DEFAULT 0,
    last_job_date DATE,
    calculated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tickets (the core entity)
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_number VARCHAR(20) UNIQUE NOT NULL, -- TCK-000001
    client_id UUID NOT NULL REFERENCES clients(id),
    property_id UUID NOT NULL REFERENCES properties(id),
    unit_id UUID REFERENCES units(id),
    requester_contact_id UUID REFERENCES contacts(id),
    status VARCHAR(30) NOT NULL DEFAULT 'new',
    -- Statuses: new, qualifying, dispatching, quotes_pending,
    --           awaiting_approval, scheduled, in_progress,
    --           awaiting_invoice, awaiting_payment, closed
    priority VARCHAR(20) NOT NULL DEFAULT 'routine',
    -- Priorities: emergency, urgent, routine
    trade VARCHAR(50), -- plumbing, electrical, hvac, general, roofing, appliance, etc
    summary TEXT NOT NULL,
    description TEXT,
    photo_urls TEXT[],
    source VARCHAR(20) NOT NULL, -- sms, email, web_form, phone, manual
    approved_amount NUMERIC(10,2),
    approved_by UUID REFERENCES contacts(id),
    approved_at TIMESTAMPTZ,
    closed_at TIMESTAMPTZ,
    closed_reason VARCHAR(50), -- completed, duplicate, cancelled, no_action_needed
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Work orders (child of ticket, one per vendor dispatch)
CREATE TABLE work_orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID NOT NULL REFERENCES tickets(id),
    vendor_id UUID REFERENCES vendors(id),
    scope_summary TEXT,
    scope_line_items JSONB DEFAULT '[]',
    assumptions JSONB DEFAULT '[]',
    completion_evidence_required JSONB DEFAULT '[]',
    status VARCHAR(30) NOT NULL DEFAULT 'draft',
    -- draft, sent_to_vendor, accepted, in_progress, completed, cancelled
    scheduled_date DATE,
    scheduled_window VARCHAR(50), -- morning, afternoon, 9am-12pm, etc
    completion_notes TEXT,
    completion_photos TEXT[],
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Quotes
CREATE TABLE quotes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID NOT NULL REFERENCES tickets(id),
    work_order_id UUID REFERENCES work_orders(id),
    vendor_id UUID NOT NULL REFERENCES vendors(id),
    total_amount NUMERIC(10,2) NOT NULL,
    labor_amount NUMERIC(10,2),
    materials_amount NUMERIC(10,2),
    warranty_terms TEXT,
    earliest_availability DATE,
    exclusions TEXT,
    notes TEXT,
    quote_document_url TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'received',
    -- received, normalized, recommended, approved, declined, expired
    received_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Appointments
CREATE TABLE appointments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID NOT NULL REFERENCES tickets(id),
    work_order_id UUID NOT NULL REFERENCES work_orders(id),
    vendor_id UUID NOT NULL REFERENCES vendors(id),
    property_id UUID NOT NULL REFERENCES properties(id),
    unit_id UUID REFERENCES units(id),
    scheduled_date DATE NOT NULL,
    scheduled_window VARCHAR(50) NOT NULL,
    access_method VARCHAR(50), -- lockbox, tenant_present, key_with_manager
    access_instructions TEXT,
    parking_notes TEXT,
    pet_notes TEXT,
    tenant_confirmed BOOLEAN DEFAULT FALSE,
    vendor_confirmed BOOLEAN DEFAULT FALSE,
    owner_notified BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
    -- scheduled, confirmed, in_progress, completed, cancelled, no_show
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Invoices
CREATE TABLE invoices (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID NOT NULL REFERENCES tickets(id),
    work_order_id UUID REFERENCES work_orders(id),
    vendor_id UUID NOT NULL REFERENCES vendors(id),
    client_id UUID NOT NULL REFERENCES clients(id),
    invoice_number VARCHAR(50),
    amount NUMERIC(10,2) NOT NULL,
    approved_amount NUMERIC(10,2),
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    -- pending, approved, paid, disputed, overdue
    invoice_document_url TEXT,
    payment_link TEXT,
    stripe_payment_intent_id VARCHAR(255),
    due_date DATE,
    paid_at TIMESTAMPTZ,
    notes TEXT,
    is_change_order BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Messages (all inbound/outbound comms)
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID REFERENCES tickets(id),
    contact_id UUID REFERENCES contacts(id),
    vendor_id UUID REFERENCES vendors(id),
    direction VARCHAR(10) NOT NULL, -- inbound, outbound
    channel VARCHAR(20) NOT NULL, -- sms, email, web, whatsapp, voice, internal
    from_address VARCHAR(255),
    to_address VARCHAR(255),
    subject VARCHAR(500),
    body TEXT NOT NULL,
    media_urls TEXT[],
    external_id VARCHAR(255), -- twilio SID, email message-id, etc
    sentiment_score NUMERIC(3,2), -- -1.00 to 1.00
    agent_name VARCHAR(50), -- which agent sent/processed this
    status VARCHAR(20) DEFAULT 'sent', -- sent, delivered, failed, received
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Audit events (every decision, every action)
CREATE TABLE audit_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ticket_id UUID REFERENCES tickets(id),
    event_type VARCHAR(100) NOT NULL,
    -- ticket_created, status_changed, message_sent, message_received,
    -- vendor_dispatched, quote_received, quote_normalized, approval_requested,
    -- approval_granted, appointment_scheduled, work_completed,
    -- invoice_received, payment_processed, escalation_triggered,
    -- emergency_detected, policy_enforced
    agent_name VARCHAR(50), -- which agent triggered this
    actor_type VARCHAR(20), -- system, agent, owner, tenant, vendor
    actor_id VARCHAR(255),
    detail TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- =============================================
-- Indices
-- =============================================

CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_priority ON tickets(priority);
CREATE INDEX idx_tickets_property_id ON tickets(property_id);
CREATE INDEX idx_tickets_client_id ON tickets(client_id);
CREATE INDEX idx_tickets_created_at ON tickets(created_at);
CREATE INDEX idx_tickets_number ON tickets(ticket_number);

CREATE INDEX idx_messages_ticket_id ON messages(ticket_id);
CREATE INDEX idx_messages_created_at ON messages(created_at);
CREATE INDEX idx_messages_channel ON messages(channel);

CREATE INDEX idx_audit_events_ticket_id ON audit_events(ticket_id);
CREATE INDEX idx_audit_events_created_at ON audit_events(created_at);
CREATE INDEX idx_audit_events_event_type ON audit_events(event_type);

CREATE INDEX idx_work_orders_ticket_id ON work_orders(ticket_id);
CREATE INDEX idx_quotes_ticket_id ON quotes(ticket_id);
CREATE INDEX idx_appointments_ticket_id ON appointments(ticket_id);
CREATE INDEX idx_appointments_scheduled_date ON appointments(scheduled_date);
CREATE INDEX idx_invoices_ticket_id ON invoices(ticket_id);
CREATE INDEX idx_invoices_status ON invoices(status);

CREATE INDEX idx_properties_client_id ON properties(client_id);
CREATE INDEX idx_units_property_id ON units(property_id);
CREATE INDEX idx_contacts_client_id ON contacts(client_id);
CREATE INDEX idx_vendors_trades ON vendors USING GIN(trades);
CREATE INDEX idx_vendors_do_not_dispatch ON vendors(do_not_dispatch) WHERE do_not_dispatch = TRUE;

-- =============================================
-- Ticket number sequence
-- =============================================

CREATE SEQUENCE ticket_number_seq START 1;

CREATE OR REPLACE FUNCTION generate_ticket_number()
RETURNS TRIGGER AS $$
BEGIN
    NEW.ticket_number := 'TCK-' || LPAD(nextval('ticket_number_seq')::TEXT, 6, '0');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER set_ticket_number
    BEFORE INSERT ON tickets
    FOR EACH ROW
    WHEN (NEW.ticket_number IS NULL OR NEW.ticket_number = '')
    EXECUTE FUNCTION generate_ticket_number();

-- =============================================
-- Updated_at trigger
-- =============================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_clients_updated_at BEFORE UPDATE ON clients FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_properties_updated_at BEFORE UPDATE ON properties FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_units_updated_at BEFORE UPDATE ON units FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_contacts_updated_at BEFORE UPDATE ON contacts FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_vendors_updated_at BEFORE UPDATE ON vendors FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_tickets_updated_at BEFORE UPDATE ON tickets FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_work_orders_updated_at BEFORE UPDATE ON work_orders FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_appointments_updated_at BEFORE UPDATE ON appointments FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER update_invoices_updated_at BEFORE UPDATE ON invoices FOR EACH ROW EXECUTE FUNCTION update_updated_at();
