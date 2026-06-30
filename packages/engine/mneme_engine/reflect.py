"""Agentic reflection loop — LLM-driven multi-round synthesis.

The reflect loop retrieves memories, feeds them to an LLM, and iterates:
the LLM can request more recall, identify contradictions, or synthesize
new observations. The loop is bounded by tier.reflect_max_rounds.

Design principles:
- 6-step reasoning chain
- Anti-hallucination rules (only use retrieved facts)
- Conflict arbitration (RESOLVABLE vs UNRESOLVABLE)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from mneme_engine.engine import Engine

logger = structlog.get_logger()


class ReflectLoop:
    """Agentic reflection: recall → LLM reason → synthesize → repeat (bounded)."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    async def run(
        self,
        query: str,
        top_k: int = 10,
        fact_types: list[str] | None = None,
    ) -> dict:
        """Execute the reflection loop.

        Returns a dict with:
          - query: the input query
          - rounds: number of rounds executed
          - memories_found: count of memories retrieved
          - synthesis: LLM synthesis text (or None if no LLM)
          - conflicts: list of identified conflicts
          - new_observations: list of new MemCell IDs created (for consolidation)
        """
        engine = self._engine
        max_rounds = engine.tier.reflect_max_rounds

        # If no LLM is configured, we can still do recall but not synthesis
        if not engine.plugins.llm:
            logger.info("reflect.no_llm")
            results = await engine.recall(query, top_k=top_k, fact_types=fact_types)
            return {
                "query": query,
                "rounds": 0,
                "memories_found": len(results),
                "synthesis": None,
                "conflicts": [],
                "new_observations": [],
                "message": "No LLM backend configured — recall only, no synthesis",
            }

        all_results: list = []
        synthesis = None
        conflicts: list = []
        new_observations: list = []
        rounds_done = 0

        for round_num in range(1, max_rounds + 1):
            rounds_done = round_num
            logger.info("reflect.round", round=round_num, max=max_rounds)

            # 1. Recall memories for this round
            results = await engine.recall(query, top_k=top_k, fact_types=fact_types)
            all_results.extend(results)

            # 2. Build context for LLM
            context = self._build_context(query, results, synthesis)

            # 3. LLM reasoning
            llm_response = engine.plugins.llm.complete(
                messages=[
                    {"role": "system", "content": REFLECT_SYSTEM_PROMPT},
                    {"role": "user", "content": context},
                ],
            )

            # 4. Parse LLM response
            parsed = self._parse_response(llm_response)
            synthesis = parsed.get("synthesis", synthesis)

            # Collect conflicts and new observations
            conflicts.extend(parsed.get("conflicts", []))
            new_observations.extend(parsed.get("new_observations", []))

            # 5. Early exit if confidence is high enough
            if parsed.get("confidence", 0.0) >= engine.config.reflect.early_exit_confidence:
                logger.info("reflect.early_exit", round=round_num, confidence=parsed["confidence"])
                break

            # 6. If LLM says no more rounds needed, break
            if parsed.get("done", False):
                logger.info("reflect.llm_done", round=round_num)
                break

        logger.info(
            "reflect.complete",
            rounds=rounds_done,
            memories_found=len(all_results),
            conflicts=len(conflicts),
            new_observations=len(new_observations),
        )

        return {
            "query": query,
            "rounds": rounds_done,
            "memories_found": len(all_results),
            "synthesis": synthesis,
            "conflicts": conflicts,
            "new_observations": new_observations,
        }

    def _build_context(self, query: str, results: list, prev_synthesis: str | None) -> str:
        """Build the LLM prompt context from retrieved memories."""
        lines = [f"Query: {query}\n"]
        if prev_synthesis:
            lines.append(f"Previous synthesis: {prev_synthesis}\n")
        lines.append("Retrieved memories:")
        for i, r in enumerate(results, 1):
            mem = r.memory
            lines.append(
                f"  {i}. [{mem.fact_type.value}] {mem.content} "
                f"(confidence={mem.confidence:.2f}, provenance={mem.provenance.value}, "
                f"mentioned={mem.mentioned_at.isoformat()})"
            )
        lines.append(
            "\nAnalyze these memories. Identify: (1) synthesis, (2) conflicts, "
            "(3) new observations to consolidate. If confident, set done=true."
        )
        return "\n".join(lines)

    def _parse_response(self, response: str) -> dict:
        """Parse LLM response. Currently expects JSON-ish, falls back gracefully."""
        import json

        try:
            return json.loads(response)
        except (json.JSONDecodeError, TypeError):
            # Fallback: treat the whole response as synthesis text
            return {
                "synthesis": response,
                "confidence": 0.0,
                "conflicts": [],
                "new_observations": [],
                "done": False,
            }


REFLECT_SYSTEM_PROMPT = """\
You are the reflection agent for mneme-memory, a human-like memory system.

Your job is to analyze retrieved memories and produce:
1. A synthesis — a coherent summary of what the memories tell us
2. Conflicts — any contradictions between memories (mark as RESOLVABLE or UNRESOLVABLE)
3. New observations — synthetic facts that can be consolidated into the observation layer

Rules:
- Use ONLY the retrieved memories. Do NOT hallucinate facts.
- If memories conflict, apply time-based arbitration: the one with more recent
  last_mentioned_at and higher proof_count wins.
- If conflict cannot be resolved by time, mark it UNRESOLVABLE.
- Output JSON with fields: synthesis, confidence (0-1), conflicts, new_observations, done.

Example output:
{
  "synthesis": "The user is a Python developer who enjoys science fiction.",
  "confidence": 0.85,
  "conflicts": [{"type": "RESOLVABLE", "description": "..."}],
  "new_observations": ["User prefers concise technical responses"],
  "done": true
}
"""
