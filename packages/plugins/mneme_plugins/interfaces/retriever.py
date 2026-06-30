"""Retriever: Search memories by a specific strategy."""

from __future__ import annotations

from abc import ABC, abstractmethod

from mneme_core import Capability, SearchResult


class Retriever(ABC):
    """Abstract base for retrieval strategies (semantic, BM25, graph, temporal)."""

    @abstractmethod
    def search(self, query: str, top_k: int = 10, filters: dict | None = None) -> list[SearchResult]:
        """Search for memories matching the query."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Retriever name (e.g. 'semantic', 'bm25', 'graph', 'temporal')."""
        ...

    @abstractmethod
    def capability(self) -> Capability:
        """Declare resource requirements."""
        ...
