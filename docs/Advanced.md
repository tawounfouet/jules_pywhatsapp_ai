# Advanced Usage

The `whatsapp-ai` SDK is built with Clean Architecture, making it easy to swap implementations and add new providers.

## 1. Creating a Custom AI Provider

If you prefer to use Anthropic, a local LLM via Ollama, or a different API, simply implement `BaseAIProvider`.

```python
from typing import Any, Dict, List
from whatsapp_ai.ai.base import BaseAIProvider

class MockAIProvider(BaseAIProvider):
    """A dummy AI provider for testing."""

    async def generate_response(
        self,
        user_id: str,
        message: str,
        context: List[Dict[str, Any]]
    ) -> str:
        # Here you would make your HTTP call to your API
        return f"Hello, you said: {message}"
```

In your application:

```python
ai = MockAIProvider()
router = MessageRouter(client=client, ai_provider=ai, memory=memory)
```

## 2. Using Redis for Memory

For production, you'll need a persistent memory store instead of `InMemoryStore` to retain context across restarts and worker threads.

Here is an example using `redis-py` (you must install it first `pip install redis`).

```python
import json
import redis.asyncio as redis
from typing import Any, Dict, List
from whatsapp_ai.memory import BaseMemoryStore

class RedisMemoryStore(BaseMemoryStore):
    def __init__(self, redis_url: str = "redis://localhost"):
        self.client = redis.from_url(redis_url, decode_responses=True)

    def _key(self, user_id: str) -> str:
        return f"whatsapp_chat:{user_id}"

    async def get_messages(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        raw_msgs = await self.client.lrange(self._key(user_id), -limit, -1)
        return [json.loads(msg) for msg in raw_msgs]

    async def add_message(self, user_id: str, role: str, content: str) -> None:
        payload = json.dumps({"role": role, "content": content})
        await self.client.rpush(self._key(user_id), payload)
        # Keep only the last 50 messages
        await self.client.ltrim(self._key(user_id), -50, -1)

    async def clear_history(self, user_id: str) -> None:
        await self.client.delete(self._key(user_id))
```

In your application:

```python
memory = RedisMemoryStore("redis://localhost:6379/0")
router = MessageRouter(client=client, ai_provider=ai, memory=memory)
```

## 3. Extending the Settings

If you need to add configuration values (like `REDIS_URL` or `ANTHROPIC_API_KEY`), subclass `WhatsAppConfig`:

```python
from whatsapp_ai import WhatsAppConfig

class AppConfig(WhatsAppConfig):
    redis_url: str = "redis://localhost:6379"
    anthropic_api_key: str | None = None
```

```python
config = AppConfig()
```
