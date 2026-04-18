"""
Cost Tracker — Per-Request and Cumulative Cost Tracking

Tracks token usage and computes cost per model call and per cascade request.
Enforces cost caps per request and cumulative budgets.

Pricing defaults from ARCHITECTURE.md Section 2.3:
  Claude Opus:     $0.015 / $0.075  (input / output per 1K tokens)
  Claude Sonnet:   $0.003 / $0.015
  GPT-4o:          $0.005 / $0.015
  GPT-4o-mini:     $0.00015 / $0.0006
  Gemini-Pro:      $0.00125 / $0.005
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

from .models import (
    AttemptCost,
    CascadeConfig,
    ModelPricing,
    DEFAULT_MODEL_PRICING,
)


class CostTracker:
    """
    Track costs for a single cascade request (and cumulatively across sessions).

    Usage:
        tracker = CostTracker()
        tracker.reset()  # Start new request
        cost = tracker.add_cost("claude-opus-4", input_tokens=500, output_tokens=200)
        print(tracker.get_total_cost())  # ~$0.018
        if tracker.is_within_budget(config):
            ...  # OK to continue
    """

    def __init__(self) -> None:
        """
        Initialize CostTracker.
        """
        self._lock = threading.RLock()
        self._attempt_costs: List[AttemptCost] = []
        self._total_cost_usd: float = 0.0
        self._token_pricing: Dict[str, ModelPricing] = {}
        self._request_total: float = 0.0  # Reset per request

    # ─────────────────────────────────────────────────────────────────────────
    # Cost Recording
    # ─────────────────────────────────────────────────────────────────────────

    def add_cost(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cost_per_1k_input: float,
        cost_per_1k_output: float,
    ) -> float:
        """
        Record a model call's cost.

        Args:
            provider:           Provider name (e.g., "anthropic")
            model:              Model name (e.g., "claude-opus-4")
            input_tokens:       Number of input tokens
            output_tokens:      Number of output tokens
            cost_per_1k_input:  Cost per 1K input tokens (USD)
            cost_per_1k_output: Cost per 1K output tokens (USD)

        Returns:
            Cost in USD for this specific call.
        """
        input_cost = (input_tokens / 1000.0) * cost_per_1k_input
        output_cost = (output_tokens / 1000.0) * cost_per_1k_output
        call_cost = input_cost + output_cost

        with self._lock:
            self._total_cost_usd += call_cost
            self._request_total += call_cost
            record = AttemptCost(
                model_name=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                cost_usd=round(call_cost, 6),
                timestamp=datetime.now(timezone.utc),
            )
            self._attempt_costs.append(record)
            return round(call_cost, 6)

    def add_cost_from_pricing(
        self,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
    ) -> float:
        """
        Record cost using the model's default pricing.

        Looks up pricing from DEFAULT_MODEL_PRICING or uses zeros if unknown.
        """
        pricing = DEFAULT_MODEL_PRICING.get(model.lower(), (0.0, 0.0))
        return self.add_cost(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_per_1k_input=pricing[0],
            cost_per_1k_output=pricing[1],
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Queries
    # ─────────────────────────────────────────────────────────────────────────

    def get_total_cost(self) -> float:
        """
        Get total cost for the current cascade request.

        Returns:
            Cumulative cost in USD.
        """
        with self._lock:
            return round(self._request_total, 6)

    def get_session_total(self) -> float:
        """
        Get total cost across all requests in this session.
        """
        with self._lock:
            return round(self._total_cost_usd, 6)

    def is_within_budget(self, config: CascadeConfig) -> bool:
        """
        Check if remaining budget allows another attempt.

        Args:
            config: The current CascadeConfig with cost_cap_usd.

        Returns:
            True if (total cost + estimated minimum cost) < cost_cap_usd.
        """
        with self._lock:
            return self._request_total < config.cost_cap_usd

    def get_remaining_budget(self, config: CascadeConfig) -> float:
        """
        Get remaining budget in USD.
        """
        with self._lock:
            return max(0.0, config.cost_cap_usd - self._request_total)

    def get_cost_breakdown(self) -> List[AttemptCost]:
        """
        Get per-attempt cost breakdown for the current request.
        """
        with self._lock:
            return list(self._attempt_costs)

    def get_cost_breakdown_summary(self) -> Dict[str, float]:
        """
        Get a summary of costs per model.
        """
        with self._lock:
            summary: Dict[str, float] = {}
            for record in self._attempt_costs:
                summary[record.model_name] = summary.get(record.model_name, 0.0) + record.cost_usd
            return {k: round(v, 6) for k, v in summary.items()}

    # ─────────────────────────────────────────────────────────────────────────
    # Token Pricing
    # ─────────────────────────────────────────────────────────────────────────

    def register_pricing(self, pricing: ModelPricing) -> None:
        """
        Register or override token pricing for a model.
        """
        with self._lock:
            self._token_pricing[pricing.model_name] = pricing

    def get_pricing(self, model: str) -> Optional[ModelPricing]:
        """
        Get pricing for a model.
        """
        with self._lock:
            return self._token_pricing.get(model)

    # ─────────────────────────────────────────────────────────────────────────
    # Reset
    # ─────────────────────────────────────────────────────────────────────────

    def reset(self) -> None:
        """
        Reset cost tracking for a new cascade request.
        Does NOT reset session total (_total_cost_usd).
        """
        with self._lock:
            self._attempt_costs.clear()
            self._request_total = 0.0

    def reset_session(self) -> None:
        """
        Reset ALL cost tracking including session totals.
        Use with caution — this is typically only called at startup.
        """
        with self._lock:
            self._attempt_costs.clear()
            self._request_total = 0.0
            self._total_cost_usd = 0.0
