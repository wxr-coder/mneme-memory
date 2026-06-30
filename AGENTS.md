# AGENTS.md — mneme-memory

## Project Overview

mneme-memory is an open-source human-like memory system for AI agents.
Core paradigm: **reconstructive recall** (read-modify-write, not store-retrieve).

## Architecture

```
packages/core      — Core models (MemCell, SearchResult, Link), Capability/Tier detection, Config
packages/plugins   — 6 plugin interfaces + built-in implementations
apps/mneme-server  — FastAPI server (retain / recall / reflect / health)
apps/mneme-cli     — CLI tool (init / retain / recall / serve)
demos/quickstart   — Minimal demo
```

## Key Commands

```bash
mise run repo-install   # First-time setup
mise format             # Format all code
mise lint               # Lint all code
mise test               # Quick tests (skip live_llm marker)
mise test-all           # Full test suite
uv sync --frozen        # Sync dependencies
uv add --package <member> <pkg>  # Add dep to workspace member
```

## Conventions

- Build backend: `hatchling` (not uv_build, for broader compatibility)
- Python: >=3.11
- Import names: `mneme_core`, `mneme_plugins`, `mneme_server`, `mneme_cli`
- Never use `pip install` — always `uv add` / `uv sync`
- Never run bare `python` — use `uv run python` or `mise exec -- uv run`
- Commit `uv.lock` — it is the single source of truth for reproducibility
- Config templates (`*tpl.toml`) are committed; local configs (`*.local.*`) are gitignored

## Dependency Graph

```
mneme-core (base library)
├── mneme-plugins → mneme-core
└── apps/*
    ├── mneme-server → mneme-core, mneme-plugins
    ├── mneme-cli → mneme-core, mneme-plugins
    └── demos/quickstart → mneme-core
```

Rule: apps depend on packages, packages may depend on core, packages should NOT depend on apps.
