"""Engine orchestrator — wires plugins into a cohesive memory system.

This is the shared brain. Both the SDK (mneme.Mneme) and the server
(mneme-server) delegate to Engine for all business logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import structlog

from mneme_core import (
    EmotionalValence,
    FactType,
    HardwareInfo,
    MemCell,
    MnemeConfig,
    PrivacyLevel,
    Provenance,
    SearchResult,
    Tier,
)
from mneme_core.capability import detect_hardware, detect_tier

if TYPE_CHECKING:
    from mneme_engine.consolidate import ConsolidationEngine
    from mneme_engine.personality import PersonalityEvolver
    from mneme_engine.recall import RecallPipeline
    from mneme_engine.reflect import ReflectLoop
    from mneme_plugins import EmbeddingProvider, LLMBackend, MemoryLinker, Reranker, Retriever, StorageBackend

logger = structlog.get_logger()


@dataclass
class PluginBundle:
    """Container for the six plugin slots. Any slot may be None (not yet configured)."""

    embedding: EmbeddingProvider | None = None
    retrievers: list[Retriever] = field(default_factory=list)
    reranker: Reranker | None = None
    llm: LLMBackend | None = None
    storage: StorageBackend | None = None
    linker: MemoryLinker | None = None


class Engine:
    """The memory engine. Holds config, tier, plugins, and orchestrates operations."""

    def __init__(
        self,
        config: MnemeConfig | None = None,
        tier: Tier | None = None,
        hardware: HardwareInfo | None = None,
        plugins: PluginBundle | None = None,
    ) -> None:
        self.config = config or MnemeConfig()
        self.hardware = hardware or detect_hardware()
        self.tier = tier or detect_tier(self.hardware, override=self.config.tier)
        self.plugins = plugins or PluginBundle()

        # Sub-orchestrators (lazy: import here to avoid circular refs at module level)
        from mneme_engine.consolidate import ConsolidationEngine
        from mneme_engine.personality import PersonalityEvolver
        from mneme_engine.recall import RecallPipeline
        from mneme_engine.reflect import ReflectLoop

        self._recall = RecallPipeline(self)
        self._reflect = ReflectLoop(self)
        self._consolidate = ConsolidationEngine(self)
        self._personality = PersonalityEvolver(self)

        logger.info(
            "engine.initialized",
            tier=self.tier.value,
            retrieval_paths=self.tier.retrieval_paths,
            has_storage=self.plugins.storage is not None,
            has_embedding=self.plugins.embedding is not None,
            num_retrievers=len(self.plugins.retrievers),
        )

    @property
    def recall_pipeline(self) -> RecallPipeline:
        return self._recall

    @property
    def reflect_loop(self) -> ReflectLoop:
        return self._reflect

    @property
    def consolidation_engine(self) -> ConsolidationEngine:
        return self._consolidate

    @property
    def personality_evolver(self) -> PersonalityEvolver:
        return self._personality

    # ── Public API ──────────────────────────────────────────

    async def retain(
        self,
        content: str,
        fact_type: FactType | str = FactType.EXPERIENCE,
        provenance: Provenance | str = Provenance.INFERRED_FROM_INPUT,
        valence: float = 0.0,
        intensity: float = 0.0,
        emotion_type: str = "neutral",
        confidence: float = 0.5,
        privacy: PrivacyLevel | str = PrivacyLevel.PRIVATE,
        metadata: dict | None = None,
    ) -> MemCell:
        """Store a new memory. This is the primary write path."""
        ft = FactType(fact_type) if isinstance(fact_type, str) else fact_type
        prov = Provenance(provenance) if isinstance(provenance, str) else provenance
        priv = PrivacyLevel(privacy) if isinstance(privacy, str) else privacy

        memory = MemCell(
            content=content,
            fact_type=ft,
            emotional_valence=EmotionalValence(
                valence=valence,
                intensity=intensity,
                emotion_type=emotion_type,
            ),
            provenance=prov,
            confidence=confidence,
            privacy_level=priv,
            metadata=metadata or {},
        )

        # Embed if we have an embedding provider
        if self.plugins.embedding:
            emb = self.plugins.embedding.embed([content])
            memory.embedding = list(emb[0]) if hasattr(emb, "__getitem__") else list(emb)

        # Persist if we have a storage backend
        if self.plugins.storage:
            await self.plugins.storage.store_memory(memory)

        # Create links if we have a linker
        if self.plugins.linker:
            links = self.plugins.linker.create_links(memory, context=None)
            for link in links:
                if self.plugins.storage:
                    await self.plugins.storage.store_link(link)

        logger.info(
            "engine.retain",
            memory_id=memory.id,
            fact_type=ft.value,
            content_preview=content[:80],
        )
        return memory

    async def recall(
        self,
        query: str,
        top_k: int = 10,
        fact_types: list[str] | None = None,
    ) -> list[SearchResult]:
        """Retrieve memories by query. Delegates to RecallPipeline."""
        return await self._recall.search(query, top_k=top_k, fact_types=fact_types)

    async def reflect(
        self,
        query: str,
        top_k: int = 10,
        fact_types: list[str] | None = None,
    ) -> dict:
        """Run agentic reflection loop. Delegates to ReflectLoop."""
        return await self._reflect.run(query, top_k=top_k, fact_types=fact_types)

    async def consolidate(self) -> dict:
        """Run consolidation pass (dedup, decay, conflict resolution). Delegates to ConsolidationEngine."""
        return await self._consolidate.run()

    def stats(self) -> dict:
        """Quick stats about the engine state."""
        return {
            "tier": self.tier.value,
            "retrieval_paths": self.tier.retrieval_paths,
            "reflect_max_rounds": self.tier.reflect_max_rounds,
            "consolidation_mode": self.tier.consolidation_mode,
            "has_reranker": self.tier.has_reranker,
            "personality_momentum": self.tier.personality_momentum,
            "has_storage": self.plugins.storage is not None,
            "has_embedding": self.plugins.embedding is not None,
            "has_llm": self.plugins.llm is not None,
            "num_retrievers": len(self.plugins.retrievers),
        }
