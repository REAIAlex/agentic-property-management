# Agentic Property Management - Runbook

## Architecture Overview

```
Tenants/Owners → [SMS/Email/Web] → Twilio/SendGrid Webhooks
                                          ↓
                                    FastAPI (api)
                                    ├── /webhooks/* (inbound channels)
                                    ├── /tickets (CRUD)
                                    ├── /events (orchestrator)
                                    ├── /quotes
                                    ├── /appointments
                                    └── /invoices
                                          ↓
                               Orchestrator State Machine
                                          ↓
                                   Agent Runner Service
                                   ├── intake_triage
                                   ├── scope_drafting
                                   ├── vendor_dispatch
                                   ├── quote_analyst
                                   ├── scheduling_access
                                   ├── customer_comms
                                   ├── billing_closeout
                                   └── onboarding
                                          ↓
                                  n8n Workflow Engine
                                  (timers, connectors, glue)
                                          ↓
                                     PostgreSQL
                                  (system of record)
```

## Local Development

### Prerequisites
- Docker Desktop
- Git

### Quick Start
```bash
# Clone
git clone https://github.com/REAIAlex/agentic-property-management.git
cd agentic-property-management

# Copy environment
cp .env.example .env
# Edit .env with your API keys

# Start all services
cd infra
docker compose up -d

# Check services
docker compose ps

# View API logs
docker compose logs -f api
```

### Service URLs (local)
- API: http://localhost:8000
- API docs: http://localhost:8000/docs
- Agent Runner: http://localhost:8001
- Agent Runner docs: http://localhost:8001/docs
- n8n: http://localhost:5678 (admin/admin)
- PostgreSQL: localhost:5432 (postgres/postgres)

### GitHub Codespaces
1. Open the repo in VS Code
2. Ctrl+Shift+P → "Codespaces: Create New Codespace"
3. The .devcontainer config auto-provisions everything
4. Ports are auto-forwarded

## Twilio Configuration

### Inbound SMS Webhook Setup
1. Go to https://console.twilio.com
2. Navigate to Phone Numbers → Manage → Active Numbers
3. Select your number
4. Under "Messaging", set the webhook:
   - **When a message comes in**: `https://your-domain.com/webhooks/twilio/inbound`
   - **HTTP Method**: POST
5. Save

### For Local Testing with ngrok
```bash
# Install ngrok
# Start tunnel
ngrok http 8000

# Use the ngrok URL in Twilio console:
# https://abc123.ngrok.io/webhooks/twilio/inbound
```

### Required Twilio Environment Variables
```
TWILIO_ACCOUNT_SID=ACxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+1234567890
```

## Database

### Running Migrations
```bash
# Via Docker (recommended)
docker exec -i agentic-pm-db psql -U postgres -d agentic_pm < db/migrations/001_initial_schema.sql

# Via Python
cd apps/api
python -m app.db_migrate
```

### Connecting to Database
```bash
# Via Docker
docker exec -it agentic-pm-db psql -U postgres -d agentic_pm

# Direct
psql postgresql://postgres:postgres@localhost:5432/agentic_pm
```

## n8n Workflows

### Importing Workflows
1. Open n8n at http://localhost:5678
2. Go to Workflows → Import from File
3. Import each file from `n8n/workflows/` directory:
   - `01_inbound_intake.json`
   - `02_vendor_dispatch.json`
   - `03_quote_processing.json`
   - `04_scheduling.json`
   - `05_invoicing.json`
4. Activate each workflow

### n8n Environment Variables
Set these in n8n's settings or via environment:
- `API_BASE_URL`: http://api:8000 (Docker) or http://localhost:8000
- `AGENT_RUNNER_URL`: http://agent-runner:8001 (Docker) or http://localhost:8001

## End-to-End Test Scenarios

### Scenario 1: Basic SMS Ticket Flow
```bash
# Simulate inbound SMS
curl -X POST http://localhost:8000/webhooks/twilio/inbound \
  -d "MessageSid=SM123&AccountSid=AC123&From=+15551234567&To=+15559876543&Body=My+kitchen+faucet+is+leaking&NumMedia=0"

# Check ticket was created
curl http://localhost:8000/tickets

# Check ticket timeline
curl http://localhost:8000/tickets/{ticket_id}/timeline
```

