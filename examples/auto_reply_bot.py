import logging
import uvicorn

from whatsapp_ai.client import BaseMessagingClient
from whatsapp_ai import (
    WhatsAppConfig,
    WhatsAppClient,
    MessageRouter,
    WebhookReceiver,
    InMemoryStore,
    MessageEvent,
)
from whatsapp_ai.ai.openai_provider import OpenAIProvider

logging.basicConfig(level=logging.INFO)

# 1. Configuration (loaded from .env)
config = WhatsAppConfig()

# 2. Components
client = WhatsAppClient(config)
memory = InMemoryStore()
ai_provider = OpenAIProvider(config, model="gpt-3.5-turbo")

# 3. Router
router = MessageRouter(client=client, ai_provider=ai_provider, memory=memory)

# Optional: Add a custom rule-based handler BEFORE the AI is triggered
async def ping_pong_handler(event: MessageEvent, messaging_client: BaseMessagingClient) -> bool:
    if event.text.lower() == "ping":
        await messaging_client.send_text_message(event.sender, "Pong! (Rule-based reply)")
        return True # Handled, do not call AI
    return False

router.register_handler(ping_pong_handler)

# 4. Webhook Server
webhook_receiver = WebhookReceiver(config=config, router=router)
app = webhook_receiver.get_app()

if __name__ == "__main__":
    uvicorn.run(app, host=config.webhook_host, port=config.webhook_port)
