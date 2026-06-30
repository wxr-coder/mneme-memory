"""Capability detection and tier determination.

mneme-memory auto-detects hardware capability at startup and selects
the appropriate tier (S/A/B/C). Users can override via config.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from enum import StrEnum
from typing import Any


class Tier(StrEnum):
    """Hardware capability level."""

    S = "S"  # 16GB+ VRAM — optimal
    A = "A"  # 8-16GB VRAM — high performance
    B = "B"  # 4-8GB VRAM — balanced
    C = "C"  # <4GB or CPU — minimal

    @property
    def reflect_max_rounds(self) -> int:
        return {"S": 10, "A": 5, "B": 3, "C": 2}[self.value]

    @property
    def consolidation_mode(self) -> str:
        return {"S": "realtime", "A": "near_realtime", "B": "nightly", "C": "nightly"}[self.value]

    @property
    def retrieval_paths(self) -> list[str]:
        return {
            "S": ["semantic", "bm25", "graph", "temporal"],
            "A": ["semantic", "bm25", "graph", "temporal"],
            "B": ["semantic", "bm25", "temporal"],
            "C": ["semantic", "bm25"],
        }[self.value]

    @property
    def has_reranker(self) -> bool:
        return self.value in ("S", "A")

    @property
    def personality_momentum(self) -> float:
        return {"S": 0.95, "A": 0.92, "B": 0.90, "C": 0.85}[self.value]


@dataclass
class Capability:
    """Plugin resource requirements declaration."""

    min_vram_gb: float = 0.0
    min_ram_gb: float = 2.0
    min_cpu_cores: int = 2
    recommended_tier: Tier = Tier.S
    gpu_required: bool = False
    network_required: bool = False
    description: str = ""


@dataclass
class HardwareInfo:
    """Detected hardware characteristics."""

    gpu_vram_gb: float = 0.0
    gpu_name: str = ""
    cpu_cores: int = 0
    ram_gb: float = 0.0
    has_nvidia: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "gpu_vram_gb": self.gpu_vram_gb,
            "gpu_name": self.gpu_name,
            "cpu_cores": self.cpu_cores,
            "ram_gb": self.ram_gb,
            "has_nvidia": self.has_nvidia,
        }


def detect_hardware() -> HardwareInfo:
    """Detect GPU, CPU, and RAM at startup."""
    info = HardwareInfo()

    # CPU cores
    info.cpu_cores = os.cpu_count() or 2

    # RAM (Linux: /proc/meminfo)
    try:
        with open("/proc/meminfo") as f:
            for line in f:
                if line.startswith("MemTotal:"):
                    info.ram_gb = int(line.split()[1]) / (1024 * 1024)
                    break
    except (OSError, ValueError, IndexError):
        info.ram_gb = 16.0  # fallback assumption

    # NVIDIA GPU
    nvidia_smi = shutil.which("nvidia-smi")
    if nvidia_smi:
        info.has_nvidia = True
        try:
            result = subprocess.run(
                [nvidia_smi, "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0 and result.stdout.strip():
                parts = result.stdout.strip().split(", ")
                info.gpu_name = parts[0] if len(parts) >= 1 else ""
                if len(parts) >= 2:
                    info.gpu_vram_gb = float(parts[1]) / 1024.0
        except (subprocess.TimeoutExpired, ValueError, IndexError):
            pass

    return info


def _tier_from_vram(vram_gb: float) -> Tier:
    if vram_gb >= 16:
        return Tier.S
    elif vram_gb >= 8:
        return Tier.A
    elif vram_gb >= 4:
        return Tier.B
    return Tier.C


def detect_tier(
    hardware: HardwareInfo | None = None,
    capabilities: list[Capability] | None = None,
    override: str | None = None,
) -> Tier:
    """Determine the active tier.

    Args:
        hardware: Detected hardware info (auto-detected if None)
        capabilities: Plugin capabilities (for constraint checking)
        override: Manual override ("S", "A", "B", "C", or None for auto)
    """
    if override and override.upper() in ("S", "A", "B", "C"):
        return Tier(override.upper())

    if hardware is None:
        hardware = detect_hardware()

    candidate = _tier_from_vram(hardware.gpu_vram_gb)

    # Check plugin constraints (木桶效应: weakest plugin determines tier)
    if capabilities:
        for cap in capabilities:
            if cap.gpu_required and not hardware.has_nvidia:
                candidate = _downgrade(candidate)
            if cap.min_vram_gb > hardware.gpu_vram_gb:
                candidate = _downgrade(candidate)

    return candidate


def _downgrade(tier: Tier) -> Tier:
    order = [Tier.S, Tier.A, Tier.B, Tier.C]
    idx = order.index(tier)
    if idx < len(order) - 1:
        return order[idx + 1]
    return tier
