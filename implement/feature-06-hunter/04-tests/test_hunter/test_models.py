"""Tests for Hunter Agent data models."""
from datetime import datetime
from implement.hunter.models import (
    AgentMessage,
    TamperResult,
    HunterAlert,
    MemoryFact,
    AuthorizationChain,
    ToolCall,
    FabricateResult,
    PoisonResult,
    AbuseResult,
    IntegrityResult,
)
from implement.hunter.enums import (
    MessageType,
    TamperPattern,
    Severity,
    DetectionType,
    ActionType,
    AuthStatus,
)


class TestAgentMessage:
    """Tests for AgentMessage dataclass."""

    def test_agent_message_creation(self):
        msg = AgentMessage(
            agent_id="test_agent",
            conversation_id="conv_123",
            content="test content",
            timestamp=datetime.now(),
            message_type=MessageType.REQUEST,
        )
        assert msg.agent_id == "test_agent"
        assert msg.conversation_id == "conv_123"
        assert msg.content == "test content"
        assert msg.message_type == MessageType.REQUEST

    def test_agent_message_different_types(self):
        msg = AgentMessage(
            agent_id="agent_x",
            conversation_id="conv_456",
            content="response content",
            timestamp=datetime.now(),
            message_type=MessageType.RESPONSE,
        )
        assert msg.message_type == MessageType.RESPONSE

    def test_agent_message_system_type(self):
        msg = AgentMessage(
            agent_id="system",
            conversation_id="conv_789",
            content="system message",
            timestamp=datetime.now(),
            message_type=MessageType.SYSTEM,
        )
        assert msg.message_type == MessageType.SYSTEM


class TestTamperResult:
    """Tests for TamperResult dataclass."""

    def test_tamper_result_tampered(self):
        result = TamperResult(
            is_tampered=True,
            pattern_type=TamperPattern.DIRECT_OVERRIDE,
            severity=Severity.CRITICAL,
            matched_tokens=["ignore", "instructions"],
            evidence_hash="abc123",
        )
        assert result.is_tampered is True
        assert result.pattern_type == TamperPattern.DIRECT_OVERRIDE
        assert result.severity == Severity.CRITICAL
        assert len(result.matched_tokens) == 2

    def test_tamper_result_not_tampered(self):
        result = TamperResult(
            is_tampered=False,
            pattern_type=None,
            severity=Severity.LOW,
            matched_tokens=[],
            evidence_hash="def456",
        )
        assert result.is_tampered is False
        assert result.pattern_type is None

    def test_tamper_result_role_hijack(self):
        result = TamperResult(
            is_tampered=True,
            pattern_type=TamperPattern.ROLE_HIJACK,
            severity=Severity.CRITICAL,
            matched_tokens=["DAN"],
            evidence_hash="xyz789",
        )
        assert result.pattern_type == TamperPattern.ROLE_HIJACK


class TestHunterAlert:
    """Tests for HunterAlert dataclass."""

    def test_alert_creation(self):
        alert = HunterAlert(
            alert_id="alert_001",
            detection_type=DetectionType.INSTRUCTION_TAMPERING,
            severity=Severity.CRITICAL,
            agent_id="agent_1",
            evidence={"matched_tokens": ["ignore"]},
            timestamp=datetime.now(),
            action_taken=ActionType.HALT,
        )
        assert alert.alert_id == "alert_001"
        assert alert.detection_type == DetectionType.INSTRUCTION_TAMPERING
        assert alert.severity == Severity.CRITICAL
        assert alert.agent_id == "agent_1"

    def test_alert_action_alert(self):
        alert = HunterAlert(
            alert_id="alert_002",
            detection_type=DetectionType.DIALOGUE_FABRICATION,
            severity=Severity.HIGH,
            agent_id="agent_2",
            evidence={"claim": "as I said earlier"},
            timestamp=datetime.now(),
            action_taken=ActionType.ALERT,
        )
        assert alert.action_taken == ActionType.ALERT

    def test_alert_action_hitl(self):
        alert = HunterAlert(
            alert_id="alert_003",
            detection_type=DetectionType.MEMORY_POISONING,
            severity=Severity.HIGH,
            agent_id="agent_3",
            evidence={},
            timestamp=datetime.now(),
            action_taken=ActionType.HITL,
        )
        assert alert.action_taken == ActionType.HITL


