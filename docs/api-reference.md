# API Reference

## Python SDK (mneme)

The primary way to use mneme-memory. `pip install mneme`.

### Mneme.embed()

Create an embedded client. Runs the engine in-process — no server needed.

```python
from mneme import Mneme

mneme = Mneme.embed()                      # auto-loads config.yaml
mneme = Mneme.embed(config="my.yaml")      # explicit config path
mneme = Mneme.embed(config=MnemeConfig())  # config object
```

### Mneme.connect()

Create a remote client. Connects to a running mneme-server via HTTP.

```python
mneme = Mneme.connect("http://localhost:9177")
mneme = Mneme.connect("http://my-server:9177", timeout=60.0)
```

### retain()

Store a new memory.

```python
await mneme.retain(
    content="User enjoys reading science fiction novels",
    fact_type="world",            # world | experience | observation | mental_models
    provenance="user_declared",   # user_declared | inference_backstory | inferred_from_input
    valence=0.6,                  # -1.0 to 1.0
    intensity=0.7,                # 0.0 to 1.0
    emotion_type="joy",
    confidence=0.90,
    privacy="private",            # public | private | deep_private
)

# Sync wrapper (for non-async contexts)
mneme.retain_sync(content="User likes Python", fact_type="world")
```

### recall()

Retrieve memories by query.

```python
results = await mneme.recall(
    query="What books does the user like?",
    top_k=10,
    fact_types=["world", "experience"],  # optional filter
)

for r in results:
    print(f"[{r['score']:.3f}] {r['content']}")
```

### reflect()

Run agentic reflection loop.

```python
result = await mneme.reflect(
    query="Recent experiences with the user",
    top_k=10,
)

print(f"Rounds: {result['rounds']}")
print(f"Synthesis: {result['synthesis']}")
```

### health() / stats()

```python
health = await mneme.health()
# {"status": "ok", "mode": "embedded", "tier": "B", "hardware": {...}}

stats = await mneme.stats()
# {"tier": "B", "has_storage": False, "num_retrievers": 0, ...}
```

---

## HTTP API (mneme-server)

mneme-server exposes the same operations as REST endpoints on port 9177.

### GET /health

```json
{
  "status": "ok",
  "tier": "B",
  "hardware": {
    "gpu_vram_gb": 4.0,
    "gpu_name": "NVIDIA GeForce GTX 1050",
    "cpu_cores": 6,
    "ram_gb": 15.5
  },
  "config": {"mode": "embedded"}
}
```

### POST /retain

```json
{
  "content": "User enjoys reading science fiction novels",
  "fact_type": "world",
  "provenance": "user_declared",
  "valence": 0.6,
  "intensity": 0.7,
  "emotion_type": "joy",
  "confidence": 0.9,
  "privacy": "private"
}
```

### POST /recall

```json
{
  "query": "What books does the user like?",
  "top_k": 10,
  "fact_types": []
}
```

### POST /reflect

Same request shape as /recall. Returns synthesis + conflicts + observations.

### GET /stats

```json
{
  "tier": "B",
  "has_storage": false,
  "num_retrievers": 0
}
```

---

## CLI (mneme-cli)

```bash
# Initialize — show detected hardware, tier, and engine stats
uv run mneme init

# Retain a memory (embedded mode)
uv run mneme retain -c "User likes Python" -t world

# Recall memories
uv run mneme recall "What programming languages?" -k 5

# Run reflection
uv run mneme reflect "User's technical background"

# Connect to remote server
uv run mneme --remote http://localhost:9177 recall "test"

# Start the API server
uv run mneme serve
```

---

## Integration Example (for Agent developers)

```python
from mneme import Mneme

# Initialize once
mneme = Mneme.embed()

# In your agent's conversation loop:
async def handle_user_message(user_input: str):
    # 1. Recall relevant memories
    memories = await mneme.recall(user_input, top_k=5)

    # 2. Build context for your LLM
    context = "\n".join(f"- {m['content']}" for m in memories)

    # 3. Generate response (your own LLM)
    response = await your_llm.generate(user_input, context=context)

    # 4. Store the interaction as a memory
    await mneme.retain(
        content=f"User said: {user_input}",
        fact_type="experience",
        provenance="user_declared",
    )

    return response
```
