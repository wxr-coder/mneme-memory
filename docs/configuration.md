# Configuration

mneme-memory uses YAML configuration. The system searches for config files in
this order:

1. Path passed to `load_config(path)` (CLI `--config` flag)
2. `./config.yaml` (project root — **local dev**)
3. `./mneme.yaml`
4. `~/.mneme/config.yaml`
5. `/etc/mneme/config.yaml`

The first file found wins. If none exists, built-in defaults are used.

## Quick Start

```bash
# Copy the template
cp config.example.yaml config.yaml

# Edit for your environment
vim config.yaml
```

**Note**: `config.yaml` is gitignored (contains local credentials).
`config.example.yaml` is the committed template.

## Full Reference

```yaml
# ─── Tier ────────────────────────────────────────────
tier: auto              # auto | S | A | B | C
                        # "auto" = detect from hardware

# ─── Embedding ───────────────────────────────────────
embedding:
  model: bge-m3                    # Primary model
  model_low: bge-small-zh-v1.5     # Fallback for TIER C
  device: auto                     # auto | cuda | cpu
  batch_size: 0                    # 0 = auto-detect from VRAM

# ─── Retrieval ───────────────────────────────────────
retrieval:
  paths: [semantic, bm25, graph, temporal]   # TIER S/A
  paths_low: [semantic, bm25]                 # TIER C fallback
  rrf_k: 60                                  # Reciprocal Rank Fusion constant
  reranker: cross-encoder/ms-marco-MiniLM-L-6-v2
  reranker_device: auto

# ─── Reflect (agentic reflection loop) ───────────────
reflect:
  max_rounds: 10           # TIER S
  max_rounds_low: 2        # TIER C
  early_exit_confidence: 0.85   # Stop if confidence ≥ this

# ─── Consolidation ───────────────────────────────────
consolidation:
  mode: realtime           # realtime | near_realtime | nightly
  batch_size: 5            # For near_realtime mode

# ─── Memory ──────────────────────────────────────────
memory:
  layers: [world, experience, observation, mental_models]
  emotional_tag: true      # Attach EmotionalValence to every memory
  forgetting:              # Four forgetting mechanisms
    - active               # Active forgetting (relevance-based)
    - privacy              # Privacy-driven suppression
    - ebbinghaus           # Ebbinghaus decay curve
    - conflict             # Conflict-driven (contradictory facts)
  personality_momentum: 0.95  # personality = momentum * old + (1-momentum) * new

# ─── Storage ─────────────────────────────────────────
storage:
  backend: postgresql
  vector_extension: pgvector
  hnsw_ef_search: 200      # HNSW search parameter (higher = more accurate)
  hnsw_m: 16               # HNSW graph degree
  dsn: postgresql://mneme:password@localhost:5432/mneme

# ─── Plugins ─────────────────────────────────────────
plugins:
  embedding: bge_m3
  reranker: cross_encoder
  llm: openai_compatible
  storage: pgvector
  retrievers: [semantic, bm25, graph, temporal]
```

## Local Development Config

For local development, create `config.yaml` in the project root:

```yaml
tier: auto

embedding:
  model: bge-m3
  device: cpu              # Force CPU for dev

storage:
  backend: postgresql
  dsn: postgresql://mneme:devpass@localhost:5432/mneme_dev

plugins:
  embedding: ollama        # Use local Ollama for embeddings
  llm: openai_compatible
  storage: pgvector
  retrievers: [semantic, bm25]
```

## Environment Variables

Config values can be overridden via environment variables (planned):

| Env Var | Config Key |
|---------|-----------|
| `MNEME_TIER` | `tier` |
| `MNEME_STORAGE_DSN` | `storage.dsn` |
| `MNEME_EMBEDDING_DEVICE` | `embedding.device` |

## Config Validation

Config is loaded into a Pydantic model (`MnemeConfig`), which validates types
and ranges:

```python
from mneme_core.config import load_config

config = load_config("config.yaml")
# → MnemeConfig object with typed access

config.tier                # "auto"
config.embedding.model     # "bge-m3"
config.storage.dsn         # "postgresql://..."
config.memory.layers       # ["world", "experience", ...]
```

Invalid values raise `pydantic.ValidationError` at load time.
