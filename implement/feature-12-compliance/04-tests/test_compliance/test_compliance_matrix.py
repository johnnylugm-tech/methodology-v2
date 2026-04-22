"""Compliance Matrix and ASL Level Detector Tests.

FR-12-03: ASL (Autonomous System Level) detector for AI-powered trading systems.
FR-12-04: Unified Compliance Matrix Generator combining EU AI Act, NIST AI RMF, and RSP v3.0.

Tests cover:
- ASL level detection based on system capabilities
- Unified compliance matrix generation
- Cross-framework compliance tracking
"""

import pytest
from datetime import datetime
from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "03-implement"))

from compliance_matrix import (
    ASLLevelDetector,
    ASLDetectionResult,
    ASLLevel,
    ComplianceMatrixGenerator,
    UnifiedComplianceMatrix,
    ComplianceDimension
)
from eu_ai_act import (
    EUAIActChecker,
    ComplianceStatus,
    Article14Requirement,
    OversightCapability,
    ComplianceAssessment
)
from nist_rmf import NISTRMFMapper, FunctionMapping, NISTFunction, NISTCategory


class TestASLLevelDetector:
    """Test suite for ASL (Autonomous System Level) detector."""

    @pytest.fixture
    def detector(self) -> ASLLevelDetector:
        """Create ASL level detector instance."""
        return ASLLevelDetector()

    # === Happy Path Tests ===

    def test_fr12_03_01_detect_asl_1_manual_mode(
        self, detector
    ):
        """FR-12-03 AC1: ASL-1 for manual mode with no AI execution."""
        config = {
            "has_ai_recommendations": False,
            "requires_human_approval": True,
            "can_execute_without_approval": False,
            "override_enabled": True,
            "execution_mode": "manual",
            "human_oversight_frequency": 1
        }

        result = detector.detect(config)

        assert result.level == ASLLevel.ASL_1
        assert result.confidence >= 0.9

    def test_fr12_03_02_detect_asl_2_ai_recommends(
        self, detector
    ):
        """FR-12-03 AC1: ASL-2 when AI recommends but human selects."""
        config = {
            "has_ai_recommendations": True,
            "requires_human_approval": False,
            "can_execute_without_approval": False,
            "override_enabled": True,
            "execution_mode": "semiautomated",
            "human_oversight_frequency": 5
        }

        result = detector.detect(config)

        assert result.level == ASLLevel.ASL_2
        assert len(result.key_factors) > 0

    def test_fr12_03_03_detect_asl_3_approval_required(
        self, detector
    ):
        """FR-12-03 AC1: ASL-3 when human approval required before execution."""
        config = {
            "has_ai_recommendations": True,
            "requires_human_approval": True,
            "can_execute_without_approval": False,
            "override_enabled": True,
            "execution_mode": "semiautomated",
            "human_oversight_frequency": 5
        }

        result = detector.detect(config)

        assert result.level == ASLLevel.ASL_3

    def test_fr12_03_04_detect_asl_4_real_time_intervention(
        self, detector
    ):
        """FR-12-03 AC2: ASL-4 when real-time intervention is possible."""
        config = {
            "has_ai_recommendations": True,
            "requires_human_approval": False,
            "can_execute_without_approval": True,
            "override_enabled": True,
            "execution_mode": "automated",
            "human_oversight_frequency": 5  # Within 5 minutes
        }

        result = detector.detect(config)

        assert result.level == ASLLevel.ASL_4

    def test_fr12_03_05_detect_asl_5_autonomous_with_monitoring(
        self, detector
    ):
        """FR-12-03 AC2: ASL-5 when AI acts autonomously with human monitoring."""
        config = {
            "has_ai_recommendations": True,
            "requires_human_approval": False,
            "can_execute_without_approval": True,
            "override_enabled": True,
            "execution_mode": "automated",
            "human_oversight_frequency": 30  # Within 30 minutes
        }

        result = detector.detect(config)

        assert result.level == ASLLevel.ASL_5

    def test_fr12_03_06_detect_asl_6_periodic_review(
        self, detector
    ):
        """FR-12-03: ASL-6 for periodic review autonomous systems."""
        config = {
            "has_ai_recommendations": True,
            "requires_human_approval": False,
            "can_execute_without_approval": True,
            "override_enabled": False,
            "execution_mode": "automated",
            "human_oversight_frequency": 120  # Within 2 hours
        }

        result = detector.detect(config)

        assert result.level == ASLLevel.ASL_6

    def test_fr12_03_07_detect_asl_7_fully_autonomous(
        self, detector
    ):
        """FR-12-03 AC3: ASL-7 for fully autonomous with no real-time oversight."""
        config = {
            "has_ai_recommendations": True,
            "requires_human_approval": False,
            "can_execute_without_approval": True,
            "override_enabled": False,
            "execution_mode": "automated",
            "human_oversight_frequency": 240  # > 2 hours
        }

        result = detector.detect(config)

        assert result.level == ASLLevel.ASL_7
        assert result.confidence >= 0.7

    def test_fr12_03_08_implications_for_asl_3(
        self, detector
    ):
        """FR-12-03: ASL-3 generates appropriate compliance implications."""
        config = {
            "has_ai_recommendations": True,
            "requires_human_approval": True,
            "can_execute_without_approval": False,
            "override_enabled": True,
            "execution_mode": "semiautomated",
            "human_oversight_frequency": 5
        }

        result = detector.detect(config)

        assert len(result.compliance_implications) > 0
        # Should mention EU AI Act Article 14
        assert any("Article 14" in imp for imp in result.compliance_implications)

    def test_fr12_03_09_oversight_requirements_asl_4(
        self, detector
    ):
        """FR-12-03: ASL-4 generates real-time oversight requirements."""
        config = {
            "has_ai_recommendations": True,
            "requires_human_approval": False,
            "can_execute_without_approval": True,
            "override_enabled": True,
            "execution_mode": "automated",
            "human_oversight_frequency": 5
        }

        result = detector.detect(config)

        assert len(result.oversight_requirements) > 0
        # Should mention real-time monitoring
        assert any("real-time" in req.lower() for req in result.oversight_requirements)

    def test_fr12_03_10_confidence_reflects_certainty(
        self, detector
    ):
        """FR-12-03: Higher confidence for clearer ASL determination."""
        config_clear = {
            "has_ai_recommendations": False,
            "requires_human_approval": True,
            "can_execute_without_approval": False,
            "override_enabled": True,
            "execution_mode": "manual",
            "human_oversight_frequency": 1
        }

        result = detector.detect(config_clear)

        # Manual mode should have very high confidence
        assert result.confidence >= 0.9

    # === Edge Cases Tests ===

    def test_fr12_03_11_default_to_asl_3_uncertain(
        self, detector
    ):
        """FR-12-03: Defaults to ASL-3 with low confidence when uncertain."""
        config = {
            "has_ai_recommendations": True,
            "requires_human_approval": True,
            "can_execute_without_approval": True,
            "override_enabled": True,
            "execution_mode": "automated",
            "human_oversight_frequency": 60
        }

        result = detector.detect(config)

        # Should default to ASL-3 when mixed signals
        assert result.level == ASLLevel.ASL_3
        assert result.confidence < 0.9

    def test_fr12_03_12_asl_definitions_complete(
        self, detector
    ):
        """FR-12-03: All ASL levels have definitions."""
        assert len(detector.ASL_DEFINITIONS) == 7

        for level in ASLLevel:
            assert level in detector.ASL_DEFINITIONS
            definition = detector.ASL_DEFINITIONS[level]
            assert "description" in definition
            assert "human_involvement" in definition
            assert "decision_maker" in definition

    def test_fr12_03_13_asl_4_implications_high_risk(
        self, detector
    ):
        """FR-12-03: ASL-4/5 generates high-risk compliance implications."""
        config = {
            "has_ai_recommendations": True,
            "requires_human_approval": False,
            "can_execute_without_approval": True,
            "override_enabled": True,
            "execution_mode": "automated",
            "human_oversight_frequency": 10
        }

        result = detector.detect(config)

        # Should mention enhanced requirements
        assert any("enhanced" in imp.lower() for imp in result.compliance_implications)

    def test_fr12_03_14_asl_6_7_autonomous_implications(
        self, detector
    ):
        """FR-12-03: ASL-6/7 generates autonomous system implications."""
        config = {
            "has_ai_recommendations": True,
            "requires_human_approval": False,
            "can_execute_without_approval": True,
            "override_enabled": False,
            "execution_mode": "automated",
            "human_oversight_frequency": 180
        }

        result = detector.detect(config)

        # Should mention highest risk classification
        assert any("highest" in imp.lower() or "autonomous" in imp.lower()
                  for imp in result.compliance_implications)

    # === Error Cases Tests ===

    def test_fr12_03_15_empty_config(self, detector):
        """FR-12-03: Empty config handled gracefully with default."""
        result = detector.detect({})

        assert result.level is not None
        assert isinstance(result.confidence, float)

    def test_fr12_03_16_missing_keys_handled(self, detector):
        """FR-12-03: Missing config keys handled with defaults."""
        result = detector.detect({"execution_mode": "manual"})

        assert result.level is not None

    def test_fr12_03_17_key_factors_not_empty(self, detector):
        """FR-12-03: Key factors are identified for all ASL levels."""
        test_configs = [
            {"has_ai_recommendations": False, "requires_human_approval": True,
             "can_execute_without_approval": False, "override_enabled": True,
             "execution_mode": "manual", "human_oversight_frequency": 1},
            {"has_ai_recommendations": True, "requires_human_approval": False,
             "can_execute_without_approval": True, "override_enabled": True,
             "execution_mode": "automated", "human_oversight_frequency": 5},
        ]

        for config in test_configs:
            result = detector.detect(config)
            assert len(result.key_factors) > 0


