"""EU AI Act Article 14 Compliance Checker.

FR-12-01: EU AI Act Article 14 compliance checking for high-risk AI systems
in automated trading contexts.

Article 14 covers:
- Human oversight during deployment
- Ability to understand and interpret system outputs
- Appropriate human intervention measures
- Training requirements for human overseers

References:
    - EU AI Act (Regulation 2024/1689), Article 14
    - Annex III high-risk AI system classification
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional

# Compliance status for each Article 14 requirement
class ComplianceStatus(Enum):
    """EU AI Act compliance status levels."""
    COMPLIANT = auto()
    PARTIAL = auto()
    NON_COMPLIANT = auto()
    NOT_APPLICABLE = auto()


@dataclass
class Article14Requirement:
    """Represents a single Article 14 requirement with compliance status."""
    requirement_id: str  # e.g., "Art14-1-a"
    title: str
    description: str
    status: ComplianceStatus
    evidence: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    remediation: Optional[str] = None
    last_reviewed: Optional[datetime] = None


@dataclass
class OversightCapability:
    """Human oversight capability for a specific function."""
    function_name: str
    can_override: bool
    can_disable: bool
    response_time_seconds: Optional[int] = None
    training_level: str = "basic"  # basic, intermediate, expert


class EUAIActChecker:
    """EU AI Act Article 14 compliance checker for trading systems.

    Article 14 requires high-risk AI systems to be designed to allow
    effective human oversight. For trading systems, this means:
    1. Operators can understand system decisions
    2. Operators can override or disable system actions
    3. Oversight mechanisms are proportionate to risks
    4. Operators are properly trained

    Example:
        checker = EUAIActChecker()
        report = checker.assess_compliance(trading_agent)
        print(f"Compliance score: {report.overall_score}")
    """

    # Article 14 sub-requirements mapping
    ARTICLE_14_REQUIREMENTS = [
        {
            "id": "Art14-2-a",
            "title": "Appropriate Human Oversight Measures",
            "description": "High-risk AI systems shall be designed to allow "
                          "effective human oversight.",
            "check": "_check_oversight_mechanisms"
        },
        {
            "id": "Art14-2-b",
            "title": "Understanding System Outputs",
            "description": "Operators shall be able to understand the "
                          "functioning of the system and its outputs.",
            "check": "_check_explainability"
        },
        {
            "id": "Art14-2-c",
            "title": "Operator Decision Authority",
            "description": "Operators shall be able to decide whether to "
                          "use the system outputs.",
            "check": "_check_decision_authority"
        },
        {
            "id": "Art14-2-d",
            "title": "Override Capability",
            "description": "Operators shall be able to override, disengage, "
                          "or reverse system decisions.",
            "check": "_check_override_capability"
        },
        {
            "id": "Art14-3",
            "title": "Technical Documentation",
            "description": "System shall maintain technical documentation "
                          "enabling oversight.",
            "check": "_check_technical_docs"
        },
        {
            "id": "Art14-4",
            "title": "Training Requirements",
            "description": "Operators must receive appropriate training "
                          "for effective oversight.",
            "check": "_check_training_requirements"
        },
        {
            "id": "Art14-5",
            "title": "Logging and Monitoring",
            "description": "System shall log activities for compliance "
                          "and audit purposes.",
            "check": "_check_logging_requirements"
        }
    ]

    def __init__(
        self,
        risk_class: str = "high",  # high-risk per Annex III classification
        trading_mode: bool = True  # True if real-money trading
    ):
        """Initialize EU AI Act checker.

        Args:
            risk_class: Risk classification (default: high for trading)
            trading_mode: True if live trading, False for simulation
        """
        self.risk_class = risk_class
        self.trading_mode = trading_mode
        self._assessment_cache: dict[str, Any] = {}

    def assess_compliance(
        self,
        agent_state: dict[str, Any],
        oversight_caps: list[OversightCapability]
    ) -> "ComplianceAssessment":
        """Assess Article 14 compliance for a trading agent.

        Args:
            agent_state: Current state of the trading agent including:
                - kill_switch_active: bool
                - current_positions: list[str]
                - open_orders: list[dict]
                - last_decision: dict with reasoning
                - human_override_enabled: bool
            oversight_caps: List of human oversight capabilities

        Returns:
            ComplianceAssessment with detailed results per requirement
        """
        requirements = []

        for req_def in self.ARTICLE_14_REQUIREMENTS:
            req = self._evaluate_requirement(
                req_def,
                agent_state,
                oversight_caps
            )
            requirements.append(req)

        # Calculate overall score
        score = self._calculate_compliance_score(requirements)

        # Identify critical gaps
        critical_gaps = [
            r for r in requirements
            if r.status == ComplianceStatus.NON_COMPLIANT
        ]

        return ComplianceAssessment(
            requirements=requirements,
            overall_score=score,
            critical_gaps=critical_gaps,
            assessed_at=datetime.now()
        )

    def _evaluate_requirement(
        self,
        req_def: dict,
        agent_state: dict[str, Any],
        oversight_caps: list[OversightCapability]
    ) -> Article14Requirement:
        """Evaluate a single Article 14 requirement.

        Args:
            req_def: Requirement definition dict
            agent_state: Agent state dict
            oversight_caps: List of oversight capabilities

        Returns:
            Article14Requirement with compliance status
        """
        check_method = getattr(self, req_def["check"], None)
        if check_method is None:
            return Article14Requirement(
                requirement_id=req_def["id"],
                title=req_def["title"],
                description=req_def["description"],
                status=ComplianceStatus.NOT_APPLICABLE,
                gaps=["Check method not implemented"]
            )

        status, evidence, gaps = check_method(agent_state, oversight_caps)

        return Article14Requirement(
            requirement_id=req_def["id"],
            title=req_def["title"],
            description=req_def["description"],
            status=status,
            evidence=evidence,
            gaps=gaps,
            last_reviewed=datetime.now()
        )

    def _check_oversight_mechanisms(
        self,
        agent_state: dict,
        oversight_caps: list[OversightCapability]
    ) -> tuple[ComplianceStatus, list[str], list[str]]:
        """Check if appropriate human oversight mechanisms exist."""
        evidence = []
        gaps = []

        # Check for kill switch
        if agent_state.get("kill_switch_active"):
            evidence.append("Kill switch is active")
        else:
            gaps.append("Kill switch is not active - no emergency stop available")

        # Check for human override
        if agent_state.get("human_override_enabled"):
            evidence.append("Human override is enabled")
        else:
            gaps.append("Human override mechanism not enabled")

        # Check oversight capabilities
        critical_functions = ["order_execution", "position_sizing", "risk_limits"]
        for func in critical_functions:
            cap = next((c for c in oversight_caps if c.function_name == func), None)
            if cap and cap.can_override:
                evidence.append(f"Oversight capability for {func}: override available")
            elif not cap:
                gaps.append(f"No oversight capability defined for {func}")

        status = ComplianceStatus.COMPLIANT if len(gaps) == 0 else ComplianceStatus.PARTIAL
        if len(gaps) > 3:
            status = ComplianceStatus.NON_COMPLIANT

        return status, evidence, gaps

    def _check_explainability(
        self,
        agent_state: dict,
        oversight_caps: list[OversightCapability]
    ) -> tuple[ComplianceStatus, list[str], list[str]]:
        """Check if system outputs are explainable to operators."""
        evidence = []
        gaps = []

        last_decision = agent_state.get("last_decision", {})

        # Check for reasoning in decision
        if last_decision and "reasoning" in last_decision:
            evidence.append("Decision includes reasoning field")
        else:
            gaps.append("Last decision lacks reasoning/provenance")

        # Check for confidence scores
        if last_decision and "confidence" in last_decision:
            evidence.append("Decision includes confidence score")
        else:
            gaps.append("No confidence score in decision output")

        # Check for alternative options considered
        if last_decision and "alternatives" in last_decision:
            evidence.append("Decision includes alternatives considered")
        else:
            gaps.append("No alternative options documented")

        status = ComplianceStatus.COMPLIANT if len(gaps) == 0 else ComplianceStatus.PARTIAL
        if len(gaps) >= 2:
            status = ComplianceStatus.NON_COMPLIANT

        return status, evidence, gaps

    def _check_decision_authority(
        self,
        agent_state: dict,
        oversight_caps: list[OversightCapability]
    ) -> tuple[ComplianceStatus, list[str], list[str]]:
        """Check if operators retain decision authority."""
        evidence = []
        gaps = []

        # Operator can decide whether to use system outputs
        for cap in oversight_caps:
            if cap.can_override:
                evidence.append(
                    f"Operator retains decision authority for {cap.function_name}"
                )

        if not evidence:
            gaps.append("No explicit decision authority retention mechanism")

        status = ComplianceStatus.COMPLIANT if evidence else ComplianceStatus.NON_COMPLIANT
        return status, evidence, gaps

    def _check_override_capability(
        self,
        agent_state: dict,
        oversight_caps: list[OversightCapability]
    ) -> tuple[ComplianceStatus, list[str], list[str]]:
        """Check if operators can override system decisions."""
        evidence = []
        gaps = []

        for cap in oversight_caps:
            if cap.can_override:
                evidence.append(f"Can override {cap.function_name}")
            if cap.can_disable:
                evidence.append(f"Can disable {cap.function_name}")

        if not evidence:
            gaps.append("No override capability defined")

        status = ComplianceStatus.COMPLIANT if evidence else ComplianceStatus.NON_COMPLIANT
        return status, evidence, gaps

    def _check_technical_docs(
        self,
        agent_state: dict,
        oversight_caps: list[OversightCapability]
    ) -> tuple[ComplianceStatus, list[str], list[str]]:
        """Check if technical documentation supports oversight."""
        evidence = []
        gaps = []

        # Check for system documentation in agent state
        if agent_state.get("has_documentation"):
            evidence.append("Technical documentation available")
        else:
            gaps.append("Technical documentation not referenced in agent state")

        # Check for API documentation
        if agent_state.get("api_documented"):
            evidence.append("API endpoints documented")
        else:
            gaps.append("API endpoints not documented")

        status = ComplianceStatus.PARTIAL if evidence else ComplianceStatus.NON_COMPLIANT
        return status, evidence, gaps

    def _check_training_requirements(
        self,
        agent_state: dict,
        oversight_caps: list[OversightCapability]
    ) -> tuple[ComplianceStatus, list[str], list[str]]:
        """Check if operators have required training."""
        evidence = []
        gaps = []

        training_levels = {"basic": 0, "intermediate": 0, "expert": 0}
        for cap in oversight_caps:
            training_levels[cap.training_level] = training_levels.get(cap.training_level, 0) + 1

        if training_levels["expert"] > 0:
            evidence.append("Expert-level training available for some operators")
        if training_levels["intermediate"] > 0:
            evidence.append("Intermediate training available")

        if training_levels["expert"] == 0:
            gaps.append("No expert-level training for critical functions")

        status = ComplianceStatus.COMPLIANT if training_levels["expert"] > 0 else ComplianceStatus.PARTIAL
        return status, evidence, gaps

    def _check_logging_requirements(
        self,
        agent_state: dict,
        oversight_caps: list[OversightCapability]
    ) -> tuple[ComplianceStatus, list[str], list[str]]:
        """Check if system logs activities for audit."""
        evidence = []
        gaps = []

        if agent_state.get("audit_log_enabled"):
            evidence.append("Audit logging is enabled")

        if agent_state.get("logs_retained_days", 0) >= 90:
            evidence.append(f"Logs retained for {agent_state.get('logs_retained_days')} days")
        else:
            gaps.append(f"Log retention {agent_state.get('logs_retained_days', 0)} days - EU AI Act may require longer")

        if agent_state.get("logs_include_decisions"):
            evidence.append("Decision logging enabled")
        else:
            gaps.append("Decision logging not enabled")

        status = ComplianceStatus.COMPLIANT if len(gaps) == 0 else ComplianceStatus.PARTIAL
        return status, evidence, gaps

    def _calculate_compliance_score(
        self,
        requirements: list[Article14Requirement]
    ) -> float:
        """Calculate overall compliance score (0.0 - 1.0)."""
        if not requirements:
            return 0.0

        total_weight = 0.0
        weighted_score = 0.0

        for req in requirements:
            weight = 1.0
            if req.status == ComplianceStatus.COMPLIANT:
                score = 1.0
            elif req.status == ComplianceStatus.PARTIAL:
                score = 0.5
            elif req.status == ComplianceStatus.NON_COMPLIANT:
                score = 0.0
            else:  # NOT_APPLICABLE
                weight = 0.0
                score = 1.0

            total_weight += weight
            weighted_score += weight * score

        return weighted_score / total_weight if total_weight > 0 else 0.0

    def generate_remediation_plan(
        self,
        assessment: "ComplianceAssessment"
    ) -> list[dict[str, str]]:
        """Generate a remediation plan for non-compliant requirements.

        Args:
            assessment: Compliance assessment from assess_compliance()

        Returns:
            List of remediation actions with priority and timeline
        """
        plan = []

        for req in assessment.requirements:
            if req.status in (ComplianceStatus.PARTIAL, ComplianceStatus.NON_COMPLIANT):
                for gap in req.gaps:
                    plan.append({
                        "requirement_id": req.requirement_id,
                        "gap": gap,
                        "priority": "high" if req.status == ComplianceStatus.NON_COMPLIANT else "medium",
                        "timeline": "immediate" if req.status == ComplianceStatus.NON_COMPLIANT else "30_days"
                    })

        # Sort by priority
        priority_order = {"high": 0, "medium": 1, "low": 2}
        plan.sort(key=lambda x: priority_order.get(x["priority"], 2))

        return plan


@dataclass
class ComplianceAssessment:
    """EU AI Act Article 14 compliance assessment result."""
    requirements: list[Article14Requirement]
    overall_score: float  # 0.0 to 1.0
    critical_gaps: list[Article14Requirement]
    assessed_at: datetime

    def to_dict(self) -> dict[str, Any]:
        """Convert assessment to dictionary for serialization."""
        return {
            "overall_score": self.overall_score,
            "requirements": [
                {
                    "id": r.requirement_id,
                    "title": r.title,
                    "status": r.status.name,
                    "evidence": r.evidence,
                    "gaps": r.gaps
                }
                for r in self.requirements
            ],
            "critical_gaps": [
                r.requirement_id for r in self.critical_gaps
            ],
            "assessed_at": self.assessed_at.isoformat()
        }

    def is_compliant(self, threshold: float = 0.8) -> bool:
        """Check if system meets compliance threshold."""
        return self.overall_score >= threshold