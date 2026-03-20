from abc import ABC, abstractmethod
from typing import Any, Dict, List

class BaseAIProvider(ABC):
    """Abstract interface for AI Providers (OpenAI, Anthropic, etc.)."""

    @abstractmethod
    async def generate_response(
        self,
        user_id: str,
        message: str,
        context: List[Dict[str, Any]]
    ) -> str:
        """
        Generate a text response given a user's message and their conversational context.
        """
        pass