### Scenario 2: Emergency Detection
```bash
# Simulate emergency SMS
curl -X POST http://localhost:8000/webhooks/twilio/inbound \
  -d "MessageSid=SM456&AccountSid=AC123&From=+15551234567&To=+15559876543&Body=I+smell+gas+in+my+apartment&NumMedia=0"

# Verify priority is "emergency"
curl http://localhost:8000/tickets?priority=emergency
```

### Scenario 3: Web Form Submission
```bash
curl -X POST http://localhost:8000/webhooks/form/inbound \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Smith",
    "email": "john@example.com",
    "phone": "+15551234567",
    "property_address": "123 Main St",
    "unit_number": "4B",
    "issue_description": "AC unit is not cooling",
    "urgency": "urgent"
  }'
```

### Scenario 4: Full Ticket Lifecycle
```bash
# 1. Create ticket via API
curl -X POST http://localhost:8000/tickets \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "YOUR_CLIENT_UUID",
    "property_id": "YOUR_PROPERTY_UUID",
    "summary": "Broken garbage disposal",
    "source": "manual",
    "priority": "routine",
    "trade": "plumbing"
  }'

# 2. Transition through statuses
curl -X PATCH http://localhost:8000/tickets/{id} \
  -H "Content-Type: application/json" \
  -d '{"status": "qualifying"}'

# 3. Run agent
curl -X POST http://localhost:8001/run \
  -H "Content-Type: application/json" \
  -d '{
    "agent_name": "intake_triage",
    "context": {"issue": "Broken garbage disposal", "property": "123 Main St"},
    "ticket_id": "TICKET_UUID"
  }'

# 4. Continue through lifecycle...
```

## Azure Deployment

### Prerequisites
```bash
az login
az account set --subscription YOUR_SUBSCRIPTION_ID
```

### Create Resources (first time only)
```bash
# Resource group
az group create --name agentic-pm-rg --location eastus

# Container registry
az acr create --resource-group agentic-pm-rg --name agenticpmacr --sku Basic

# Postgres
az postgres flexible-server create \
  --resource-group agentic-pm-rg \
  --name agentic-pm-db \
  --location eastus \
  --admin-user pmadmin \
  --admin-password "CHANGE_ME" \
  --sku-name Standard_B1ms --tier Burstable --version 14

# Container Apps environment
az containerapp env create \
  --name agentic-pm-env \
  --resource-group agentic-pm-rg \
  --location eastus

# Storage account
az storage account create \
  --name agenticpmstorage \
  --resource-group agentic-pm-rg \
  --location eastus --sku Standard_LRS
```

### GitHub Secrets Required
Set these in repo Settings → Secrets → Actions:
- `AZURE_CREDENTIALS` - service principal JSON
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `ANTHROPIC_API_KEY`
- `STRIPE_SECRET_KEY`
- `SENDGRID_API_KEY`

### Manual Deploy
```bash
# Build and push
az acr build --registry agenticpmacr --image api:latest -f apps/api/Dockerfile .

# Deploy
az containerapp update --name agentic-pm-api \
  --resource-group agentic-pm-rg \
  --image agenticpmacr.azurecr.io/api:latest
```

## Monitoring

### Logs
```bash
# Docker local
docker compose logs -f api
docker compose logs -f agent-runner

# Azure
az containerapp logs show --name agentic-pm-api --resource-group agentic-pm-rg
```

### Key Metrics to Monitor
- **Time-to-first-response**: from ticket creation to first outbound message
- **Quote SLA**: from dispatch to all quotes received
- **Completion SLA**: from scheduled to work completed
- **Invoice aging**: from invoice received to payment
- **Vendor performance**: response time, completion rate, quality score

### Health Checks
```bash
curl http://localhost:8000/health  # API
curl http://localhost:8001/health  # Agent Runner
```
