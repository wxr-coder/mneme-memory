"""NullReranker: No-op reranker for TIER B/C."""

from __future__ import annotations

from mneme_core import Capability, SearchResult, Tier
from mneme_plugins.interfaces.reranker import Reranker


class NullReranker(Reranker):
    """Pass-through reranker — no reordering.

    Used when TIER B/C has no GPU for cross-encoder,
    or when reranking is disabled in config.
    """

    @property
    def name(self) -> str:
        return "null"

    def rerank(self, query: str, candidates: list[SearchResult], top_k: int = 10) -> list[SearchResult]:
        return candidates[:top_k]

    def capability(self) -> Capability:
        return Capability(
            min_vram_gb=0.0,
            recommended_tier=Tier.C,
            gpu_required=False,
            description="No-op reranker",
        )
