"""OverrideManager — FR-TG-8: Override Mechanisms.

Allows authorized roles to override tier assignments with mandatory justification.
Repeated overrides by the same actor trigger automatic review flagging.
Emergency override bypass (HOOTL activation) is restricted to emergency responder roles.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .enums import (
    AuthorizedRole,
    Tier,
)
from .exceptions import (
    UnauthorizedOverrideError,
)
from .models import (
    OverrideRecord,
    OverrideResult,
    ReviewFlagStatus,
)


# ─── Authorization Matrix ─────────────────────────────────────────────────────

# Map: (from_role, from_tier, to_tier) → allowed (True/False)
# Explicit True entries; absent entries default to False.
_AUTHORIZATION_MATRIX: Dict[tuple, bool] = {
    # ADMIN: can escalate any tier up (single-step)
    (AuthorizedRole.ADMIN, Tier.HOTL, Tier.HITL): True,
    (AuthorizedRole.ADMIN, Tier.HITL, Tier.HOOTL): True,
    (AuthorizedRole.ADMIN, Tier.HOTL, Tier.HOOTL): True,
    # ADMIN: can de-escalate
    (AuthorizedRole.ADMIN, Tier.HITL, Tier.HOTL): True,
    (AuthorizedRole.ADMIN, Tier.HOOTL, Tier.HITL): True,
    # SECURITY_ADMIN: can escalate security-relevant tiers
    (AuthorizedRole.SECURITY_ADMIN, Tier.HOTL, Tier.HITL): True,
    (AuthorizedRole.SECURITY_ADMIN, Tier.HITL, Tier.HOOTL): True,
    (AuthorizedRole.SECURITY_ADMIN, Tier.HOTL, Tier.HOOTL): True,
    # COMPLIANCE_OFFICER: can escalate compliance-relevant tiers
    (AuthorizedRole.COMPLIANCE_OFFICER, Tier.HOTL, Tier.HITL): True,
    (AuthorizedRole.COMPLIANCE_OFFICER, Tier.HITL, Tier.HOOTL): True,
    # OPERATOR: can only elevate HOTL→HITL for routine operations
    (AuthorizedRole.OPERATOR, Tier.HOTL, Tier.HITL): True,
}

# Override count threshold for review flagging
_REVIEW_FLAG_THRESHOLD = 3
_REVIEW_FLAG_WINDOW_HOURS = 24


class OverrideManager:
    """
    Manages tier override requests from authorized roles.

    Every override requires mandatory justification. Repeated overrides
    by the same actor within a time window trigger an automatic review flag.
    Unauthorized override attempts are logged as security events.

    Emergency override (direct HOOTL activation without trigger) is
    restricted to specific emergency responder configurations.
    """

    def __init__(self) -> None:
        self._override_history: List[OverrideRecord] = []
        self._review_flags: Dict[str, ReviewFlagStatus] = {}
        self._authorized_roles: Dict[AuthorizedRole, bool] = {
            role: True for role in AuthorizedRole
        }

    def override_tier(
        self,
        operation_id: str,
        new_tier: Tier,
        justification: str,
        role: AuthorizedRole,
        actor_identity: str,
        original_tier: Tier,
    ) -> OverrideResult:
        """
        Override the tier assignment for an operation.

        Args:
            operation_id: The operation whose tier is being overridden.
            new_tier: The desired new tier.
            justification: Mandatory justification (must be non-empty).
            role: The role of the actor requesting the override.
            actor_identity: The identity of the actor.
            original_tier: The tier before override.

        Returns:
            OverrideResult indicating success/failure.

        Raises:
            UnauthorizedOverrideError: If the role is not authorized for this override.
            ValueError: If justification is empty.
        """
        # Validate justification
        if not justification or not justification.strip():
            raise ValueError("Justification is required for all tier overrides")

        # Check authorization
        if not self._is_authorized(role, original_tier, new_tier):
            raise UnauthorizedOverrideError(
                f"Role {role.name} is not authorized to override "
                f"{original_tier.name} → {new_tier.name}"
            )

        # Record the override
        record = OverrideRecord(
            operation_id=operation_id,
            original_tier=original_tier,
            new_tier=new_tier,
            justification=justification,
            actor_identity=actor_identity,
            role=role,
            timestamp=datetime.utcnow(),
            review_flagged=False,
        )

        # Append first, THEN check for review flag (count includes this new record)
        self._override_history.append(record)

        if self._should_flag_for_review(actor_identity):
            record.review_flagged = True
            self._update_review_flag(actor_identity)

        return OverrideResult(
            success=True,
            message=f"Tier overridden from {original_tier.name} to {new_tier.name}",
            new_tier=new_tier,
            review_flagged=record.review_flagged,
        )

    def is_authorized(
        self,
        role: AuthorizedRole,
        from_tier: Tier,
        to_tier: Tier,
    ) -> bool:
        """
        Check if a role is authorized for a specific tier transition.

        Args:
            role: The role attempting the override.
            from_tier: Current tier.
            to_tier: Desired new tier.

        Returns:
            True if the role is authorized for this transition.
        """
        return self._is_authorized(role, from_tier, to_tier)

    def emergency_override(
        self,
        operation_id: str,
        emergency_tier: Tier,
        justification: str,
        role: AuthorizedRole,
        actor_identity: str,
    ) -> OverrideResult:
        """
        Perform an emergency override (activate HOOTL without waiting for trigger).

        This is a restricted operation only available to emergency responder roles.

        Args:
            operation_id: The operation being escalated.
            emergency_tier: The target tier (must be HOOTL for true emergencies).
            justification: Mandatory justification.
            role: The role of the actor (must be authorized for emergency overrides).
            actor_identity: The identity of the actor.

        Returns:
            OverrideResult indicating success/failure.

        Raises:
            UnauthorizedOverrideError: If the role is not authorized for emergency override.
        """
        # Emergency override is only valid for HOOTL activation
        if emergency_tier != Tier.HOOTL:
            raise UnauthorizedOverrideError(
                "Emergency override can only activate HOOTL tier"
            )

        # Check if role is authorized for emergency overrides
        if not self._can_emergency_override(role):
            raise UnauthorizedOverrideError(
                f"Role {role.name} is not authorized for emergency HOOTL override"
            )

        if not justification or not justification.strip():
            raise ValueError("Justification is required for emergency overrides")

        # Record as normal override with emergency flag
        record = OverrideRecord(
            operation_id=operation_id,
            original_tier=Tier.HITL,   # Assume it was coming from HITL
            new_tier=emergency_tier,
            justification=f"[EMERGENCY OVERRIDE] {justification}",
            actor_identity=actor_identity,
            role=role,
            timestamp=datetime.utcnow(),
            review_flagged=True,    # Emergency overrides always get flagged for review
        )
        self._override_history.append(record)
        self._update_review_flag(actor_identity)

        return OverrideResult(
            success=True,
            message=f"Emergency HOOTL override activated by {actor_identity}",
            new_tier=emergency_tier,
            review_flagged=True,
        )

    def get_override_history(
        self,
        actor_identity: Optional[str] = None,
        operation_id: Optional[str] = None,
    ) -> List[OverrideRecord]:
        """
        Query override history.

        Args:
            actor_identity: Filter by actor (None = all).
            operation_id: Filter by operation (None = all).

        Returns:
            List of matching OverrideRecords, most recent first.
        """
        records = list(self._override_history)
        if actor_identity:
            records = [r for r in records if r.actor_identity == actor_identity]
        if operation_id:
            records = [r for r in records if r.operation_id == operation_id]
        records.sort(key=lambda r: r.timestamp, reverse=True)
        return records

    def check_review_flag(self, actor_identity: str) -> ReviewFlagStatus:
        """
        Check if an actor is currently flagged for review.

        Args:
            actor_identity: The actor to check.

        Returns:
            ReviewFlagStatus for the actor.
        """
        if actor_identity not in self._review_flags:
            return ReviewFlagStatus(
                actor_identity=actor_identity,
                flagged=False,
                override_count=0,
            )
        return self._review_flags[actor_identity]

    def get_flagged_actors(self) -> List[ReviewFlagStatus]:
        """
        Get all actors currently flagged for review.

        Returns:
            List of ReviewFlagStatus for all flagged actors.
        """
        return [
            status for status in self._review_flags.values()
            if status.flagged
        ]

    # ─── Internal Helpers ───────────────────────────────────────────────────────

    def _is_authorized(self, role: AuthorizedRole, from_tier: Tier, to_tier: Tier) -> bool:
        """Check authorization matrix for a tier transition. Default is DENY."""
        key = (role, from_tier, to_tier)
        return _AUTHORIZATION_MATRIX.get(key, False)

    def _can_emergency_override(self, role: AuthorizedRole) -> bool:
        """Check if a role is authorized for emergency (HOOTL) override."""
        return role in (
            AuthorizedRole.ADMIN,
            AuthorizedRole.SECURITY_ADMIN,
        )

    def _should_flag_for_review(self, actor_identity: str) -> bool:
        """
        Determine if an actor should be flagged for review.

        Flags an actor if they have made 3+ overrides within the last 24 hours.
        """
        window_start = datetime.utcnow() - timedelta(hours=_REVIEW_FLAG_WINDOW_HOURS)
        recent_overrides = [
            r for r in self._override_history
            if r.actor_identity == actor_identity and r.timestamp >= window_start
        ]
        return len(recent_overrides) >= _REVIEW_FLAG_THRESHOLD

    def _update_review_flag(self, actor_identity: str) -> None:
        """Update or create a review flag for an actor."""
        window_start = datetime.utcnow() - timedelta(hours=_REVIEW_FLAG_WINDOW_HOURS)
        recent_count = sum(
            1 for r in self._override_history
            if r.actor_identity == actor_identity and r.timestamp >= window_start
        )

        self._review_flags[actor_identity] = ReviewFlagStatus(
            actor_identity=actor_identity,
            flagged=recent_count >= _REVIEW_FLAG_THRESHOLD,
            override_count=recent_count,
            last_override_at=datetime.utcnow(),
        )
