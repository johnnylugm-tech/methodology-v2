"""
Feedback-aware AutoQualityGate hook.

Wraps AutoQualityGate so that every check() result is automatically
transformed into StandardFeedback items and submitted to a FeedbackStore.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from . import AutoQualityGate

__all__ = ["AutoQualityGateWithFeedback"]


class AutoQualityGateWithFeedback(AutoQualityGate):
    """
    Enhanced AutoQualityGate that submits feedback automatically.

    After each check(), any violations found are converted to
    StandardFeedback and routed through the feedback loop.

    Usage:
        store = FeedbackStore()
        gate = AutoQualityGateWithFeedback(feedback_store=store)
        result = gate.check(phase=2, artifacts={...})
        # Feedback items are already in store
    """

    def __init__(
        self,
        *args: Any,
        feedback_store: Any = None,  # FeedbackStore | None — avoid circular import
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._feedback_store = feedback_store
        self._adapter: Any = None  # lazy import

    def _get_adapter(self) -> Any:
        """
        Lazily import and create the adapter.

        Uses sys.path manipulation to ensure 'feedback' is resolved from the
        core/ level (where it lives as a sibling to quality_gate), regardless
        of what directory pytest is run from.
        """
        if self._adapter is None and self._feedback_store is not None:
            # _file_ is quality_gate/feedback_hook.py
            # its parent parent is core/
            core_dir = Path(__file__).parent.parent
            if str(core_dir) not in sys.path:
                sys.path.insert(0, str(core_dir))
            from feedback.quality_gate_adapter import QualityGateFeedbackAdapter

            self._adapter = QualityGateFeedbackAdapter(self._feedback_store)
        return self._adapter

    def check(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        result = super().check(*args, **kwargs)

        adapter = self._get_adapter()
        if adapter and result.get("phase") is not None:
            adapter.on_quality_gate_complete(
                gate_result=result,
                phase=result["phase"],
                artifacts=kwargs.get("artifacts", {}),
            )

        return result

    def run(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Alias for check() — kept for backward compatibility."""
        return self.check(*args, **kwargs)
