# Architecture

## Design Philosophy

mneme-memory is built on one core insight from cognitive science: **human memory
is reconstructive, not reproductive**. Every act of recall subtly alters the
memory being recalled. This contrasts with traditional vector databases that
treat retrieval as a read-only operation.

### Three Principles

1. **Reconstructive Recall (read-modify-write)**
   - `MemCell.touch()` is called on every recall, updating `last_accessed` and
     `access_count`.
   - Emotional valence can strengthen or weaken based on recall context.
   - Recall is never a pure read — it is a state mutation.

2. **Four-Layer Memory Classification**
   - `world` — External facts about the world
   - `experience` — The agent's own episodic experiences
   - `observation` — Auto-consolidated synthetic knowledge (from reflection)
   - `mental_models` — User-curated high-level summaries and beliefs

3. **Emotional Valence as First-Class**
   - Every `MemCell` carries `EmotionalValence(valence, intensity, emotion_type)`.
   - Emotional memories decay slower (Ebbinghaus curve adjusted by intensity).
   - Recall can amplify or dampen emotional tags over time.

## Monorepo Layout

```
mneme-memory/
├── packages/
│   ├── core/              # mneme-core: shared models, capability, config
│   │   └── mneme_core/
│   │       ├── models.py       # MemCell, SearchResult, Link, enums
│   │       ├── capability.py   # Tier detection, HardwareInfo, Capability
│   │       └── config.py       # MnemeConfig + load_config()
│   │
│   └── plugins/           # mneme-plugins: 6 plugin interfaces + built-ins
│       └── mneme_plugins/
│           ├── interfaces/     # Abstract base classes
│           │   ├── embedding.py
│           │   ├── retriever.py
│           │   ├── reranker.py
│           │   ├── llm.py
│           │   ├── storage.py
│           │   └── linker.py
│           └── reranker/
│               └── null_reranker.py   # Built-in: TIER B/C fallback
│
├── apps/
│   ├── mneme-server/      # FastAPI HTTP server (port 9177)
│   │   └── mneme_server/main.py
│   │
│   └── mneme-cli/         # Click CLI tool
│       └── mneme_cli/cli.py
│
├── demos/
│   └── quickstart/        # Minimal demo
│
├── docs/                  # ← you are here
│
├── config.yaml            # Local dev config (gitignored)
├── config.example.yaml    # Template — commit this
│
├── pyproject.toml         # uv workspace root
├── uv.lock                # Lockfile — commit this
├── .mise/                 # mise tasks (format/lint/test)
├── Dockerfile             # All-in-one image
└── docker-compose.yml     # Server + PostgreSQL
```

## Dependency Graph

```
mneme-core (base library — no deps on other workspace members)
├── mneme-plugins → depends on mneme-core
└── apps/*
    ├── mneme-server → depends on mneme-core, mneme-plugins
    ├── mneme-cli    → depends on mneme-core, mneme-plugins
    └── mneme-quickstart → depends on mneme-core
```

**Rule**: apps depend on packages; packages may depend on core; packages
should NOT depend on apps.

## Data Flow: Retain → Consolidate → Recall

```
User input
    │
    ▼
┌──────────┐     ┌────────────────┐     ┌──────────────┐
│ Retain   │────▶│ EmbeddingProvider │──▶│ StorageBackend│
│ (API/CLI)│     │ .embed(texts)     │   │ .store_memory │
└──────────┘     └────────────────┘     └──────────────┘
                                               │
                                    MemoryLinker │
                                    .create_links│
                                               ▼
                                         ┌──────────┐
                                         │ Link Table│
                                         └──────────┘

         ┌──────────────────────────────────────────────┐
         │              Consolidation (nightly)          │
         │  merge duplicates → observation layer          │
         │  decay by Ebbinghaus → trend=WEAKENING         │
         │  personality momentum update                   │
         └──────────────────────────────────────────────┘

Recall request
    │
    ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│ Semantic Ret │   │ BM25 Ret     │   │ Temporal Ret │   (Graph only in S/A)
└──────┬───────┘   └──────┬───────┘   └──────┬───────┘
       │                  │                  │
       └──────────┬───────┘──────────────────┘
                  ▼
         ┌──────────────┐
         │ RRF Fusion   │   (Reciprocal Rank Fusion, k=60)
         └──────┬───────┘
                ▼
         ┌──────────────┐
         │ Reranker     │   (TIER S/A only; NullReranker for B/C)
         └──────┬───────┘
                ▼
         ┌──────────────┐
         │ MemCell.touch│   ← reconstructive: mutate state
         └──────┬───────┘
                ▼
            Results
```

## Three-Field Timestamp Model

Every `MemCell` has three timestamps (inspired by hindsight):

| Field | Meaning | Updated when |
|-------|---------|-------------|
| `mentioned_at` | First time this fact was mentioned | Never (immutable) |
| `last_mentioned_at` | Last time user reiterated this | On re-mention |
| `last_accessed` | Last time recalled by system | On every `touch()` |

Conflict arbitration: when two memories disagree, the one with more recent
`last_mentioned_at` and higher `proof_count` wins.

## Personality Evolution

```
personality = momentum × old + (1 - momentum) × new
```

| Tier | Momentum | Meaning |
|------|----------|---------|
| S | 0.95 | Very stable, slow evolution |
| A | 0.92 | Stable |
| B | 0.90 | Moderate |
| C | 0.85 | Faster adaptation (less data) |

## Six Plugin Interfaces

| Interface | Method(s) | Purpose |
|-----------|-----------|---------|
| `EmbeddingProvider` | `embed()`, `dimension()` | Text → vectors |
| `Retriever` | `search()` | Query → SearchResult list |
| `Reranker` | `rerank()` | Reorder for precision |
| `LLMBackend` | `complete()` | LLM completions (reflection, consolidation) |
| `StorageBackend` | `store_memory()`, `search_vector()`, etc. | Persistence |
| `MemoryLinker` | `create_links()` | Build memory graph edges |

Every plugin declares a `Capability` — the system uses the **weakest plugin**
(木桶效应 / barrel effect) to determine the effective tier.
