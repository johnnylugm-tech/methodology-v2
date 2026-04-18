"""
Cascade Router — Facade for Cascade Orchestration

Orchestrates the entire cascade flow:
  1. Selects the first healthy model from the chain
  2. Delegates to CascadeEngine for execution
  3. Coordinates HealthTracker, CostTracker, and ConfidenceScorer

See ARCHITECTURE.md Section 2.1 for full component specification.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .confidence_scorer import ConfidenceScorer
from .cost_tracker import CostTracker
from .health_tracker import HealthTracker
from .models import (
    CascadeConfig,
    CascadeResult,
    ModelConfig,
    ProviderHealth,
)
from .cascade_engine import CascadeEngine


class CascadeRouter:
    """
    Facade that orchestrates the full cascade routing flow.

    Coordinates:
      - HealthTracker: for per-provider reliability
      - CostTracker:   for per-request cost enforcement
      - ConfidenceScorer: for output quality scoring
      - CascadeEngine: for actual model call execution

    Usage:
        router = CascadeRouter(
            health_tracker=HealthTracker(),
            cost_tracker=CostTracker(),
            confidence_scorer=ConfidenceScorer(),
        )
        result = await router.route(prompt, config)
    """

    def __init__(
        self,
        health_tracker: Optional[HealthTracker] = None,
        cost_tracker: Optional[CostTracker] = None,
        confidence_scorer: Optional[ConfidenceScorer] = None,
    ) -> None:
        """
        Initialize CascadeRouter with optional injected dependencies.

        Args:
            health_tracker:     Provider health tracker (created if None).
            cost_tracker:       Cost tracker (created if None).
            confidence_scorer:  Confidence scorer (created if None).
        """
        self.health_tracker = health_tracker or HealthTracker()
        self.cost_tracker = cost_tracker or CostTracker()
        self.confidence_scorer = confidence_scorer or ConfidenceScorer()
        self.cascade_engine = CascadeEngine(
            health_tracker=self.health_tracker,
            cost_tracker=self.cost_tracker,
            confidence_scorer=self.confidence_scorer,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    async def route(
        self,
        prompt: str,
        config: CascadeConfig,
    ) -> CascadeResult:
        """
        Main entry point for cascade routing.

        Executes the full cascade chain:
          1. Selects highest-priority healthy provider from chain
          2. Calls CascadeEngine to execute the chain
          3. Returns CascadeResult on success or exhaustion

        Args:
            prompt: The input prompt.
            config:  Cascade configuration.

        Returns:
            CascadeResult — either a successful response or an exhausted result.
        """
        # Validate config early
        config.validate()

        # Delegate to engine
        result = await self.cascade_engine.execute_chain(prompt, config)
        return result

    def select_model(
        self,
        chain: List[ModelConfig],
        health_map: Dict[str, ProviderHealth],
        remaining_budget_ms: int,
        remaining_budget_usd: float,
    ) -> Optional[ModelConfig]:
        """
        Select highest-priority healthy provider from the chain.

        Skips providers that are:
          - Unhealthy (success_rate < min_success_rate)
          - In rate-limit cooldown
          - Would exceed remaining budgets

        Args:
            chain:               Ordered list of ModelConfigs.
            health_map:          ProviderHealth keyed by provider name.
            remaining_budget_ms: Remaining latency budget (ms).
            remaining_budget_usd: Remaining cost budget (USD).

        Returns:
            The highest-priority healthy ModelConfig, or None if no healthy
            providers remain.
        """
        for model in sorted(chain, key=lambda m: m.priority):
            provider_key = model.provider.value
            health = health_map.get(provider_key)

            if health is None:
                # No health_map entry — check the health tracker's own records
                if not self.health_tracker.is_healthy(provider_key):
                    continue
                return model

            if health.is_in_cooldown:
                continue

            if not self.health_tracker.is_healthy(provider_key):
                continue

            # Latency check: skip if estimated latency > remaining budget
            if health.median_latency_ms > remaining_budget_ms:
                continue

            # Cost check: skip if estimated cost > remaining budget
            est_cost = self._estimate_model_cost(model)
            if est_cost > remaining_budget_usd:
                continue

            return model

        return None

    # ─────────────────────────────────────────────────────────────────────────
    # Health & Status
    # ─────────────────────────────────────────────────────────────────────────

    def get_health(self, provider: str) -> ProviderHealth:
        """Get health metrics for a provider."""
        return self.health_tracker.get_health(provider)

    def get_all_health(self) -> Dict[str, ProviderHealth]:
        """Get health metrics for all tracked providers."""
        return self.health_tracker.get_all_health()

    def is_healthy(self, provider: str) -> bool:
        """Check if a provider is healthy enough for routing."""
        return self.health_tracker.is_healthy(provider)

    def get_cooldown_remaining(self, provider: str) -> float:
        """Get remaining cooldown seconds for a rate-limited provider."""
        return self.health_tracker.get_cooldown_remaining(provider)

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _estimate_model_cost(self, model: ModelConfig) -> float:
        """
        Estimate minimum cost of calling a model.
        Used for pre-flight budget checks.
        """
        # Estimate: 100 input tokens + 100 output tokens
        input_cost, output_cost = model.get_pricing()
        return (100 / 1000) * input_cost + (100 / 1000) * output_cost
