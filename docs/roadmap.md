# Roadmap

## Phase 1: Foundation (current)

- [x] Monorepo initialization (uv workspace + mise + hatchling)
- [x] Core models: MemCell, SearchResult, Link, enums
- [x] Tier detection: S/A/B/C with hardware auto-detection
- [x] Config system: MnemeConfig + load_config() with YAML
- [x] Plugin interfaces: 6 abstract base classes
- [x] NullReranker: built-in fallback for TIER B/C
- [x] mneme-server: FastAPI skeleton (health/retain/recall/reflect/stats)
- [x] mneme-cli: Click CLI skeleton (init/retain/recall/serve/status)
- [x] Quickstart demo
- [x] CI: GitHub Actions (ruff + pytest)
- [x] Docker: Dockerfile + docker-compose with pgvector
- [x] Documentation: architecture, tier, models, plugins, config, API

## Phase 2: Core Plugins

- [ ] BgeM3Embedder (sentence-transformers + torch)
- [ ] OllamaEmbedder (Ollama HTTP API, no GPU needed)
- [ ] PgvectorStorage (asyncpg + pgvector)
- [ ] BM25Retriever (rank-bm25)
- [ ] TemporalRetriever (pure Python, recency-weighted)
- [ ] GraphRetriever (uses StorageBackend.traverse_graph)
- [ ] CrossEncoderReranker (sentence-transformers)
- [ ] OpenAICompatibleLLM (httpx, supports Ark/OpenAI/Ollama)
- [ ] EntityLinker (NER-based memory linking)

## Phase 3: Memory Engine

- [ ] Reconstructive recall pipeline (RRF fusion + touch)
- [ ] Agentic reflection loop (LLM-driven multi-round)
- [ ] Consolidation engine (9 rules from hindsight)
  - [ ] Duplicate detection + merge
  - [ ] Ebbinghaus decay scheduler
  - [ ] Conflict arbitration
  - [ ] Observation synthesis
- [ ] Personality momentum evolution
- [ ] Cold start initialization (user profile → LLM expansion → seed memories)

## Phase 4: Plugin Auto-Discovery

- [ ] setuptools entry_points registration
- [ ] Plugin loading from config.yaml
- [ ] Capability-based tier negotiation (barrel effect)
- [ ] Plugin marketplace / registry

## Phase 5: Deployment

- [ ] All-in-one Docker image (TIER B/C, single container)
- [ ] Docker Compose stack (TIER A/S, server + PostgreSQL + Ollama)
- [ ] pip install mneme-memory (TIER C, pure Python)
- [ ] Helm chart (Kubernetes)
- [ ] Config UI (web-based)

## Phase 6: Evaluation

- [ ] LongMemEval benchmark
- [ ] LoCoMo benchmark
- [ ] Custom "reconstructive recall" benchmark
- [ ] A/B test: reconstructive vs. read-only recall
- [ ] Personality evolution metrics

## Phase 7: Ecosystem

- [ ] Hermes Agent integration (as memory backend)
- [ ] LangChain memory adapter
- [ ] LlamaIndex memory adapter
- [ ] OpenAI Assistants API adapter
- [ ] Mem0 / Letta migration guide
- [ ] Community plugin registry

---

## Milestone Tracking

| Milestone | Target | Status |
|-----------|--------|--------|
| M1: Monorepo + models + skeleton APIs | ✅ | Done |
| M2: First working retain → recall cycle | Next | — |
| M3: Reflection + consolidation | — | — |
| M4: First benchmark pass | — | — |
| M5: v0.1.0 release | — | — |
