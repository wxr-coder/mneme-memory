"""Personality evolution — momentum-based personality update.

personality = momentum × old + (1 - momentum) × new

The personality is a summary vector / text that evolves slowly as new
memories are accumulated. High momentum = stable personality (TIER S),
low momentum = faster adaptation (TIER C).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from mneme_engine.engine import Engine

logger = structlog.get_logger()


class PersonalityEvolver:
    """Evolves the agent's personality model based on accumulated memories."""

    def __init__(self, engine: Engine) -> None:
        self._engine = engine
        self._current: str | None = None  # In-memory cache of current personality

    @property
    def momentum(self) -> float:
        """The personality momentum for this tier."""
        return self._engine.tier.personality_momentum

    def update(self, new_signal: str) -> str:
        """Apply momentum-based update.

        personality = momentum × old + (1 - momentum) × new

        Since personality is text-based, we use an LLM to blend the old and
        new descriptions. If no LLM is available, we simply append.

        Args:
            new_signal: A text description of new personality traits observed.

        Returns:
            The updated personality text.
        """
        if self._current is None:
            # First ever update — just take the new signal
            self._current = new_signal
            logger.info("personality.init", signal_preview=new_signal[:80])
            return self._current

        # If we have an LLM, use it to blend
        llm = self._engine.plugins.llm
        if llm:
            prompt = self._build_blend_prompt(self._current, new_signal)
            blended = llm.complete(
                messages=[
                    {"role": "system", "content": PERSONALITY_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
            )
            self._current = blended.strip()
        else:
            # Fallback: simple concatenation (momentum controls how much new we add)
            # In text mode this is approximate — a real implementation would
            # use embedding interpolation, but that's Phase 3+.
            self._current = f"{self._current}\n{new_signal}"

        logger.info(
            "personality.update",
            momentum=self.momentum,
            old_preview=self._current[:80],
            new_preview=new_signal[:80],
        )
        return self._current

    def _build_blend_prompt(self, old: str, new: str) -> str:
        """Build the LLM prompt for personality blending."""
        return (
            f"Current personality description:\n{old}\n\n"
            f"New observations:\n{new}\n\n"
            f"Blend these into an updated personality description. "
            f"The old personality has weight {self.momentum:.2f} (momentum), "
            f"the new observations have weight {1 - self.momentum:.2f}. "
            f"Produce a concise, coherent personality summary that reflects "
            f"this weighting. Output only the summary text."
        )


PERSONALITY_SYSTEM_PROMPT = """\
You are the personality evolution module for mneme-memory.
Your job is to blend old and new personality descriptions into a coherent
updated description, respecting the momentum weighting.
Keep the output concise (3-5 sentences). Do not hallucinate traits that
are not supported by the input.
"""
