"""Global configuration for mneme-memory."""

from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class EmbeddingConfig(BaseModel):
    model: str = "bge-m3"
    model_low: str = "bge-small-zh-v1.5"
    device: str = "auto"  # auto | cuda | cpu
    batch_size: int = 0  # 0 = auto-detect


class RetrievalConfig(BaseModel):
    paths: list[str] = Field(default_factory=lambda: ["semantic", "bm25", "graph", "temporal"])
    paths_low: list[str] = Field(default_factory=lambda: ["semantic", "bm25"])
    rrf_k: int = 60
    reranker: str | None = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    reranker_device: str = "auto"


class ReflectConfig(BaseModel):
    max_rounds: int = 10
    max_rounds_low: int = 2
    early_exit_confidence: float = 0.85


class ConsolidationConfig(BaseModel):
    mode: str = "realtime"  # realtime | near_realtime | nightly
    batch_size: int = 5  # for near_realtime


class MemoryConfig(BaseModel):
    layers: list[str] = Field(default_factory=lambda: ["world", "experience", "observation", "mental_models"])
    emotional_tag: bool = True
    forgetting: list[str] = Field(default_factory=lambda: ["active", "privacy", "ebbinghaus", "conflict"])
    personality_momentum: float = 0.95


class StorageConfig(BaseModel):
    backend: str = "postgresql"
    vector_extension: str = "pgvector"
    hnsw_ef_search: int = 200
    hnsw_m: int = 16
    dsn: str = "postgresql://mneme:mneme@localhost:5432/mneme"


class PluginsConfig(BaseModel):
    embedding: str = "bge_m3"
    reranker: str | None = "cross_encoder"
    llm: str = "openai_compatible"
    storage: str = "pgvector"
    retrievers: list[str] = Field(default_factory=lambda: ["semantic", "bm25", "graph", "temporal"])


class MnemeConfig(BaseModel):
    """Top-level configuration for mneme-memory."""

    tier: str = "auto"  # auto | S | A | B | C
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    retrieval: RetrievalConfig = Field(default_factory=RetrievalConfig)
    reflect: ReflectConfig = Field(default_factory=ReflectConfig)
    consolidation: ConsolidationConfig = Field(default_factory=ConsolidationConfig)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    plugins: PluginsConfig = Field(default_factory=PluginsConfig)


def load_config(config_path: str | Path | None = None) -> MnemeConfig:
    """Load config from YAML file, or return defaults.

    Args:
        config_path: Path to config.yaml. If None, looks for
                     ./mneme.yaml, ~/.mneme/config.yaml, /etc/mneme/config.yaml
    """
    search_paths = []
    if config_path:
        search_paths.append(Path(config_path))
    search_paths.extend(
        [
            Path("mneme.yaml"),
            Path.home() / ".mneme" / "config.yaml",
            Path("/etc/mneme/config.yaml"),
        ]
    )

    for p in search_paths:
        if p.exists():
            with open(p) as f:
                data = yaml.safe_load(f) or {}
            return MnemeConfig(**data)

    return MnemeConfig()
