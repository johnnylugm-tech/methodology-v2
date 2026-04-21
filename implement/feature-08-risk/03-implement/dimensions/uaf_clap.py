"""
D4: UAF/CLAP Risk Assessor [FR-R-4]

Evaluates risk of Unbounded Agent Frameworks or Cumulative LLM Agentic Processing.
"""

from __future__ import annotations

from typing import Optional

from . import AbstractDimensionAssessor, DimensionResult


class UAFClapAssessor(AbstractDimensionAssessor):
    """
    D4: UAF/CLAP Risk Assessor [FR-R-4]

    Assessment Factors:
    - Recursive agent depth
    - Cumulative context window growth
    - Loop detection (same agent called >N times)
    - Frame boundary enforcement
    """

    DEFAULT_MAX_DEPTH = 5

    def assess(self, context: dict) -> float:
        """
        Calculate UAF/CLAP risk score.

        Args:
            context: Must contain agent interaction information

        Returns:
            Risk score 0.0-1.0
        """
        max_depth = context.get("max_agent_depth", self.DEFAULT_MAX_DEPTH)

        # Depth score
        agent_depth = context.get("agent_depth", 1)
        depth_score = min(1.0, agent_depth / max_depth) * 0.3 if max_depth > 0 else agent_depth * 0.3

        # Context growth score
        context_growth_score = self._measure_context_growth_rate(context) * 0.3

        # Loop detection score
        loop_score = self._detect_loop(context) * 0.25

        # Boundary enforcement score
        boundary_score = self._evaluate_frame_boundaries(context) * 0.15

        return depth_score + context_growth_score + loop_score + boundary_score

    def _measure_context_growth_rate(self, context: dict) -> float:
        """Measure rate of context window growth."""
        growth_rate = context.get("context_growth_rate", 0)
        # If growth rate > 50% per step, high risk
        if growth_rate > 0.5:
            return 1.0
        elif growth_rate > 0.3:
            return 0.7
        elif growth_rate > 0.1:
            return 0.4
        elif growth_rate > 0:
            return 0.2
        return 0.0

    def _detect_loop(self, context: dict) -> float:
        """Detect if same agent is being called repeatedly."""
        agent_call_count = context.get("agent_call_count", {})
        max_calls = context.get("max_loop_calls", 3)

        if not agent_call_count:
            return 0.0

        # Check for excessive calls
        max_count = max(agent_call_count.values()) if agent_call_count else 1
        if max_count > max_calls:
            return 1.0
        elif max_count > max_calls * 0.7:
            return 0.6
        elif max_count > max_calls * 0.5:
            return 0.3
        return 0.0

    def _evaluate_frame_boundaries(self, context: dict) -> float:
        """Evaluate frame boundary enforcement."""
        boundary_enforcement = context.get("boundary_enforcement", "strict")

        if boundary_enforcement == "none":
            return 1.0
        elif boundary_enforcement == "weak":
            return 0.6
        elif boundary_enforcement == "moderate":
            return 0.3
        elif boundary_enforcement == "strict":
            return 0.0
        return 0.2

    def get_dimension_id(self) -> str:
        return "D4"

    def assess_with_details(self, context: dict) -> DimensionResult:
        """Perform detailed UAF/CLAP risk assessment."""
        agent_depth = context.get("agent_depth", 1)
        max_depth = context.get("max_agent_depth", self.DEFAULT_MAX_DEPTH)
        agent_call_count = context.get("agent_call_count", {})

        evidence = [
            f"Agent depth: {agent_depth} / {max_depth} max",
        ]

        if agent_call_count:
            max_count = max(agent_call_count.values())
            evidence.append(f"Max agent calls: {max_count}")

        warnings = []
        if agent_depth > max_depth:
            warnings.append("DEPTH EXCEEDED - Potential infinite loop")

        metadata = {
            "depth_ratio": agent_depth / max_depth if max_depth > 0 else 0,
            "call_counts": agent_call_count,
        }

        score = self.assess(context)
        return DimensionResult(
            dimension_id=self.get_dimension_id(),
            score=score,
            evidence=evidence,
            metadata=metadata,
            warnings=warnings,
        )