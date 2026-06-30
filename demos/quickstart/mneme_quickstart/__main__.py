"""Quick demo: create MemCells, show tier, simulate reconstructive recall."""

from mneme_core import EmotionalValence, FactType, MemCell, Provenance
from mneme_core.capability import detect_hardware, detect_tier


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
    print(f"Reflect rounds: {tier.reflect_max_rounds}")

    # 2. Create some MemCells
    memories = [
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
    ]

    print(f"\nCreated {len(memories)} memories:")
    for i, m in enumerate(memories):
        print(f"  [{i}] [{m.fact_type.value}] {m.content}")
        print(
            f"      emotion={m.emotional_valence.emotion_type} "
            f"valence={m.emotional_valence.valence:+.1f} "
            f"confidence={m.confidence:.2f} "
            f"provenance={m.provenance.value}"
        )

    # 3. Simulate reconstructive recall
    print("\n--- Reconstructive Recall Simulation ---")
    target = memories[1]
    print(f"Recalling: {target.content}")
    print(f"  Before: access_count={target.access_count}, last_accessed={target.last_accessed}")
    target.touch()
    print(f"  After:  access_count={target.access_count}, last_accessed={target.last_accessed}")
    print("  (Memory state altered by recall — reconstructive!)")

    print("\n" + "=" * 60)
    print("Demo complete. Next steps: configure a storage backend and LLM.")
    print("=" * 60)


if __name__ == "__main__":
    main()
