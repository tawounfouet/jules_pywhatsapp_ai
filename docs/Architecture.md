# Architecture & Design Patterns

The `whatsapp-ai` SDK is built around **Clean Architecture**, allowing you to decouple the core domain from the underlying implementation details (e.g., HTTP clients, specific AI Providers).

## 1. Domain vs. Infrastructure

### Interfaces (The Domain)

- `BaseMessagingClient` (`client.py`): The interface for sending messages. We could add `SMSClient` or `EmailClient` later without breaking the business logic.
- `BaseMemoryStore` (`memory.py`): The interface for managing conversational context.
- `BaseAIProvider` (`ai/base.py`): The interface for interacting with an AI language model.

### Implementations (The Infrastructure)

- `WhatsAppClient`: Uses `httpx` to communicate with Meta APIs. Uses `tenacity` for resilience against 429 Rate Limits and Network timeouts.
- `InMemoryStore`: A simple Python dictionary storage that drops data when the app restarts. Perfect for development, simple testing.
- `OpenAIProvider`: Uses `httpx` directly (no `openai` SDK dependency) to stay purely `async` and aligned with the rest of the project.

## 2. Webhook & Message Router

The `WebhookReceiver` is a `FastAPI` application wrapper.
When a webhook hits `/webhook`, it validates the signature and payload structure using `Pydantic v2`.

The valid payloads are then mapped to a `MessageEvent` object:

```python
class MessageEvent(BaseModel):
    message_id: str
    sender: str
    text: str
    timestamp: str
    raw_payload: dict[str, Any]
```

This `MessageEvent` is then passed to the `MessageRouter`.

## 3. The MessageRouter

The `MessageRouter` acts as the dispatcher.

When `router.handle_event(event)` is called:

1. **Rule-based Handlers:** It iterates over any registered `MessageHandler` (custom Python async functions). If a handler processes the event and returns `True`, routing stops.
2. **AI Fallback:** If no custom handler matched the message (or if they returned `False`), it falls back to the configured `BaseAIProvider`.
3. **Context Injection:** Before sending to the AI provider, the router retrieves previous messages via `BaseMemoryStore` to preserve conversational context.

## 4. Why Use `httpx` Directly?

You might wonder why we implement an `OpenAIProvider` manually instead of relying on the official `openai` Python SDK.

The design goal of this package is to be lightweight, modular, and natively async.
By using `httpx` (which we already depend on for Meta's API calls), we reduce the dependency footprint significantly.
It keeps error handling and rate limiting concepts unified across the SDK (using `tenacity` retry logic).
