"""
D3: Cost/Token Risk Assessor [FR-R-3]

Evaluates risk of excessive token consumption or cost overrun.
"""

from __future__ import annotations

from typing import Optional

from . import AbstractDimensionAssessor, DimensionResult


class CostAssessor(AbstractDimensionAssessor):
    """
    D3: Cost/Token Risk Assessor [FR-R-3]

    Assessment Factors:
    - Estimated token budget vs. actual usage
    - Context window utilization
    - Batch vs. streaming cost comparison
    - Retry/redundancy overhead
    """

    def assess(self, context: dict) -> float:
        """
        Calculate cost/token risk score.

        Args:
            context: Must contain usage information

        Returns:
            Risk score 0.0-1.0
        """
        # Budget ratio calculation
        actual_tokens = context.get("actual_tokens", 0)
        budget_tokens = context.get("budget_tokens", 100000)
        budget_ratio = actual_tokens / budget_tokens if budget_tokens > 0 else 0

        # If already over budget, maximum risk
        if actual_tokens > budget_tokens and budget_tokens > 0:
            return 1.0

        # Window utilization
        context_used = context.get("context_used", 0)
        context_limit = context.get("context_limit", 200000)
        window_utilization = context_used / context_limit if context_limit > 0 else 0

        # Redundancy overhead
        retry_cost = context.get("retry_cost", 0)
        total_cost = context.get("total_cost", max(actual_tokens, 1))
        redundancy_overhead = retry_cost / total_cost if total_cost > 0 else 0

        # Batch efficiency
        batch_waste = context.get("batch_waste", 0)
        batch_efficiency = (1 - batch_waste / total_cost) if total_cost > 0 else 1.0
        batch_efficiency_score = batch_efficiency * 0.2

        return min(
            1.0,
            budget_ratio * 0.4 +
            window_utilization * 0.3 +
            redundancy_overhead * 0.1 +
            batch_efficiency_score
        )

    def get_dimension_id(self) -> str:
        return "D3"

    def assess_with_details(self, context: dict) -> DimensionResult:
        """Perform detailed cost risk assessment."""
        actual_tokens = context.get("actual_tokens", 0)
        budget_tokens = context.get("budget_tokens", 100000)
        context_used = context.get("context_used", 0)
        context_limit = context.get("context_limit", 200000)

        evidence = [
            f"Tokens: {actual_tokens:,} / {budget_tokens:,} budget",
            f"Context: {context_used:,} / {context_limit:,} limit ({context_used/context_limit*100:.1f}%)" if context_limit > 0 else "Context: N/A",
        ]

        warnings = []
        if actual_tokens > budget_tokens:
            warnings.append("BUDGET EXCEEDED")
        elif actual_tokens > budget_tokens * 0.9:
            warnings.append("Approaching budget limit")

        metadata = {
            "budget_ratio": actual_tokens / budget_tokens if budget_tokens > 0 else 0,
            "window_utilization": context_used / context_limit if context_limit > 0 else 0,
        }

        score = self.assess(context)
        return DimensionResult(
            dimension_id=self.get_dimension_id(),
            score=score,
            evidence=evidence,
            metadata=metadata,
            warnings=warnings,
        )