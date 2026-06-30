# Tier System

mneme-memory auto-detects hardware capability at startup and selects the
appropriate **tier** (S / A / B / C). Each tier trades quality for resource
usage. Users can override via `config.yaml`.

## Tier Table

| Tier | VRAM | Retrieval Paths | Reranker | Reflect Rounds | Consolidation | Personality Momentum |
|------|------|-----------------|----------|----------------|---------------|---------------------|
| **S** | 16 GB+ | semantic + bm25 + graph + temporal | cross-encoder (GPU) | 10 | realtime | 0.95 |
| **A** | 8–16 GB | semantic + bm25 + graph + temporal | lightweight cross-encoder | 5 | near-realtime | 0.92 |
| **B** | 4–8 GB | semantic + bm25 + temporal | none | 3 | nightly batch | 0.90 |
| **C** | < 4 GB / CPU | semantic + bm25 | none | 2 | nightly batch | 0.85 |

## Detection Algorithm

```
1. detect_hardware()
   ├── nvidia-smi → GPU name + VRAM
   ├── /proc/meminfo → RAM
   └── os.cpu_count() → CPU cores

2. _tier_from_vram(vram)
   ├── ≥ 16 GB → S
   ├── ≥ 8 GB  → A
   ├── ≥ 4 GB  → B
   └── < 4 GB  → C

3. Plugin constraint check (barrel effect)
   For each plugin's Capability:
   ├── if gpu_required and no GPU → downgrade
   └── if min_vram > actual → downgrade

4. Override: if config.tier != "auto", use that tier directly.
```

## Code Reference

```python
from mneme_core.capability import detect_hardware, detect_tier

hw = detect_hardware()
# HardwareInfo(gpu_vram_gb=4.0, gpu_name="NVIDIA GeForce GTX 1050", ...)

tier = detect_tier(hw)
# Tier.B

tier.retrieval_paths      # ["semantic", "bm25", "temporal"]
tier.reflect_max_rounds   # 3
tier.consolidation_mode   # "nightly"
tier.has_reranker          # False
tier.personality_momentum # 0.90
```

## Manual Override

In `config.yaml`:

```yaml
tier: B  # force tier, skip auto-detection
# tier: auto  # auto-detect (default)
```

## Why Graph Retrieval Is Dropped in B/C

Graph traversal (`StorageBackend.traverse_graph()`) requires multi-hop queries
that are expensive on large memory stores. In TIER B (limited VRAM) and C
(no GPU), the cost-benefit ratio is too low — semantic + BM25 + temporal
covers >90% of recall quality at a fraction of the cost.

## Benchmark Targets

| Tier | LongMemEval | LoCoMo | Notes |
|------|-------------|--------|-------|
| S | > 90% | > 89% | Full 4-way + cross-encoder |
| A | ~85% | ~86% | 4-way + lightweight reranker |
| B | ~78% | ~82% | 3-way, no reranker |
| C | ~70% | ~78% | 2-way, minimal |

Sources: LongMemEval, LoCoMo benchmarks.
