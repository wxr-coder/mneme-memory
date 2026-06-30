"""FastAPI application for mneme-memory server.

This is a thin HTTP wrapper around the mneme SDK.
All business logic lives in mneme-engine; the server just translates
HTTP requests into SDK calls.
"""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from pydantic import BaseModel, Field

from mneme import Mneme

logger = structlog.get_logger()


class RetainRequest(BaseModel):
    content: str
    fact_type: str = "experience"
    provenance: str = "inferred_from_input"
    valence: float = 0.0
    intensity: float = 0.0
    emotion_type: str = "neutral"
    confidence: float = 0.5
    privacy: str = "private"
    metadata: dict | None = None


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
    """Initialize the embedded Mneme client on startup."""
    mneme = Mneme.embed()
    app.state.mneme = mneme
    health = await mneme.health()
    logger.info("mneme-server starting", tier=health["tier"], mode=health["mode"])
    yield
    logger.info("mneme-server shutting down")


app = FastAPI(
    title="mneme-memory",
    description="Human-like memory system for AI agents",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health():
    """System health, detected tier, and hardware info."""
    data = await app.state.mneme.health()
    return HealthResponse(
        status=data["status"],
        tier=data["tier"],
        hardware=data["hardware"],
        config={"mode": data["mode"]},
    )


@app.post("/retain")
async def retain(req: RetainRequest):
    """Store a new memory."""
    return await app.state.mneme.retain(
        content=req.content,
        fact_type=req.fact_type,
        provenance=req.provenance,
        valence=req.valence,
        intensity=req.intensity,
        emotion_type=req.emotion_type,
        confidence=req.confidence,
        privacy=req.privacy,
        metadata=req.metadata,
    )


@app.post("/recall")
async def recall(req: RecallRequest):
    """Retrieve memories by query."""
    results = await app.state.mneme.recall(
        query=req.query,
        top_k=req.top_k,
        fact_types=req.fact_types or None,
    )
    return {
        "status": "ok",
        "query": req.query,
        "results": results,
    }


@app.post("/reflect")
async def reflect(req: RecallRequest):
    """Run agentic reflection loop."""
    return await app.state.mneme.reflect(
        query=req.query,
        top_k=req.top_k,
        fact_types=req.fact_types or None,
    )


@app.get("/stats")
async def stats():
    """Memory statistics."""
    data = await app.state.mneme.stats()
    return {"status": "ok", **data}


def run():
    """Entry point for the mneme-server CLI command."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=9177, log_level="info")
