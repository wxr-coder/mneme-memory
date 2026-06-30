"""mneme-plugins: Plugin interfaces and built-in implementations."""

__version__ = "0.1.0"

from mneme_plugins.interfaces.embedding import EmbeddingProvider
from mneme_plugins.interfaces.linker import MemoryLinker
from mneme_plugins.interfaces.llm import LLMBackend
from mneme_plugins.interfaces.reranker import Reranker
from mneme_plugins.interfaces.retriever import Retriever
from mneme_plugins.interfaces.storage import StorageBackend
from mneme_plugins.reranker import NullReranker

__all__ = [
    "EmbeddingProvider",
    "Retriever",
    "Reranker",
    "LLMBackend",
    "StorageBackend",
    "MemoryLinker",
    "NullReranker",
]
