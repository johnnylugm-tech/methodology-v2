"""
Tests for quality_gate/sensors/
ComputationalSensors Facade Pattern
"""

import pytest
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from quality_gate.sensors.module_weights import ModuleWeights
from quality_gate.sensors.sensors import ComputationalSensors, SensorResult, SensorReport


class TestModuleWeights:
    """Test ModuleWeights validation"""

    def test_default_weights_sum_to_one(self):
        """Default weights should sum to 1.0"""
        weights = ModuleWeights()
        total = weights.complexity + weights.coupling + weights.coverage + weights.maintainability
        assert abs(total - 1.0) < 0.001

    def test_custom_weights_must_sum_to_one(self):
        """Custom weights must sum to 1.0"""
        # Valid case
        weights = ModuleWeights(complexity=0.4, coupling=0.2, coverage=0.2, maintainability=0.2)
        assert abs(weights.complexity + weights.coupling + weights.coverage + weights.maintainability - 1.0) < 0.001

    def test_invalid_weights_raise_error(self):
        """Weights that don't sum to 1.0 should raise ValueError"""
        with pytest.raises(ValueError, match="Weights must sum to 1.0"):
            ModuleWeights(complexity=0.5, coupling=0.5, coverage=0.5, maintainability=0.5)

    def test_from_config(self):
        """Test creating weights from config dict"""
        config = {"complexity": 0.35, "coupling": 0.30, "coverage": 0.20, "maintainability": 0.15}
        weights = ModuleWeights.from_config(config)
        assert weights.complexity == 0.35
        assert weights.coupling == 0.30
        assert weights.coverage == 0.20
        assert weights.maintainability == 0.15

    def test_from_config_with_defaults(self):
        """Test from_config uses defaults for missing keys"""
        # All provided values must sum to 1.0 together
        config = {"complexity": 0.30, "coupling": 0.25, "coverage": 0.25}
        weights = ModuleWeights.from_config(config)
        assert weights.complexity == 0.30
        assert weights.coupling == 0.25
        assert weights.coverage == 0.25
        assert weights.maintainability == 0.20  # default

    def test_to_dict(self):
        """Test serializing weights to dict"""
        weights = ModuleWeights()
        d = weights.to_dict()
        assert d["complexity"] == 0.30
        assert d["coupling"] == 0.25
        assert d["coverage"] == 0.25
        assert d["maintainability"] == 0.20


class TestSensorResult:
    """Test SensorResult dataclass"""

    def test_sensor_result_creation(self):
        """Test creating SensorResult"""
        result = SensorResult(
            name="complexity",
            passed=True,
            score=0.85,
            details={"avg_cc": 8.5},
            violations=[]
        )
        assert result.name == "complexity"
        assert result.passed is True
        assert result.score == 0.85
        assert result.details["avg_cc"] == 8.5


class TestSensorReport:
    """Test SensorReport dataclass"""

    def test_sensor_report_creation(self):
        """Test creating SensorReport"""
        sensors = {
            "complexity": SensorResult(name="complexity", passed=True, score=0.8),
            "coupling": SensorResult(name="coupling", passed=True, score=0.75),
        }
        report = SensorReport(
            project_path="/test/project",
            timestamp="2024-01-01T00:00:00Z",
            passed=True,
            weighted_score=0.78,
            sensors=sensors,
            total_violations=0,
        )
        assert report.project_path == "/test/project"
        assert report.passed is True
        assert report.weighted_score == 0.78
        assert len(report.sensors) == 2

    def test_sensor_report_to_dict(self):
        """Test serializing SensorReport to dict"""
        sensors = {
            "complexity": SensorResult(name="complexity", passed=True, score=0.8),
        }
        report = SensorReport(
            project_path="/test/project",
            timestamp="2024-01-01T00:00:00Z",
            passed=True,
            weighted_score=0.8,
            sensors=sensors,
            total_violations=0,
        )
        d = report.to_dict()
        assert d["project_path"] == "/test/project"
        assert d["passed"] is True
        assert d["weighted_score"] == 0.8


