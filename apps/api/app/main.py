"""Agentic Property Management - API Service."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.routers import webhooks, tickets, events
from app.config import settings

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
)

app = FastAPI(
    title="Agentic Property Management API",
    description="AI-driven property maintenance workflow automation",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(webhooks.router)
app.include_router(tickets.router)
app.include_router(events.router)


@app.get("/")
async def root():
    return {
        "service": "Agentic Property Management API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