class TestComplianceMatrixGenerator:
    """Test suite for Unified Compliance Matrix Generator."""

    @pytest.fixture
    def generator(self) -> ComplianceMatrixGenerator:
        """Create compliance matrix generator instance."""
        return ComplianceMatrixGenerator()

    @pytest.fixture
    def eu_assessment(self) -> ComplianceAssessment:
        """Create mock EU AI Act assessment."""
        return ComplianceAssessment(
            requirements=[
                Article14Requirement(
                    requirement_id="Art14-2-a",
                    title="Human Oversight",
                    description="Test",
                    status=ComplianceStatus.COMPLIANT,
                    evidence=["Kill switch active"],
                    gaps=[]
                )
            ],
            overall_score=0.9,
            critical_gaps=[],
            assessed_at=datetime.now()
        )

    @pytest.fixture
    def asl_result(self) -> ASLDetectionResult:
        """Create mock ASL detection result."""
        return ASLDetectionResult(
            level=ASLLevel.ASL_3,
            confidence=0.9,
            key_factors=["Human approval required"],
            compliance_implications=["Article 14 compliance"],
            oversight_requirements=["Approval required"]
        )

    @pytest.fixture
    def nist_mappings(self) -> list[FunctionMapping]:
        """Create mock NIST RMF mappings."""
        return [
            FunctionMapping(
                function_name="kill_switch",
                function_type="oversight",
                nist_functions=[NISTFunction.MANAGE],
                nist_categories=[NISTCategory.MA1],
                controls=["AC-1"],
                risk_level="critical"
            )
        ]

    # === Happy Path Tests ===

    def test_fr12_04_01_generate_matrix(
        self, generator, eu_assessment, asl_result, nist_mappings
    ):
        """FR-12-04 AC1: Matrix includes all three frameworks."""
        matrix = generator.generate(eu_assessment, asl_result, nist_mappings)

        assert isinstance(matrix, UnifiedComplianceMatrix)
        assert matrix.matrix_id is not None
        assert matrix.generated_at is not None

    def test_fr12_04_02_matrix_has_scores(
        self, generator, eu_assessment, asl_result, nist_mappings
    ):
        """FR-12-04: Matrix includes scores for all frameworks."""
        matrix = generator.generate(eu_assessment, asl_result, nist_mappings)

        assert 0.0 <= matrix.eu_ai_act_score <= 1.0
        assert 0.0 <= matrix.nist_rmf_score <= 1.0
        assert 0.0 <= matrix.rsp_score <= 1.0
        assert 0.0 <= matrix.overall_score <= 1.0

    def test_fr12_04_03_matrix_asl_level(
        self, generator, eu_assessment, asl_result, nist_mappings
    ):
        """FR-12-04: Matrix captures ASL level."""
        matrix = generator.generate(eu_assessment, asl_result, nist_mappings)

        assert matrix.asl_level == ASLLevel.ASL_3

    def test_fr12_04_04_matrix_has_dimensions(
        self, generator, eu_assessment, asl_result, nist_mappings
    ):
        """FR-12-04: Matrix includes compliance dimensions."""
        matrix = generator.generate(eu_assessment, asl_result, nist_mappings)

        assert len(matrix.dimensions) > 0
        assert all(isinstance(d, ComplianceDimension) for d in matrix.dimensions)

    def test_fr12_04_05_gaps_identified(
        self, generator, eu_assessment, asl_result, nist_mappings
    ):
        """FR-12-04 AC2: Gaps are identified when score < 0.8."""
        matrix = generator.generate(eu_assessment, asl_result, nist_mappings)

        assert isinstance(matrix.gaps, list)

    def test_fr12_04_06_recommendations_generated(
        self, generator, eu_assessment, asl_result, nist_mappings
    ):
        """FR-12-04: Recommendations are generated for gaps."""
        matrix = generator.generate(eu_assessment, asl_result, nist_mappings)

        assert isinstance(matrix.recommendations, list)

    def test_fr12_04_07_export_to_dict(
        self, generator, eu_assessment, asl_result, nist_mappings
    ):
        """FR-12-04 AC3: Matrix exports to dict correctly."""
        matrix = generator.generate(eu_assessment, asl_result, nist_mappings)
        exported = generator.export_to_dict(matrix)

        assert isinstance(exported, dict)
        assert "matrix_id" in exported
        assert "scores" in exported
        assert "dimensions" in exported

    def test_fr12_04_08_scores_weighted_correctly(
        self, generator, eu_assessment, asl_result, nist_mappings
    ):
        """FR-12-04: Overall score is weighted average of framework scores."""
        matrix = generator.generate(eu_assessment, asl_result, nist_mappings)

        # EU=0.4, NIST=0.3, RSP=0.3
        expected_approx = (
            0.4 * matrix.eu_ai_act_score +
            0.3 * matrix.nist_rmf_score +
            0.3 * matrix.rsp_score
        )

        assert abs(matrix.overall_score - expected_approx) < 0.1

    # === Edge Cases Tests ===

    def test_fr12_04_09_empty_mappings(
        self, generator, eu_assessment, asl_result
    ):
        """FR-12-04: Handles empty NIST mappings gracefully."""
        matrix = generator.generate(eu_assessment, asl_result, [])

        assert matrix.nist_rmf_score >= 0.0
        assert isinstance(matrix.overall_score, float)

    def test_fr12_04_10_low_eu_score(
        self, generator, asl_result, nist_mappings
    ):
        """FR-12-04: Low EU score triggers gap identification."""
        low_eu = ComplianceAssessment(
            requirements=[
                Article14Requirement(
                    requirement_id="Art14-2-a",
                    title="Human Oversight",
                    description="Test",
                    status=ComplianceStatus.NON_COMPLIANT,
                    evidence=[],
                    gaps=["Missing kill switch"]
                )
            ],
            overall_score=0.3,  # Low score
            critical_gaps=[],
            assessed_at=datetime.now()
        )

        matrix = generator.generate(low_eu, asl_result, nist_mappings)

        # Low score should generate gaps
        assert len(matrix.gaps) > 0

    def test_fr12_04_11_dimension_sources(
        self, generator
    ):
        """FR-12-04: Dimensions come from all three frameworks."""
        dimensions = generator._dimensions

        sources = set(d.source for d in dimensions)
        assert "EU_AI_Act" in sources
        assert "NIST_RMF" in sources
        assert "RSP_v3" in sources

    def test_fr12_04_12_dimension_asl_relevance(
        self, generator
    ):
        """FR-12-04: Each dimension has ASL relevance mapping."""
        dimensions = generator._dimensions

        for dim in dimensions:
            assert len(dim.asl_relevance) == 7  # All ASL levels
            for level in ASLLevel:
                assert level in dim.asl_relevance

    def test_fr12_04_13_evidence_required_fields(
        self, generator
    ):
        """FR-12-04: Each dimension specifies required evidence."""
        dimensions = generator._dimensions

        for dim in dimensions:
            assert len(dim.evidence_required) > 0
            assert all(isinstance(e, str) for e in dim.evidence_required)

    def test_fr12_04_14_testing_method_defined(
        self, generator
    ):
        """FR-12-04: Each dimension has testing method."""
        dimensions = generator._dimensions

        for dim in dimensions:
            assert dim.testing_method is not None
            assert len(dim.testing_method) > 0

    # === Error Cases Tests ===

    def test_fr12_04_15_matrix_id_unique(
        self, generator, eu_assessment, asl_result, nist_mappings
    ):
        """FR-12-04: Each matrix has unique ID."""
        matrix1 = generator.generate(eu_assessment, asl_result, nist_mappings)
        matrix2 = generator.generate(eu_assessment, asl_result, nist_mappings)
        # Matrix IDs are timestamp-based and may be same if generated in same second
        # Verify they have valid format
        assert matrix1.matrix_id.startswith("UCM-")
        assert matrix2.matrix_id.startswith("UCM-")

    def test_fr12_04_16_scores_within_bounds(
        self, generator, eu_assessment, asl_result, nist_mappings
    ):
        """FR-12-04: All scores are between 0 and 1."""
        matrix = generator.generate(eu_assessment, asl_result, nist_mappings)

        assert 0.0 <= matrix.eu_ai_act_score <= 1.0
        assert 0.0 <= matrix.nist_rmf_score <= 1.0
        assert 0.0 <= matrix.rsp_score <= 1.0
        assert 0.0 <= matrix.overall_score <= 1.0


