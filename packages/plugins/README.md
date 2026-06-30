# mneme-plugins

Plugin interfaces and built-in implementations for mneme-memory.

## Plugin Interfaces (6)

| Interface | Purpose | Built-in Implementations |
|-----------|---------|--------------------------|
| `EmbeddingProvider` | Generate vector embeddings | BGE_M3, Ollama, API |
| `Retriever` | Search memories by strategy | Semantic, BM25, Graph, Temporal |
| `Reranker` | Re-order retrieved results | CrossEncoder, NullReranker |
| `LLMBackend` | LLM completion with tool-calling | OpenAI-compatible, Ollama |
| `StorageBackend` | Persist and query memories | PgvectorStorage |
| `MemoryLinker` | Create links between memories | Entity, Temporal, Semantic, Causal |

## Contributing a Plugin

Plugins are discovered via setuptools entry points:

```toml
# In your pyproject.toml
[project.entry-points."mneme_memory.plugins"]
my_plugin = "my_package:MyPlugin"
```
