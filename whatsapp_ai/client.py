import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from whatsapp_ai.config import WhatsAppConfig
from whatsapp_ai.exceptions import WhatsAppAPIError

logger = logging.getLogger(__name__)


class BaseMessagingClient(ABC):
    """Abstract interface for messaging clients (WhatsApp, SMS, etc.)."""

    @abstractmethod
    async def send_text_message(self, to: str, text: str) -> Dict[str, Any]:
        """Send a plain text message to the specified recipient."""
        pass

    @abstractmethod
    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str,
        components: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Send a template message."""
        pass


class WhatsAppClient(BaseMessagingClient):
    """WhatsApp Cloud API client implementation."""

    def __init__(self, config: WhatsAppConfig):
        self.config = config
        self.base_url = (
            f"https://graph.facebook.com/{config.whatsapp_api_version}/"
            f"{config.whatsapp_phone_number_id}"
        )
        self.headers = {
            "Authorization": f"Bearer {config.whatsapp_access_token}",
            "Content-Type": "application/json",
        }

    def _handle_error(self, response: httpx.Response) -> None:
        if response.status_code >= 400:
            error_msg = f"API Error ({response.status_code}): "
            try:
                data = response.json()
                error_msg += str(data.get("error", data))
            except ValueError:
                error_msg += response.text

            logger.error(error_msg)
            raise WhatsAppAPIError(
                message=error_msg,
                status_code=response.status_code,
                response_data=response.json() if response.content else None,
            )

    @retry(
        retry=retry_if_exception_type((httpx.RequestError, WhatsAppAPIError)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    async def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            logger.debug(f"Sending payload to WhatsApp API: {payload}")
            response = await client.post(
                f"{self.base_url}/messages",
                headers=self.headers,
                json=payload,
                timeout=30.0,
            )
            self._handle_error(response)
            return dict(response.json())

    async def send_text_message(self, to: str, text: str) -> Dict[str, Any]:
        """Send a plain text message."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "text",
            "text": {"preview_url": False, "body": text},
        }
        return await self._post(payload)

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str,
        components: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Send a template message."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": language_code},
                "components": components or [],
            },
        }
        return await self._post(payload)
