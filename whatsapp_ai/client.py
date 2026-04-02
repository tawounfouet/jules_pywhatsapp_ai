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

    @abstractmethod
    async def send_media_message(
        self,
        to: str,
        media_type: str,
        media_link: Optional[str] = None,
        media_id: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a media message (image, document, audio, video, sticker)."""
        pass

    @abstractmethod
    async def send_interactive_message(
        self,
        to: str,
        interactive_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send an interactive message (buttons, lists, product)."""
        pass

    @abstractmethod
    async def mark_message_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark an incoming message as read."""
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

    async def send_media_message(
        self,
        to: str,
        media_type: str,
        media_link: Optional[str] = None,
        media_id: Optional[str] = None,
        caption: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Send a media message (image, document, audio, video, sticker)."""
        if not media_link and not media_id:
            raise ValueError("Either media_link or media_id must be provided")

        media_obj: Dict[str, Any] = {}
        if media_link:
            media_obj["link"] = media_link
        if media_id:
            media_obj["id"] = media_id
        if caption and media_type in ["image", "video", "document"]:
            media_obj["caption"] = caption

        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": media_type,
            media_type: media_obj,
        }
        return await self._post(payload)

    async def send_interactive_message(
        self,
        to: str,
        interactive_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Send an interactive message (buttons, lists, product)."""
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": to,
            "type": "interactive",
            "interactive": interactive_data,
        }
        return await self._post(payload)

    async def mark_message_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark an incoming message as read."""
        payload = {
            "messaging_product": "whatsapp",
            "status": "read",
            "message_id": message_id,
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
