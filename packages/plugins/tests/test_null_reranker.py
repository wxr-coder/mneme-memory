"""Tests for NullReranker."""

from mneme_core import MemCell, SearchResult
from mneme_plugins.reranker import NullReranker


def test_null_reranker_passthrough():
    reranker = NullReranker()
    results = [SearchResult(memory=MemCell(content=f"test {i}"), score=0.5, source="semantic") for i in range(5)]
    reranked = reranker.rerank("query", results, top_k=3)
    assert len(reranked) == 3
    assert reranked[0].memory.content == "test 0"


def test_null_reranker_capability():
    reranker = NullReranker()
    cap = reranker.capability()
    assert cap.gpu_required is False
    assert cap.min_vram_gb == 0.0
