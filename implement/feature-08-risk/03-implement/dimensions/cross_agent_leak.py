"""
D6: Cross-Agent Leak Risk Assessor [FR-R-6]

Evaluates risk of information leakage between agents.
"""

from __future__ import annotations

from typing import Optional

from . import AbstractDimensionAssessor, DimensionResult


class CrossAgentLeakAssessor(AbstractDimensionAssessor):
    """
    D6: Cross-Agent Leak Risk Assessor [FR-R-6]

    Assessment Factors:
    - Agent isolation level
    - Shared state exposure
    - Message sanitization between agents
    - Authorization checks on inter-agent calls
    """

    def assess(self, context: dict) -> float:
        """
        Calculate cross-agent leak risk score.

        Args:
            context: Must contain agent interaction information

        Returns:
            Risk score 0.0-1.0
        """
        # Isolation score (inverted - higher isolation = lower risk)
        isolation_level = context.get("agent_isolation_level", 1.0)
        isolation_score = (1 - isolation_level) * 0.3

        # Shared state exposure
        shared_state_score = self._measure_shared_state_exposure(context) * 0.3

        # Message sanitization score (inverted)
        message_sanitized = context.get("inter_agent_messages_sanitized", True)
        message_sanitization_score = 0 if message_sanitized else 0.25

        # Authorization checks score (inverted)
        auth_checks = context.get("has_authorization_checks", True)
        auth_check_score = 0 if auth_checks else 0.15

        return isolation_score + shared_state_score + message_sanitization_score + auth_check_score

    def _measure_shared_state_exposure(self, context: dict) -> float:
        """Measure exposure to shared state."""
        shared_state = context.get("shared_state_access", [])
        if not shared_state:
            return 0.0

        # Count sensitive shared state access
        sensitive_access = context.get("sensitive_shared_state_access", 0)
        total_access = len(shared_state)

        if sensitive_access > 0:
            return min(1.0, sensitive_access / total_access + 0.3)

        return min(1.0, total_access * 0.1)

    def get_dimension_id(self) -> str:
        return "D6"

    def assess_with_details(self, context: dict) -> DimensionResult:
        """Perform detailed cross-agent leak assessment."""
        isolation_level = context.get("agent_isolation_level", 1.0)
        shared_state = context.get("shared_state_access", [])

        evidence = [
            f"Agent isolation: {isolation_level:.0%}",
            f"Shared state access: {len(shared_state)} items",
        ]

        warnings = []
        if isolation_level < 0.5:
            warnings.append("Low agent isolation - higher leak risk")

        if not context.get("inter_agent_messages_sanitized", True):
            warnings.append("Inter-agent messages not sanitized")

        if not context.get("has_authorization_checks", True):
            warnings.append("Missing authorization checks")

        metadata = {
            "isolation_level": isolation_level,
            "shared_state_count": len(shared_state),
        }

        score = self.assess(context)
        return DimensionResult(
            dimension_id=self.get_dimension_id(),
            score=score,
            evidence=evidence,
            metadata=metadata,
            warnings=warnings,
        )