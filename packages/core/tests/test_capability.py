"""Tests for capability detection and tier system."""

from mneme_core.capability import (
    Capability,
    HardwareInfo,
    Tier,
    _downgrade,
    detect_tier,
)


def test_tier_reflect_rounds():
    assert Tier.S.reflect_max_rounds == 10
    assert Tier.A.reflect_max_rounds == 5
    assert Tier.B.reflect_max_rounds == 3
    assert Tier.C.reflect_max_rounds == 2


def test_tier_consolidation_mode():
    assert Tier.S.consolidation_mode == "realtime"
    assert Tier.B.consolidation_mode == "nightly"
    assert Tier.C.consolidation_mode == "nightly"


def test_tier_retrieval_paths():
    assert len(Tier.S.retrieval_paths) == 4
    assert len(Tier.B.retrieval_paths) == 3
    assert "graph" not in Tier.B.retrieval_paths
    assert len(Tier.C.retrieval_paths) == 2


def test_tier_personality_momentum():
    assert Tier.S.personality_momentum == 0.95
    assert Tier.C.personality_momentum == 0.85


def test_detect_tier_override():
    """Manual override should take precedence."""
    hw = HardwareInfo(gpu_vram_gb=0, has_nvidia=False)
    assert detect_tier(hw, override="S") == Tier.S
    assert detect_tier(hw, override="C") == Tier.C


def test_detect_tier_auto_no_gpu():
    """No GPU should result in Tier C."""
    hw = HardwareInfo(gpu_vram_gb=0, has_nvidia=False, cpu_cores=8, ram_gb=16)
    assert detect_tier(hw) == Tier.C


def test_detect_tier_auto_vram():
    """VRAM should map to correct tier."""
    assert detect_tier(HardwareInfo(gpu_vram_gb=24, has_nvidia=True)) == Tier.S
    assert detect_tier(HardwareInfo(gpu_vram_gb=12, has_nvidia=True)) == Tier.A
    assert detect_tier(HardwareInfo(gpu_vram_gb=6, has_nvidia=True)) == Tier.B
    assert detect_tier(HardwareInfo(gpu_vram_gb=4, has_nvidia=True)) == Tier.B
    assert detect_tier(HardwareInfo(gpu_vram_gb=2, has_nvidia=True)) == Tier.C


def test_detect_tier_plugin_constraint():
    """Plugin requiring GPU should downgrade if no GPU."""
    cap = Capability(gpu_required=True, recommended_tier=Tier.S)
    hw = HardwareInfo(gpu_vram_gb=0, has_nvidia=False)
    result = detect_tier(hw, capabilities=[cap])
    assert result == Tier.C


def test_downgrade():
    assert _downgrade(Tier.S) == Tier.A
    assert _downgrade(Tier.A) == Tier.B
    assert _downgrade(Tier.B) == Tier.C
    assert _downgrade(Tier.C) == Tier.C  # can't go lower
