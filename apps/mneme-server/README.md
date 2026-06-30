# mneme-server

FastAPI server for mneme-memory.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/retain` | Store a new memory |
| POST | `/recall` | Retrieve memories by query |
| POST | `/reflect` | Run agentic reflection loop |
| GET | `/health` | Health check |
| GET | `/stats` | Memory statistics |

## Run

```bash
uv run mneme-server
# or
uv run uvicorn mneme_server.main:app --reload
```

Default port: 9177 (same as hindsight for familiarity).
