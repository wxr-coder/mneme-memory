"""Tests for classification-aware recall pipeline."""

from __future__ import annotations

import pytest

from mneme_core import FactType, MemCell
from mneme_engine.engine import Engine, PluginBundle
from mneme_plugins.retriever.in_memory import BM25Retriever
from mneme_plugins.storage.in_memory import InMemoryStorage


@pytest.mark.asyncio
async def test_recall_with_fact_type_filter():
    """Recall should only return memories matching the fact_type filter."""
    storage = InMemoryStorage()

    # Store memories of different fact_types
    await storage.store_memory(MemCell(content="Python is a programming language", fact_type=FactType.WORLD))
    await storage.store_memory(MemCell(content="I wrote Python code today", fact_type=FactType.EXPERIENCE))
    await storage.store_memory(MemCell(content="The sky is blue", fact_type=FactType.WORLD))

    # Build engine with BM25 retriever
    bundle = PluginBundle(
        storage=storage,
        retrievers=[BM25Retriever(storage)],
    )
    engine = Engine(plugins=bundle)

    # Recall without filter — should return all Python-related
    all_results = await engine.recall("Python")
    assert len(all_results) >= 2

    # Recall with filter: only WORLD
    world_results = await engine.recall("Python", fact_types=["world"])
    assert len(world_results) == 1
    assert world_results[0].memory.fact_type == FactType.WORLD
    assert "programming language" in world_results[0].memory.content

    # Recall with filter: only EXPERIENCE
    exp_results = await engine.recall("Python", fact_types=["experience"])
    assert len(exp_results) == 1
    assert exp_results[0].memory.fact_type == FactType.EXPERIENCE
    assert "wrote Python code" in exp_results[0].memory.content

    # Recall with filter: non-existent type
    empty = await engine.recall("Python", fact_types=["observation"])
    assert len(empty) == 0


@pytest.mark.asyncio
async def test_recall_with_multiple_fact_types():
    """Recall should support filtering by multiple fact_types."""
    storage = InMemoryStorage()
    await storage.store_memory(MemCell(content="Python language", fact_type=FactType.WORLD))
    await storage.store_memory(MemCell(content="I coded in Python", fact_type=FactType.EXPERIENCE))
    await storage.store_memory(MemCell(content="Debugging is hard", fact_type=FactType.OBSERVATION))

    bundle = PluginBundle(
        storage=storage,
        retrievers=[BM25Retriever(storage)],
    )
    engine = Engine(plugins=bundle)

    # Filter: WORLD + EXPERIENCE (not OBSERVATION)
    results = await engine.recall("Python", fact_types=["world", "experience"])
    assert len(results) == 2
    fact_types_in_results = {r.memory.fact_type for r in results}
    assert FactType.OBSERVATION not in fact_types_in_results


@pytest.mark.asyncio
async def test_recall_no_filter_returns_all():
    """Recall without fact_types filter should return all matches."""
    storage = InMemoryStorage()
    await storage.store_memory(MemCell(content="Python is great", fact_type=FactType.WORLD))
    await storage.store_memory(MemCell(content="I love Python", fact_type=FactType.EXPERIENCE))

    bundle = PluginBundle(
        storage=storage,
        retrievers=[BM25Retriever(storage)],
    )
    engine = Engine(plugins=bundle)

    results = await engine.recall("Python")
    assert len(results) == 2


@pytest.mark.asyncio
async def test_recall_reconstructive_touch_persisted():
    """Recall should persist touch() updates via storage.update_memory."""
    storage = InMemoryStorage()
    cell = MemCell(content="Python is great", fact_type=FactType.WORLD)
    await storage.store_memory(cell)

    bundle = PluginBundle(
        storage=storage,
        retrievers=[BM25Retriever(storage)],
    )
    engine = Engine(plugins=bundle)

    # Recall once
    results = await engine.recall("Python")
    assert len(results) == 1
    assert results[0].memory.access_count == 1

    # Verify it was persisted to storage
    stored = await storage.get_memory(cell.id)
    assert stored is not None
    assert stored.access_count == 1
    assert stored.last_accessed is not None
