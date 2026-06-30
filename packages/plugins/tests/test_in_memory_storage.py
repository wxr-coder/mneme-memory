"""Tests for InMemoryStorage and classification-aware retrieval."""

from __future__ import annotations

import numpy as np
import pytest

from mneme_core import FactType, MemCell, MemoryFilter, Provenance
from mneme_plugins.storage.in_memory import InMemoryStorage

# ── InMemoryStorage unit tests ────────────────────────────


@pytest.mark.asyncio
async def test_store_and_get_memory():
    """store_memory should persist; get_memory should retrieve."""
    storage = InMemoryStorage()
    cell = MemCell(content="Hello world", fact_type=FactType.WORLD)
    mid = await storage.store_memory(cell)
    assert mid == cell.id

    retrieved = await storage.get_memory(mid)
    assert retrieved is not None
    assert retrieved.content == "Hello world"
    assert retrieved.fact_type == FactType.WORLD


@pytest.mark.asyncio
async def test_update_memory():
    """update_memory should persist changes."""
    storage = InMemoryStorage()
    cell = MemCell(content="Original")
    await storage.store_memory(cell)

    cell.touch()
    ok = await storage.update_memory(cell)
    assert ok is True

    retrieved = await storage.get_memory(cell.id)
    assert retrieved.access_count == 1


@pytest.mark.asyncio
async def test_update_nonexistent_returns_false():
    """update_memory should return False for unknown ID."""
    storage = InMemoryStorage()
    cell = MemCell(content="Ghost")
    ok = await storage.update_memory(cell)
    assert ok is False


# ── BM25 search with filters ──────────────────────────────


@pytest.mark.asyncio
async def test_bm25_search_basic():
    """BM25 search should find relevant documents."""
    storage = InMemoryStorage()
    await storage.store_memory(MemCell(content="Python is a programming language"))
    await storage.store_memory(MemCell(content="Rust is a systems programming language"))
    await storage.store_memory(MemCell(content="I like pizza"))

    results = await storage.search_bm25("programming language", top_k=3)
    assert len(results) >= 2
    # Both Python and Rust docs should be in results
    contents = [r.memory.content for r in results]
    assert any("Python" in c for c in contents)
    assert any("Rust" in c for c in contents)
    # Pizza should not be relevant
    assert not any("pizza" in c.lower() for c in contents)


@pytest.mark.asyncio
async def test_bm25_search_with_fact_type_filter():
    """BM25 search should respect fact_type filter."""
    storage = InMemoryStorage()
    await storage.store_memory(MemCell(content="Python programming", fact_type=FactType.WORLD))
    await storage.store_memory(MemCell(content="I programmed in Python today", fact_type=FactType.EXPERIENCE))

    # Search with filter: only WORLD memories
    filt = MemoryFilter(fact_types=[FactType.WORLD])
    results = await storage.search_bm25("Python", top_k=10, filters=filt)
    assert len(results) == 1
    assert results[0].memory.fact_type == FactType.WORLD
    assert results[0].memory.content == "Python programming"


@pytest.mark.asyncio
async def test_bm25_search_with_provenance_filter():
    """BM25 search should respect provenance filter."""
    storage = InMemoryStorage()
    await storage.store_memory(
        MemCell(
            content="User prefers dark mode",
            provenance=Provenance.USER_DECLARED,
        )
    )
    await storage.store_memory(
        MemCell(
            content="User might like dark mode",
            provenance=Provenance.INFERRED_FROM_INPUT,
        )
    )

    filt = MemoryFilter(provenance=[Provenance.USER_DECLARED])
    results = await storage.search_bm25("dark mode", top_k=10, filters=filt)
    assert len(results) == 1
    assert results[0].memory.provenance == Provenance.USER_DECLARED


@pytest.mark.asyncio
async def test_bm25_search_empty_storage():
    """BM25 search on empty storage should return []."""
    storage = InMemoryStorage()
    results = await storage.search_bm25("anything")
    assert results == []


# ── Vector search with filters ────────────────────────────


@pytest.mark.asyncio
async def test_vector_search_with_filter():
    """Vector search should respect fact_type filter."""
    storage = InMemoryStorage()
    # Two memories with same content but different fact_type
    await storage.store_memory(
        MemCell(
            content="Python is great",
            fact_type=FactType.WORLD,
            embedding=[1.0, 0.0, 0.0],
        )
    )
    await storage.store_memory(
        MemCell(
            content="Python is great",
            fact_type=FactType.EXPERIENCE,
            embedding=[1.0, 0.0, 0.0],
        )
    )

    query_vec = np.array([1.0, 0.0, 0.0], dtype=np.float32)
    filt = MemoryFilter(fact_types=[FactType.WORLD])
    results = await storage.search_vector(query_vec, top_k=10, filters=filt)
    assert len(results) == 1
    assert results[0].memory.fact_type == FactType.WORLD


@pytest.mark.asyncio
async def test_vector_search_no_embedding_skipped():
    """Memories without embedding should be skipped in vector search."""
    storage = InMemoryStorage()
    await storage.store_memory(MemCell(content="no embedding"))
    query_vec = np.array([1.0, 0.0], dtype=np.float32)
    results = await storage.search_vector(query_vec)
    assert results == []


# ── Graph traversal ───────────────────────────────────────


@pytest.mark.asyncio
async def test_create_and_traverse_links():
    """create_link + traverse_graph should work bidirectionally."""
    storage = InMemoryStorage()
    a = MemCell(content="A")
    b = MemCell(content="B")
    c = MemCell(content="C")
    for m in (a, b, c):
        await storage.store_memory(m)

    await storage.create_link(a.id, b.id, "semantic")
    await storage.create_link(b.id, c.id, "semantic")

    # 1 hop from A → B
    hop1 = await storage.traverse_graph([a.id], hops=1)
    assert b.id in hop1
    assert c.id not in hop1

    # 2 hops from A → B → C
    hop2 = await storage.traverse_graph([a.id], hops=2)
    assert b.id in hop2
    assert c.id in hop2


@pytest.mark.asyncio
async def test_create_link_nonexistent_fails():
    """create_link should return False for unknown memory IDs."""
    storage = InMemoryStorage()
    ok = await storage.create_link("ghost1", "ghost2", "semantic")
    assert ok is False


# ── MemoryFilter unit tests ───────────────────────────────


def test_memory_filter_matches_fact_type():
    """MemoryFilter.matches should check fact_type."""
    cell = MemCell(content="test", fact_type=FactType.WORLD)
    filt = MemoryFilter(fact_types=[FactType.WORLD])
    assert filt.matches(cell) is True

    filt2 = MemoryFilter(fact_types=[FactType.EXPERIENCE])
    assert filt2.matches(cell) is False


def test_memory_filter_matches_confidence():
    """MemoryFilter.matches should check min_confidence."""
    cell = MemCell(content="test", confidence=0.3)
    filt = MemoryFilter(min_confidence=0.5)
    assert filt.matches(cell) is False

    filt2 = MemoryFilter(min_confidence=0.2)
    assert filt2.matches(cell) is True


def test_memory_filter_from_fact_types_strings():
    """from_fact_types should convert string list to MemoryFilter."""
    filt = MemoryFilter.from_fact_types(["world", "experience"])
    assert filt is not None
    assert len(filt.fact_types) == 2
    assert FactType.WORLD in filt.fact_types
    assert FactType.EXPERIENCE in filt.fact_types


def test_memory_filter_from_fact_types_none():
    """from_fact_types should return None for empty/None input."""
    assert MemoryFilter.from_fact_types(None) is None
    assert MemoryFilter.from_fact_types([]) is None
