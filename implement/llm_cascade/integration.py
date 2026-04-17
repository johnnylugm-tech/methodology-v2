"""
Integration Layer — LLM Cascade Integration with Core Infrastructure

Provides integration points for:
  - Configuration Store (v3/config)
  - Metrics Infrastructure (observability)
  - Feature interdependencies (Prompt Shields, Tiered Governance, MCP/SAIF)

See ARCHITECTURE.md Section 9 for dependency mapping.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from .models import (
    CascadeConfig,
    CascadeResult,
    CascadeStats,
    LLMCascadeConfig,
    ModelConfig,
    ProviderHealth,
)

if TYPE_CHECKING:
    from .api import LLMCascade

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Config Store Integration
# ─────────────────────────────────────────────────────────────────────────────


class CascadeConfigStore:
    """
    Integration with the configuration store (v3/config).

    Loads and validates cascade configurations from the config system.
    Supports per-task-type chains, threshold overrides, and model pricing.

    Usage:
        store = CascadeConfigStore()
        config = store.load_config(task_type="code")
        cascade.update_config(config)
    """

    def __init__(self, config_path: Optional[str] = None) -> None:
        """
        Initialize with optional config path.

        Args:
            config_path: Path to llm_cascade_config.yaml.
                         If None, uses bundled defaults.
        """
        self.config_path = config_path
        self._config_cache: Dict[str, CascadeConfig] = {}
        self._global_config: Optional[LLMCascadeConfig] = None

    def load_global_config(self) -> LLMCascadeConfig:
        """
        Load the global LLMCascadeConfig from the config store.

        Returns:
            LLMCascadeConfig with defaults and overrides.
        """
        if self._global_config:
            return self._global_config

        # ── TODO (FR-Core-ConfigStore): Wire to v3/config system ────────────
        # Stub: returns default config. Replace with:
        #   raw = self.config_store.get("llm_cascade")
        #   return LLMCascadeConfig(**raw)
        # ─────────────────────────────────────────────────────────────────────
        self._global_config = LLMCascadeConfig(
            default_chain=ModelConfig.default_chain(),
            default_latency_budget_ms=10000,
            default_cost_cap_usd=0.50,
            default_confidence_threshold=0.7,
            default_timeout_per_call_ms=5000,
            health_window_seconds=86400,
            rate_limit_cooldown_seconds=60.0,
            min_provider_success_rate=0.8,
            enable_request_isolation=True,
        )
        return self._global_config

    def load_config(self, task_type: str = "general") -> CascadeConfig:
        """
        Load a CascadeConfig for a specific task type.

        Args:
            task_type: One of "general", "code", "json", "creative", "analysis".
                      Each task type may have different chains and thresholds.

        Returns:
            CascadeConfig tuned for the task type.
        """
        if task_type in self._config_cache:
            return self._config_cache[task_type]

        # ── TODO (FR-Core-ConfigStore): Load from YAML ──────────────────────
        # Stub: return default config with task-type hints.
        # Real implementation would read from llm_cascade_config.yaml:
        #   chain_config = yaml.safe_load(open(self.config_path))["tasks"][task_type]
        #   return CascadeConfig(**chain_config)
        # ─────────────────────────────────────────────────────────────────────
        chain = ModelConfig.default_chain()
        thresholds = self._task_thresholds.get(task_type, {})
        config = CascadeConfig(
            chain=chain,
            latency_budget_ms=thresholds.get("latency_budget_ms", 10000),
            cost_cap_usd=thresholds.get("cost_cap_usd", 0.50),
            confidence_threshold=thresholds.get("confidence_threshold", 0.7),
            timeout_per_call_ms=thresholds.get("timeout_per_call_ms", 5000),
        )
        self._config_cache[task_type] = config
        return config

    def save_config(self, task_type: str, config: CascadeConfig) -> None:
        """
        Save a CascadeConfig to the config store (write-through).

        Args:
            task_type: Task type identifier.
            config:     CascadeConfig to persist.
        """
        # ── TODO (FR-Core-ConfigStore): Persist to YAML ──────────────────────
        # Stub: just cache in memory
        self._config_cache[task_type] = config
        logger.info(f"CascadeConfig for task_type='{task_type}' saved to cache")
        # Real: write to llm_cascade_config.yaml

    # Task-type-specific thresholds (defaults)
    _task_thresholds: Dict[str, Dict[str, Any]] = {
        "general": {
            "latency_budget_ms": 10000,
            "cost_cap_usd": 0.50,
            "confidence_threshold": 0.7,
            "timeout_per_call_ms": 5000,
        },
        "code": {
            "latency_budget_ms": 15000,
            "cost_cap_usd": 1.00,
            "confidence_threshold": 0.8,
            "timeout_per_call_ms": 8000,
        },
        "json": {
            "latency_budget_ms": 8000,
            "cost_cap_usd": 0.30,
            "confidence_threshold": 0.85,
            "timeout_per_call_ms": 4000,
        },
        "creative": {
            "latency_budget_ms": 12000,
            "cost_cap_usd": 0.60,
            "confidence_threshold": 0.6,
            "timeout_per_call_ms": 6000,
        },
        "analysis": {
            "latency_budget_ms": 15000,
            "cost_cap_usd": 0.80,
            "confidence_threshold": 0.75,
            "timeout_per_call_ms": 8000,
        },
    }


# ─────────────────────────────────────────────────────────────────────────────
# Metrics & Observability Integration
# ─────────────────────────────────────────────────────────────────────────────


class CascadeMetricsEmitter:
    """
    Integration with the metrics infrastructure (observability layer).

    Emits structured events for:
      - CascadeResult (every request)
      - ProviderHealth snapshots
      - CascadeStats aggregates

    Usage:
        emitter = CascadeMetricsEmitter()
        emitter.emit_result(result)
        emitter.emit_stats(cascade.get_cascade_stats())
    """

    def __init__(
        self,
        metrics_adapter: Optional[Any] = None,
        enable_logging: bool = True,
    ) -> None:
        """
        Initialize metrics emitter.

        Args:
            metrics_adapter: Adapter for the metrics infrastructure.
                             If None, uses logging-based fallback.
            enable_logging:  Whether to also log metrics as structured log events.
        """
        self.metrics_adapter = metrics_adapter
        self.enable_logging = enable_logging

    def emit_result(self, result: CascadeResult) -> None:
        """
        Emit a CascadeResult as a metrics event.

        Args:
            result: The cascade result to emit.
        """
        event = {
            "event": "cascade_result",
            "success": result.success,
            "model_used": result.model_used,
            "cascade_depth": result.cascade_depth,
            "cascade_hit": result.cascade_hit,
            "cascade_failure": result.cascade_failure,
            "cascade_exhausted": result.cascade_exhausted,
            "total_cost_usd": result.total_cost_usd,
            "latency_ms": result.latency_ms,
            "confidence": result.confidence,
            "attempt_count": len(result.attempt_history),
            "error": result.error,
        }

        self._emit(event)

        # Per-attempt events
        for i, record in enumerate(result.attempt_history):
            attempt_event = {
                "event": "cascade_attempt",
                "depth": i,
                "model_name": record.model_name,
                "provider": record.provider,
                "success": record.success,
                "latency_ms": record.latency_ms,
                "confidence": record.confidence,
                "cost_usd": record.cost_usd,
                "error_type": record.error_type,
                "escalated_reason": record.escalated_reason,
            }
            self._emit(attempt_event)

    def emit_provider_health(self, health: ProviderHealth) -> None:
        """
        Emit a ProviderHealth snapshot.

        Args:
            health: Provider health data.
        """
        event = {
            "event": "provider_health",
            "provider": health.provider,
            "success_rate": health.success_rate,
            "median_latency_ms": health.median_latency_ms,
            "rate_limit_count": health.rate_limit_count,
            "is_in_cooldown": health.is_in_cooldown,
            "error_types": health.error_types,
        }
        self._emit(event)

    def emit_stats(self, stats: CascadeStats) -> None:
        """
        Emit aggregate cascade statistics.

        Args:
            stats: Aggregate stats snapshot.
        """
        event = {
            "event": "cascade_stats",
            **stats.to_dict(),
        }
        self._emit(event)

    def _emit(self, event: Dict[str, Any]) -> None:
        """
        Internal emit — routes to adapter or logs.
        """
        if self.metrics_adapter:
            # ── TODO: Wire to actual metrics infrastructure ────────────────
            # self.metrics_adapter.emit(event)
            pass

        if self.enable_logging:
            logger.info(f"[cascade_metrics] {event}")


# ─────────────────────────────────────────────────────────────────────────────
# Feature Interdependency Integration
# ─────────────────────────────────────────────────────────────────────────────


class CascadeIntegration:
    """
    Integration broker for LLM Cascade with other system components.

    Manages integration points with:
      - Prompt Shields (Feature #2): Input/output validation
      - Tiered Governance (Feature #3): Policy triggers
      - MCP/SAIF (Feature #1): Identity propagation

    Usage:
        integration = CascadeIntegration(cascade)
        # Pre-call: validate input with Prompt Shields
        integration.pre_route_validate(prompt, config)
        # Post-call: governance check on result
        integration.post_route_governance(result)
    """

    def __init__(self, cascade: "LLMCascade") -> None:
        """
        Initialize integration broker.

        Args:
            cascade: The LLMCascade instance to integrate.
        """
        self.cascade = cascade

    def pre_route_validate(
        self,
        prompt: str,
        config: Optional[CascadeConfig] = None,
    ) -> tuple[bool, Optional[str]]:
        """
        Validate prompt with Prompt Shields before routing.

        Args:
            prompt: Input prompt to validate.
            config:  Cascade config (for chain inspection if needed).

        Returns:
            Tuple of (is_valid, rejection_reason).
            If is_valid=True, routing proceeds.
            If is_valid=False, rejection_reason contains the policy violation.
        """
        # ── TODO (FR-LC-Integration): Wire to Prompt Shields (Feature #2) ────
        # Stub: always pass. Replace with:
        #   shield = self._get_prompt_shield()
        #   result = await shield.validate(prompt)
        #   return result.is_valid, result.rejection_reason
        # ─────────────────────────────────────────────────────────────────────
        return True, None

    def post_route_governance(
        self,
        result: CascadeResult,
    ) -> tuple[bool, Optional[str]]:
        """
        Run governance check on cascade result via Tiered Governance (Feature #3).

        Args:
            result: The CascadeResult to evaluate.

        Returns:
            Tuple of (is_approved, governance_concern).
            If is_approved=True, result is returned to user.
            If is_approved=False, governance_concern contains the policy flag.
        """
        # ── TODO (FR-LC-Integration): Wire to Tiered Governance (Feature #3) ─
        # Stub: always approve. Replace with:
        #   governance = self._get_governance_layer()
        #   decision = await governance.evaluate_cascade_result(result)
        #   return decision.is_approved, decision.concern
        # ─────────────────────────────────────────────────────────────────────
        return True, None

    def propagate_identity(
        self,
        model: ModelConfig,
        prompt: str,
    ) -> Dict[str, str]:
        """
        Propagate identity attribution via MCP/SAIF (Feature #1).

        Adds identity headers/tags to model calls for attribution.

        Args:
            model:  The model being called.
            prompt: The input prompt.

        Returns:
            Dict of headers/attributes to add to the API call.
        """
        # ── TODO (FR-LC-Integration): Wire to MCP/SAIF (Feature #1) ─────────
        # Stub: return empty. Replace with:
        #   saif = self._get_saif_client()
        #   return saif.get_identity_headers(
        #       source="llm_cascade",
        #       model=model.model_name,
        #       provider=model.provider.value,
        #   )
        # ─────────────────────────────────────────────────────────────────────
        return {}

    def get_integration_status(self) -> Dict[str, str]:
        """
        Return integration status for each dependent feature.

        Returns:
            Dict mapping feature name → status ("wired", "stubbed", "error").
        """
        return {
            "prompt_shields": "stubbed",   # TODO: wire to Feature #2
            "tiered_governance": "stubbed", # TODO: wire to Feature #3
            "mcp_saif": "stubbed",          # TODO: wire to Feature #1
            "config_store": "stubbed",      # TODO: wire to v3/config
            "metrics_infrastructure": "stubbed",  # TODO: wire to observability
        }
