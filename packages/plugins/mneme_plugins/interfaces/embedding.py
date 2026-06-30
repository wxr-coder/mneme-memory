"""EmbeddingProvider: Generate vector embeddings for text."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from mneme_core.capability import Capability


class EmbeddingProvider(ABC):
    """Abstract base for embedding providers."""

    @abstractmethod
    def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts. Returns array of shape (n, dim)."""
        ...

    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        ...

    @abstractmethod
    def capability(self) -> Capability:
        """Declare resource requirements."""
        ...
