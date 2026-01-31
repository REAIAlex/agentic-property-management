from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/agentic_pm"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_base_url: str = "http://localhost:8000"
    webhook_base_url: str = "http://localhost:8000"

    # Twilio
    twilio_account_sid: str = ""
    twilio_auth_token: str = ""
    twilio_phone_number: str = ""

    # AI
    anthropic_api_key: str = ""

    # Stripe
    stripe_secret_key: str = ""
    stripe_webhook_secret: str = ""

    # n8n
    n8n_webhook_url: str = "http://localhost:5678"

    # Email
    sendgrid_api_key: str = ""
    from_email: str = "maintenance@yourdomain.com"

    # App config
    approval_threshold_routine: float = 300.00
    approval_threshold_capex: float = 1500.00
    emergency_keywords: str = "gas,sparking,flooding,smoke,fire,carbon monoxide"

    # Auth
    jwt_secret: str = "change-me-in-production"
    magic_link_secret: str = "change-me-in-production"

    @property
    def emergency_keyword_list(self) -> List[str]:
        return [kw.strip().lower() for kw in self.emergency_keywords.split(",")]

    class Config:
        env_file = "../../.env"
        env_file_encoding = "utf-8"


settings = Settings()
