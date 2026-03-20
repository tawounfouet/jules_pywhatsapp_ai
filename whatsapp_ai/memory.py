from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseMemoryStore(ABC):
    """Abstract interface for managing conversational context."""

    @abstractmethod
    async def get_messages(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Retrieve recent messages for a specific user.
        Format should generally be lists of dictionaries (e.g., {"role": "user", "content": "..."})
        """
        pass

    @abstractmethod
    async def add_message(self, user_id: str, role: str, content: str) -> None:
        """Add a new message to the user's conversational history."""
        pass

    @abstractmethod
    async def clear_history(self, user_id: str) -> None:
        """Clear the conversational history for a user."""
        pass


class InMemoryStore(BaseMemoryStore):
    """In-memory dictionary based store for conversational context."""

    def __init__(self) -> None:
        self.store: Dict[str, List[Dict[str, Any]]] = {}

    async def get_messages(self, user_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        if user_id not in self.store:
            return []
        # Return the last `limit` messages
        return self.store[user_id][-limit:]

    async def add_message(self, user_id: str, role: str, content: str) -> None:
        if user_id not in self.store:
            self.store[user_id] = []
        self.store[user_id].append({"role": role, "content": content})

    async def clear_history(self, user_id: str) -> None:
        if user_id in self.store:
            self.store[user_id] = []
