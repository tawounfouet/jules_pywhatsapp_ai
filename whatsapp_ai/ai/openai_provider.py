import logging
from typing import Any, Dict, List

import httpx

from whatsapp_ai.ai.base import BaseAIProvider
from whatsapp_ai.config import WhatsAppConfig

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseAIProvider):
    """OpenAI implementation using httpx."""

    def __init__(self, config: WhatsAppConfig, model: str = "gpt-3.5-turbo"):
        if not config.openai_api_key:
            raise ValueError("OpenAI API Key is missing in configuration.")

        self.api_key = config.openai_api_key
        self.model = model
        self.base_url = "https://api.openai.com/v1/chat/completions"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    async def generate_response(
        self, user_id: str, message: str, context: List[Dict[str, Any]]
    ) -> str:
        # Build messages payload combining context and current user message
        messages = []
        for ctx_msg in context:
            messages.append({"role": ctx_msg["role"], "content": ctx_msg["content"]})

        # We append the newest message directly
        # Context building happens usually in the router/manager,
        # but the latest message should also be sent. If it's already in the context, we shouldn't duplicate.
        # Assuming `context` already contains the latest message or the caller expects us to add it.
        # Generally it's better if `context` is EXACTLY the messages to send.
        # But per our interface, we receive the current message too.
        # Let's assume the caller just passed past history in `context` and we add the new one.
        messages.append({"role": "user", "content": message})

        payload = {
            "model": self.model,
            "messages": messages,
        }

        async with httpx.AsyncClient() as client:
            logger.debug(f"Sending prompt to OpenAI for user {user_id}")
            response = await client.post(
                self.base_url, headers=self.headers, json=payload, timeout=30.0
            )

            if response.status_code >= 400:
                logger.error(f"OpenAI Error: {response.text}")
                response.raise_for_status()

            data = response.json()
            return str(data["choices"][0]["message"]["content"])
