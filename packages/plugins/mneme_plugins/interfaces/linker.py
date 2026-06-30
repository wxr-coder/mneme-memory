"""MemoryLinker: Create links between memories."""

from __future__ import annotations

from abc import ABC, abstractmethod

from mneme_core import Capability, Link, MemCell


class MemoryLinker(ABC):
    """Abstract base for memory linkers."""

    @abstractmethod
    def create_links(self, memory: MemCell, context: list[MemCell]) -> list[Link]:
        """Analyze a memory and create links to context memories."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Linker name (e.g. 'entity', 'temporal', 'semantic', 'causal')."""
        ...

    @abstractmethod
    def capability(self) -> Capability:
        """Declare resource requirements."""
        ...
