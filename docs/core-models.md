# Core Models

All models are Pydantic v2 `BaseModel` subclasses defined in
`packages/core/mneme_core/models.py`.

## MemCell

The fundamental memory unit. Inspired by EverMemOS MemCell: episodic fragment
+ atomic facts + metadata. Every recall is a read-modify-write.

```python
from mneme_core import MemCell, FactType, EmotionalValence, Provenance

memory = MemCell(
    content="User enjoys reading science fiction novels",
    fact_type=FactType.WORLD,
    emotional_valence=EmotionalValence(
        valence=0.6,       # -1.0 to 1.0 (negative ↔ positive)
        intensity=0.7,     # 0.0 to 1.0 (calm ↔ intense)
        emotion_type="joy",
    ),
    provenance=Provenance.USER_DECLARED,
    confidence=0.90,
)

# Reconstructive recall — state mutation
memory.touch()
# → last_accessed = now, access_count += 1
```

### Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `id` | `str` | UUID4 | Unique identifier |
| `content` | `str` | required | Raw text content |
| `fact_type` | `FactType` | `EXPERIENCE` | Memory layer |
| `embedding` | `list[float] \| None` | `None` | Vector embedding |
| `emotional_valence` | `EmotionalValence` | `{0, 0, "neutral"}` | Emotional tag |
| `provenance` | `Provenance` | `INFERRED_FROM_INPUT` | Trust level |
| `privacy_level` | `PrivacyLevel` | `PRIVATE` | Privacy classification |
| `confidence` | `float` | `0.5` | 0.0–1.0 |
| `mentioned_at` | `datetime` | now (UTC) | First mention (immutable) |
| `last_mentioned_at` | `datetime` | now (UTC) | Last re-mention |
| `last_accessed` | `datetime \| None` | `None` | Last recall |
| `access_count` | `int` | `0` | Total recall count |
| `trend` | `str` | `"NEW"` | STABLE/STRENGTHENING/WEAKENING/NEW/STALE |
| `source_memory_ids` | `list[str]` | `[]` | Parent memories (for consolidation) |
| `proof_count` | `int` | `0` | Corroboration count |
| `metadata` | `dict` | `{}` | Extension field |

### Methods

- `touch()` — Update `last_accessed` and `access_count`. Called on every recall.
- `to_embedding_array()` — Returns `np.ndarray` or `None`.

---

## SearchResult

A single retrieval result from a `Retriever` or `StorageBackend` search.

```python
from mneme_core import SearchResult, MemCell

result = SearchResult(
    memory=some_memcell,
    score=0.87,
    source="semantic",  # which retriever produced this
)
```

| Field | Type | Description |
|-------|------|-------------|
| `memory` | `MemCell` | The matched memory |
| `score` | `float` | 0.0–1.0 relevance |
| `source` | `str` | Retriever name (semantic/bm25/graph/temporal) |
| `metadata` | `dict` | Extra info (e.g. graph hop count) |

---

## Link

A typed connection between two memories.

```python
from mneme_core import Link, LinkType

link = Link(
    source_id="abc-123",
    target_id="def-456",
    link_type=LinkType.CAUSES,
    weight=0.8,
)
```

| Field | Type | Description |
|-------|------|-------------|
| `source_id` | `str` | Source memory ID |
| `target_id` | `str` | Target memory ID |
| `link_type` | `LinkType` | Edge type |
| `weight` | `float` | 0.0–1.0 |
| `metadata` | `dict` | Extension field |

---

## Enums

### FactType — Four-layer memory classification

| Value | Description |
|-------|-------------|
| `WORLD` | External world facts |
| `EXPERIENCE` | Agent's own experiences |
| `OBSERVATION` | Auto-consolidated synthetic knowledge |
| `MENTAL_MODELS` | User-curated high-level summaries |

### LinkType — Seven memory link types

| Value | Description |
|-------|-------------|
| `TEMPORAL` | Sequential ordering |
| `SEMANTIC` | Meaning similarity |
| `ENTITY` | Shared entity |
| `CAUSES` | A causes B |
| `CAUSED_BY` | A caused by B (inverse) |
| `ENABLES` | A enables B |
| `PREVENTS` | A prevents B |

### Provenance — Three-level trust

| Value | Description |
|-------|-------------|
| `USER_DECLARED` | User explicitly stated (highest trust) |
| `INFERENCE_BACKSTORY` | LLM-expanded from user template |
| `INFERRED_FROM_INPUT` | Deduced from user messages (lowest trust) |

### PrivacyLevel

| Value | Description |
|-------|-------------|
| `PUBLIC` | Shareable |
| `PRIVATE` | User-only |
| `DEEP_PRIVATE` | Never surface in recall |

### EmotionalValence

| Field | Range | Description |
|-------|-------|-------------|
| `valence` | -1.0 to 1.0 | Negative ↔ positive |
| `intensity` | 0.0 to 1.0 | Calm ↔ intense |
| `emotion_type` | str | e.g. joy, sadness, fear, anger, surprise, trust |
