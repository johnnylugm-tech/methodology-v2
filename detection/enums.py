# detection/enums.py
"""Enumerations for Layer 3: UQLM + Activation Probes.

This module re-exports all enums from data_models.py for convenience.
The actual enum definitions live in data_models.py to keep all
data models in one place.

Version: 1.0.0
Date: 2026-04-19
"""

from __future__ import annotations

# Re-export enums from data_models for public API convenience
from detection.data_models import (
    Decision,
    GapSeverity,
    GapType,
    ProbeType,
)

__all__ = [
    "Decision",
    "GapSeverity",
    "GapType",
    "ProbeType",
]