class TestComputationalSensors:
    """Test ComputationalSensors Facade"""

    def test_init_with_defaults(self, tmp_path):
        """Test initializing sensors with default weights"""
        sensors = ComputationalSensors(project_path=str(tmp_path))
        assert sensors.project_path == tmp_path
        assert sensors.weights.complexity == 0.30
        assert sensors.weights.coupling == 0.25
        assert sensors.weights.coverage == 0.25
        assert sensors.weights.maintainability == 0.20

    def test_init_with_custom_weights(self, tmp_path):
        """Test initializing sensors with custom weights"""
        weights = ModuleWeights(complexity=0.4, coupling=0.3, coverage=0.2, maintainability=0.1)
        sensors = ComputationalSensors(project_path=str(tmp_path), weights=weights)
        assert sensors.weights.complexity == 0.4
        assert sensors.weights.coupling == 0.3
        assert sensors.weights.coverage == 0.2
        assert sensors.weights.maintainability == 0.1

    def test_scan_returns_sensor_report(self, tmp_path):
        """Test that scan() returns a SensorReport"""
        sensors = ComputationalSensors(project_path=str(tmp_path))
        report = sensors.scan()

        assert isinstance(report, SensorReport)
        assert report.project_path == str(tmp_path)
        assert isinstance(report.timestamp, str)
        assert isinstance(report.passed, bool)
        assert isinstance(report.weighted_score, float)
        assert isinstance(report.sensors, dict)
        assert isinstance(report.total_violations, int)

    def test_scan_includes_all_four_sensors(self, tmp_path):
        """Test that scan() includes all four sensors"""
        sensors = ComputationalSensors(project_path=str(tmp_path))
        report = sensors.scan()

        assert "complexity" in report.sensors
        assert "coupling" in report.sensors
        assert "coverage" in report.sensors
        assert "maintainability" in report.sensors

    def test_weighted_score_calculation(self, tmp_path):
        """Test that weighted_score is calculated correctly"""
        # Use uniform weights for easy verification
        weights = ModuleWeights(complexity=0.25, coupling=0.25, coverage=0.25, maintainability=0.25)
        sensors = ComputationalSensors(project_path=str(tmp_path), weights=weights)
        report = sensors.scan()

        expected = (
            report.sensors["complexity"].score * 0.25 +
            report.sensors["coupling"].score * 0.25 +
            report.sensors["coverage"].score * 0.25 +
            report.sensors["maintainability"].score * 0.25
        )

        assert abs(report.weighted_score - expected) < 0.001

    def test_sensor_results_have_required_fields(self, tmp_path):
        """Test that each sensor result has required fields"""
        sensors = ComputationalSensors(project_path=str(tmp_path))
        report = sensors.scan()

        for name, result in report.sensors.items():
            assert result.name == name
            assert isinstance(result.passed, bool)
            assert isinstance(result.score, float)
            assert 0.0 <= result.score <= 1.0
            assert isinstance(result.details, dict)
            assert isinstance(result.violations, list)

    def test_scan_on_empty_project(self, tmp_path):
        """Test scanning an empty project directory"""
        sensors = ComputationalSensors(project_path=str(tmp_path))
        report = sensors.scan()

        # Should complete without errors
        assert report.weighted_score >= 0.0
        assert report.total_violations >= 0

    def test_scan_with_python_files(self, tmp_path):
        """Test scanning a project with Python files"""
        # Create a simple Python file
        (tmp_path / "test_module.py").write_text("""
def hello():
    return "Hello World"

class MyClass:
    def method(self):
        pass
""")

        sensors = ComputationalSensors(project_path=str(tmp_path))
        report = sensors.scan()

        # Should detect complexity
        complexity_result = report.sensors["complexity"]
        assert isinstance(complexity_result.score, float)

        # Should calculate LOC
        maintainability_result = report.sensors["maintainability"]
        assert maintainability_result.details.get("LOC", 0) > 0


class TestComputationalSensorsEdgeCases:
    """Edge case tests for ComputationalSensors"""

    def test_invalid_weights_rejected_at_init(self, tmp_path):
        """Test that invalid weights are rejected when creating ModuleWeights"""
        # ModuleWeights itself raises on invalid sum
        with pytest.raises(ValueError):
            ModuleWeights(complexity=0.1, coupling=0.1, coverage=0.1, maintainability=0.1)


    def test_valid_weights_accepted_at_init(self, tmp_path):
        """"Test that valid weights are accepted"""
        weights = ModuleWeights(complexity=0.25, coupling=0.25, coverage=0.25, maintainability=0.25)
        sensors = ComputationalSensors(project_path=str(tmp_path), weights=weights)
        assert sensors.weights == weights

    def test_sensor_passed_threshold(self, tmp_path):
        """Test that sensors correctly set passed based on threshold"""
        # With default threshold of 0.7, sensors with score >= 0.7 should pass
        sensors = ComputationalSensors(project_path=str(tmp_path))
        report = sensors.scan()

        for name, result in report.sensors.items():
            if result.score >= 0.7:
                assert result.passed is True
            else:
                assert result.passed is False

    def test_report_passed_is_based_on_weighted_score(self, tmp_path):
        """Test that report.passed is based on weighted_score >= 0.7"""
        sensors = ComputationalSensors(project_path=str(tmp_path))
        report = sensors.scan()

        if report.weighted_score >= 0.7:
            assert report.passed is True
        else:
            assert report.passed is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
