# WhatsApp AI

A modular, extensible, production-ready Python SDK for integrating the **WhatsApp Cloud API** with **AI providers** (like OpenAI) to create smart conversational bots.

## Features

- **Clean Architecture:** Domain and infrastructure are decoupled using abstract interfaces (`BaseMessagingClient`, `BaseMemoryStore`, `BaseAIProvider`).
- **Async First:** Full `asyncio` compatibility using `httpx` and `FastAPI`.
- **Typing & Validation:** Built entirely with `Pydantic v2` and strict typing for MyPy.
- **Resilience:** Automatic retries and exponential backoff on API errors via `tenacity`.
- **Routing Engine:** Support for custom rule-based handlers *and* fallback to AI.
- **Conversational Memory:** Easily store context via abstract memory stores.
- **CLI Toolkit:** Ship with a built-in CLI using `Typer`.

## Installation

```bash
pip install whatsapp-ai
```

## Configuration

The package relies on environment variables. Create a `.env` file in your root folder:

```env
WHATSAPP_ACCESS_TOKEN="EAAX..."
WHATSAPP_PHONE_NUMBER_ID="123456789"
WHATSAPP_VERIFY_TOKEN="my_secure_token"
WHATSAPP_API_VERSION="v18.0"

OPENAI_API_KEY="sk-..."
```

## Usage

### 1. Sending a Simple Message

```python
import asyncio
from whatsapp_ai import WhatsAppClient, WhatsAppConfig

async def main():
    config = WhatsAppConfig()
    client = WhatsAppClient(config)
    await client.send_text_message(to="33612345678", text="Hello world!")

asyncio.run(main())
```

### 2. Auto-Reply AI Bot (FastAPI Webhook)

See `examples/auto_reply_bot.py` for a full example with custom handlers and AI fallback.

```python
from whatsapp_ai import WhatsAppClient, WhatsAppConfig, MessageRouter, WebhookReceiver, InMemoryStore
from whatsapp_ai.ai.openai_provider import OpenAIProvider
import uvicorn

config = WhatsAppConfig()
client = WhatsAppClient(config)
memory = InMemoryStore()
ai = OpenAIProvider(config)

router = MessageRouter(client, ai_provider=ai, memory=memory)
webhook = WebhookReceiver(config, router)
app = webhook.get_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### 3. CLI Toolkit

You can use the built-in CLI to send messages or start a webhook testing server:

```bash
# Send a message
whatsapp-ai send 33612345678 "Test from CLI"

# Start the webhook server with AI enabled
whatsapp-ai serve --ai
```

## Architecture

```text
/whatsapp_ai/
    __init__.py
    cli.py                 # Typer CLI definition
    client.py              # WhatsAppCloud API core (httpx)
    config.py              # Pydantic v2 Settings config
    exceptions.py          # Custom exceptions
    memory.py              # In-memory context storage implementation
    models.py              # Pydantic v2 domain & API payload models
    router.py              # Logic router between custom rules & AI
    webhook.py             # FastAPI integration for webhooks
    ai/
        base.py            # AI Provider Interface
        openai_provider.py # OpenAI httpx provider implementation
```

## Future Extensions

Because this SDK is built with Clean Architecture, you can extend it effortlessly:
- Add a new Provider by implementing `BaseAIProvider` (e.g., Anthropic).
- Add Redis context by implementing `BaseMemoryStore`.
- Add SMS channels by implementing `BaseMessagingClient`.
