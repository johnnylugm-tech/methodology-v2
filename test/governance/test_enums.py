"""Tests for governance enums."""

import pytest
from implement.governance.enums import (
    Tier,
    GovernanceDecision,
    ApprovalStatus,
    RiskLevel,
    AuthorizedRole,
    OperationType,
    OperationScope,
)


class TestTierValues:
    def test_tier_values(self):
        """HOTL, HITL, HOOTL exist as distinct Tier enum members."""
        assert Tier.HOTL is not None
        assert Tier.HITL is not None
        assert Tier.HOOTL is not None
        # They must be distinct
        assert Tier.HOTL != Tier.HITL
        assert Tier.HITL != Tier.HOOTL
        assert Tier.HOTL != Tier.HOOTL


class TestGovernanceDecisionValues:
    def test_governance_decision_values(self):
        """All 5 decision types exist: AUTO_APPROVE, PENDING_APPROVAL, BLOCK, ESCALATE, EMERGENCY_TRIGGER."""
        decisions = list(GovernanceDecision)
        assert GovernanceDecision.AUTO_APPROVE in decisions
        assert GovernanceDecision.PENDING_APPROVAL in decisions
        assert GovernanceDecision.BLOCK in decisions
        assert GovernanceDecision.ESCALATE in decisions
        assert GovernanceDecision.EMERGENCY_TRIGGER in decisions
        assert len(decisions) == 5


class TestApprovalStatusValues:
    def test_approval_status_values(self):
        """All 6 status types exist: PENDING, APPROVED, DENIED, MODIFIED, ESCALATED, TIMEOUT."""
        statuses = list(ApprovalStatus)
        assert ApprovalStatus.PENDING in statuses
        assert ApprovalStatus.APPROVED in statuses
        assert ApprovalStatus.DENIED in statuses
        assert ApprovalStatus.MODIFIED in statuses
        assert ApprovalStatus.ESCALATED in statuses
        assert ApprovalStatus.TIMEOUT in statuses
        assert len(statuses) == 6


class TestRiskLevelValues:
    def test_risk_level_values(self):
        """All 3 risk levels exist: ROUTINE, ELEVATED, CRITICAL."""
        levels = list(RiskLevel)
        assert RiskLevel.ROUTINE in levels
        assert RiskLevel.ELEVATED in levels
        assert RiskLevel.CRITICAL in levels
        assert len(levels) == 3


class TestAuthorizedRoleValues:
    def test_authorized_role_values(self):
        """All 4 roles exist: ADMIN, SECURITY_ADMIN, COMPLIANCE_OFFICER, OPERATOR."""
        roles = list(AuthorizedRole)
        assert AuthorizedRole.ADMIN in roles
        assert AuthorizedRole.SECURITY_ADMIN in roles
        assert AuthorizedRole.COMPLIANCE_OFFICER in roles
        assert AuthorizedRole.OPERATOR in roles
        assert len(roles) == 4
