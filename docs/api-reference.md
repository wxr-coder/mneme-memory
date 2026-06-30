# API Reference

mneme-server exposes a REST API on port 9177.

## Base URL

```
http://localhost:9177
```

## Endpoints

### GET /health

Returns system health, detected tier, and hardware info.

**Response**:
```json
{
  "status": "ok",
  "tier": "B",
  "hardware": {
    "gpu_vram_gb": 4.0,
    "gpu_name": "NVIDIA GeForce GTX 1050",
    "cpu_cores": 6,
    "ram_gb": 15.5,
    "has_nvidia": true
  },
  "config": {
    "tier": "auto",
    "embedding": "bge-m3"
  }
}
```

---

### POST /retain

Store a new memory.

**Request**:
```json
{
  "content": "User enjoys reading science fiction novels",
  "fact_type": "world",
  "provenance": "user_declared",
  "valence": 0.6,
  "intensity": 0.7,
  "emotion_type": "joy"
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `content` | string | required | Memory text |
| `fact_type` | string | `"experience"` | world / experience / observation / mental_models |
| `provenance` | string | `"inferred_from_input"` | Trust level |
| `valence` | float | `0.0` | -1.0 to 1.0 |
| `intensity` | float | `0.0` | 0.0 to 1.0 |
| `emotion_type` | string | `"neutral"` | joy, sadness, fear, etc. |

**Response**:
```json
{
  "status": "ok",
  "message": "Memory stored",
  "tier": "B",
  "content_preview": "User enjoys reading science fiction novels"
}
```

---

### POST /recall

Retrieve memories by query.

**Request**:
```json
{
  "query": "What books does the user like?",
  "top_k": 10,
  "fact_types": ["world", "experience"]
}
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | required | Natural language query |
| `top_k` | int | `10` | Max results |
| `fact_types` | string[] | `[]` | Filter by layer (empty = all) |

**Response**:
```json
{
  "status": "ok",
  "query": "What books does the user like?",
  "tier": "B",
  "results": [],
  "message": "No storage backend configured yet"
}
```

*Note: Results will be populated once a StorageBackend plugin is implemented.*

---

### POST /reflect

Run agentic reflection loop on a query.

**Request** (same as /recall):
```json
{
  "query": "Recent experiences with the user",
  "top_k": 10,
  "fact_types": []
}
```

**Response**:
```json
{
  "status": "ok",
  "query": "Recent experiences with the user",
  "tier": "B",
  "max_rounds": 3,
  "message": "No reflect engine configured yet"
}
```

---

### GET /stats

Memory statistics.

**Response**:
```json
{
  "status": "ok",
  "tier": "B",
  "total_memories": 0,
  "message": "No storage backend configured yet"
}
```

---

## CLI

The CLI tool (`mneme-cli`) provides the same operations from the terminal:

```bash
# Initialize — show detected hardware and tier
uv run mneme init

# Retain a memory
uv run mneme retain "User likes Python" --type world

# Recall memories
uv run mneme recall "What programming languages?" --top-k 5

# Start the server
uv run mneme serve

# Show status
uv run mneme status
```

## Python SDK

```python
from mneme_core import MemCell, FactType, EmotionalValence, Provenance
from mneme_core.config import load_config
from mneme_core.capability import detect_hardware, detect_tier

# Load config
config = load_config("config.yaml")

# Detect tier
hw = detect_hardware()
tier = detect_tier(hw, override=config.tier)
print(f"Tier: {tier.value}")
print(f"Retrieval paths: {tier.retrieval_paths}")

# Create a memory
memory = MemCell(
    content="User prefers concise technical responses",
    fact_type=FactType.OBSERVATION,
    emotional_valence=EmotionalValence(valence=0.2, intensity=0.3),
    provenance=Provenance.INFERRED_FROM_INPUT,
    confidence=0.60,
)
```