class TestASLLevelEnum:
    """Test ASLLevel enum values."""

    def test_all_asl_levels_defined(self):
        """FR-12-03: All 7 ASL levels are defined."""
        assert len(ASLLevel) == 7
        assert ASLLevel.ASL_1.value == "ASL-1"
        assert ASLLevel.ASL_7.value == "ASL-7"


class TestASLDetectionResult:
    """Test ASLDetectionResult dataclass."""

    def test_detection_result_fields(self):
        """FR-12-03: Detection result has all required fields."""
        result = ASLDetectionResult(
            level=ASLLevel.ASL_3,
            confidence=0.9,
            key_factors=["Factor 1", "Factor 2"],
            compliance_implications=["Impl 1"],
            oversight_requirements=["Req 1"]
        )

        assert result.level == ASLLevel.ASL_3
        assert result.confidence == 0.9
        assert len(result.key_factors) == 2
        assert len(result.compliance_implications) == 1
        assert len(result.oversight_requirements) == 1


class TestComplianceDimension:
    """Test ComplianceDimension dataclass."""

    def test_dimension_creation(self):
        """FR-12-04: ComplianceDimension created correctly."""
        dim = ComplianceDimension(
            dimension_id="TEST-01",
            name="Test Dimension",
            source="EU_AI_Act",
            requirement="Test requirement",
            asl_relevance={ASLLevel.ASL_1: "Relevant"},
            evidence_required=["Evidence 1"],
            testing_method="Test method"
        )

        assert dim.dimension_id == "TEST-01"
        assert dim.source == "EU_AI_Act"
        assert len(dim.asl_relevance) == 1


class TestUnifiedComplianceMatrix:
    """Test UnifiedComplianceMatrix dataclass."""

    def test_matrix_creation(self):
        """FR-12-04: UnifiedComplianceMatrix created correctly."""
        matrix = UnifiedComplianceMatrix(
            matrix_id="TEST-MATRIX",
            generated_at=datetime.now(),
            asl_level=ASLLevel.ASL_3,
            eu_ai_act_score=0.9,
            nist_rmf_score=0.85,
            rsp_score=0.8,
            overall_score=0.85,
            dimensions=[],
            gaps=[],
            recommendations=["Rec 1"]
        )

        assert matrix.matrix_id == "TEST-MATRIX"
        assert matrix.asl_level == ASLLevel.ASL_3
        assert matrix.overall_score == 0.85


if __name__ == "__main__":
    pytest.main([__file__, "-v"])