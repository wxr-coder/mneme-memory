# mneme-memory

Human-like memory system for AI agents — reconstruction, not just access.

## Overview

mneme-memory is an open-source memory system that makes AI agents feel more human-like.
Instead of simply storing and retrieving data, every recall is a **reconstruction**
(read-modify-write) that subtly alters memory state — just like human memory.

## Key Features

- **Reconstructive Recall**: Each recall modifies memory state (last_accessed, access_count, emotional_resonance)
- **Four-Layer Memory**: world / experience / observation / mental_models — each with distinct decay and retrieval strategies
- **Emotional Valence**: Every memory carries {valence, intensity, emotion_type} as first-class citizens
- **Four Types of Forgetting**: Active, privacy-driven, Ebbinghaus decay, conflict-driven
- **Dual-Process Retrieval**: Fast path (<50ms) + slow path (<3s) — inspired by System 1 / System 2
- **Personality Evolution**: personality = momentum * old + (1-momentum) * new
- **Tiered Architecture**: Auto-detects hardware capability (S/A/B/C) and adjusts features accordingly
- **Plugin System**: 6 plugin interfaces (EmbeddingProvider, Retriever, Reranker, LLMBackend, StorageBackend, MemoryLinker)
- **Cold Start Initialization**: Structured user profile → LLM expansion → seed memories

## Quick Start

```bash
# Clone
git clone https://github.com/wxr-coder/mneme-memory.git
cd mneme-memory

# Install tools
mise install

# Sync dependencies
uv sync

# Run demo
uv run python -m mneme_quickstart

# Start server
uv run mneme-server
```

## Tier System

| Tier | VRAM | Retrieval | Reranker | Reflect | Consolidation |
|------|------|-----------|----------|---------|---------------|
| S | 16GB+ | 4-way parallel | cross-encoder (GPU) | 10 rounds | realtime |
| A | 8-16GB | 4-way parallel | lightweight cross-encoder | 5 rounds | near-realtime |
| B | 4-8GB | 3-way | none | 3 rounds | nightly batch |
| C | <4GB/CPU | 2-way | none | 2 rounds | nightly batch |

## License

MIT
