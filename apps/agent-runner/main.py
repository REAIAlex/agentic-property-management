"""Agent Runner Service - Loads prompts, calls Claude, validates output, emits events."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
from typing import Optional
from pathlib import Path
import json

import anthropic
import httpx
import jsonschema
import structlog

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
)
logger = structlog.get_logger()


class Settings(BaseSettings):
    anthropic_api_key: str = ""
    api_base_url: str = "http://localhost:8000"
    prompts_dir: str = "../../prompts"

    class Config:
        env_file = "../../.env"


settings = Settings()
app = FastAPI(title="Agent Runner", version="0.1.0")

# Load prompts from files
PROMPTS_DIR = Path(settings.prompts_dir)
AGENTS_DIR = PROMPTS_DIR / "agents"
SCHEMAS_DIR = PROMPTS_DIR / "schemas"
POLICIES_DIR = PROMPTS_DIR / "policies"


def load_prompt(agent_name: str) -> str:
    """Load an agent's system prompt from the prompts directory."""
    prompt_file = AGENTS_DIR / f"{agent_name}.md"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    return prompt_file.read_text()


def load_schema(schema_name: str) -> dict:
    """Load a JSON schema for output validation."""
    schema_file = SCHEMAS_DIR / f"{schema_name}.json"
    if not schema_file.exists():
        return {}
    return json.loads(schema_file.read_text())


def load_policies() -> str:
    """Load global policies."""
    policies_file = POLICIES_DIR / "global_policies.md"
    if policies_file.exists():
        return policies_file.read_text()
    return ""


class AgentRequest(BaseModel):
    agent_name: str = Field(..., description="Name of the agent to invoke")
    context: dict = Field(default_factory=dict, description="Context data for the agent")
    ticket_id: Optional[str] = None
    validate_output: bool = True


class AgentResponse(BaseModel):
    agent_name: str
    output: dict
    validation_passed: bool
    raw_response: str


@app.post("/run", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    """Run an agent: load prompt, inject context, call Claude, validate, emit events."""
    logger.info("Running agent", agent_name=request.agent_name, ticket_id=request.ticket_id)

    # Load the agent prompt
    try:
        system_prompt = load_prompt(request.agent_name)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Load and append global policies
    policies = load_policies()
    if policies:
        system_prompt += f"\n\n---\nGLOBAL POLICIES:\n{policies}"

    # Build the user message with context
    user_message = f"""Process this request. Return valid JSON only.

Context:
```json
{json.dumps(request.context, indent=2, default=str)}
```

Respond with a JSON object containing your analysis and actions."""

    # Call Claude
    if not settings.anthropic_api_key:
        raise HTTPException(
            status_code=500,
            detail="ANTHROPIC_API_KEY not configured. Set it in .env file.",
        )

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        raw_text = response.content[0].text
    except Exception as e:
        logger.error("Claude API call failed", agent=request.agent_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"AI call failed: {str(e)}")

    # Parse JSON output
    try:
        # Try to extract JSON from the response
        output = json.loads(raw_text)
    except json.JSONDecodeError:
        # Try to find JSON in markdown code blocks
        import re
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", raw_text)
        if json_match:
            try:
                output = json.loads(json_match.group(1))
            except json.JSONDecodeError:
                output = {"raw_text": raw_text, "parse_error": True}
        else:
            output = {"raw_text": raw_text, "parse_error": True}

    # Validate output against schema
    validation_passed = True
    if request.validate_output and not output.get("parse_error"):
        schema = load_schema(request.agent_name)
        if schema:
            try:
                jsonschema.validate(output, schema)
            except jsonschema.ValidationError as e:
                logger.warning(
                    "Output validation failed",
                    agent=request.agent_name,
                    error=str(e.message),
                )
                validation_passed = False

    # Log audit event via API
    if request.ticket_id:
        try:
            async with httpx.AsyncClient() as http_client:
                await http_client.post(
                    f"{settings.api_base_url}/events",
                    json={
                        "event_type": f"agent_{request.agent_name}_completed",
                        "ticket_id": request.ticket_id,
                        "payload": {
                            "agent_output": output,
                            "validation_passed": validation_passed,
                        },
                    },
                    timeout=10,
                )
        except Exception as e:
            logger.warning("Failed to emit event to API", error=str(e))

    logger.info(
        "Agent completed",
        agent_name=request.agent_name,
        validation_passed=validation_passed,
    )

    return AgentResponse(
        agent_name=request.agent_name,
        output=output,
        validation_passed=validation_passed,
        raw_response=raw_text,
    )


@app.get("/agents")
async def list_agents():
    """List all available agents."""
    agents = []
    if AGENTS_DIR.exists():
        for f in AGENTS_DIR.glob("*.md"):
            agents.append(f.stem)
    return {"agents": sorted(agents)}


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "agent-runner"}
