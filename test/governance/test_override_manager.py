"""Tests for OverrideManager."""

import pytest
from datetime import datetime, timedelta
from implement.governance.enums import Tier, AuthorizedRole
from implement.governance.exceptions import UnauthorizedOverrideError
from implement.governance.override_manager import OverrideManager, _REVIEW_FLAG_THRESHOLD


@pytest.fixture
def override_manager():
    return OverrideManager()


class TestAuthorizedOverride:
    def test_authorized_override_succeeds(self, override_manager):
        """ADMIN role can override HOTL → HITL successfully."""
        result = override_manager.override_tier(
            operation_id="op-ovr-001",
            new_tier=Tier.HITL,
            justification="Requires human review due to scope change",
            role=AuthorizedRole.ADMIN,
            actor_identity="admin@example.com",
            original_tier=Tier.HOTL,
        )
        assert result.success is True
        assert result.new_tier == Tier.HITL
        assert "overridden from" in result.message.lower() and "hotl" in result.message.lower() and "hitl" in result.message.lower()

    def test_admin_can_escalate_to_hootl(self, override_manager):
        """ADMIN can directly escalate HOTL → HOOTL."""
        result = override_manager.override_tier(
            operation_id="op-ovr-002",
            new_tier=Tier.HOOTL,
            justification="Emergency escalation",
            role=AuthorizedRole.ADMIN,
            actor_identity="admin@example.com",
            original_tier=Tier.HOTL,
        )
        assert result.success is True
        assert result.new_tier == Tier.HOOTL

    def test_security_admin_can_elevate_hotl_to_hitl(self, override_manager):
        """SECURITY_ADMIN can escalate HOTL → HITL."""
        result = override_manager.override_tier(
            operation_id="op-sec-001",
            new_tier=Tier.HITL,
            justification="Security-relevant operation",
            role=AuthorizedRole.SECURITY_ADMIN,
            actor_identity="sec-admin@example.com",
            original_tier=Tier.HOTL,
        )
        assert result.success is True
        assert result.new_tier == Tier.HITL

    def test_compliance_officer_can_escalate(self, override_manager):
        """COMPLIANCE_OFFICER can escalate HOTL → HITL."""
        result = override_manager.override_tier(
            operation_id="op-comp-001",
            new_tier=Tier.HITL,
            justification="Compliance review required",
            role=AuthorizedRole.COMPLIANCE_OFFICER,
            actor_identity="compliance@example.com",
            original_tier=Tier.HOTL,
        )
        assert result.success is True


class TestUnauthorizedOverride:
    def test_unauthorized_override_denied(self, override_manager):
        """OPERATOR cannot perform ADMIN-only tier transition."""
        with pytest.raises(UnauthorizedOverrideError):
            override_manager.override_tier(
                operation_id="op-unauth-001",
                new_tier=Tier.HOOTL,   # OPERATOR can't escalate to HOOTL
                justification="Trying to bypass",
                role=AuthorizedRole.OPERATOR,
                actor_identity="operator@example.com",
                original_tier=Tier.HOTL,
            )

    def test_operator_limited_to_routine_escalation(self, override_manager):
        """OPERATOR can only do HOTL → HITL for routine operations."""
        # OPERATOR can do HOTL → HITL (allowed)
        result = override_manager.override_tier(
            operation_id="op-op-001",
            new_tier=Tier.HITL,
            justification="Routine escalation",
            role=AuthorizedRole.OPERATOR,
            actor_identity="operator@example.com",
            original_tier=Tier.HOTL,
        )
        assert result.success is True

        # But OPERATOR cannot do HITL → HOOTL (not in matrix)
        with pytest.raises(UnauthorizedOverrideError):
            override_manager.override_tier(
                operation_id="op-op-002",
                new_tier=Tier.HOOTL,
                justification="Not allowed",
                role=AuthorizedRole.OPERATOR,
                actor_identity="operator@example.com",
                original_tier=Tier.HITL,
            )


class TestEmptyJustificationDenied:
    def test_empty_justification_denied(self, override_manager):
        """Empty justification raises ValueError."""
        with pytest.raises(ValueError):
            override_manager.override_tier(
                operation_id="op-empty-001",
                new_tier=Tier.HITL,
                justification="",   # empty
                role=AuthorizedRole.ADMIN,
                actor_identity="admin@example.com",
                original_tier=Tier.HOTL,
            )

    def test_whitespace_only_justification_denied(self, override_manager):
        """Whitespace-only justification raises ValueError."""
        with pytest.raises(ValueError):
            override_manager.override_tier(
                operation_id="op-space-001",
                new_tier=Tier.HITL,
                justification="   ",   # whitespace only
                role=AuthorizedRole.ADMIN,
                actor_identity="admin@example.com",
                original_tier=Tier.HOTL,
            )


