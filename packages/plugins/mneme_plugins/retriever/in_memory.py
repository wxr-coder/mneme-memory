"""InMemoryRetriever: Retrieval strategies backed by InMemoryStorage.

Provides two retriever strategies:
  - SemanticRetriever: embeds the query, delegates to storage.search_vector()
  - BM25Retriever: delegates to storage.search_bm25()

Both pass MemoryFilter through to the storage layer so that classification
constraints (fact_type, provenance, privacy, etc.) are enforced at the
storage level for maximum efficiency.
"""

from __future__ import annotations

from mneme_core import Capability, MemoryFilter, SearchResult, Tier
from mneme_plugins.interfaces.embedding import EmbeddingProvider
from mneme_plugins.interfaces.retriever import Retriever
from mneme_plugins.interfaces.storage import StorageBackend


class SemanticRetriever(Retriever):
    """Vector similarity retriever.

    Embeds the query text via an EmbeddingProvider and delegates to
    StorageBackend.search_vector() with the same MemoryFilter.
    """

    def __init__(self, storage: StorageBackend, embedding: EmbeddingProvider) -> None:
        self._storage = storage
        self._embedding = embedding

    @property
    def name(self) -> str:
        return "semantic"

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: MemoryFilter | None = None,
    ) -> list[SearchResult]:
        query_vec = self._embedding.embed([query])[0]
        # search_vector is async — but Retriever.search is sync.
        # We use a sync wrapper since the recall pipeline calls us synchronously.
        import asyncio

        coro = self._storage.search_vector(query_vec, top_k=top_k, filters=filters)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in an async context — schedule it
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, coro).result()
        except RuntimeError:
            pass
        return asyncio.run(coro)

    def capability(self) -> Capability:
        return Capability(
            min_vram_gb=0.0,
            min_ram_gb=1.0,
            recommended_tier=Tier.C,
            gpu_required=False,
            description="Semantic retrieval (cosine similarity)",
        )


class BM25Retriever(Retriever):
    """Lexical retriever using BM25 ranking.

    Delegates to StorageBackend.search_bm25() with the same MemoryFilter.
    """

    def __init__(self, storage: StorageBackend) -> None:
        self._storage = storage

    @property
    def name(self) -> str:
        return "bm25"

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: MemoryFilter | None = None,
    ) -> list[SearchResult]:
        import asyncio

        coro = self._storage.search_bm25(query, top_k=top_k, filters=filters)
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as pool:
                    return pool.submit(asyncio.run, coro).result()
        except RuntimeError:
            pass
        return asyncio.run(coro)

    def capability(self) -> Capability:
        return Capability(
            min_vram_gb=0.0,
            min_ram_gb=0.5,
            recommended_tier=Tier.C,
            gpu_required=False,
            description="BM25 lexical retrieval",
        )
