"""mneme-engine: Memory engine — recall, reflection, consolidation, personality."""

__version__ = "0.1.0"

from mneme_engine.consolidate import ConsolidationEngine
from mneme_engine.engine import Engine
from mneme_engine.personality import PersonalityEvolver
from mneme_engine.recall import RecallPipeline
from mneme_engine.reflect import ReflectLoop

__all__ = [
    "Engine",
    "RecallPipeline",
    "ReflectLoop",
    "ConsolidationEngine",
    "PersonalityEvolver",
]
