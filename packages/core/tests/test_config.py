"""Tests for config loading."""

from mneme_core.config import MnemeConfig, load_config


def test_default_config():
    config = MnemeConfig()
    assert config.tier == "auto"
    assert config.embedding.model == "bge-m3"
    assert config.retrieval.rrf_k == 60
    assert config.reflect.max_rounds == 10
    assert config.consolidation.mode == "realtime"
    assert config.memory.emotional_tag is True
    assert "ebbinghaus" in config.memory.forgetting
    assert config.storage.backend == "postgresql"


def test_load_config_no_file():
    """load_config should return defaults when no file found."""
    config = load_config("/nonexistent/path.yaml")
    assert isinstance(config, MnemeConfig)
    assert config.tier == "auto"
