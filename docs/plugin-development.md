# Plugin Development

mneme-memory uses six plugin interfaces. Every plugin declares its resource
requirements via `Capability`, enabling automatic tier-based selection.

## The Six Interfaces

| Interface | File | Key Method |
|-----------|------|------------|
| `EmbeddingProvider` | `interfaces/embedding.py` | `embed(texts) → np.ndarray` |
| `Retriever` | `interfaces/retriever.py` | `search(query, top_k) → list[SearchResult]` |
| `Reranker` | `interfaces/reranker.py` | `rerank(query, candidates) → list[SearchResult]` |
| `LLMBackend` | `interfaces/llm.py` | `complete(messages) → str` |
| `StorageBackend` | `interfaces/storage.py` | `store_memory()`, `search_vector()`, etc. |
| `MemoryLinker` | `interfaces/linker.py` | `create_links(memory, context) → list[Link]` |

## Capability Declaration

Every plugin returns a `Capability` dataclass:

```python
from mneme_core.capability import Capability, Tier

def capability(self) -> Capability:
    return Capability(
        min_vram_gb=4.0,        # Minimum VRAM needed
        min_ram_gb=8.0,         # Minimum RAM
        min_cpu_cores=2,        # Minimum CPU cores
        recommended_tier=Tier.B, # Best tier for this plugin
        gpu_required=True,       # Must have NVIDIA GPU
        network_required=False,  # Needs internet?
        description="BGE-M3 embedding provider",
    )
```

The system uses the **weakest plugin** (barrel effect / 木桶效应) to determine
the effective tier. If a plugin requires 8 GB VRAM but the machine has 4 GB,
the whole system downgrades.

## Writing a Plugin

### Example: Custom EmbeddingProvider

```python
from __future__ import annotations
import numpy as np
from mneme_core.capability import Capability, Tier
from mneme_plugins.interfaces.embedding import EmbeddingProvider

class MyEmbedder(EmbeddingProvider):
    """Custom embedding provider using a local model."""

    def __init__(self, model_path: str):
        self._model = load_model(model_path)
        self._dim = self._model.get_dimension()

    def embed(self, texts: list[str]) -> np.ndarray:
        return np.array([self._model.encode(t) for t in texts])

    def dimension(self) -> int:
        return self._dim

    def capability(self) -> Capability:
        return Capability(
            min_vram_gb=2.0,
            recommended_tier=Tier.B,
            gpu_required=True,
            description="Custom local embedder",
        )
```

### Example: Custom Reranker

```python
from mneme_core import Capability, SearchResult, Tier
from mneme_plugins.interfaces.reranker import Reranker

class CrossEncoderReranker(Reranker):
    def __init__(self, model_name: str):
        from sentence_transformers import CrossEncoder
        self._model = CrossEncoder(model_name)

    def rerank(self, query: str, candidates: list[SearchResult], top_k: int = 10):
        pairs = [(query, c.memory.content) for c in candidates]
        scores = self._model.predict(pairs)
        ranked = sorted(zip(candidates, scores), key=lambda x: x[1], reverse=True)
        return [c for c, _ in ranked[:top_k]]

    def capability(self) -> Capability:
        return Capability(
            min_vram_gb=4.0,
            recommended_tier=Tier.S,
            gpu_required=True,
            description="Cross-encoder reranker",
        )
```

## Built-in Plugins

| Plugin | Package | TIER | Description |
|--------|---------|------|-------------|
| `NullReranker` | `mneme_plugins.reranker.null_reranker` | C | Pass-through, no reordering |

More built-in plugins will be added:

| Planned | Type | Dependencies |
|---------|------|-------------|
| `BgeM3Embedder` | EmbeddingProvider | sentence-transformers, torch |
| `OllamaEmbedder` | EmbeddingProvider | httpx (Ollama API) |
| `PgvectorStorage` | StorageBackend | asyncpg, pgvector |
| `BM25Retriever` | Retriever | rank-bm25 |
| `GraphRetriever` | Retriever | (uses StorageBackend.traverse_graph) |
| `TemporalRetriever` | Retriever | (pure Python, no extra deps) |
| `CrossEncoderReranker` | Reranker | sentence-transformers, torch |
| `OpenAICompatibleLLM` | LLMBackend | httpx |
| `EntityLinker` | MemoryLinker | (NER-based) |

## Optional Dependencies

`mneme-plugins` declares optional dependency groups:

```bash
# Install with transformers support
uv add --package mneme-plugins sentence-transformers torch

# Or use the optional group
uv sync --extra mneme-plugins transformers
```

| Group | Packages | For |
|-------|----------|-----|
| `transformers` | sentence-transformers, torch | BGE-M3, cross-encoder |
| `postgres` | asyncpg, pgvector | PgvectorStorage |
| `bm25` | rank-bm25 | BM25Retriever |

## Plugin Registration (Future)

Planned: `setuptools` entry_points for auto-discovery.

```toml
# In your plugin's pyproject.toml:
[project.entry-points."mneme.plugins"]
my_embedder = "my_package:MyEmbedder"
```

The system will scan `mneme.plugins` entry points at startup and load
matching plugins based on `config.yaml` and tier constraints.
