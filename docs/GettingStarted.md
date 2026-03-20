# Getting Started

Welcome to the `whatsapp-ai` SDK! This guide will help you set up and build your first WhatsApp Bot powered by AI.

## 1. Installation

Install the package via `pip` (or `poetry`, `pipenv`, etc.):

```bash
pip install whatsapp-ai
```

## 2. Meta WhatsApp Cloud API Setup

Before you write any code, you need a WhatsApp Cloud API application set up via the [Meta Developer Portal](https://developers.facebook.com/).
1. Create a Facebook App with the "Business" type.
2. Add the "WhatsApp" product to your app.
3. Note your **Phone Number ID**, **Access Token** (use a permanent system user token in production).
4. Decide on a **Verify Token** (a random string you'll use to verify webhooks).

## 3. Configuration

The package relies heavily on environment variables for configuration. Create a `.env` file in the root of your project:

```env
# Meta / WhatsApp API
WHATSAPP_ACCESS_TOKEN="EAAX..."
WHATSAPP_PHONE_NUMBER_ID="123456789"
WHATSAPP_VERIFY_TOKEN="my_secure_token_123"
WHATSAPP_API_VERSION="v18.0"

# Provider APIs
OPENAI_API_KEY="sk-..."

# App Config (Optional, defaults shown)
WEBHOOK_HOST="0.0.0.0"
WEBHOOK_PORT=8000
```

## 4. Basic Client: Sending a Message

If you only want to send messages out (e.g., alerts, OTPs), you only need the `WhatsAppClient`.

```python
import asyncio
from whatsapp_ai import WhatsAppClient, WhatsAppConfig

async def send_alert():
    # Automatically loads from the .env file
    config = WhatsAppConfig()
    client = WhatsAppClient(config)

    response = await client.send_text_message(
        to="33612345678", # Country code without the '+'
        text="Hello! This is an alert from your bot."
    )
    print("Message ID:", response["messages"][0]["id"])

if __name__ == "__main__":
    asyncio.run(send_alert())
```

## 5. Webhook & AI: Building a Bot

To receive messages and reply automatically using AI, you'll need the complete stack: **Client**, **Memory Store**, **AI Provider**, **Message Router**, and **Webhook Receiver**.

Create `bot.py`:

```python
import logging
import uvicorn

from whatsapp_ai import (
    WhatsAppConfig,
    WhatsAppClient,
    MessageRouter,
    WebhookReceiver,
    InMemoryStore,
    MessageEvent,
)
from whatsapp_ai.client import BaseMessagingClient
from whatsapp_ai.ai.openai_provider import OpenAIProvider

logging.basicConfig(level=logging.INFO)

# Load configuration
config = WhatsAppConfig()

# Initialize components
client = WhatsAppClient(config)
memory = InMemoryStore()
ai_provider = OpenAIProvider(config, model="gpt-3.5-turbo")

# Connect them via the router
router = MessageRouter(client=client, ai_provider=ai_provider, memory=memory)

# (Optional) Add a custom rule-based handler BEFORE the AI
# E.g., if a user sends "help", don't call the AI, reply statically.
async def help_handler(event: MessageEvent, messaging_client: BaseMessagingClient) -> bool:
    if event.text.lower() == "help":
        await messaging_client.send_text_message(event.sender, "This is the help menu. You can chat with the AI!")
        return True # Handled, do not call AI
    return False

router.register_handler(help_handler)

# Start Webhook Receiver
webhook = WebhookReceiver(config=config, router=router)
app = webhook.get_app()

if __name__ == "__main__":
    uvicorn.run(app, host=config.webhook_host, port=config.webhook_port)
```

Start the bot:
```bash
python bot.py
```

### Exposing your Localhost
To configure your Webhook URL in Meta's Developer Portal, you need a public URL. Use a tool like **ngrok** to expose your local server:

```bash
ngrok http 8000
```

Use `https://<ngrok-id>.ngrok-free.app/webhook` as your Webhook URL in the Meta portal and provide your `WHATSAPP_VERIFY_TOKEN`.
