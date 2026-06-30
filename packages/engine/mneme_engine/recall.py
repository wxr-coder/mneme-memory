"""Recall pipeline — multi-path retrieval + RRF fusion + reconstructive touch.

The core insight from cognitive science: human memory is reconstructive, not
reproductive. Every act of recall subtly alters the memory being recalled.
This pipeline implements that principle via MemCell.touch().
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from mneme_core import SearchResult

if TYPE_CHECKING:
    from mneme_engine.engine import Engine

logger = structlog.get_logger()

# Reciprocal Rank Fusion constant
RRF_K = 60


class RecallPipeline:
    """Orchestrates multi-path retrieval, RRF fusion, reranking, and reconstructive touch."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    async def search(
        self,
        query: str,
        top_k: int = 10,
        fact_types: list[str] | None = None,
    ) -> list[SearchResult]:
        """Full recall pipeline:

        1. Query all configured retrievers in parallel
        2. RRF fuse the results
        3. Rerank if a reranker is available (TIER S/A)
        4. Reconstructive touch — update last_accessed + access_count
        """
        plugins = self._engine.plugins

        # If no retrievers are configured, return empty
        if not plugins.retrievers:
            logger.warning("recall.no_retrievers")
            return []

        # 1. Query all retrievers in parallel
        # TODO: use asyncio.gather once retrievers are async-capable
        all_results: dict[str, list[SearchResult]] = {}
        for retriever in plugins.retrievers:
            try:
                results = retriever.search(query, top_k=top_k * 2)  # over-fetch 2x
                all_results[retriever.name] = results
            except Exception:
                logger.exception("recall.retriever_error", retriever=retriever.name)

        if not all_results:
            return []

        # 2. RRF fusion
        fused = self._rrf_fuse(all_results, top_k=top_k * 2)

        # 3. Rerank if available
        if plugins.reranker and self._engine.tier.has_reranker:
            try:
                fused = plugins.reranker.rerank(query, fused, top_k=top_k)
            except Exception:
                logger.exception("recall.reranker_error")

        # 4. Trim to top_k
        final = fused[:top_k]

        # 5. Reconstructive touch — mutate memory state on recall
        for result in final:
            result.memory.touch()
            # Persist the touched state
            if plugins.storage:
                try:
                    await plugins.storage.update_memory(result.memory)
                except Exception:
                    logger.exception("recall.touch_persist_error", memory_id=result.memory.id)

        logger.info(
            "recall.complete",
            query_preview=query[:80],
            num_results=len(final),
            retrievers_used=list(all_results.keys()),
        )
        return final

    def _rrf_fuse(
        self,
        all_results: dict[str, list[SearchResult]],
        top_k: int,
    ) -> list[SearchResult]:
        """Reciprocal Rank Fusion.

        score(d) = sum over retrievers: 1 / (k + rank(d))
        """
        scores: dict[str, float] = {}
        memory_map: dict[str, SearchResult] = {}

        for _retriever_name, results in all_results.items():
            for rank, result in enumerate(results):
                mid = result.memory.id
                # RRF formula
                scores[mid] = scores.get(mid, 0.0) + 1.0 / (RRF_K + rank + 1)
                # Keep the SearchResult with the highest individual score for metadata
                if mid not in memory_map or result.score > memory_map[mid].score:
                    memory_map[mid] = result

        # Sort by fused score
        ranked_ids = sorted(scores.keys(), key=lambda mid: scores[mid], reverse=True)

        fused: list[SearchResult] = []
        for mid in ranked_ids[:top_k]:
            result = memory_map[mid]
            # Create a new SearchResult with the fused score
            fused.append(
                SearchResult(
                    memory=result.memory,
                    score=scores[mid],
                    source="rrf_fusion",
                    metadata={**result.metadata, "fused_score": scores[mid]},
                )
            )

        return fused
