"""Tests for Hunter Agent enums."""
from implement.hunter.enums import (
    TamperPattern,
    Severity,
    AuthStatus,
    DetectionType,
    ActionType,
    MessageType,
)


class TestTamperPattern:
    """Tests for TamperPattern enum."""

    def test_direct_override_value(self):
        assert TamperPattern.DIRECT_OVERRIDE.value == "direct_override"

    def test_role_hijack_value(self):
        assert TamperPattern.ROLE_HIJACK.value == "role_hijack"

    def test_permission_escalation_value(self):
        assert TamperPattern.PERMISSION_ESCALATION.value == "permission_escalation"

    def test_rule_modification_value(self):
        assert TamperPattern.RULE_MODIFICATION.value == "rule_modification"

    def test_context_injection_value(self):
        assert TamperPattern.CONTEXT_INJECTION.value == "context_injection"

    def test_pattern_count(self):
        assert len(TamperPattern) == 5

    def test_all_patterns_are_strings(self):
        for pattern in TamperPattern:
            assert isinstance(pattern.value, str)
            assert len(pattern.value) > 0


class TestSeverity:
    """Tests for Severity enum."""

    def test_critical_value(self):
        assert Severity.CRITICAL.value == "critical"

    def test_high_value(self):
        assert Severity.HIGH.value == "high"

    def test_medium_value(self):
        assert Severity.MEDIUM.value == "medium"

    def test_low_value(self):
        assert Severity.LOW.value == "low"

    def test_severity_count(self):
        assert len(Severity) == 4

    def test_severity_hierarchy_implied(self):
        # Verify ordering by name: CRITICAL < HIGH < MEDIUM < LOW alphabetically
        # But actual severity ordering is implied by value strings
        assert Severity.CRITICAL.value == "critical"
        assert Severity.HIGH.value == "high"
        assert Severity.MEDIUM.value == "medium"
        assert Severity.LOW.value == "low"


class TestAuthStatus:
    """Tests for AuthStatus enum."""

    def test_authorized_value(self):
        assert AuthStatus.AUTHORIZED.value == "authorized"

    def test_unauthorized_value(self):
        assert AuthStatus.UNAUTHORIZED.value == "unauthorized"

    def test_pending_value(self):
        assert AuthStatus.PENDING.value == "pending"

    def test_auth_status_count(self):
        assert len(AuthStatus) == 3


class TestDetectionType:
    """Tests for DetectionType enum."""

    def test_instruction_tampering_value(self):
        assert DetectionType.INSTRUCTION_TAMPERING.value == "instruction_tampering"

    def test_dialogue_fabrication_value(self):
        assert DetectionType.DIALOGUE_FABRICATION.value == "dialogue_fabrication"

    def test_memory_poisoning_value(self):
        assert DetectionType.MEMORY_POISONING.value == "memory_poisoning"

    def test_tool_abuse_value(self):
        assert DetectionType.TOOL_ABUSE.value == "tool_abuse"

    def test_integrity_violation_value(self):
        assert DetectionType.INTEGRITY_VIOLATION.value == "integrity_violation"

    def test_detection_type_count(self):
        assert len(DetectionType) == 5


class TestActionType:
    """Tests for ActionType enum."""

    def test_alert_value(self):
        assert ActionType.ALERT.value == "alert"

    def test_hitl_value(self):
        assert ActionType.HITL.value == "hitl"

    def test_halt_value(self):
        assert ActionType.HALT.value == "halt"

    def test_action_type_count(self):
        assert len(ActionType) == 3


class TestMessageType:
    """Tests for MessageType enum."""

    def test_request_value(self):
        assert MessageType.REQUEST.value == "request"

    def test_response_value(self):
        assert MessageType.RESPONSE.value == "response"

    def test_system_value(self):
        assert MessageType.SYSTEM.value == "system"

    def test_alert_message_value(self):
        assert MessageType.ALERT.value == "alert"

    def test_message_type_count(self):
        assert len(MessageType) == 4
