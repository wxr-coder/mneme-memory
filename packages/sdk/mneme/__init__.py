"""mneme: Human-like memory system for AI agents.

Usage:
    from mneme import Mneme

    # Embedded mode (no server needed)
    mneme = Mneme.embed()
    mneme.retain("User likes Python")
    results = mneme.recall("User preferences?")

    # Remote mode (connect to mneme-server)
    mneme = Mneme.connect("http://localhost:9177")
    mneme.retain("User likes Python")
    results = mneme.recall("User preferences?")
"""

__version__ = "0.1.0"

from mneme.client import Mneme

__all__ = ["Mneme"]
