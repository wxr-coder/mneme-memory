"""InMemoryStorage: Simple in-process storage backend.

Stores memories in a Python dict. Provides vector cosine similarity
search, BM25-style full-text search, and graph traversal — all with
MemoryFilter support for classification-aware queries.

This backend is intended for development, testing, and small-scale
embedded usage. For production, use a PostgreSQL+pgvector backend.
"""

from __future__ import annotations

import math
import re
from collections import defaultdict

import numpy as np

from mneme_core import Capability, MemCell, MemoryFilter, SearchResult, Tier
from mneme_plugins.interfaces.storage import StorageBackend

_WORD_RE = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    """Simple tokenizer for BM25."""
    return [t.lower() for t in _WORD_RE.findall(text)]


class InMemoryStorage(StorageBackend):
    """In-memory storage with cosine similarity + BM25 + graph links."""

    def __init__(self) -> None:
        self._memories: dict[str, MemCell] = {}
        self._links: list[tuple[str, str, str, float]] = []
        # BM25 index structures
        self._doc_freqs: dict[str, dict[str, int]] = {}  # id -> {term: freq}
        self._doc_len: dict[str, int] = {}
        self._avgdl: float = 0.0
        self._n_docs: int = 0

    # ── Store ──────────────────────────────────────────────

    async def store_memory(self, memory: MemCell) -> str:
        self._memories[memory.id] = memory
        # Update BM25 index
        tokens = _tokenize(memory.content)
        freqs: dict[str, int] = defaultdict(int)
        for tok in tokens:
            freqs[tok] += 1
        self._doc_freqs[memory.id] = dict(freqs)
        self._doc_len[memory.id] = len(tokens)
        self._n_docs = len(self._memories)
        self._avgdl = sum(self._doc_len.values()) / max(self._n_docs, 1)
        return memory.id

    async def update_memory(self, memory: MemCell) -> bool:
        if memory.id not in self._memories:
            return False
        self._memories[memory.id] = memory
        # Re-index BM25 if content changed
        tokens = _tokenize(memory.content)
        freqs: dict[str, int] = defaultdict(int)
        for tok in tokens:
            freqs[tok] += 1
        self._doc_freqs[memory.id] = dict(freqs)
        self._doc_len[memory.id] = len(tokens)
        self._avgdl = sum(self._doc_len.values()) / max(self._n_docs, 1)
        return True

    async def get_memory(self, memory_id: str) -> MemCell | None:
        return self._memories.get(memory_id)

    # ── Vector search ─────────────────────────────────────

    async def search_vector(
        self,
        query_vec: np.ndarray,
        top_k: int = 10,
        filters: MemoryFilter | None = None,
    ) -> list[SearchResult]:
        results: list[SearchResult] = []
        for _mid, mem in self._memories.items():
            # Apply classification filter
            if filters and not filters.matches(mem):
                continue
            if mem.embedding is None:
                continue
            emb = np.array(mem.embedding, dtype=np.float32)
            score = float(np.dot(query_vec, emb) / (np.linalg.norm(query_vec) * np.linalg.norm(emb) + 1e-8))
            results.append(SearchResult(memory=mem, score=score, source="vector"))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    # ── BM25 search ───────────────────────────────────────

    async def search_bm25(
        self,
        query: str,
        top_k: int = 10,
        filters: MemoryFilter | None = None,
    ) -> list[SearchResult]:
        if self._n_docs == 0:
            return []

        query_terms = _tokenize(query)
        if not query_terms:
            return []

        # BM25 parameters
        k1 = 1.5
        b = 0.75

        scores: dict[str, float] = {}
        for term in query_terms:
            # Document frequency for this term
            df = sum(1 for freqs in self._doc_freqs.values() if term in freqs)
            if df == 0:
                continue
            idf = math.log((self._n_docs - df + 0.5) / (df + 0.5) + 1.0)

            for mid, freqs in self._doc_freqs.items():
                if term not in freqs:
                    continue
                mem = self._memories[mid]
                # Apply classification filter
                if filters and not filters.matches(mem):
                    continue
                tf = freqs[term]
                dl = self._doc_len[mid]
                denom = tf + k1 * (1 - b + b * dl / max(self._avgdl, 1))
                score = idf * (tf * (k1 + 1)) / denom
                scores[mid] = scores.get(mid, 0.0) + score

        results: list[SearchResult] = []
        for mid, score in scores.items():
            mem = self._memories[mid]
            # Normalize score to [0, 1]
            normalized = min(score / 10.0, 1.0)
            results.append(SearchResult(memory=mem, score=normalized, source="bm25"))
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    # ── Graph ──────────────────────────────────────────────

    async def create_link(self, src_id: str, dst_id: str, link_type: str, weight: float = 0.5) -> bool:
        if src_id not in self._memories or dst_id not in self._memories:
            return False
        self._links.append((src_id, dst_id, link_type, weight))
        return True

    async def traverse_graph(self, seed_ids: list[str], hops: int = 2) -> list[str]:
        visited: set[str] = set()
        frontier = set(seed_ids)
        for _ in range(hops):
            next_frontier: set[str] = set()
            for src, dst, _, _ in self._links:
                if src in frontier and dst not in visited:
                    next_frontier.add(dst)
                if dst in frontier and src not in visited:
                    next_frontier.add(src)
            visited |= frontier
            frontier = next_frontier
            if not frontier:
                break
        visited |= frontier
        return list(visited - set(seed_ids))

    # ── Capability ────────────────────────────────────────

    def capability(self) -> Capability:
        return Capability(
            min_vram_gb=0.0,
            min_ram_gb=0.5,
            min_cpu_cores=1,
            recommended_tier=Tier.C,
            gpu_required=False,
            description="In-memory storage (dev/testing)",
        )
