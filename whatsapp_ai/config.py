from typing import Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class WhatsAppConfig(BaseSettings):
    """Configuration for WhatsApp API and the application."""

    # Meta / WhatsApp API
    whatsapp_access_token: str = Field(..., description="Meta API access token")
    whatsapp_phone_number_id: str = Field(..., description="WhatsApp Phone Number ID")
    whatsapp_verify_token: str = Field(..., description="Webhook verification token")
    whatsapp_api_version: str = Field("v18.0", description="WhatsApp API version")

    # Provider APIs
    openai_api_key: str | None = Field(None, description="OpenAI API Key")

    # App Config
    webhook_host: str = Field("0.0.0.0", description="Host to bind the webhook server")
    webhook_port: int = Field(8000, description="Port to bind the webhook server")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    def __init__(self, **kwargs: Any) -> None:
        # Allow default instantiation by letting settings pull from environment/defaults
        super().__init__(**kwargs)
