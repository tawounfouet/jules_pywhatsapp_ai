from typing import Any

class WhatsAppError(Exception):
    """Base exception for all WhatsApp errors."""
    pass

class WhatsAppAPIError(WhatsAppError):
    """Raised when the WhatsApp API returns an error."""
    def __init__(self, message: str, status_code: int | None = None, response_data: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.response_data = response_data

class ConfigurationError(WhatsAppError):
    """Raised when there is a configuration error."""
    pass

class WebhookError(WhatsAppError):
    """Raised when there is an issue with the webhook (e.g., signature verification)."""
    pass

class RoutingError(WhatsAppError):
    """Raised when there is an issue routing a message."""
    pass
