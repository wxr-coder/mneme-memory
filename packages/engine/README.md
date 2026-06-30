# mneme-engine

Memory engine for mneme-memory. Contains the core business logic:

- **Recall pipeline** — multi-path retrieval + RRF fusion + reconstructive touch
- **Reflection loop** — agentic, LLM-driven multi-round synthesis
- **Consolidation engine** — 9 rules (duplicate merge, Ebbinghaus decay, conflict arbitration, etc.)
- **Personality evolution** — momentum-based personality update

## Usage

```python
from mneme_engine import Engine

engine = Engine(config, tier, hardware, plugins)
await engine.retain(content, fact_type=..., provenance=...)
results = await engine.recall(query, top_k=10)
```

The engine is the shared brain between `mneme` (SDK) and `mneme-server` (HTTP).
