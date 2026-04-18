"""Main facade for Hunter Agent."""
import uuid
from typing import List, Optional
from datetime import datetime

from .enums import DetectionType, Severity, ActionType
from .models import (
    AgentMessage, HunterAlert, IntegrityResult, AbuseResult,
    ToolCall
)
from .integrity_validator import IntegrityValidator
from .anomaly_detector import AnomalyDetector
from .rule_compliance import RuleCompliance
from .runtime_monitor import RuntimeMonitor


class HunterAgent:
    """Layer 2.5 Hunter Agent - Monitors all Agent communications."""

    def __init__(self, config: Optional[dict] = None) -> None:
        """Initialize Hunter Agent with sub-detectors."""
        self._config = config or {}
        self._alerts: List[HunterAlert] = []
        self._integrity_validator = IntegrityValidator(config)
        self._anomaly_detector = AnomalyDetector(config)
        self._rule_compliance = RuleCompliance(config)
        self._runtime_monitor = RuntimeMonitor(config)

    def inspect_message(self, message: AgentMessage) -> List[HunterAlert]:
        """
        Main entry point - inspects all agent-to-agent messages.

        Args:
            message: AgentMessage to inspect

        Returns:
            List of HunterAlert (empty if no threats detected)
        """
        alerts: List[HunterAlert] = []

        # FR-H-1: Instruction tampering
        tamper_result = self._integrity_validator.detect_tampering(message.content)
        if tamper_result.is_tampered:
            alert = HunterAlert(
                alert_id=self._generate_id(),
                detection_type=DetectionType.INSTRUCTION_TAMPERING,
                severity=tamper_result.severity,
                agent_id=message.agent_id,
                evidence={"matched_tokens": tamper_result.matched_tokens},
                timestamp=message.timestamp,
                action_taken=self._action_for_severity(tamper_result.severity)
            )
            alerts.append(alert)

        # FR-H-2: Dialogue fabrication
        claims = self._anomaly_detector.extract_claims(message.content)
        for claim in claims:
            fabricate_result = self._anomaly_detector.detect_fabrication(
                message.agent_id, claim, message.conversation_id
            )
            if fabricate_result.is_fabricated:
                alert = HunterAlert(
                    alert_id=self._generate_id(),
                    detection_type=DetectionType.DIALOGUE_FABRICATION,
                    severity=Severity.HIGH,
                    agent_id=message.agent_id,
                    evidence={"claim": claim},
                    timestamp=message.timestamp,
                    action_taken=ActionType.ALERT
                )
                alerts.append(alert)

        self._alerts.extend(alerts)
        return alerts

    def validate_integrity(
        self, agent_id: str, source: str, expected_hash: Optional[str] = None
    ) -> IntegrityResult:
        """
        Runtime integrity validation on memory/context read.

        Args:
            agent_id: ID of the agent performing the read
            source: Path or identifier of the source being read
            expected_hash: Optional pre-known hash for verification

        Returns:
            IntegrityResult with validation outcome
        """
        return self._runtime_monitor.validate_read(agent_id, source, expected_hash)

    def check_tool_usage(self, agent_id: str, tool_call: ToolCall) -> AbuseResult:
        """
        Check if a tool call is within the agent's allowed whitelist.

        Args:
            agent_id: ID of the agent making the tool call
            tool_call: ToolCall dataclass with tool name and parameters

        Returns:
            AbuseResult indicating whether tool is whitelisted
        """
        return self._rule_compliance.check_whitelist(agent_id, tool_call.tool_name)

    def get_alert_history(
        self,
        agent_id: Optional[str] = None,
        since: Optional[datetime] = None
    ) -> List[HunterAlert]:
        """
        Query historical alerts.

        Args:
            agent_id: Filter by agent (None = all agents)
            since: Filter by timestamp (None = all time)

        Returns:
            List of matching HunterAlert sorted by timestamp desc
        """
        alerts = self._alerts
        if agent_id:
            alerts = [a for a in alerts if a.agent_id == agent_id]
        if since:
            alerts = [a for a in alerts if a.timestamp > since]
        return alerts

    def _action_for_severity(self, severity: Severity) -> ActionType:
        """Map severity to action type."""
        if severity == Severity.CRITICAL:
            return ActionType.HALT
        elif severity == Severity.HIGH:
            return ActionType.HITL
        else:
            return ActionType.ALERT

    def _generate_id(self) -> str:
        """Generate UUID4 alert ID."""
        return str(uuid.uuid4())
