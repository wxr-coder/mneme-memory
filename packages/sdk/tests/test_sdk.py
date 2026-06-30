"""Tests for mneme SDK."""

from __future__ import annotations

import pytest

from mneme import Mneme


@pytest.mark.asyncio
async def test_embed_basic():
    """Test Mneme.embed() creates a working embedded client."""
    mneme = Mneme.embed()
    health = await mneme.health()
    assert health["status"] == "ok"
    assert health["mode"] == "embedded"
    assert "tier" in health


@pytest.mark.asyncio
async def test_embed_retain():
    """Test retain works in embedded mode (no storage backend)."""
    mneme = Mneme.embed()
    result = await mneme.retain("User likes Python", fact_type="world")
    assert result["status"] == "ok"
    assert "memory_id" in result
    assert result["content_preview"] == "User likes Python"


@pytest.mark.asyncio
async def test_embed_recall_empty():
    """Test recall returns empty list when no retrievers configured."""
    mneme = Mneme.embed()
    results = await mneme.recall("test query")
    assert results == []


@pytest.mark.asyncio
async def test_embed_reflect_no_llm():
    """Test reflect returns gracefully when no LLM configured."""
    mneme = Mneme.embed()
    result = await mneme.reflect("test query")
    assert result["rounds"] == 0
    assert result["synthesis"] is None


@pytest.mark.asyncio
async def test_embed_stats():
    """Test stats returns engine info."""
    mneme = Mneme.embed()
    stats = await mneme.stats()
    assert "tier" in stats
    assert stats["has_storage"] is False


@pytest.mark.asyncio
async def test_connect_creates_remote_backend():
    """Test Mneme.connect() creates a remote backend (no actual HTTP call)."""
    mneme = Mneme.connect("http://localhost:9177")
    # Just verify the backend was created — we won't actually hit the server
    from mneme.client import RemoteBackend

    assert isinstance(mneme._backend, RemoteBackend)
    assert mneme._backend._url == "http://localhost:9177"


def test_sync_wrappers():
    """Test sync wrappers work."""
    mneme = Mneme.embed()
    result = mneme.retain_sync(content="Test", fact_type="world")
    assert result["status"] == "ok"


def test_embed_with_config_path():
    """Test embed with explicit config path."""
    mneme = Mneme.embed(config="config.example.yaml")
    assert mneme is not None
