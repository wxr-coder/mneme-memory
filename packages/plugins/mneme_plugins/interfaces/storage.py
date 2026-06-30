"""StorageBackend: Persist and query memories."""

from __future__ import annotations

from abc import ABC, abstractmethod

import numpy as np

from mneme_core import Capability, MemCell, MemoryFilter, SearchResult


class StorageBackend(ABC):
    """Abstract base for storage backends."""

    @abstractmethod
    async def store_memory(self, memory: MemCell) -> str:
        """Store a memory cell. Returns the memory ID."""
        ...

    @abstractmethod
    async def search_vector(
        self,
        query_vec: np.ndarray,
        top_k: int = 10,
        filters: MemoryFilter | None = None,
    ) -> list[SearchResult]:
        """Vector similarity search."""
        ...

    @abstractmethod
    async def search_bm25(
        self,
        query: str,
        top_k: int = 10,
        filters: MemoryFilter | None = None,
    ) -> list[SearchResult]:
        """Full-text search."""
        ...

    @abstractmethod
    async def create_link(self, src_id: str, dst_id: str, link_type: str, weight: float = 0.5) -> bool:
        """Create a link between two memories."""
        ...

    @abstractmethod
    async def traverse_graph(self, seed_ids: list[str], hops: int = 2) -> list[str]:
        """Traverse memory links from seeds."""
        ...

    @abstractmethod
    async def get_memory(self, memory_id: str) -> MemCell | None:
        """Retrieve a single memory by ID."""
        ...

    @abstractmethod
    async def update_memory(self, memory: MemCell) -> bool:
        """Persist updates to a memory (e.g. after reconstructive touch)."""
        ...

    @abstractmethod
    def capability(self) -> Capability:
        """Declare resource requirements."""
        ...
