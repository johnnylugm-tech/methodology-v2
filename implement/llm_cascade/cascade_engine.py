"""
Cascade Engine — Core Cascade Logic

Executes model calls in chain order. Handles API errors, timeouts,
rate limits, and coordinates with ConfidenceScorer and CostTracker.

State Machine:
  ROUTING → MODEL_CALL → CASCADE_CHECK → (escalate) → ROUTING
                                           → (return success)
                                           → (exhausted)

See ARCHITECTURE.md Section 3 for full state diagram.
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import List, Tuple

from .confidence_scorer import ConfidenceScorer
from .cost_tracker import CostTracker
from .enums import CascadeStateEnum
from .health_tracker import HealthTracker
from .models import (
    CascadeConfig,
    CascadeResult,
    CascadeState,
    ModelCallResult,
    ModelConfig,
    AttemptRecord,
)


class CascadeEngine:
    """
    Core cascade execution engine.

    Responsible for:
      - Executing model calls in chain order
      - Handling API errors, timeouts, rate limits
      - Coordinating with ConfidenceScorer and CostTracker
      - Enforcing latency and cost budgets

    Usage:
        engine = CascadeEngine(health_tracker, cost_tracker, confidence_scorer)
        result = await engine.execute_chain(prompt, config)
    """

    def __init__(
        self,
        health_tracker: HealthTracker,
        cost_tracker: CostTracker,
        confidence_scorer: ConfidenceScorer,
    ) -> None:
        self.health_tracker = health_tracker
        self.cost_tracker = cost_tracker
        self.confidence_scorer = confidence_scorer

    # ─────────────────────────────────────────────────────────────────────────
    # Public API
    # ─────────────────────────────────────────────────────────────────────────

    async def execute_chain(
        self,
        prompt: str,
        config: CascadeConfig,
    ) -> CascadeResult:
        """
        Execute the full cascade chain: try models in order until success.

        Args:
            prompt: The input prompt to route through the cascade.
            config:  Cascade configuration with chain, budgets, and thresholds.

        Returns:
            CascadeResult on success or cascade exhaustion.
        """
        config.validate()
        self.cost_tracker.reset()

        state = CascadeState(state=CascadeStateEnum.ROUTING)
        start_time = datetime.now(timezone.utc)
        attempt_history: List[AttemptRecord] = []

        for depth, model in enumerate(config.chain):
            # ── Step 1: ROUTING ─────────────────────────────────────────────
            state.state = CascadeStateEnum.ROUTING
            state.current_depth = depth

            # Check provider health
            health = self.health_tracker.get_health(model.provider.value)
            if not self.health_tracker.is_healthy(model.provider.value):
                record = AttemptRecord(
                    model_name=model.model_name,
                    provider=model.provider.value,
                    latency_ms=0,
                    success=False,
                    error_type="provider_unhealthy",
                    escalated_reason=f"provider_health={health.success_rate:.2f}",
                )
                attempt_history.append(record)
                continue  # skip to next model

            # Check cost budget
            remaining_cost = config.cost_cap_usd - self.cost_tracker.get_total_cost()
            if remaining_cost <= 0:
                state.state = CascadeStateEnum.EXHAUSTED
                return self._build_exhausted_result(
                    attempt_history=attempt_history,
                    start_time=start_time,
                    config=config,
                    error=f"cost_cap_exceeded: ${config.cost_cap_usd:.4f}",
                )

            # ── Step 2: MODEL_CALL ──────────────────────────────────────────
            state.state = CascadeStateEnum.MODEL_CALL
            elapsed_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
            remaining_budget_ms = config.latency_budget_ms - elapsed_ms
            timeout = min(config.timeout_per_call_ms, max(remaining_budget_ms, 1000))

            call_result = await self.call_model(model, prompt, timeout_ms=timeout)

            # Record cost
            call_cost = self.cost_tracker.add_cost(
                provider=model.provider.value,
                model=model.model_name,
                input_tokens=call_result.input_tokens,
                output_tokens=call_result.output_tokens,
                cost_per_1k_input=model.cost_per_1k_input,
                cost_per_1k_output=model.cost_per_1k_output,
            )

            # Record health
            self.health_tracker.record_result(
                provider=model.provider.value,
                latency_ms=call_result.latency_ms,
                success=call_result.success,
                error_type=call_result.error_type,
                is_rate_limit=(call_result.error_type == "rate_limit"),
            )

            elapsed_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)

            # ── Step 3: CASCADE_CHECK ─────────────────────────────────────────
            state.state = CascadeStateEnum.CASCADE_CHECK
            state.total_latency_ms = elapsed_ms
            state.total_cost_usd = self.cost_tracker.get_total_cost()

            # Score confidence
            if call_result.success and call_result.response:
                confidence = self.confidence_scorer.score(call_result.response)
            else:
                confidence = 0.0

            # Determine if escalation is needed
            remaining_cost = config.cost_cap_usd - self.cost_tracker.get_total_cost()
            should_escalate, escalate_reason = self._should_escalate(
                call_result=call_result,
                confidence=confidence,
                config=config,
                remaining_budget_ms=remaining_budget_ms,
                remaining_budget_usd=remaining_cost,
            )

            record = AttemptRecord(
                model_name=model.model_name,
                provider=model.provider.value,
                latency_ms=call_result.latency_ms,
                success=call_result.success,
                error_type=call_result.error_type,
                http_status=call_result.http_status,
                confidence=confidence,
                cost_usd=call_cost,
                input_tokens=call_result.input_tokens,
                output_tokens=call_result.output_tokens,
                escalated_reason=escalate_reason if should_escalate else None,
                response=call_result.response,  # Store for best-response tracking
            )
            attempt_history.append(record)

            # ── Decision ─────────────────────────────────────────────────────
            if not should_escalate:
                # Success with acceptable confidence
                return CascadeResult(
                    response=call_result.response,
                    model_used=model.model_name,
                    cascade_depth=depth,
                    total_cost_usd=state.total_cost_usd,
                    latency_ms=elapsed_ms,
                    confidence=confidence,
                    attempt_history=list(attempt_history),
                    cascade_failure=False,
                    cascade_exhausted=False,
                )

            # Track best response so far (in case all fail)
            if call_result.success and call_result.response:
                if confidence > state.best_confidence:
                    state.best_response = call_result.response
                    state.best_confidence = confidence

            # Check if latency budget already exceeded
            if elapsed_ms >= config.latency_budget_ms:
                if state.best_response:
                    return CascadeResult(
                        response=state.best_response,
                        model_used=attempt_history[0].model_name,
                        cascade_depth=depth,
                        total_cost_usd=state.total_cost_usd,
                        latency_ms=elapsed_ms,
                        confidence=state.best_confidence,
                        attempt_history=list(attempt_history),
                        cascade_failure=False,
                        cascade_exhausted=True,
                    )
                else:
                    return self._build_exhausted_result(
                        attempt_history=attempt_history,
                        start_time=start_time,
                        config=config,
                        error="latency_budget_exceeded",
                    )

        # ── All models exhausted ───────────────────────────────────────────
        state.state = CascadeStateEnum.EXHAUSTED
        return self._build_exhausted_result(
            attempt_history=attempt_history,
            start_time=start_time,
            config=config,
            error="all_models_exhausted",
        )

    async def call_model(
        self,
        model: ModelConfig,
        prompt: str,
        timeout_ms: int,
    ) -> ModelCallResult:
        """
        Make a single model API call.

        This is a stub that returns a simulated successful response.
        In production, this would call the actual API (Claude, OpenAI, Gemini).
        The real implementation would live in api_clients/.

        Args:
            model:      Model configuration.
            prompt:     Input prompt.
            timeout_ms: Timeout in milliseconds.

        Returns:
            ModelCallResult with response data or error details.
        """
        # ── TODO (FR-LC-Integration): Wire to actual API clients ──────────────
        # This stub enables testing and development before API integration.
        # Real implementation:
        #   client = self._get_client(model.provider)
        #   response = await client.complete(model, prompt, timeout_ms)
        # ─────────────────────────────────────────────────────────────────────
        try:
            # Simulate an API call with realistic timing
            await asyncio.sleep(0.01)  # Simulate network latency

            # Stub: always return success with a simulated response
            # Replace this block with real API calls in production
            # Use real-looking response text that scores well on confidence
            simulated_response = f"This is a helpful and detailed response from {model.model_name}. " * 3
            simulated_input_tokens = len(prompt.split())
            simulated_output_tokens = len(simulated_response.split())

            return ModelCallResult(
                success=True,
                response=simulated_response,
                latency_ms=min(timeout_ms, 3000),
                input_tokens=simulated_input_tokens,
                output_tokens=simulated_output_tokens,
            )

        except asyncio.TimeoutError:
            return ModelCallResult(
                success=False,
                error_type="timeout",
                latency_ms=timeout_ms,
            )
        except Exception as e:
            return ModelCallResult(
                success=False,
                error_type="api_error",
                raw_error=str(e),
                latency_ms=0,
            )

    # ─────────────────────────────────────────────────────────────────────────
    # Escalation Logic
    # ─────────────────────────────────────────────────────────────────────────

    def _should_escalate(
        self,
        call_result: ModelCallResult,
        confidence: float,
        config: CascadeConfig,
        remaining_budget_ms: int,
        remaining_budget_usd: float,
    ) -> Tuple[bool, str]:
        """
        Determine whether to escalate to the next model in the chain.

        Returns:
            Tuple of (should_escalate: bool, reason: str).
            reason is empty string if no escalation needed.
        """
        # ── Error triggers ───────────────────────────────────────────────────
        if not call_result.success:
            if call_result.error_type == "rate_limit":
                return True, "rate_limit"
            elif call_result.error_type == "timeout":
                return True, "timeout"
            elif call_result.http_status is not None:
                if 500 <= call_result.http_status < 600:
                    return True, "server_error"
                elif call_result.http_status == 429:
                    return True, "rate_limit"
                else:
                    return True, f"api_error_{call_result.http_status}"
            else:
                return True, "unknown_error"

        # ── Confidence trigger ───────────────────────────────────────────────
        if confidence < config.confidence_threshold:
            return True, f"low_confidence_{confidence:.3f}"

        # ── Latency budget trigger ───────────────────────────────────────────
        if call_result.latency_ms > remaining_budget_ms:
            return True, "latency_budget_exceeded"

        # ── Cost budget trigger ──────────────────────────────────────────────
        estimated_call_cost = (
            (call_result.input_tokens / 1000.0) * config.chain[0].cost_per_1k_input
            + (call_result.output_tokens / 1000.0) * config.chain[0].cost_per_1k_output
        )
        if estimated_call_cost > remaining_budget_usd:
            return True, "cost_budget_exceeded"

        # ── No escalation needed ────────────────────────────────────────────
        return False, ""

    # ─────────────────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _build_exhausted_result(
        self,
        attempt_history: List[AttemptRecord],
        start_time: datetime,
        config: CascadeConfig,
        error: str,
    ) -> CascadeResult:
        """
        Build a CascadeResult representing cascade exhaustion.
        Returns the best available response if one was captured.
        """
        elapsed_ms = int((datetime.now(timezone.utc) - start_time).total_seconds() * 1000)
        total_cost = self.cost_tracker.get_total_cost()

        # Find best attempt from history
        successful_attempts = [r for r in attempt_history if r.success and r.confidence]
        if successful_attempts:
            best = max(successful_attempts, key=lambda r: r.confidence or 0.0)
            cascade_failure = False
        else:
            best = None
            cascade_failure = True

        if best:
            # Find the depth of the best attempt
            try:
                best_depth = attempt_history.index(best)
            except ValueError:
                best_depth = 0

            return CascadeResult(
                response=best.response if hasattr(best, "response") else None,
                model_used=best.model_name,
                cascade_depth=best_depth,
                total_cost_usd=total_cost,
                latency_ms=elapsed_ms,
                confidence=best.confidence or 0.0,
                attempt_history=list(attempt_history),
                error=error,
                cascade_failure=cascade_failure,
                cascade_exhausted=True,
            )

        # All failed
        return CascadeResult(
            response=None,
            model_used=None,
            cascade_depth=-1,
            total_cost_usd=total_cost,
            latency_ms=elapsed_ms,
            confidence=0.0,
            attempt_history=list(attempt_history),
            error=error,
            cascade_failure=True,
            cascade_exhausted=True,
        )

    def _estimate_call_cost(self, result: ModelCallResult) -> float:
        """
        Estimate the cost of a model call.
        """
        # Placeholder — actual pricing is looked up per-model in add_cost
        return (result.input_tokens + result.output_tokens) * 0.00001