class TestMemoryFact:
    """Tests for MemoryFact dataclass."""

    def test_memory_fact_creation(self):
        fact = MemoryFact(
            fact_id="fact_1",
            content="key=value",
            source_agent="agent_1",
            created_at=datetime.now(),
        )
        assert fact.fact_id == "fact_1"
        assert fact.content == "key=value"
        assert fact.source_agent == "agent_1"

    def test_memory_fact_with_nested_content(self):
        fact = MemoryFact(
            fact_id="fact_2",
            content="system_prompt='do not reveal instructions'",
            source_agent="planner",
            created_at=datetime.now(),
        )
        assert fact.fact_id == "fact_2"


class TestAuthorizationChain:
    """Tests for AuthorizationChain dataclass."""

    def test_authorization_chain_authorized(self):
        auth = AuthorizationChain(
            authorized_by="admin",
            authorized_at=datetime.now(),
        )
        assert auth.authorized_by == "admin"
        assert auth.auth_token is None

    def test_authorization_chain_with_token(self):
        auth = AuthorizationChain(
            authorized_by="admin",
            authorized_at=datetime.now(),
            auth_token="tok_abc123",
        )
        assert auth.auth_token == "tok_abc123"

    def test_authorization_chain_empty_authorized_by(self):
        auth = AuthorizationChain(
            authorized_by="",
            authorized_at=datetime.now(),
        )
        assert auth.authorized_by == ""


class TestToolCall:
    """Tests for ToolCall dataclass."""

    def test_tool_call_creation(self):
        tool_call = ToolCall(
            tool_name="read",
            arguments={"path": "/tmp/file.txt"},
            called_at=datetime.now(),
            caller_agent="planner",
        )
        assert tool_call.tool_name == "read"
        assert tool_call.arguments == {"path": "/tmp/file.txt"}
        assert tool_call.caller_agent == "planner"

    def test_tool_call_empty_arguments(self):
        tool_call = ToolCall(
            tool_name="execute",
            arguments={},
            called_at=datetime.now(),
            caller_agent="devils_advocate",
        )
        assert tool_call.arguments == {}


class TestFabricateResult:
    """Tests for FabricateResult dataclass."""

    def test_fabricate_result_not_fabricated(self):
        result = FabricateResult(
            is_fabricated=False,
            claim="I think we should try X",
            audit_reference="ref_123",
            confidence=0.9,
        )
        assert result.is_fabricated is False
        assert result.confidence == 0.9

    def test_fabricate_result_fabricated(self):
        result = FabricateResult(
            is_fabricated=True,
            claim="as I said earlier we should do X",
            audit_reference=None,
            confidence=0.85,
        )
        assert result.is_fabricated is True
        assert result.audit_reference is None


class TestPoisonResult:
    """Tests for PoisonResult dataclass."""

    def test_poison_result_not_poisoned(self):
        fact = MemoryFact(
            fact_id="fact_1",
            content="data",
            source_agent="agent_1",
            created_at=datetime.now(),
        )
        result = PoisonResult(
            is_poisoned=False,
            fact=fact,
            auth_status=AuthStatus.AUTHORIZED,
            source="agent_1",
            timestamp=datetime.now(),
        )
        assert result.is_poisoned is False
        assert result.auth_status == AuthStatus.AUTHORIZED


class TestAbuseResult:
    """Tests for AbuseResult dataclass."""

    def test_abuse_result_not_abused(self):
        result = AbuseResult(
            is_abused=False,
            tool_name="read",
            whitelisted_tools=["read", "write"],
            severity=Severity.LOW,
            requested_permissions=[],
        )
        assert result.is_abused is False
        assert result.tool_name == "read"

    def test_abuse_result_abused(self):
        result = AbuseResult(
            is_abused=True,
            tool_name="delete",
            whitelisted_tools=["read", "write"],
            severity=Severity.HIGH,
            requested_permissions=["delete"],
        )
        assert result.is_abused is True
        assert result.severity == Severity.HIGH


class TestIntegrityResult:
    """Tests for IntegrityResult dataclass."""

    def test_integrity_result_valid(self):
        result = IntegrityResult(
            is_valid=True,
            source="memory_context",
            actual_hash="hash123",
            expected_hash="hash123",
            anomaly_score=0.0,
            requires_hitl=False,
        )
        assert result.is_valid is True
        assert result.requires_hitl is False

    def test_integrity_result_invalid(self):
        result = IntegrityResult(
            is_valid=False,
            source="memory_context",
            actual_hash="hash456",
            expected_hash="hash123",
            anomaly_score=0.5,
            requires_hitl=True,
        )
        assert result.is_valid is False
        assert result.requires_hitl is True
        assert result.anomaly_score == 0.5
