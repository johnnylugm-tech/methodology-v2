"""
D7: Latency/SLO Risk Assessor [FR-R-7]

Evaluates risk of exceeding response time targets or SLO breaches.
"""

from __future__ import annotations

from typing import Optional

from . import AbstractDimensionAssessor, DimensionResult


class LatencyAssessor(AbstractDimensionAssessor):
    """
    D7: Latency/SLO Risk Assessor [FR-R-7]

    Assessment Factors:
    - Historical latency vs. SLO target
    - Current queue depth
    - Timeout configuration
    - Degradation detection
    """

    DEFAULT_SLO_TARGET_MS = 2000  # 2 seconds default

    def assess(self, context: dict) -> float:
        """
        Calculate latency/SLO risk score.

        Args:
            context: Must contain latency and SLO information

        Returns:
            Risk score 0.0-1.0
        """
        slo_target = context.get("slo_target_ms", self.DEFAULT_SLO_TARGET_MS)
        current_latency = context.get("current_latency_ms", 0)

        # SLO violation score
        if current_latency <= slo_target:
            slo_violation_score = 0.0
        else:
            slo_violation_score = min(1.0, (current_latency - slo_target) / slo_target)

        # Queue depth score
        queue_depth = context.get("queue_depth", 0)
        max_queue = context.get("max_queue", 100)
        queue_score = min(1.0, queue_depth / max_queue) * 0.25 if max_queue > 0 else 0

        # Timeout configuration score
        timeout_score = (1 - self._configure_timeouts(context)) * 0.2

        # Degradation detection score
        degradation_score = self._detect_performance_degradation(context) * 0.15

        return slo_violation_score * 0.4 + queue_score + timeout_score + degradation_score

    def _configure_timeouts(self, context: dict) -> float:
        """Check timeout configuration."""
        timeout_configured = context.get("timeout_configured", False)
        timeout_ms = context.get("timeout_ms", 0)
        slo_target = context.get("slo_target_ms", self.DEFAULT_SLO_TARGET_MS)

        if not timeout_configured:
            return 0.0  # No timeout = high risk

        # Timeout should be at least SLO target
        if timeout_ms >= slo_target:
            return 1.0
        elif timeout_ms >= slo_target * 0.8:
            return 0.6
        return 0.3

    def _detect_performance_degradation(self, context: dict) -> float:
        """Detect performance degradation trends."""
        degradation_detected = context.get("performance_degradation", False)
        degradation_trend = context.get("degradation_trend", 0)  # percentage

        if degradation_detected:
            return min(1.0, degradation_trend / 50)  # 50% degradation = max risk
        return 0.0

    def get_dimension_id(self) -> str:
        return "D7"

    def assess_with_details(self, context: dict) -> DimensionResult:
        """Perform detailed latency risk assessment."""
        current_latency = context.get("current_latency_ms", 0)
        slo_target = context.get("slo_target_ms", self.DEFAULT_SLO_TARGET_MS)
        queue_depth = context.get("queue_depth", 0)

        evidence = [
            f"Current latency: {current_latency}ms",
            f"SLO target: {slo_target}ms",
            f"Queue depth: {queue_depth}",
        ]

        warnings = []
        if current_latency > slo_target:
            overrun_pct = (current_latency - slo_target) / slo_target * 100
            warnings.append(f"SLO overrun: {overrun_pct:.1f}%")

        if context.get("performance_degradation", False):
            warnings.append("Performance degradation detected")

        metadata = {
            "latency_ratio": current_latency / slo_target if slo_target > 0 else 0,
            "queue_utilization": queue_depth / context.get("max_queue", 100) if context.get("max_queue", 0) > 0 else 0,
        }

        score = self.assess(context)
        return DimensionResult(
            dimension_id=self.get_dimension_id(),
            score=score,
            evidence=evidence,
            metadata=metadata,
            warnings=warnings,
        )