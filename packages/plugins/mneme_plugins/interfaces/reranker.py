"""Reranker: Re-order retrieved results for better precision."""

from __future__ import annotations

from abc import ABC, abstractmethod

from mneme_core import Capability, SearchResult


class Reranker(ABC):
    """Abstract base for rerankers."""

    @abstractmethod
    def rerank(self, query: str, candidates: list[SearchResult], top_k: int = 10) -> list[SearchResult]:
        """Re-order candidates by relevance to the query."""
        ...

    @abstractmethod
    def capability(self) -> Capability:
        """Declare resource requirements."""
        ...
