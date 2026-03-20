import logging
from typing import Awaitable, Callable, List, Optional

from whatsapp_ai.ai.base import BaseAIProvider
from whatsapp_ai.client import BaseMessagingClient
from whatsapp_ai.memory import BaseMemoryStore
from whatsapp_ai.models import MessageEvent

logger = logging.getLogger(__name__)

# A handler takes an event and a client, and returns True if it handled the event
MessageHandler = Callable[[MessageEvent, BaseMessagingClient], Awaitable[bool]]

class MessageRouter:
    """Routes incoming WhatsApp messages to appropriate handlers or AI layer."""

    def __init__(
        self,
        client: BaseMessagingClient,
        ai_provider: Optional[BaseAIProvider] = None,
        memory: Optional[BaseMemoryStore] = None,
    ):
        self.client = client
        self.ai_provider = ai_provider
        self.memory = memory
        self.handlers: List[MessageHandler] = []

    def register_handler(self, handler: MessageHandler) -> None:
        """Register a custom rule-based handler."""
        self.handlers.append(handler)

    async def handle_event(self, event: MessageEvent) -> None:
        """Main entry point to handle an incoming message."""
        logger.info(f"Received message from {event.sender}: {event.text}")

        # 1. Try rule-based custom handlers first
        for handler in self.handlers:
            handled = await handler(event, self.client)
            if handled:
                logger.debug(f"Event handled by custom handler: {handler.__name__}")
                return

        # 2. If no handler processed it, fall back to AI if configured
        if self.ai_provider:
            await self._handle_with_ai(event)
        else:
            logger.warning("No AI provider configured and no handlers matched the event.")

    async def _handle_with_ai(self, event: MessageEvent) -> None:
        if not self.ai_provider:
            return

        context = []
        if self.memory:
            # Fetch last N messages
            context = await self.memory.get_messages(event.sender, limit=10)

        try:
            # Generate response via AI
            response_text = await self.ai_provider.generate_response(
                user_id=event.sender,
                message=event.text,
                context=context
            )

            # Send back the reply
            await self.client.send_text_message(event.sender, response_text)

            # Store in memory if enabled
            if self.memory:
                await self.memory.add_message(event.sender, "user", event.text)
                await self.memory.add_message(event.sender, "assistant", response_text)

        except Exception as e:
            logger.error(f"Error handling message with AI: {e}")
            await self.client.send_text_message(
                event.sender, "Désolé, une erreur est survenue lors de la génération de ma réponse."
            )
