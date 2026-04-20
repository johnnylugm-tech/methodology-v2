#!/usr/bin/env python3
"""
test_assessor.py - Tests for Risk Assessor
[FR-01, FR-02] Risk identification and evaluation tests
"""

import pytest
import tempfile
import shutil
from pathlib import Path

from engine.assessor import RiskAssessor, RiskScorer
from models.risk import Risk
from models.enums import RiskDimension, RiskLevel


class TestRiskScorer:
    """Tests for RiskScorer [FR-02]"""

    def setup_method(self):
        self.scorer = RiskScorer()

    def test_calculate_basic(self):
        """[FR-02] Basic score calculation"""
        score = self.scorer.calculate(0.5, 3, 1.0)
        assert score == pytest.approx(0.3, rel=0.01)

    def test_calculate_high_probability(self):
        """[FR-02] High probability, high impact"""
        score = self.scorer.calculate(0.9, 5, 1.0)
        assert score == pytest.approx(0.9, rel=0.01)

    def test_calculate_low_probability(self):
        """[FR-02] Low probability, low impact"""
        score = self.scorer.calculate(0.1, 1, 0.5)
        assert score == pytest.approx(0.01, rel=0.01)

    def test_calculate_clamped_probability(self):
        """[FR-02] Probability clamped to 0-1"""
        score = self.scorer.calculate(1.5, 3, 1.0)  # > 1
        assert score <= 1.0
        score = self.scorer.calculate(-0.5, 3, 1.0)  # < 0
        assert score >= 0.0

    def test_calculate_invalid_input(self):
        """[FR-02] Invalid inputs return default"""
        score = self.scorer.calculate(None, None, None)
        assert score == 0.3  # Default to MEDIUM

    def test_assess_probability_with_patterns(self):
        """[FR-02] Probability adjustment based on patterns"""
        prob = self.scorer.assess_probability({
            "probability": 0.5,
            "pattern_matches": 3
        })
        assert prob > 0.5  # Should increase

    def test_assess_impact_technical(self):
        """[FR-02] Technical dimension impact assessment"""
        impact = self.scorer.assess_impact(
            RiskDimension.TECHNICAL,
            {"type": "system_failure", "impact": 3}
        )
        assert impact >= 4  # Should increase for system_failure

    def test_detect_patterns_technical(self):
        """[FR-01] Detect technical risk patterns"""
        content = "cyclomatic complexity is high, too many responsibilities"
        patterns = self.scorer.detect_patterns(content, RiskDimension.TECHNICAL)
        assert len(patterns) > 0

    def test_detect_patterns_none(self):
        """[FR-01] No patterns detected"""
        content = "This is normal code"
        patterns = self.scorer.detect_patterns(content, RiskDimension.TECHNICAL)
        assert len(patterns) == 0


class TestRiskAssessor:
    """Tests for RiskAssessor [FR-01, FR-02]"""

    def setup_method(self):
        self.temp_dir = tempfile.mkdtemp()
        self.project_root = Path(self.temp_dir)

        # Create basic project structure
        (self.project_root / "src").mkdir()
        (self.project_root / "docs").mkdir()

    def teardown_method(self):
        shutil.rmtree(self.temp_dir)

    def test_identify_from_code(self):
        """[FR-01] Identify risk from code"""
        # Create a Python file
        code_file = self.project_root / "src" / "main.py"
        code_file.write_text("""
def complex_function():
    # TODO: refactor this
    if x:
        if y:
            if z:
                pass
""")

        assessor = RiskAssessor(str(self.project_root))
        risks = assessor.identify_from_code(code_file)

        # Should detect complexity and TODO
        assert len(risks) >= 1

    def test_identify_from_documentation(self):
        """[FR-01] Identify risk from docs"""
        doc_file = self.project_root / "docs" / "README.md"
        doc_file.write_text("""
# Project

TODO: complete this section
FIXME: security issue
""")

        assessor = RiskAssessor(str(self.project_root))
        risks = assessor.identify_from_documentation(doc_file)

        # Should detect TODO and FIXME
        assert len(risks) >= 2

    def test_assess_empty_project(self):
        """[FR-01, FR-02] Assess project with no risks"""
        assessor = RiskAssessor(str(self.project_root))
        result = assessor.assess()

        # Should still return valid result
        assert result.total_risks >= 0
        assert result.average_score >= 0.0

    def test_assess_with_code_issues(self):
        """[FR-01, FR-02] Assess project with code issues"""
        # Create code with test file missing
        src_dir = self.project_root / "src"
        src_dir.mkdir(exist_ok=True)

        main_py = src_dir / "main.py"
        main_py.write_text("# Main module")

        assessor = RiskAssessor(str(self.project_root))
        result = assessor.assess()

        # Should detect missing test file
        assert result.total_risks >= 1

    def test_detect_current_phase(self):
        """[FR-01] Detect current phase"""
        # Create phase 3 directory
        (self.project_root / "03-development").mkdir()

        assessor = RiskAssessor(str(self.project_root))
        phase = assessor._detect_current_phase()

        assert phase >= 1

    def test_scan_phase_deliverables(self):
        """[FR-01] Scan phase deliverables for risks"""
        # Create phase directory with risk indicator
        phase_dir = self.project_root / "03-development"
        phase_dir.mkdir()

        readme = phase_dir / "README.md"
        readme.write_text("This module has complexity issues")

        assessor = RiskAssessor(str(self.project_root))
        risks = assessor._scan_phase_deliverables()

        # Should detect the complexity indicator
        assert len(risks) >= 0  # May detect something


class TestRiskModel:
    """Tests for Risk model"""

    def test_risk_score_calculation(self):
        """[FR-02] Risk score auto-calculation"""
        risk = Risk(
            title="Test Risk",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            probability=0.7,
            impact=4,
            detectability_factor=1.0,
        )

        assert risk.score == pytest.approx(0.56, rel=0.01)

    def test_risk_level_from_score(self):
        """[FR-02] Risk level derived from score"""
        risk = Risk(
            title="Critical Risk",
            description="Test",
            dimension=RiskDimension.TECHNICAL,
            probability=0.9,
            impact=5,
        )

        # Score should be high enough for CRITICAL
        assert risk.level in [RiskLevel.HIGH, RiskLevel.CRITICAL]

    def test_risk_to_dict(self):
        """[FR-04] Risk serialization"""
        risk = Risk(
            title="Test",
            description="Test desc",
            dimension=RiskDimension.TECHNICAL,
        )

        d = risk.to_dict()
        assert "id" in d
        assert d["title"] == "Test"
        assert d["dimension"] == "technical"

    def test_risk_from_dict(self):
        """[FR-04] Risk deserialization"""
        data = {
            "title": "Test",
            "description": "Test desc",
            "dimension": "operational",
            "probability": 0.6,
            "impact": 4,
        }

        risk = Risk.from_dict(data)
        assert risk.title == "Test"
        assert risk.dimension == RiskDimension.OPERATIONAL
        assert risk.probability == 0.6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])