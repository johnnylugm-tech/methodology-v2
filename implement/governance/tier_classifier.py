"""TierClassifier — FR-TG-1: Tier Classification Engine.

Classifies every agent operation into exactly one tier: HOTL, HITL, or HOOTL.
Classification is based on operation type, risk level, scope, and policy rules.
Low-confidence classifications default to the higher (safer) tier.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from .enums import (
    LOW_CONFIDENCE_THRESHOLD,
    OperationScope,
    OperationType,
    RiskLevel,
    Tier,
    TIER_ORDER,
)
from .exceptions import TierClassificationError
from .models import (
    GovernanceContext,
    TierDecision,
)


# ─── Policy Store (static default rules) ─────────────────────────────────────

# Map: (operation_type, risk_level, scope) → default tier
_DEFAULT_POLICY_RULES: Dict[tuple, Tier] = {
    # Code Generation
    (OperationType.CODE_GENERATION, RiskLevel.ROUTINE, OperationScope.SINGLE_AGENT): Tier.HOTL,
    (OperationType.CODE_GENERATION, RiskLevel.ROUTINE, OperationScope.MULTI_AGENT): Tier.HITL,
    (OperationType.CODE_GENERATION, RiskLevel.ELEVATED, OperationScope.SINGLE_AGENT): Tier.HITL,
    (OperationType.CODE_GENERATION, RiskLevel.ELEVATED, OperationScope.MULTI_AGENT): Tier.HITL,
    (OperationType.CODE_GENERATION, RiskLevel.CRITICAL, OperationScope.SINGLE_AGENT): Tier.HITL,
    (OperationType.CODE_GENERATION, RiskLevel.CRITICAL, OperationScope.MULTI_AGENT): Tier.HOOTL,

    # Automated Testing
    (OperationType.AUTOMATED_TESTING, RiskLevel.ROUTINE, OperationScope.SINGLE_AGENT): Tier.HOTL,
    (OperationType.AUTOMATED_TESTING, RiskLevel.ROUTINE, OperationScope.MULTI_AGENT): Tier.HITL,
    (OperationType.AUTOMATED_TESTING, RiskLevel.ELEVATED, OperationScope.SINGLE_AGENT): Tier.HITL,

    # Refactoring
    (OperationType.REFACTORING, RiskLevel.ROUTINE, OperationScope.SINGLE_AGENT): Tier.HOTL,
    (OperationType.REFACTORING, RiskLevel.ELEVATED, OperationScope.SINGLE_AGENT): Tier.HITL,
    (OperationType.REFACTORING, RiskLevel.ELEVATED, OperationScope.MULTI_AGENT): Tier.HITL,
    (OperationType.REFACTORING, RiskLevel.CRITICAL, OperationScope.MULTI_AGENT): Tier.HOOTL,

    # Configuration
    (OperationType.CONFIGURATION, RiskLevel.ROUTINE, OperationScope.SINGLE_AGENT): Tier.HOTL,
    (OperationType.CONFIGURATION, RiskLevel.ELEVATED, OperationScope.SINGLE_AGENT): Tier.HITL,
    (OperationType.CONFIGURATION, RiskLevel.CRITICAL, OperationScope.SINGLE_AGENT): Tier.HOOTL,

    # Data Operations
    (OperationType.DATA_OPERATION, RiskLevel.ROUTINE, OperationScope.SINGLE_AGENT): Tier.HOTL,
    (OperationType.DATA_OPERATION, RiskLevel.ELEVATED, OperationScope.SINGLE_AGENT): Tier.HITL,
    (OperationType.DATA_OPERATION, RiskLevel.ELEVATED, OperationScope.MULTI_AGENT): Tier.HITL,
    (OperationType.DATA_OPERATION, RiskLevel.CRITICAL, OperationScope.MULTI_AGENT): Tier.HOOTL,

    # Multi-Agent Coordination
    (OperationType.MULTI_AGENT_COORDINATION, RiskLevel.ROUTINE, OperationScope.SINGLE_AGENT): Tier.HOTL,
    (OperationType.MULTI_AGENT_COORDINATION, RiskLevel.ROUTINE, OperationScope.MULTI_AGENT): Tier.HITL,
    (OperationType.MULTI_AGENT_COORDINATION, RiskLevel.ELEVATED, OperationScope.MULTI_AGENT): Tier.HITL,
    (OperationType.MULTI_AGENT_COORDINATION, RiskLevel.CRITICAL, OperationScope.CROSS_WORKSPACE): Tier.HOOTL,

    # Security — never HOTL
    (OperationType.SECURITY, RiskLevel.ROUTINE, OperationScope.SINGLE_AGENT): Tier.HITL,
    (OperationType.SECURITY, RiskLevel.ELEVATED, OperationScope.MULTI_AGENT): Tier.HITL,
    (OperationType.SECURITY, RiskLevel.CRITICAL, OperationScope.SINGLE_AGENT): Tier.HOOTL,
    (OperationType.SECURITY, RiskLevel.CRITICAL, OperationScope.MULTI_AGENT): Tier.HOOTL,
    (OperationType.SECURITY, RiskLevel.CRITICAL, OperationScope.CROSS_WORKSPACE): Tier.HOOTL,

    # Compliance
    (OperationType.COMPLIANCE, RiskLevel.ROUTINE, OperationScope.SINGLE_AGENT): Tier.HITL,
    (OperationType.COMPLIANCE, RiskLevel.ELEVATED, OperationScope.MULTI_AGENT): Tier.HITL,
    (OperationType.COMPLIANCE, RiskLevel.CRITICAL, OperationScope.CROSS_WORKSPACE): Tier.HOOTL,

    # System Health
    (OperationType.SYSTEM_HEALTH, RiskLevel.ROUTINE, OperationScope.SINGLE_AGENT): Tier.HOTL,
    (OperationType.SYSTEM_HEALTH, RiskLevel.ELEVATED, OperationScope.SINGLE_AGENT): Tier.HITL,
    (OperationType.SYSTEM_HEALTH, RiskLevel.CRITICAL, OperationScope.MULTI_AGENT): Tier.HOOTL,

    # Agent Lifecycle — always at least HITL
    (OperationType.AGENT_LIFECYCLE, RiskLevel.ROUTINE, OperationScope.SINGLE_AGENT): Tier.HITL,

    # Constitution Modification — always HITL (never HOOTL bypass)
    (OperationType.CONSTITUTION_MODIFICATION, RiskLevel.ROUTINE, OperationScope.SINGLE_AGENT): Tier.HITL,

    # Emergency — always HOOTL
    (OperationType.EMERGENCY, RiskLevel.CRITICAL, OperationScope.SINGLE_AGENT): Tier.HOOTL,
    (OperationType.EMERGENCY, RiskLevel.CRITICAL, OperationScope.MULTI_AGENT): Tier.HOOTL,
}


class TierClassifier:
    """
    Classifies agent operations into HOTL, HITL, or HOOTL tiers.

    Classification is deterministic based on operation type, risk level, and scope.
    When confidence is below 0.60, the result defaults to the higher (safer) tier.
    Every classification decision is logged and stored in history.
    """

    def __init__(self) -> None:
        self._policy_rules: Dict[tuple, Tier] = dict(_DEFAULT_POLICY_RULES)
        self._classification_history: List[TierDecision] = []
        self._metrics: Dict[Tier, int] = {Tier.HOTL: 0, Tier.HITL: 0, Tier.HOOTL: 0}

    def classify_operation(self, context: GovernanceContext) -> TierDecision:
        """
        Classify a single operation into a governance tier.

        Args:
            context: Governance context containing operation details.

        Returns:
            TierDecision with the assigned tier, rationale, and confidence score.

        Raises:
            TierClassificationError: If classification cannot be determined.
        """
        if not context.operation_id:
            raise TierClassificationError("operation_id is required for classification")

        # Look up policy rule
        tier, confidence = self._lookup_policy(context)

        # Build reason string
        reason = (
            f"Policy match: op_type={context.operation_type.name}, "
            f"risk={context.risk_level.name}, scope={context.scope.name}, "
            f"confidence={confidence:.2f}"
        )

        # Apply low-confidence safety default: escalate to next tier
        original_tier = tier
        if confidence < LOW_CONFIDENCE_THRESHOLD:
            tier = self._escalate_for_low_confidence(tier)
            reason += (
                f" [LOW CONFIDENCE {confidence:.2f} < {LOW_CONFIDENCE_THRESHOLD}, "
                f"escalated from {original_tier.name} to {tier.name}]"
            )

        decision = TierDecision(
            operation_id=context.operation_id,
            tier=tier,
            classification_reason=reason,
            timestamp=datetime.utcnow(),
            confidence=confidence,
            overrides=[],
        )

        self._store_decision(decision)
        return decision

    def classify_batch(self, contexts: List[GovernanceContext]) -> List[TierDecision]:
        """
        Classify a batch of operations.

        Args:
            contexts: List of governance contexts.

        Returns:
            List of TierDecision objects, one per input context.
        """
        return [self.classify_operation(ctx) for ctx in contexts]

    def get_classification_rules(self) -> Dict[str, Tier]:
        """
        Return the current policy rules as a dict.

        Returns:
            Dict mapping rule descriptions to assigned tiers.
        """
        return {
            f"{op_type.name}_{risk.name}_{scope.name}": tier
            for (op_type, risk, scope), tier in self._policy_rules.items()
        }

    def get_metrics(self) -> Dict[Tier, int]:
        """Return tier distribution metrics."""
        return dict(self._metrics)

    def get_history(
        self,
        operation_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[TierDecision]:
        """
        Query classification history.

        Args:
            operation_id: Filter by specific operation (None = all).
            limit: Maximum number of entries to return.

        Returns:
            List of matching TierDecision objects, most recent first.
        """
        history = self._classification_history
        if operation_id:
            history = [d for d in history if d.operation_id == operation_id]
        return history[-limit:][::-1]   # most recent first

    # ─── Internal Helpers ───────────────────────────────────────────────────────

    def _lookup_policy(
        self,
        context: GovernanceContext,
    ) -> tuple[Tier, float]:
        """
        Look up the tier for an operation using policy rules.

        Returns:
            (tier, confidence) tuple.
        """
        key = (context.operation_type, context.risk_level, context.scope)
        if key in self._policy_rules:
            return self._policy_rules[key], 0.95

        # Fallback: derive tier from risk and scope heuristics
        return self._derive_tier_fallback(context), 0.60

    def _derive_tier_fallback(self, context: GovernanceContext) -> Tier:
        """Derive tier using heuristic rules when no explicit policy exists."""
        # CRITICAL risk → at least HITL
        if context.risk_level == RiskLevel.CRITICAL:
            return Tier.HITL

        # CROSS_WORKSPACE scope → at least HITL
        if context.scope == OperationScope.CROSS_WORKSPACE:
            return Tier.HITL

        # ELEVATED risk + MULTI_AGENT scope → HITL
        if context.risk_level == RiskLevel.ELEVATED and context.scope == OperationScope.MULTI_AGENT:
            return Tier.HITL

        # Default to HOTL
        return Tier.HOTL

    def _escalate_for_low_confidence(self, tier: Tier) -> Tier:
        """Escalate tier by one level when confidence is low."""
        order = TIER_ORDER.get(tier, 0)
        for t in Tier:
            if TIER_ORDER.get(t, 0) == order + 1:
                return t
        return Tier.HOOTL   # cap at HOOTL

    def _store_decision(self, decision: TierDecision) -> None:
        """Append decision to history and update metrics."""
        self._classification_history.append(decision)
        self._metrics[decision.tier] = self._metrics.get(decision.tier, 0) + 1
