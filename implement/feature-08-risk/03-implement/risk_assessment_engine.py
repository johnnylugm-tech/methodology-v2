"""
Risk Assessment Engine [FR-R-12]

Main facade providing 8-dimensional risk evaluation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List
import time
import uuid

from config import RiskConfig
from decision_log import DecisionLog, DecisionInput
from confidence_calibration import ConfidenceCalibrator, CalibrationResult
from effort_tracker import EffortTracker
from alert_manager import AlertManager, Alert
from uqlm_integration import UQLMIntegration

from dimensions import (
    AbstractDimensionAssessor,
    DimensionResult,
    PrivacyAssessor,
    InjectionAssessor,
    CostAssessor,
    UAFClapAssessor,
    MemoryPoisoningAssessor,
    CrossAgentLeakAssessor,
    LatencyAssessor,
    ComplianceAssessor,
)


class RiskLevel(Enum):
    """Risk level classification."""
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class RiskAssessmentResult:
    """
    Result of a complete risk assessment.

    [FR-R-12]
    """

    assessment_id: str
    timestamp: str

    # Individual dimension scores
    dimension_scores: dict[str, float] = field(default_factory=dict)

    # Composite score
    composite_score: float = 0.0

    # Risk level
    risk_level: str = "LOW"

    # Alerts triggered
    alerts: list[Alert] = field(default_factory=list)

    # Recommendations
    recommendations: list[str] = field(default_factory=list)

    # Metadata
    dimensions_assessed: list[str] = field(default_factory=list)
    assessment_duration_ms: float = 0.0

    def to_dict(self) -> dict:
        return {
            "assessment_id": self.assessment_id,
            "timestamp": self.timestamp,
            "dimension_scores": self.dimension_scores,
            "composite_score": self.composite_score,
            "risk_level": self.risk_level,
            "alerts": [a.to_dict() for a in self.alerts],
            "recommendations": self.recommendations,
            "dimensions_assessed": self.dimensions_assessed,
            "assessment_duration_ms": self.assessment_duration_ms,
        }


class RiskAssessmentEngine:
    """
    Main risk assessment engine providing 8-dimensional risk evaluation.

    [FR-R-12]

    Coordinates:
    - 8 dimension assessors (D1-D8)
    - Decision log
    - Confidence calibration
    - Effort tracking
    - Alert management
    - UQLM integration
    """

    # Dimension ID to assessor class mapping
    DIMENSION_ASSESSORS = {
        "D1": PrivacyAssessor,
        "D2": InjectionAssessor,
        "D3": CostAssessor,
        "D4": UAFClapAssessor,
        "D5": MemoryPoisoningAssessor,
        "D6": CrossAgentLeakAssessor,
        "D7": LatencyAssessor,
        "D8": ComplianceAssessor,
    }

    # Default dimensions to assess
    DEFAULT_DIMENSIONS = ["D1", "D2", "D3", "D4", "D5", "D6", "D7", "D8"]

    def __init__(self, config: RiskConfig = None):
        """
        Initialize RiskAssessmentEngine.

        Args:
            config: RiskConfig object with thresholds, weights, and settings
        """
        self.config = config or RiskConfig()

        # Initialize components
        self.decision_log = DecisionLog(
            storage_path=self.config.decision_log_settings.get("storage_path", "memory/decisions")
        )

        self.uqlm_integration = UQLMIntegration(
            config=self.config.uqlm_settings
        )

        self.confidence_calibrator = ConfidenceCalibrator(
            uqlm_integration=self.uqlm_integration,
            config=self.config.uqlm_settings
        )

        self.effort_tracker = EffortTracker(
            config=self.config.effort_settings
        )

        self.alert_manager = AlertManager(
            config=self.config.alert_settings
        )

        # Initialize dimension assessors
        self._assessors: dict[str, AbstractDimensionAssessor] = {}
        for dim_id, assessor_class in self.DIMENSION_ASSESSORS.items():
            if self.config.is_dimension_enabled(dim_id):
                self._assessors[dim_id] = assessor_class()

    def assess_risk(
        self,
        context: dict,
        dimensions: List[str] = None
    ) -> RiskAssessmentResult:
        """
        Perform risk assessment on the given context.

        Args:
            context: Assessment context with relevant data
            dimensions: Optional list of specific dimensions to assess.
                       If None, all 8 dimensions are assessed.

        Returns:
            RiskAssessmentResult with scores, alerts, and recommendations
        """
        start_time = time.time()
        assessment_id = str(uuid.uuid4())[:8]

        # Determine which dimensions to assess
        dims_to_assess = dimensions if dimensions else self.DEFAULT_DIMENSIONS

        # Initialize dimension scores
        dimension_scores: dict[str, float] = {}
        dimension_results: dict[str, DimensionResult] = {}
        recommendations: list[str] = []

        # Assess each dimension
        for dim_id in dims_to_assess:
            if dim_id not in self._assessors:
                continue

            assessor = self._assessors[dim_id]
            result = assessor.assess_with_details(context)

            dimension_scores[dim_id] = result.score
            dimension_results[dim_id] = result

            # Generate recommendations for high-risk dimensions
            if result.score >= 0.6:
                recommendation = self._generate_recommendation(dim_id, result)
                recommendations.append(recommendation)

        # Calculate composite score
        composite_score = self._compute_composite_score(dimension_scores)

        # Determine risk level
        risk_level = self._determine_risk_level(composite_score)

        # Evaluate alerts
        alerts = self.alert_manager.evaluate(
            dimension_scores=dimension_scores,
            composite_score=composite_score,
            additional_context=context
        )

        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000

        return RiskAssessmentResult(
            assessment_id=assessment_id,
            timestamp=datetime.utcnow().isoformat(),
            dimension_scores=dimension_scores,
            composite_score=composite_score,
            risk_level=risk_level.value,
            alerts=alerts,
            recommendations=recommendations,
            dimensions_assessed=list(dims_to_assess),
            assessment_duration_ms=duration_ms,
        )

    def _compute_composite_score(self, dimension_scores: dict[str, float]) -> float:
        """
        Calculate weighted composite risk score.

        Formula: CRS = Σ(w_i × r_i) / Σ(w_i)

        Args:
            dimension_scores: Map of dimension ID to score

        Returns:
            Composite risk score (0.0-1.0)
        """
        if not dimension_scores:
            return 0.0

        weighted_sum = 0.0
        weight_sum = 0.0

        for dim_id, score in dimension_scores.items():
            weight = self.config.get_weight(dim_id)
            weighted_sum += weight * score
            weight_sum += weight

        if weight_sum == 0:
            return 0.0

        return weighted_sum / weight_sum

    def _determine_risk_level(self, composite_score: float) -> RiskLevel:
        """Determine risk level from composite score."""
        if composite_score >= self.config.get_threshold("critical"):
            return RiskLevel.CRITICAL
        elif composite_score >= self.config.get_threshold("high"):
            return RiskLevel.HIGH
        elif composite_score >= self.config.get_threshold("medium"):
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _generate_recommendation(self, dimension_id: str, result: DimensionResult) -> str:
        """Generate recommendation for a dimension."""
        recommendations = {
            "D1": "Review data privacy controls: encryption, access control, PII handling",
            "D2": "Strengthen input sanitization and validation to prevent injection attacks",
            "D3": "Optimize token usage: consider caching, batching, or streaming",
            "D4": "Implement depth limits and loop detection for agent interactions",
            "D5": "Verify memory sources and check for tampering indicators",
            "D6": "Review agent isolation and message sanitization between agents",
            "D7": "Investigate performance issues and optimize latency",
            "D8": "Review compliance requirements and ensure audit trail completeness",
        }
        base = recommendations.get(dimension_id, "Review and remediate")

        if result.score >= 0.8:
            return f"URGENT: {base}"
        return base

    def log_decision(self, decision: DecisionInput) -> str:
        """
        Log a planner decision to the decision log.

        Args:
            decision: DecisionInput to log

        Returns:
            decision_id: Unique identifier for the logged decision
        """
        return self.decision_log.append(decision)

    def calibrate_confidence(
        self,
        decision_id: str,
        actual_outcome: float
    ) -> CalibrationResult:
        """
        Perform post-hoc confidence calibration.

        Args:
            decision_id: The decision to calibrate
            actual_outcome: The actual outcome score (0.0-10.0)

        Returns:
            CalibrationResult with adjusted scores and alerts
        """
        # Get decision from log to retrieve initial confidence
        decision_record = self.decision_log.get(decision_id)
        if not decision_record:
            # Create a default result if decision not found
            return CalibrationResult(
                decision_id=decision_id,
                initial_confidence=5.0,
                actual_outcome=actual_outcome,
                calibrated_confidence=5.0,
                calibration_error=abs(5.0 - actual_outcome),
                calibration_status="unknown",
                adjustments_applied=["decision_not_found"],
            )

        initial_confidence = decision_record.confidence_score

        # Get UQLM uncertainty for context
        uqlm_uncertainty = self.uqlm_integration.get_uncertainty_score(
            {"decision_id": decision_id}
        )

        # Perform calibration
        result = self.confidence_calibrator.calibrate(
            decision_id=decision_id,
            initial_confidence=initial_confidence,
            actual_outcome=actual_outcome,
            uqlm_uncertainty=uqlm_uncertainty
        )

        # Update decision log with actual outcome
        decision_record.set_actual_outcome(actual_outcome)

        # Trigger alert if miscalibrated
        if result.calibration_status == "miscalibrated":
            self.alert_manager.trigger_confidence_mismatch(
                decision_id=decision_id,
                initial_confidence=initial_confidence,
                actual_outcome=actual_outcome,
                calibration_error=result.calibration_error
            )

        return result

    def track_effort(
        self,
        agent_id: str,
        task_id: str
    ) -> str:
        """
        Start effort tracking for an agent/task.

        Args:
            agent_id: Agent identifier
            task_id: Task identifier

        Returns:
            tracking_id for later reference
        """
        return self.effort_tracker.start_tracking(agent_id, task_id)

    def get_composite_risk_score(
        self,
        assessment: RiskAssessmentResult
    ) -> float:
        """
        Calculate composite risk score from dimension scores.

        Args:
            assessment: Completed risk assessment

        Returns:
            Composite risk score (0.0-1.0)
        """
        return self._compute_composite_score(assessment.dimension_scores)

    def get_dimension_assessor(self, dimension_id: str) -> Optional[AbstractDimensionAssessor]:
        """Get assessor for a specific dimension."""
        return self._assessors.get(dimension_id)

    def get_all_dimensions(self) -> list[str]:
        """Get list of all available dimension IDs."""
        return list(self._assessors.keys())

    def get_active_alerts(self, severity: str = None) -> list[Alert]:
        """Get currently active alerts."""
        return self.alert_manager.get_active_alerts(severity=severity)

    def acknowledge_alert(self, alert_id: str, by: str) -> bool:
        """Acknowledge an alert."""
        return self.alert_manager.acknowledge_alert(alert_id, by)

    def get_statistics(self) -> dict:
        """Get engine statistics."""
        return {
            "dimensions_enabled": list(self._assessors.keys()),
            "decision_log_count": self.decision_log.count(),
            "calibration_stats": self.confidence_calibrator.get_statistics(),
            "effort_stats": self.effort_tracker.get_statistics(),
            "alert_stats": self.alert_manager.to_dict(),
            "uqlm_stats": self.uqlm_integration.get_statistics(),
        }


def create_engine(config: RiskConfig = None) -> RiskAssessmentEngine:
    """
    Factory function to create a RiskAssessmentEngine.

    Args:
        config: Optional RiskConfig

    Returns:
        Configured RiskAssessmentEngine
    """
    return RiskAssessmentEngine(config=config)