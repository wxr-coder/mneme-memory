"""mneme-core: Core models, capability detection, and config for mneme-memory."""

__version__ = "0.1.0"

from mneme_core.capability import (
    Capability,
    Tier,
    detect_hardware,
    detect_tier,
)
from mneme_core.config import MnemeConfig, load_config
from mneme_core.models import (
    EmotionalValence,
    FactType,
    Link,
    LinkType,
    MemCell,
    PrivacyLevel,
    Provenance,
    SearchResult,
)

__all__ = [
    "MemCell",
    "SearchResult",
    "Link",
    "LinkType",
    "FactType",
    "Provenance",
    "PrivacyLevel",
    "EmotionalValence",
    "Capability",
    "Tier",
    "detect_tier",
    "detect_hardware",
    "MnemeConfig",
    "load_config",
]
