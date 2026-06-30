"""FastAPI application for mneme-memory server."""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from pydantic import BaseModel, Field

from mneme_core.capability import detect_hardware, detect_tier
from mneme_core.config import load_config

logger = structlog.get_logger()


class RetainRequest(BaseModel):
    content: str
    fact_type: str = "experience"
    provenance: str = "inferred_from_input"
    valence: float = 0.0
    intensity: float = 0.0
    emotion_type: str = "neutral"


class RecallRequest(BaseModel):
    query: str
    top_k: int = 10
    fact_types: list[str] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    tier: str
    hardware: dict
    config: dict


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = load_config()
    hardware = detect_hardware()
    tier = detect_tier(hardware, override=config.tier)
    logger.info("mneme-memory starting", tier=tier.value, hardware=hardware.to_dict())
    app.state.config = config
    app.state.tier = tier
    app.state.hardware = hardware
    yield


app = FastAPI(
    title="mneme-memory",
    description="Human-like memory system for AI agents",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(
        status="ok",
        tier=app.state.tier.value,
        hardware=app.state.hardware.to_dict(),
        config={"tier": app.state.config.tier, "embedding": app.state.config.embedding.model},
    )


@app.post("/retain")
async def retain(req: RetainRequest):
    """Store a new memory."""
    return {
        "status": "ok",
        "message": "Memory stored",
        "tier": app.state.tier.value,
        "content_preview": req.content[:100],
    }


@app.post("/recall")
async def recall(req: RecallRequest):
    """Retrieve memories by query."""
    return {
        "status": "ok",
        "query": req.query,
        "tier": app.state.tier.value,
        "results": [],
        "message": "No storage backend configured yet",
    }


@app.post("/reflect")
async def reflect(req: RecallRequest):
    """Run agentic reflection loop."""
    return {
        "status": "ok",
        "query": req.query,
        "tier": app.state.tier.value,
        "max_rounds": app.state.tier.reflect_max_rounds,
        "message": "No reflect engine configured yet",
    }


@app.get("/stats")
async def stats():
    """Memory statistics."""
    return {
        "status": "ok",
        "tier": app.state.tier.value,
        "total_memories": 0,
        "message": "No storage backend configured yet",
    }


def run():
    """Entry point for the mneme-server CLI command."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9177, log_level="info")
