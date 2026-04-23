"""
adapters/__init__.py — PhaseHooks Adapter Package

Provides PhaseHooksAdapter that integrates all 13 Features into the existing
PhaseHooks framework via the 7 hook points.
"""

from .phase_hooks_adapter import PhaseHooksAdapter

__all__ = [
    "PhaseHooksAdapter",
]
