"""Unified Compliance Matrix and ASL Level Detector.

FR-12-03: ASL Level Detector for AI-powered trading systems
FR-12-04: Unified Compliance Matrix Generator

This module provides:
1. ASL (Autonomous System Level) detection based on system capabilities
2. Unified compliance matrix mapping EU AI Act, NIST AI RMF, and RSP v3.0

References:
    - RSP v3.0 (RSK Process Standard)
    - EU AI Act (Regulation 2024/1689)
    - NIST AI RMF v1.0 (NIST AI 100-1)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional

from .eu_ai_act import ComplianceStatus
from .nist_rmf import NISTRMFMapper, NISTFunction, NISTCategory


class ASLLevel(Enum):
    """Autonomous System Level (ASL) as per RSP v3.0.

    ASL 1-3: Human involved (human in the loop)
    ASL 4-5: Human on the loop (supervisory)
    ASL 6-7: Fully autonomous (human out of the loop)
    """
    ASL_1 = "ASL-1"  # Human executes all actions
    ASL_2 = "ASL-2"  # Human selects from AI recommendations
    ASL_3 = "ASL-3"  # Human approves AI-suggested actions
    ASL_4 = "ASL-4"  # AI acts, human can intervene
    ASL_5 = "ASL-5"  # AI acts autonomously, human monitors
    ASL_6 = "ASL-6"  # AI acts autonomously, periodic human check
    ASL_7 = "ASL-7"  # Fully autonomous, no human involvement


@dataclass
class ASLDetectionResult:
    """Result of ASL level detection."""
    level: ASLLevel
    confidence: float  # 0.0 to 1.0
    key_factors: list[str]
    compliance_implications: list[str]
    oversight_requirements: list[str]


@dataclass
class ComplianceDimension:
    """A single compliance dimension in the unified matrix."""
    dimension_id: str
    name: str
    source: str  # "EU_AI_Act", "NIST_RMF", "RSP_v3"
    requirement: str
    asl_relevance: dict[ASLLevel, str]  # How this applies at each ASL level
    evidence_required: list[str]
    testing_method: str


@dataclass
class UnifiedComplianceMatrix:
    """Unified compliance matrix across all frameworks."""
    matrix_id: str
    generated_at: datetime
    asl_level: ASLLevel
    eu_ai_act_score: float
    nist_rmf_score: float
    rsp_score: float
    overall_score: float
    dimensions: list[ComplianceDimension]
    gaps: list[dict[str, str]]
    recommendations: list[str]


class ASLLevelDetector:
    """Detects the ASL (Autonomous System Level) of a trading system.

    ASL detection is based on:
    1. Decision authority - who makes the final decision
    2. Execution speed - time from signal to action
    3. Human oversight - type and frequency of human involvement
    4. Override capability - can humans override AI actions

    Example:
        detector = ASLLevelDetector()
        result = detector.detect(agent_config)
        print(f"ASL Level: {result.level.value}")
    """

    # ASL level definitions based on RSP v3.0
    ASL_DEFINITIONS = {
        ASLLevel.ASL_1: {
            "description": "Human executes all actions - AI only provides analysis",
            "human_involvement": "complete",
            "decision_maker": "human",
            "override_capability": "not_applicable"
        },
        ASLLevel.ASL_2: {
            "description": "AI recommends actions, human selects from options",
            "human_involvement": "selective",
            "decision_maker": "human",
            "override_capability": "implicit"
        },
        ASLLevel.ASL_3: {
            "description": "AI suggests actions, human must approve before execution",
            "human_involvement": "approval_required",
            "decision_maker": "human",
            "override_capability": "explicit"
        },
        ASLLevel.ASL_4: {
            "description": "AI executes actions, human can intervene in real-time",
            "human_involvement": "intervention_possible",
            "decision_maker": "ai",
            "override_capability": "real_time"
        },
        ASLLevel.ASL_5: {
            "description": "AI acts autonomously, human monitors and can intervene",
            "human_involvement": "monitoring",
            "decision_maker": "ai",
            "override_capability": "delayed"
        },
        ASLLevel.ASL_6: {
            "description": "AI acts autonomously, periodic human review",
            "human_involvement": "periodic_review",
            "decision_maker": "ai",
            "override_capability": "none_in_real_time"
        },
        ASLLevel.ASL_7: {
            "description": "Fully autonomous, no human involvement in decisions",
            "human_involvement": "none",
            "decision_maker": "ai",
            "override_capability": "none"
        }
    }

    def detect(
        self,
        system_config: dict[str, Any],
        agent_state: Optional[dict[str, Any]] = None
    ) -> ASLDetectionResult:
        """Detect the ASL level of a trading system.

        Args:
            system_config: System configuration including:
                - has_ai_recommendations: bool
                - requires_human_approval: bool
                - can_execute_without_approval: bool
                - override_enabled: bool
                - execution_mode: "manual" | "semiautomated" | "automated"
                - human_oversight_frequency: int  # minutes between oversight checks
            agent_state: Optional current agent state for verification

        Returns:
            ASLDetectionResult with detected level and confidence
        """
        # Determine key factors
        has_ai = system_config.get("has_ai_recommendations", False)
        requires_approval = system_config.get("requires_human_approval", True)
        can_execute_auto = system_config.get("can_execute_without_approval", False)
        override_enabled = system_config.get("override_enabled", True)
        exec_mode = system_config.get("execution_mode", "manual")
        oversight_freq = system_config.get("human_oversight_frequency", 60)

        # Determine ASL level
        level, confidence, factors = self._determine_asl(
            has_ai, requires_approval, can_execute_auto,
            override_enabled, exec_mode, oversight_freq
        )

        # Generate compliance implications
        implications = self._generate_implications(level, system_config)

        # Generate oversight requirements
        oversight_reqs = self._generate_oversight_requirements(level, system_config)

        return ASLDetectionResult(
            level=level,
            confidence=confidence,
            key_factors=factors,
            compliance_implications=implications,
            oversight_requirements=oversight_reqs
        )

    def _determine_asl(
        self,
        has_ai: bool,
        requires_approval: bool,
        can_execute_auto: bool,
        override_enabled: bool,
        exec_mode: str,
        oversight_freq: int
    ) -> tuple[ASLLevel, float, list[str]]:
        """Determine ASL level based on system characteristics.

        Returns:
            Tuple of (ASLLevel, confidence, key_factors)
        """
        factors = []
        confidence = 0.8  # Base confidence

        # ASL 1: Manual, no AI execution
        if exec_mode == "manual" and not has_ai:
            factors.append("Manual execution mode, AI for analysis only")
            return ASLLevel.ASL_1, 0.95, factors

        # ASL 2: AI recommends, human selects
        # (only when requires_approval is False - checked after ASL-3)
        if has_ai and not requires_approval and not can_execute_auto:
            factors.append("AI provides recommendations, human makes final selection")
            return ASLLevel.ASL_2, 0.85, factors

        # ASL 3: AI suggests, human approves
        if has_ai and requires_approval and not can_execute_auto:
            factors.append("AI suggests actions, human approval required before execution")
            return ASLLevel.ASL_3, 0.9, factors

        # ASL 4: AI executes, human can intervene
        if has_ai and can_execute_auto and override_enabled and oversight_freq <= 5:
            factors.append("AI executes actions, human intervention possible in real-time")
            return ASLLevel.ASL_4, 0.85, factors

        # ASL 5: AI autonomous, human monitors
        if has_ai and can_execute_auto and override_enabled and oversight_freq <= 30:
            factors.append("AI acts autonomously, human monitors and can intervene")
            return ASLLevel.ASL_5, 0.8, factors

        # ASL 6: AI autonomous, periodic review
        if has_ai and can_execute_auto and not override_enabled and oversight_freq <= 120:
            factors.append("AI acts autonomously, periodic human review only")
            return ASLLevel.ASL_6, 0.75, factors

        # ASL 7: Fully autonomous
        if has_ai and can_execute_auto and not override_enabled and oversight_freq > 120:
            factors.append("Fully autonomous operation, no real-time human oversight")
            return ASLLevel.ASL_7, 0.7, factors

        # Default to ASL 3 if uncertain
        factors.append("Default classification based on mixed signals")
        return ASLLevel.ASL_3, 0.6, factors

    def _generate_implications(
        self,
        level: ASLLevel,
        config: dict[str, Any]
    ) -> list[str]:
        """Generate compliance implications for detected ASL level."""
        implications = []

        if level in (ASLLevel.ASL_1, ASLLevel.ASL_2, ASLLevel.ASL_3):
            implications.append("EU AI Act Article 14(2)(d): Human override capability required")
            implications.append("EU AI Act Article 14(4): Training requirements apply")
            implications.append("Lower risk classification under EU AI Act Annex III")

        if level in (ASLLevel.ASL_4, ASLLevel.ASL_5):
            implications.append("EU AI Act Article 14: Enhanced oversight requirements")
            implications.append("NIST AI RMF MANAGE function controls required")
            implications.append("RSP v3.0 ASL 4-5 compliance documentation required")

        if level in (ASLLevel.ASL_6, ASLLevel.ASL_7):
            implications.append("Highest risk classification under EU AI Act")
            implications.append("Article 14 compliance may require system redesign")
            implications.append("NIST AI RMF GOVERN controls required for autonomous systems")
            implications.append("RSP v3.0 audit trail requirements apply")

        return implications

    def _generate_oversight_requirements(
        self,
        level: ASLLevel,
        config: dict[str, Any]
    ) -> list[str]:
        """Generate oversight requirements for detected ASL level."""
        requirements = []

        if level == ASLLevel.ASL_1:
            requirements.append("No automated execution allowed")
            requirements.append("Human reviews AI recommendations before any action")

        if level == ASLLevel.ASL_2:
            requirements.append("Human selects from AI-generated options")
            requirements.append("AI cannot execute without human selection")

        if level == ASLLevel.ASL_3:
            requirements.append("Human approval required before any execution")
            requirements.append("Approval timeout shall not exceed 5 minutes for time-sensitive trades")

        if level == ASLLevel.ASL_4:
            requirements.append("Real-time monitoring dashboard required")
            requirements.append("Human can intervene within 1 minute")
            requirements.append("Override capability must be tested weekly")

        if level == ASLLevel.ASL_5:
            requirements.append("Automated monitoring with alerts")
            requirements.append("Human can intervene within 10 minutes")
            requirements.append("Daily review of automated decisions")

        if level == ASLLevel.ASL_6:
            requirements.append("Periodic review interval ≤ 4 hours")
            requirements.append("Audit log review required")
            requirements.append("Performance metrics reporting")

        if level == ASLLevel.ASL_7:
            requirements.append("System qualifies as fully autonomous")
            requirements.append("Enhanced documentation required")
            requirements.append("Independent audit required")
            requirements.append("Kill switch must be accessible within 30 seconds")

        return requirements


class ComplianceMatrixGenerator:
    """Generates unified compliance matrices across EU AI Act, NIST AI RMF, and RSP v3.0.

    Example:
        generator = ComplianceMatrixGenerator()
        eu_checker = EUAIActChecker()
        nist_mapper = NISTRMFMapper()
        asl_detector = ASLLevelDetector()

        # Get inputs
        eu_assessment = eu_checker.assess_compliance(agent_state, oversight_caps)
        asl_result = asl_detector.detect(system_config)
        nist_mappings = nist_mapper.map_trading_functions(config)

        # Generate matrix
        matrix = generator.generate(eu_assessment, asl_result, nist_mappings)
    """

    def __init__(self):
        """Initialize compliance matrix generator."""
        self._dimensions: list[ComplianceDimension] = []
        self._init_default_dimensions()

    def _init_default_dimensions(self):
        """Initialize default compliance dimensions from all frameworks."""
        self._dimensions = [
            ComplianceDimension(
                dimension_id="EU-AI-14-2-a",
                name="Human Oversight Measures",
                source="EU_AI_Act",
                requirement="Art 14(2)(a): Appropriate oversight measures",
                asl_relevance={
                    ASLLevel.ASL_1: "Full human control",
                    ASLLevel.ASL_2: "Human selects AI recommendations",
                    ASLLevel.ASL_3: "Human approval required",
                    ASLLevel.ASL_4: "Real-time intervention capability",
                    ASLLevel.ASL_5: "Monitoring with intervention ability",
                    ASLLevel.ASL_6: "Periodic review sufficient",
                    ASLLevel.ASL_7: "System designed for autonomous operation"
                },
                evidence_required=[
                    "Oversight mechanism documentation",
                    "Human-AI interaction logs",
                    "Intervention capability test results"
                ],
                testing_method="Functional testing + human factors evaluation"
            ),
            ComplianceDimension(
                dimension_id="EU-AI-14-2-b",
                name="System Output Explainability",
                source="EU_AI_Act",
                requirement="Art 14(2)(b): Operators understand system outputs",
                asl_relevance={
                    ASLLevel.ASL_1: "High importance - human executes based on AI output",
                    ASLLevel.ASL_2: "High importance - human selects from AI output",
                    ASLLevel.ASL_3: "Medium importance - human approves AI output",
                    ASLLevel.ASL_4: "Medium importance - human monitors AI output",
                    ASLLevel.ASL_5: "Lower importance - human reviews periodically",
                    ASLLevel.ASL_6: "Lower importance - audit-based review",
                    ASLLevel.ASL_7: "Minimal importance - system operates autonomously"
                },
                evidence_required=[
                    "Decision reasoning documentation",
                    "Confidence score output",
                    "Alternative options explanation"
                ],
                testing_method="Explainability audit + operator comprehension test"
            ),
            ComplianceDimension(
                dimension_id="EU-AI-14-2-d",
                name="Human Override Capability",
                source="EU_AI_Act",
                requirement="Art 14(2)(d): Operators can override AI decisions",
                asl_relevance={
                    ASLLevel.ASL_1: "Not applicable - human makes all decisions",
                    ASLLevel.ASL_2: "Implicit - human can choose not to follow",
                    ASLLevel.ASL_3: "Explicit approval required",
                    ASLLevel.ASL_4: "Real-time override capability required",
                    ASLLevel.ASL_5: "Override capability required",
                    ASLLevel.ASL_6: "Override may not be required if periodic review adequate",
                    ASLLevel.ASL_7: "Override capability may be infeasible"
                },
                evidence_required=[
                    "Override mechanism documentation",
                    "Override capability test results",
                    "Response time measurements"
                ],
                testing_method="Override capability testing with timing measurement"
            ),
            ComplianceDimension(
                dimension_id="NIST-GOVERN-G5",
                name="AI Risk Management Processes",
                source="NIST_RMF",
                requirement="GOVERN: Establish AI risk management processes",
                asl_relevance={asl: "Risk management processes apply to all ASL levels"
                              for asl in ASLLevel},
                evidence_required=[
                    "Risk management documentation",
                    "Process implementation evidence",
                    "Regular review records"
                ],
                testing_method="Process audit + documentation review"
            ),
            ComplianceDimension(
                dimension_id="NIST-MAP-M1",
                name="Use Case Context",
                source="NIST_RMF",
                requirement="MAP: Contextualize risks based on use case",
                asl_relevance={asl: "Context analysis required for all levels"
                              for asl in ASLLevel},
                evidence_required=[
                    "Use case documentation",
                    "Contextual risk assessment",
                    "Stakeholder requirements"
                ],
                testing_method="Requirements traceability review"
            ),
            ComplianceDimension(
                dimension_id="RSP-ASL-COMPLIANCE",
                name="ASL Compliance Requirements",
                source="RSP_v3",
                requirement="RSP v3.0: Autonomous system level compliance",
                asl_relevance={asl: f"Level-specific requirements for {asl.value}"
                              for asl in ASLLevel},
                evidence_required=[
                    "ASL classification documentation",
                    "Level-specific requirement compliance",
                    "Oversight mechanism records"
                ],
                testing_method="ASL classification verification + requirements check"
            )
        ]

    def generate(
        self,
        eu_assessment: "ComplianceAssessment",
        asl_result: ASLDetectionResult,
        nist_mappings: list["FunctionMapping"]
    ) -> UnifiedComplianceMatrix:
        """Generate unified compliance matrix.

        Args:
            eu_assessment: EU AI Act compliance assessment
            asl_result: ASL detection result
            nist_mappings: NIST AI RMF function mappings

        Returns:
            UnifiedComplianceMatrix with all framework alignments
        """
        gaps = []
        recommendations = []

        # Calculate dimension scores
        for dim in self._dimensions:
            score = self._calculate_dimension_score(dim, eu_assessment, asl_result, nist_mappings)

            # Identify gaps
            if score < 0.8:
                gaps.append({
                    "dimension_id": dim.dimension_id,
                    "name": dim.name,
                    "score": score,
                    "reason": f"Score {score:.1%} below 80% threshold"
                })
                recommendations.append(
                    f"Address {dim.name}: Implement {', '.join(dim.evidence_required[:2])}"
                )

        # Calculate framework scores
        eu_score = eu_assessment.overall_score
        nist_score = self._calculate_nist_score(nist_mappings)
        rsp_score = self._calculate_rsp_score(asl_result.level)

        # Overall score (weighted average)
        overall = 0.4 * eu_score + 0.3 * nist_score + 0.3 * rsp_score

        return UnifiedComplianceMatrix(
            matrix_id=f"UCM-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            generated_at=datetime.now(),
            asl_level=asl_result.level,
            eu_ai_act_score=eu_score,
            nist_rmf_score=nist_score,
            rsp_score=rsp_score,
            overall_score=overall,
            dimensions=self._dimensions,
            gaps=gaps,
            recommendations=recommendations
        )

    def _calculate_dimension_score(
        self,
        dim: ComplianceDimension,
        eu_assessment: "ComplianceAssessment",
        asl_result: ASLDetectionResult,
        nist_mappings: list
    ) -> float:
        """Calculate compliance score for a dimension."""
        base_score = 0.7  # Start at 70%

        # Adjust based on dimension source
        if dim.source == "EU_AI_Act":
            for req in eu_assessment.requirements:
                if req.requirement_id.startswith("Art14"):
                    if req.status == ComplianceStatus.COMPLIANT:
                        base_score += 0.05
                    elif req.status == ComplianceStatus.NON_COMPLIANT:
                        base_score -= 0.15

        elif dim.source == "NIST_RMF":
            # NIST score based on function mappings
            relevant_funcs = sum(1 for m in nist_mappings
                              if any(c.value == dim.dimension_id for c in m.nist_categories))
            if nist_mappings:
                coverage = relevant_funcs / len(nist_mappings)
                base_score = 0.5 + 0.4 * coverage

        elif dim.source == "RSP_v3":
            # RSP score based on ASL level
            asl_level_num = int(asl_result.level.value.split("-")[1])
            # Higher ASL = more stringent requirements
            asl_factor = min(asl_level_num * 0.1, 0.7)
            base_score = 0.3 + asl_factor

        return max(0.0, min(1.0, base_score))

    def _calculate_nist_score(self, mappings: list) -> float:
        """Calculate NIST AI RMF compliance score."""
        if not mappings:
            return 0.0

        # Score based on control coverage
        all_controls = set()
        for m in mappings:
            all_controls.update(m.controls)

        # Simple coverage metric (would be more complex in production)
        return min(1.0, len(all_controls) / 10.0)  # Expect at least 10 controls

    def _calculate_rsp_score(self, level: ASLLevel) -> float:
        """Calculate RSP v3.0 compliance score based on ASL level."""
        # Higher ASL levels have more stringent requirements
        level_num = int(level.value.split("-")[1])
        return min(1.0, level_num / 7.0)

    def export_to_dict(self, matrix: UnifiedComplianceMatrix) -> dict[str, Any]:
        """Export compliance matrix to dictionary for serialization."""
        return {
            "matrix_id": matrix.matrix_id,
            "generated_at": matrix.generated_at.isoformat(),
            "asl_level": matrix.asl_level.value,
            "scores": {
                "eu_ai_act": matrix.eu_ai_act_score,
                "nist_rmf": matrix.nist_rmf_score,
                "rsp_v3": matrix.rsp_score,
                "overall": matrix.overall_score
            },
            "dimensions": [
                {
                    "id": d.dimension_id,
                    "name": d.name,
                    "source": d.source
                }
                for d in matrix.dimensions
            ],
            "gaps": matrix.gaps,
            "recommendations": matrix.recommendations
        }