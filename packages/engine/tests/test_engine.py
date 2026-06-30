"""Tests for mneme-engine."""

from __future__ import annotations

import pytest

from mneme_core import FactType, MemCell, Provenance, SearchResult
from mneme_engine.recall import RecallPipeline


def test_rrf_fusion_basic():
    """Test RRF fusion with two retrievers returning overlapping results."""
    from mneme_core import MnemeConfig, Tier
    from mneme_core.capability import HardwareInfo
    from mneme_engine.engine import Engine, PluginBundle

    # Create a minimal engine without any real plugins
    config = MnemeConfig()
    hardware = HardwareInfo(
        gpu_vram_gb=0.0,
        gpu_name=None,
        cpu_cores=4,
        ram_gb=8.0,
        has_nvidia=False,
    )
    tier = Tier.C
    engine = Engine(config=config, tier=tier, hardware=hardware, plugins=PluginBundle())

    pipeline = RecallPipeline(engine)

    # Create some fake results
    mem1 = MemCell(content="Memory 1", fact_type=FactType.WORLD)
    mem2 = MemCell(content="Memory 2", fact_type=FactType.WORLD)
    mem3 = MemCell(content="Memory 3", fact_type=FactType.WORLD)

    results_a = [
        SearchResult(memory=mem1, score=0.9, source="semantic"),
        SearchResult(memory=mem2, score=0.7, source="semantic"),
    ]
    results_b = [
        SearchResult(memory=mem2, score=0.85, source="bm25"),
        SearchResult(memory=mem3, score=0.6, source="bm25"),
    ]

    fused = pipeline._rrf_fuse({"semantic": results_a, "bm25": results_b}, top_k=3)

    # mem2 appears in both retrievers, should rank highest after fusion
    assert len(fused) == 3
    assert fused[0].memory.id == mem2.id  # appeared in both → highest RRF
    assert fused[0].source == "rrf_fusion"
    assert "fused_score" in fused[0].metadata


def test_engine_init_minimal():
    """Test that Engine can initialize with no plugins (skeleton mode)."""
    from mneme_core import MnemeConfig
    from mneme_core.capability import HardwareInfo, Tier
    from mneme_engine.engine import Engine, PluginBundle

    config = MnemeConfig()
    hardware = HardwareInfo(
        gpu_vram_gb=0.0,
        gpu_name=None,
        cpu_cores=4,
        ram_gb=8.0,
        has_nvidia=False,
    )

    engine = Engine(config=config, tier=Tier.C, hardware=hardware, plugins=PluginBundle())

    assert engine.tier == Tier.C
    assert engine.plugins.storage is None
    stats = engine.stats()
    assert stats["tier"] == "C"
    assert stats["has_storage"] is False


@pytest.mark.asyncio
async def test_engine_retain_no_storage():
    """Test retain works even without storage (creates MemCell in memory)."""
    from mneme_core import MnemeConfig
    from mneme_core.capability import HardwareInfo, Tier
    from mneme_engine.engine import Engine, PluginBundle

    config = MnemeConfig()
    hardware = HardwareInfo(
        gpu_vram_gb=0.0,
        gpu_name=None,
        cpu_cores=4,
        ram_gb=8.0,
        has_nvidia=False,
    )
    engine = Engine(config=config, tier=Tier.C, hardware=hardware, plugins=PluginBundle())

    memory = await engine.retain(
        content="Test memory",
        fact_type="world",
        provenance="user_declared",
    )

    assert memory.content == "Test memory"
    assert memory.fact_type == FactType.WORLD
    assert memory.provenance == Provenance.USER_DECLARED


@pytest.mark.asyncio
async def test_engine_recall_no_retrievers():
    """Test recall returns empty list when no retrievers configured."""
    from mneme_core import MnemeConfig
    from mneme_core.capability import HardwareInfo, Tier
    from mneme_engine.engine import Engine, PluginBundle

    config = MnemeConfig()
    hardware = HardwareInfo(
        gpu_vram_gb=0.0,
        gpu_name=None,
        cpu_cores=4,
        ram_gb=8.0,
        has_nvidia=False,
    )
    engine = Engine(config=config, tier=Tier.C, hardware=hardware, plugins=PluginBundle())

    results = await engine.recall("test query")
    assert results == []


@pytest.mark.asyncio
async def test_engine_reflect_no_llm():
    """Test reflect returns gracefully when no LLM configured."""
    from mneme_core import MnemeConfig
    from mneme_core.capability import HardwareInfo, Tier
    from mneme_engine.engine import Engine, PluginBundle

    config = MnemeConfig()
    hardware = HardwareInfo(
        gpu_vram_gb=0.0,
        gpu_name=None,
        cpu_cores=4,
        ram_gb=8.0,
        has_nvidia=False,
    )
    engine = Engine(config=config, tier=Tier.C, hardware=hardware, plugins=PluginBundle())

    result = await engine.reflect("test query")
    assert result["rounds"] == 0
    assert result["synthesis"] is None
    assert "No LLM" in result["message"]


def test_personality_evolver_init():
    """Test personality evolver starts with None and inits on first update."""
    from mneme_core import MnemeConfig
    from mneme_core.capability import HardwareInfo, Tier
    from mneme_engine.engine import Engine, PluginBundle

    config = MnemeConfig()
    hardware = HardwareInfo(
        gpu_vram_gb=0.0,
        gpu_name=None,
        cpu_cores=4,
        ram_gb=8.0,
        has_nvidia=False,
    )
    engine = Engine(config=config, tier=Tier.C, hardware=hardware, plugins=PluginBundle())

    evolver = engine.personality_evolver
    assert evolver._current is None

    # First update initializes
    result = evolver.update("User is detail-oriented")
    assert result == "User is detail-oriented"
    assert evolver._current == "User is detail-oriented"

    # Second update (no LLM → fallback concatenation)
    result = evolver.update("User likes concise responses")
    assert "detail-oriented" in result
    assert "concise responses" in result
