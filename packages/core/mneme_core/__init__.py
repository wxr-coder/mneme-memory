"""mneme-core: Core models, capability detection, and config for mneme-memory."""

__version__ = "0.1.0"

from mneme_core.capability import (
    Capability,
    HardwareInfo,
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
    MemoryFilter,
    PrivacyLevel,
    Provenance,
    SearchResult,
)

__all__ = [
    "MemCell",
    "MemoryFilter",
    "SearchResult",
    "Link",
    "LinkType",
    "FactType",
    "Provenance",
    "PrivacyLevel",
    "EmotionalValence",
    "Capability",
    "HardwareInfo",
    "Tier",
    "detect_tier",
    "detect_hardware",
    "MnemeConfig",
    "load_config",
]
