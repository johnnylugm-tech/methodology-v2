"""
Self-Correction Metrics.

Tracks and reports self-correction engine performance metrics
for dashboard display and analytics.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class SelfCorrectionMetrics:
    """
    Metrics for the Self-Correction Engine.

    Tracks correction counts, success rates, and learning effectiveness.

    Attributes:
        total_corrections: Total number of correction attempts made.
        auto_fixable_count: Number of auto-fixable corrections attempted.
        auto_fix_success_rate: Proportion of auto-fix attempts that succeeded.
        ai_assisted_count: Number of AI-assisted corrections attempted.
        ai_assisted_success_rate: Proportion of AI-assisted attempts that succeeded.
        manual_required_count: Number of corrections that required manual intervention.
        manual_required_rate: Proportion of corrections requiring manual review.
        learning_hit_rate: Proportion of correction attempts that found a
                          similar past correction in the library.
        avg_correction_time_hours: Average time spent on corrections (in hours).
        correction_confidence_calibration: Average absolute error between
                                            predicted confidence and actual success.
                                            Lower is better; 0.0 = perfect calibration.
    """

    total_corrections: int
    auto_fixable_count: int
    auto_fix_success_rate: float
    ai_assisted_count: int
    ai_assisted_success_rate: float
    manual_required_count: int
    manual_required_rate: float
    learning_hit_rate: float
    avg_correction_time_hours: float
    correction_confidence_calibration: float

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to a plain dict for serialization."""
        return {
            "total_corrections": self.total_corrections,
            "auto_fixable": {
                "count": self.auto_fixable_count,
                "success_rate": round(self.auto_fix_success_rate, 4),
            },
            "ai_assisted": {
                "count": self.ai_assisted_count,
                "success_rate": round(self.ai_assisted_success_rate, 4),
            },
            "manual_required": {
                "count": self.manual_required_count,
                "rate": round(self.manual_required_rate, 4),
            },
            "learning_hit_rate": round(self.learning_hit_rate, 4),
            "avg_correction_time_hours": round(self.avg_correction_time_hours, 4),
            "confidence_calibration_error": round(self.correction_confidence_calibration, 4),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SelfCorrectionMetrics:
        """Reconstruct from dict."""
        inner = data.get
        return cls(
            total_corrections=data.get("total_corrections", 0),
            auto_fixable_count=data.get("auto_fixable", {}).get("count", 0),
            auto_fix_success_rate=data.get("auto_fixable", {}).get("success_rate", 0.0),
            ai_assisted_count=data.get("ai_assisted", {}).get("count", 0),
            ai_assisted_success_rate=data.get("ai_assisted", {}).get("success_rate", 0.0),
            manual_required_count=data.get("manual_required", {}).get("count", 0),
            manual_required_rate=data.get("manual_required", {}).get("rate", 0.0),
            learning_hit_rate=data.get("learning_hit_rate", 0.0),
            avg_correction_time_hours=data.get("avg_correction_time_hours", 0.0),
            correction_confidence_calibration=data.get("confidence_calibration_error", 0.0),
        )

    def summary(self) -> str:
        """Generate a human-readable summary of the metrics."""
        lines = [
            "Self-Correction Metrics",
            "=" * 40,
            f"Total corrections:    {self.total_corrections}",
            "",
            f"Auto-fix:              {self.auto_fixable_count} attempts, "
            f"{self.auto_fix_success_rate:.1%} success",
            f"AI-assisted:           {self.ai_assisted_count} attempts, "
            f"{self.ai_assisted_success_rate:.1%} success",
            f"Manual required:      {self.manual_required_count} "
            f"({self.manual_required_rate:.1%})",
            "",
            f"Learning hit rate:     {self.learning_hit_rate:.1%}",
            f"Confidence calib err: {self.correction_confidence_calibration:.3f}",
        ]
        return "\n".join(lines)
