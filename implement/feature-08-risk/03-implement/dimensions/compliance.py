"""
D8: Compliance Risk Assessor [FR-R-8]

Evaluates risk of regulatory or policy violations.
"""

from __future__ import annotations

from typing import Optional

from . import AbstractDimensionAssessor, DimensionResult


class ComplianceAssessor(AbstractDimensionAssessor):
    """
    D8: Compliance Risk Assessor [FR-R-8]

    Assessment Factors:
    - Regulatory framework alignment (GDPR, CCPA, SOC2, etc.)
    - Policy violation detection
    - Audit trail completeness
    - Data residency requirements
    """

    REGULATORY_FRAMEWORKS = [
        "GDPR", "CCPA", "HIPAA", "SOC2", "ISO27001", "PCI-DSS", "SOX", "FedRAMP"
    ]

    def assess(self, context: dict) -> float:
        """
        Calculate compliance risk score.

        Args:
            context: Must contain compliance context

        Returns:
            Risk score 0.0-1.0
        """
        # Regulatory alignment score (inverted)
        regulatory_alignment = context.get("regulatory_alignment_score", 1.0)
        regulatory_score = (1 - regulatory_alignment) * 0.35

        # Policy violation score
        policy_violation_score = self._detect_policy_violations(context) * 0.30

        # Audit trail completeness (inverted)
        audit_trail_completeness = context.get("audit_trail_completeness", 1.0)
        audit_trail_score = (1 - audit_trail_completeness) * 0.20

        # Data residency score
        residency_score = self._check_data_residency_requirements(context) * 0.15

        return regulatory_score + policy_violation_score + audit_trail_score + residency_score

    def _detect_policy_violations(self, context: dict) -> float:
        """Detect policy violations."""
        violations = context.get("policy_violations", [])
        if not violations:
            return 0.0

        # Weight by severity
        severity_weights = {
            "critical": 1.0,
            "high": 0.7,
            "medium": 0.4,
            "low": 0.2,
        }

        total_risk = 0.0
        for violation in violations:
            severity = violation.get("severity", "medium").lower()
            weight = severity_weights.get(severity, 0.3)
            total_risk += weight

        return min(1.0, total_risk)

    def _check_data_residency_requirements(self, context: dict) -> float:
        """Check data residency compliance."""
        required_regions = context.get("required_data_regions", [])
        current_region = context.get("data_region", "unknown")

        if not required_regions:
            return 0.0  # No residency requirements

        if current_region in required_regions:
            return 0.0  # Compliant

        # Cross-border data transfer risk
        transfer_compliance = context.get("cross_border_transfer_compliant", False)
        if transfer_compliance:
            return 0.3  # Compliant with safeguards

        return 0.8  # Non-compliant

    def get_dimension_id(self) -> str:
        return "D8"

    def assess_with_details(self, context: dict) -> DimensionResult:
        """Perform detailed compliance risk assessment."""
        evidence = []

        regulatory_alignment = context.get("regulatory_alignment_score", 1.0)
        evidence.append(f"Regulatory alignment: {regulatory_alignment:.0%}")

        required_regions = context.get("required_data_regions", [])
        if required_regions:
            current_region = context.get("data_region", "unknown")
            evidence.append(f"Data region: {current_region} (required: {', '.join(required_regions)})")

        audit_completeness = context.get("audit_trail_completeness", 1.0)
        evidence.append(f"Audit trail completeness: {audit_completeness:.0%}")

        warnings = []
        violations = context.get("policy_violations", [])
        if violations:
            warnings.append(f"Policy violations: {len(violations)}")

        metadata = {
            "regulatory_frameworks": context.get("applicable_frameworks", []),
            "violation_count": len(violations),
        }

        score = self.assess(context)
        return DimensionResult(
            dimension_id=self.get_dimension_id(),
            score=score,
            evidence=evidence,
            metadata=metadata,
            warnings=warnings,
        )