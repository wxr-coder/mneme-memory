"""Tests for core data models."""

import numpy as np

from mneme_core.models import (
    EmotionalValence,
    FactType,
    Link,
    LinkType,
    MemCell,
    Provenance,
    SearchResult,
)


def test_memcell_defaults():
    """MemCell should have sensible defaults."""
    cell = MemCell(content="Hello world")
    assert cell.fact_type == FactType.EXPERIENCE
    assert cell.provenance == Provenance.INFERRED_FROM_INPUT
    assert cell.confidence == 0.5
    assert cell.access_count == 0
    assert cell.trend == "NEW"
    assert cell.emotional_valence.valence == 0.0


def test_memcell_touch():
    """touch() should update access tracking."""
    cell = MemCell(content="test")
    assert cell.access_count == 0
    assert cell.last_accessed is None

    cell.touch()
    assert cell.access_count == 1
    assert cell.last_accessed is not None

    cell.touch()
    assert cell.access_count == 2


def test_memcell_embedding_array():
    """to_embedding_array should return numpy array or None."""
    cell = MemCell(content="test", embedding=[0.1, 0.2, 0.3])
    arr = cell.to_embedding_array()
    assert arr is not None
    assert isinstance(arr, np.ndarray)
    assert arr.shape == (3,)

    cell2 = MemCell(content="no emb")
    assert cell2.to_embedding_array() is None


def test_emotional_valence_bounds():
    """EmotionalValence should enforce bounds."""
    val = EmotionalValence(valence=0.8, intensity=0.9, emotion_type="joy")
    assert val.valence == 0.8
    assert val.emotion_type == "joy"


def test_link_types():
    """Link should support all 7 link types."""
    for lt in LinkType:
        link = Link(source_id="a", target_id="b", link_type=lt)
        assert link.link_type == lt


def test_search_result():
    """SearchResult should wrap a MemCell with score."""
    cell = MemCell(content="test")
    result = SearchResult(memory=cell, score=0.85, source="semantic")
    assert result.score == 0.85
    assert result.source == "semantic"
