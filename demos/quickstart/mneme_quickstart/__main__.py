"""Quick demo: classification-aware storage, recall, and reconstructive touch.

Demonstrates the full pipeline:
  1. Detect hardware tier
  2. Store memories with different fact_types into InMemoryStorage
  3. Recall with and without classification filters
  4. Show reconstructive touch (access_count incremented on recall)
"""

import asyncio

from mneme_core import EmotionalValence, FactType, MemCell, Provenance
from mneme_core.capability import detect_hardware, detect_tier
from mneme_engine.engine import Engine, PluginBundle
from mneme_plugins.retriever.in_memory import BM25Retriever
from mneme_plugins.storage.in_memory import InMemoryStorage


def main():
    print("=" * 60)
    print("mneme-memory quickstart demo")
    print("=" * 60)

    # 1. Detect hardware and tier
    hw = detect_hardware()
    tier = detect_tier(hw)
    print(f"\nHardware: {hw.gpu_name or 'CPU only'} ({hw.gpu_vram_gb:.1f} GB VRAM)")
    print(f"Detected Tier: {tier.value}")
    print(f"Retrieval paths: {tier.retrieval_paths}")

    # 2. Build engine with InMemoryStorage + BM25Retriever
    storage = InMemoryStorage()
    bundle = PluginBundle(
        storage=storage,
        retrievers=[BM25Retriever(storage)],
    )
    engine = Engine(plugins=bundle)

    # 3. Store memories with different fact_types
    memories_data = [
        MemCell(
            content="User enjoys reading science fiction novels",
            fact_type=FactType.WORLD,
            emotional_valence=EmotionalValence(valence=0.6, intensity=0.4, emotion_type="joy"),
            provenance=Provenance.USER_DECLARED,
            confidence=0.9,
        ),
        MemCell(
            content="Agent helped user debug a memory system architecture",
            fact_type=FactType.EXPERIENCE,
            emotional_valence=EmotionalValence(valence=0.5, intensity=0.7, emotion_type="trust"),
            provenance=Provenance.USER_DECLARED,
            confidence=0.95,
        ),
        MemCell(
            content="User prefers concise technical responses over verbose ones",
            fact_type=FactType.OBSERVATION,
            emotional_valence=EmotionalValence(valence=0.2, intensity=0.3, emotion_type="neutral"),
            provenance=Provenance.INFERRED_FROM_INPUT,
            confidence=0.6,
        ),
        MemCell(
            content="User read a science fiction book about memory systems",
            fact_type=FactType.EXPERIENCE,
            emotional_valence=EmotionalValence(valence=0.7, intensity=0.5, emotion_type="joy"),
            provenance=Provenance.USER_DECLARED,
            confidence=0.8,
        ),
    ]

    print(f"\nStoring {len(memories_data)} memories:")
    for m in memories_data:
        asyncio.run(
            engine.retain(
                content=m.content,
                fact_type=m.fact_type,
                provenance=m.provenance,
                valence=m.emotional_valence.valence,
                intensity=m.emotional_valence.intensity,
                emotion_type=m.emotional_valence.emotion_type,
                confidence=m.confidence,
            )
        )
        print(f"  [{m.fact_type.value:12s}] {m.content}")

    # 4. Recall without filter
    print("\n--- Recall: 'science fiction' (no filter) ---")
    results = asyncio.run(engine.recall("science fiction"))
    for r in results:
        print(f"  [{r.memory.fact_type.value:12s}] score={r.score:.3f}  {r.memory.content}")

    # 5. Recall with filter: only EXPERIENCE
    print("\n--- Recall: 'science fiction' (fact_type=experience) ---")
    results = asyncio.run(engine.recall("science fiction", fact_types=["experience"]))
    for r in results:
        print(f"  [{r.memory.fact_type.value:12s}] score={r.score:.3f}  {r.memory.content}")
    print(f"  -> {len(results)} results (only EXPERIENCE type)")

    # 6. Recall with filter: only WORLD
    print("\n--- Recall: 'science fiction' (fact_type=world) ---")
    results = asyncio.run(engine.recall("science fiction", fact_types=["world"]))
    for r in results:
        print(f"  [{r.memory.fact_type.value:12s}] score={r.score:.3f}  {r.memory.content}")
    print(f"  -> {len(results)} result(s) (only WORLD type)")

    # 7. Show reconstructive touch
    print("\n--- Reconstructive Touch ---")
    print("Re-running same query to show access_count increment:")
    results1 = asyncio.run(engine.recall("science fiction", fact_types=["world"]))
    results2 = asyncio.run(engine.recall("science fiction", fact_types=["world"]))
    if results1 and results2:
        print(f"  First recall:  access_count={results1[0].memory.access_count}")
        print(f"  Second recall: access_count={results2[0].memory.access_count}")
        print("  (Memory state altered by recall — reconstructive!)")

    print("\n" + "=" * 60)
    print("Demo complete. Classification-aware storage + retrieval works!")
    print("Next steps: configure a real StorageBackend (PostgreSQL+pgvector)")
    print("and an EmbeddingProvider for semantic search.")
    print("=" * 60)


if __name__ == "__main__":
    main()
