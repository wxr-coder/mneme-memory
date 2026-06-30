"""Mneme client — the unified entry point for mneme-memory.

Provides two construction modes:
  - Mneme.embed()   → in-process engine, no server needed
  - Mneme.connect() → HTTP client to a running mneme-server

Both modes expose the same async API: retain(), recall(), reflect(), health(), stats().
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

from mneme_core.capability import detect_hardware, detect_tier
from mneme_core.config import MnemeConfig, load_config

if TYPE_CHECKING:
    from mneme_engine.engine import Engine, PluginBundle

logger = structlog.get_logger()


class Mneme:
    """The unified mneme-memory client.

    Use Mneme.embed() for in-process usage (no server needed).
    Use Mneme.connect(url) for remote usage (requires mneme-server running).
    """

    def __init__(self, backend: Backend) -> None:
        self._backend = backend

    # ── Factory methods ─────────────────────────────────────

    @classmethod
    def embed(
        cls,
        config: str | MnemeConfig | None = None,
        plugins: PluginBundle | None = None,
    ) -> Mneme:
        """Create an embedded client. Runs the engine in-process — no server needed.

        Args:
            config: Path to config YAML, or a MnemeConfig object, or None
                    (auto-loads config.yaml from CWD).
            plugins: A PluginBundle with configured plugin instances.
                     If None, the engine runs in skeleton mode (no storage/embedding).
        """
        cfg = _resolve_config(config)
        hardware = detect_hardware()
        tier = detect_tier(hardware, override=cfg.tier)

        from mneme_engine.engine import Engine
        from mneme_engine.engine import PluginBundle as PB

        bundle = plugins or PB()
        engine = Engine(config=cfg, tier=tier, hardware=hardware, plugins=bundle)

        backend = EmbeddedBackend(engine)
        logger.info("mneme.embed", tier=tier.value, has_storage=bundle.storage is not None)
        return cls(backend)

    @classmethod
    def connect(cls, url: str = "http://localhost:9177", timeout: float = 30.0) -> Mneme:
        """Create a remote client. Connects to a running mneme-server via HTTP.

        Args:
            url: The server URL (default http://localhost:9177).
            timeout: HTTP timeout in seconds.
        """
        backend = RemoteBackend(url, timeout=timeout)
        logger.info("mneme.connect", url=url)
        return cls(backend)

    # ── Public API ──────────────────────────────────────────

    async def retain(
        self,
        content: str,
        fact_type: str = "experience",
        provenance: str = "inferred_from_input",
        valence: float = 0.0,
        intensity: float = 0.0,
        emotion_type: str = "neutral",
        confidence: float = 0.5,
        privacy: str = "private",
        metadata: dict | None = None,
    ) -> dict:
        """Store a new memory."""
        return await self._backend.retain(
            content=content,
            fact_type=fact_type,
            provenance=provenance,
            valence=valence,
            intensity=intensity,
            emotion_type=emotion_type,
            confidence=confidence,
            privacy=privacy,
            metadata=metadata,
        )

    async def recall(
        self,
        query: str,
        top_k: int = 10,
        fact_types: list[str] | None = None,
    ) -> list[dict]:
        """Retrieve memories by query."""
        return await self._backend.recall(query, top_k=top_k, fact_types=fact_types)

    async def reflect(
        self,
        query: str,
        top_k: int = 10,
        fact_types: list[str] | None = None,
    ) -> dict:
        """Run agentic reflection loop."""
        return await self._backend.reflect(query, top_k=top_k, fact_types=fact_types)

    async def health(self) -> dict:
        """Check system health."""
        return await self._backend.health()

    async def stats(self) -> dict:
        """Get memory statistics."""
        return await self._backend.stats()

    # ── Sync wrappers (for convenience in non-async contexts) ──

    def retain_sync(self, **kwargs) -> dict:
        """Synchronous wrapper for retain()."""
        import asyncio

        return asyncio.run(self.retain(**kwargs))

    def recall_sync(self, **kwargs) -> list[dict]:
        """Synchronous wrapper for recall()."""
        import asyncio

        return asyncio.run(self.recall(**kwargs))


def _resolve_config(config: str | MnemeConfig | None) -> MnemeConfig:
    """Resolve config from various input types."""
    if config is None:
        return load_config()  # auto-discovers config.yaml
    if isinstance(config, str):
        return load_config(config)
    return config


# ── Backend protocol ─────────────────────────────────────


class Backend:
    """Abstract backend. Implemented by EmbeddedBackend and RemoteBackend."""

    async def retain(self, **kwargs) -> dict: ...
    async def recall(self, query: str, top_k: int, fact_types: list[str] | None) -> list[dict]: ...
    async def reflect(self, query: str, top_k: int, fact_types: list[str] | None) -> dict: ...
    async def health(self) -> dict: ...
    async def stats(self) -> dict: ...


# ── Embedded backend ─────────────────────────────────────


class EmbeddedBackend(Backend):
    """Runs the engine in-process. No network calls."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    async def retain(self, **kwargs) -> dict:
        memory = await self._engine.retain(**kwargs)
        return {
            "status": "ok",
            "memory_id": memory.id,
            "content_preview": memory.content[:100],
            "fact_type": memory.fact_type.value,
            "tier": self._engine.tier.value,
        }

    async def recall(self, query: str, top_k: int, fact_types: list[str] | None) -> list[dict]:
        results = await self._engine.recall(query, top_k=top_k, fact_types=fact_types)
        return [
            {
                "content": r.memory.content,
                "score": r.score,
                "source": r.source,
                "fact_type": r.memory.fact_type.value,
                "memory_id": r.memory.id,
                "access_count": r.memory.access_count,
            }
            for r in results
        ]

    async def reflect(self, query: str, top_k: int, fact_types: list[str] | None) -> dict:
        return await self._engine.reflect(query, top_k=top_k, fact_types=fact_types)

    async def health(self) -> dict:
        return {
            "status": "ok",
            "mode": "embedded",
            "tier": self._engine.tier.value,
            "hardware": self._engine.hardware.to_dict(),
        }

    async def stats(self) -> dict:
        return self._engine.stats()


# ── Remote backend ───────────────────────────────────────


class RemoteBackend(Backend):
    """HTTP client for a running mneme-server."""

    def __init__(self, url: str, timeout: float = 30.0) -> None:
        self._url = url.rstrip("/")
        self._timeout = timeout
        self._client = None  # lazy init

    async def _get_client(self):
        if self._client is None:
            import httpx

            self._client = httpx.AsyncClient(
                base_url=self._url,
                timeout=self._timeout,
            )
        return self._client

    async def retain(self, **kwargs) -> dict:
        client = await self._get_client()
        resp = await client.post("/retain", json=kwargs)
        resp.raise_for_status()
        return resp.json()

    async def recall(self, query: str, top_k: int, fact_types: list[str] | None) -> list[dict]:
        client = await self._get_client()
        payload = {"query": query, "top_k": top_k}
        if fact_types:
            payload["fact_types"] = fact_types
        resp = await client.post("/recall", json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data.get("results", [])

    async def reflect(self, query: str, top_k: int, fact_types: list[str] | None) -> dict:
        client = await self._get_client()
        payload = {"query": query, "top_k": top_k}
        if fact_types:
            payload["fact_types"] = fact_types
        resp = await client.post("/reflect", json=payload)
        resp.raise_for_status()
        return resp.json()

    async def health(self) -> dict:
        client = await self._get_client()
        resp = await client.get("/health")
        resp.raise_for_status()
        return resp.json()

    async def stats(self) -> dict:
        client = await self._get_client()
        resp = await client.get("/stats")
        resp.raise_for_status()
        return resp.json()
