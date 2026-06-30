"""Core data models for mneme-memory.

These types are the shared vocabulary across all plugins and services.
No business logic here — just Pydantic models and enums.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

import numpy as np
from pydantic import BaseModel, Field


class FactType(StrEnum):
    """Four-layer memory classification."""

    WORLD = "world"  # External world facts
    EXPERIENCE = "experience"  # Agent's own experiences
    OBSERVATION = "observation"  # Auto-consolidated synthetic knowledge
    MENTAL_MODELS = "mental_models"  # User-curated high-level summaries


class LinkType(StrEnum):
    """Seven memory link types."""

    TEMPORAL = "temporal"  # Sequential ordering
    SEMANTIC = "semantic"  # Meaning similarity
    ENTITY = "entity"  # Shared entity
    CAUSES = "causes"  # A causes B
    CAUSED_BY = "caused_by"  # A caused by B (inverse of causes)
    ENABLES = "enables"  # A enables B
    PREVENTS = "prevents"  # A prevents B


class Provenance(StrEnum):
    """Three-level trust marking for memory origin."""

    USER_DECLARED = "user_declared"  # User explicitly stated
    INFERENCE_BACKSTORY = "inference_backstory"  # LLM-expanded from user template
    INFERRED_FROM_INPUT = "inferred_from_input"  # Deduced from user's messages


class PrivacyLevel(StrEnum):
    """Three-level privacy classification."""

    PUBLIC = "public"
    PRIVATE = "private"
    DEEP_PRIVATE = "deep_private"


class EmotionalValence(BaseModel):
    """Emotional tag attached to every memory (mneme-memory unique feature)."""

    valence: float = Field(ge=-1.0, le=1.0, default=0.0, description="Pos=positive, Neg=negative")
    intensity: float = Field(ge=0.0, le=1.0, default=0.0, description="0=calm, 1=intense")
    emotion_type: str = Field(default="neutral", description="e.g. joy, sadness, fear, anger, surprise, trust")


class MemCell(BaseModel):
    """The fundamental memory unit.

    Inspired by EverMemOS MemCell: episodic fragment + atomic facts + metadata.
    Every recall is a read-modify-write (reconstructive recall).
    """

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    content: str = Field(description="Raw text content of the memory")
    fact_type: FactType = Field(default=FactType.EXPERIENCE)
    embedding: list[float] | None = Field(default=None, description="Vector embedding (set by EmbeddingProvider)")

    # Emotional dimension (mneme-memory unique)
    emotional_valence: EmotionalValence = Field(default_factory=EmotionalValence)

    # Trust and privacy
    provenance: Provenance = Field(default=Provenance.INFERRED_FROM_INPUT)
    privacy_level: PrivacyLevel = Field(default=PrivacyLevel.PRIVATE)
    confidence: float = Field(ge=0.0, le=1.0, default=0.5)

    # Timestamps (three-field model for reconstructive recall)
    mentioned_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_mentioned_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    last_accessed: datetime | None = Field(default=None)
    access_count: int = Field(default=0)

    # Trend marking (STABLE/STRENGTHENING/WEAKENING/NEW/STALE)
    trend: str = Field(default="NEW")

    # Consolidation metadata
    source_memory_ids: list[str] = Field(default_factory=list)
    proof_count: int = Field(default=0)

    # Extension metadata
    metadata: dict[str, Any] = Field(default_factory=dict)

    def touch(self) -> None:
        """Update access tracking (called on every recall — reconstructive)."""
        self.last_accessed = datetime.now(UTC)
        self.access_count += 1

    def to_embedding_array(self) -> np.ndarray | None:
        if self.embedding is None:
            return None
        return np.array(self.embedding, dtype=np.float32)


class SearchResult(BaseModel):
    """A single retrieval result."""

    memory: MemCell
    score: float = Field(ge=0.0, le=1.0)
    source: str = Field(description="Which retriever produced this (semantic/bm25/graph/temporal)")
    metadata: dict[str, Any] = Field(default_factory=dict)


class Link(BaseModel):
    """A typed connection between two memories."""

    source_id: str
    target_id: str
    link_type: LinkType
    weight: float = Field(ge=0.0, le=1.0, default=0.5)
    metadata: dict[str, Any] = Field(default_factory=dict)


class MemoryFilter(BaseModel):
    """Filter specification for memory queries.

    Carries classification constraints (fact_type, provenance, privacy)
    and quality constraints (min_confidence, date range) through the
    retrieval pipeline in a structured, type-safe way.
    """

    fact_types: list[FactType] | None = None
    provenance: list[Provenance] | None = None
    privacy: list[PrivacyLevel] | None = None
    min_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    since: datetime | None = None
    until: datetime | None = None

    def matches(self, memory: MemCell) -> bool:
        """Return True if *memory* satisfies all active constraints."""
        if self.fact_types and memory.fact_type not in self.fact_types:
            return False
        if self.provenance and memory.provenance not in self.provenance:
            return False
        if self.privacy and memory.privacy_level not in self.privacy:
            return False
        if memory.confidence < self.min_confidence:
            return False
        if self.since and memory.last_mentioned_at < self.since:
            return False
        return not (self.until and memory.last_mentioned_at > self.until)

    @classmethod
    def from_fact_types(cls, fact_types: list[str] | None) -> MemoryFilter | None:
        """Convenience: build a filter from raw fact_type strings."""
        if not fact_types:
            return None
        return cls(fact_types=[FactType(ft) for ft in fact_types])
