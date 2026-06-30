"""LLMBackend: LLM completion with optional tool-calling."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from mneme_core.capability import Capability


class LLMBackend(ABC):
    """Abstract base for LLM backends."""

    @abstractmethod
    async def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.0,
        max_tokens: int = 4096,
    ) -> str:
        """Generate a completion from messages."""
        ...

    @abstractmethod
    def capability(self) -> Capability:
        """Declare resource requirements."""
        ...