class TestReviewFlagAtThreshold:
    def test_review_flag_at_threshold(self, override_manager):
        """3+ overrides in 24h triggers review_flag."""
        actor = "flagged-actor@example.com"
        # Make exactly _REVIEW_FLAG_THRESHOLD - 1 overrides — no flag yet
        for i in range(_REVIEW_FLAG_THRESHOLD - 1):
            override_manager.override_tier(
                operation_id=f"op-flag-{i}",
                new_tier=Tier.HITL,
                justification=f"Justification {i}",
                role=AuthorizedRole.ADMIN,
                actor_identity=actor,
                original_tier=Tier.HOTL,
            )
        status_before = override_manager.check_review_flag(actor)
        assert status_before.flagged is False

        # The _REVIEW_FLAG_THRESHOLD-th override triggers the flag
        override_manager.override_tier(
            operation_id=f"op-flag-{_REVIEW_FLAG_THRESHOLD}",
            new_tier=Tier.HITL,
            justification=f"Justification {_REVIEW_FLAG_THRESHOLD}",
            role=AuthorizedRole.ADMIN,
            actor_identity=actor,
            original_tier=Tier.HOTL,
        )
        status_after = override_manager.check_review_flag(actor)
        assert status_after.flagged is True, (
            f"Expected flagged=True after {_REVIEW_FLAG_THRESHOLD} overrides, "
            f"got flagged={status_after.flagged}"
        )
        assert status_after.override_count >= _REVIEW_FLAG_THRESHOLD


class TestOverrideLoggedToAudit:
    def test_override_logged_to_audit(self, override_manager):
        """Successful override is recorded in override history."""
        actor = "history-actor@example.com"
        override_manager.override_tier(
            operation_id="op-hist-001",
            new_tier=Tier.HITL,
            justification="Test override",
            role=AuthorizedRole.ADMIN,
            actor_identity=actor,
            original_tier=Tier.HOTL,
        )
        history = override_manager.get_override_history(actor_identity=actor)
        assert len(history) == 1
        assert history[0].operation_id == "op-hist-001"
        assert history[0].new_tier == Tier.HITL
        assert history[0].original_tier == Tier.HOTL


class TestIsAuthorized:
    def test_is_authorized_admin_hotl_to_hitl(self, override_manager):
        """is_authorized returns True for ADMIN HOTL → HITL."""
        assert override_manager.is_authorized(
            AuthorizedRole.ADMIN, Tier.HOTL, Tier.HITL
        ) is True

    def test_is_authorized_operator_hootl_denied(self, override_manager):
        """is_authorized returns False for OPERATOR HOTL → HOOTL."""
        assert override_manager.is_authorized(
            AuthorizedRole.OPERATOR, Tier.HOTL, Tier.HOOTL
        ) is False


class TestGetFlaggedActors:
    def test_get_flagged_actors(self, override_manager):
        """get_flagged_actors returns all actors with review flag."""
        actor = "multi-flag@example.com"
        for i in range(_REVIEW_FLAG_THRESHOLD):
            override_manager.override_tier(
                operation_id=f"op-multiflag-{i}",
                new_tier=Tier.HITL,
                justification=f"Justification {i}",
                role=AuthorizedRole.ADMIN,
                actor_identity=actor,
                original_tier=Tier.HOTL,
            )
        flagged = override_manager.get_flagged_actors()
        assert any(f.actor_identity == actor for f in flagged)


class TestOverrideHistoryQuery:
    def test_override_history_by_operation_id(self, override_manager):
        """get_override_history can filter by operation_id."""
        op_id = "op-specific-001"
        override_manager.override_tier(
            operation_id=op_id,
            new_tier=Tier.HITL,
            justification="Specific operation",
            role=AuthorizedRole.ADMIN,
            actor_identity="admin@example.com",
            original_tier=Tier.HOTL,
        )
        history = override_manager.get_override_history(operation_id=op_id)
        assert len(history) == 1
        assert history[0].operation_id == op_id


class TestEmergencyOverride:
    def test_emergency_override_admin(self, override_manager):
        """ADMIN can perform emergency HOOTL override."""
        result = override_manager.emergency_override(
            operation_id="op-emerg-001",
            emergency_tier=Tier.HOOTL,
            justification="Active security breach",
            role=AuthorizedRole.ADMIN,
            actor_identity="admin@example.com",
        )
        assert result.success is True
        assert result.new_tier == Tier.HOOTL
        assert result.review_flagged is True  # Emergency always flagged

    def test_emergency_override_operator_denied(self, override_manager):
        """OPERATOR cannot perform emergency override."""
        with pytest.raises(UnauthorizedOverrideError):
            override_manager.emergency_override(
                operation_id="op-emerg-002",
                emergency_tier=Tier.HOOTL,
                justification="Trying emergency override",
                role=AuthorizedRole.OPERATOR,
                actor_identity="operator@example.com",
            )

    def test_emergency_override_non_hootl_denied(self, override_manager):
        """Emergency override cannot target non-HOOTL tier."""
        with pytest.raises(UnauthorizedOverrideError):
            override_manager.emergency_override(
                operation_id="op-emerg-003",
                emergency_tier=Tier.HITL,   # Must be HOOTL
                justification="Invalid emergency tier",
                role=AuthorizedRole.ADMIN,
                actor_identity="admin@example.com",
            )
