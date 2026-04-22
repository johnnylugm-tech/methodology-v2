"""NIST AI RMF Function Mapper Tests.

FR-12-02: Maps trading system functions to NIST AI Risk Management Framework
(AI RMF 1.0) functions and categories.

Tests cover:
- GOVERN: Establish and maintain AI risk management processes
- MAP: Contextualize AI risks based on intended use
- MEASURE: Analyze identified AI risks
- MANAGE: Prioritize and act on AI risks
"""

import pytest
from typing import Any

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "03-implement"))

from compliance.nist_rmf import (
    NISTRMFMapper,
    NISTFunction,
    NISTCategory,
    FunctionMapping,
    AICapability
)


class TestNISTRMFMapper:
    """Test suite for NIST AI RMF function mapper."""

    @pytest.fixture
    def mapper(self) -> NISTRMFMapper:
        """Create NIST RMF mapper instance."""
        return NISTRMFMapper()

    @pytest.fixture
    def full_system_config(self) -> dict[str, Any]:
        """System config with all trading functions enabled."""
        return {
            "enabled_functions": [
                "order_routing",
                "position_sizing",
                "strategy_execution",
                "risk_limit_enforcement",
                "kill_switch",
                "human_override",
                "market_data_analysis",
                "portfolio_optimization",
                "compliance_monitoring",
                "audit_logging"
            ]
        }

    @pytest.fixture
    def minimal_system_config(self) -> dict[str, Any]:
        """Minimal system config with only essential functions."""
        return {
            "enabled_functions": [
                "kill_switch",
                "human_override",
                "audit_logging"
            ]
        }

    # === Happy Path Tests ===

    def test_fr12_02_01_map_trading_functions_full(
        self, mapper, full_system_config
    ):
        """FR-12-02 AC1: All enabled functions are mapped."""
        mappings = mapper.map_trading_functions(full_system_config)

        assert len(mappings) == 10
        assert all(isinstance(m, FunctionMapping) for m in mappings)

    def test_fr12_02_02_map_trading_functions_minimal(
        self, mapper, minimal_system_config
    ):
        """FR-12-02 AC1: Minimal config maps successfully."""
        mappings = mapper.map_trading_functions(minimal_system_config)

        assert len(mappings) == 3
        function_names = [m.function_name for m in mappings]
        assert "kill_switch" in function_names
        assert "human_override" in function_names
        assert "audit_logging" in function_names

    def test_fr12_02_03_kill_switch_mapped_to_manage(
        self, mapper
    ):
        """FR-12-02 AC1: kill_switch maps to MANAGE function."""
        config = {"enabled_functions": ["kill_switch"]}
        mappings = mapper.map_trading_functions(config)

        kill_switch_mapping = mappings[0]
        assert NISTFunction.MANAGE in kill_switch_mapping.nist_functions
        assert kill_switch_mapping.risk_level == "critical"

    def test_fr12_02_04_govern_controls_extracted(
        self, mapper, full_system_config
    ):
        """FR-12-02 AC2: GOVERN function controls are extracted."""
        mappings = mapper.map_trading_functions(full_system_config)
        gov_controls = mapper.get_govern_controls(mappings)

        assert isinstance(gov_controls, list)
        assert len(gov_controls) > 0
        # Controls should be sorted
        assert gov_controls == sorted(gov_controls)

    def test_fr12_02_05_manage_controls_extracted(
        self, mapper, full_system_config
    ):
        """FR-12-02 AC2: MANAGE function controls are extracted."""
        mappings = mapper.map_trading_functions(full_system_config)
        manage_controls = mapper.get_manage_controls(mappings)

        assert isinstance(manage_controls, list)
        assert len(manage_controls) > 0
        # Controls should be sorted
        assert manage_controls == sorted(manage_controls)

    def test_fr12_02_06_generate_rmf_report_structure(
        self, mapper, full_system_config
    ):
        """FR-12-02 AC3: RMF report has correct structure."""
        mappings = mapper.map_trading_functions(full_system_config)
        report = mapper.generate_rmf_report(mappings)

        assert "report_date" in report
        assert "function_count" in report
        assert "by_function" in report
        assert "by_nist_function" in report
        assert "risk_distribution" in report
        assert "controls_required" in report

    def test_fr12_02_07_rmf_report_nist_functions(
        self, mapper, full_system_config
    ):
        """FR-12-02 AC1: Each NIST function has mapped functions."""
        mappings = mapper.map_trading_functions(full_system_config)
        report = mapper.generate_rmf_report(mappings)

        by_nist = report["by_nist_function"]
        assert "Govern" in by_nist
        assert "Map" in by_nist
        assert "Measure" in by_nist
        assert "Manage" in by_nist

        # Each function should have at least one mapped function
        for func_name, func_list in by_nist.items():
            assert len(func_list) > 0

    def test_fr12_02_08_risk_distribution(
        self, mapper, full_system_config
    ):
        """FR-12-02: Risk distribution calculated correctly."""
        mappings = mapper.map_trading_functions(full_system_config)
        report = mapper.generate_rmf_report(mappings)

        risk_dist = report["risk_distribution"]
        assert "critical" in risk_dist
        assert "high" in risk_dist
        assert "medium" in risk_dist
        assert "low" in risk_dist

        # Total should match function count
        total = sum(risk_dist.values())
        assert total == report["function_count"]

    def test_fr12_02_09_critical_functions_identified(
        self, mapper, full_system_config
    ):
        """FR-12-02: Critical functions are identified in report."""
        mappings = mapper.map_trading_functions(full_system_config)
        report = mapper.generate_rmf_report(mappings)

        critical = report["critical_functions"]
        assert isinstance(critical, list)
        # kill_switch, position_sizing, risk_limit_enforcement should be critical
        assert "kill_switch" in critical
        assert "position_sizing" in critical

    def test_fr12_02_10_map_ai_capability(
        self, mapper
    ):
        """FR-12-02: AI capability maps to correct NIST functions."""
        capability = AICapability(
            capability_id="cap-001",
            name="Sentiment Analysis",
            description="Analyzes news sentiment for trading signals",
            nist_functions=[NISTFunction.MAP, NISTFunction.MEASURE],
            nist_categories=[NISTCategory.M1, NISTCategory.ME1],
            potential_harms=["False signals", "Over-trading"],
            mitigations=["Confidence thresholds", "Human approval"]
        )

        result = mapper.map_ai_capability(capability)

        assert NISTFunction.MAP in result
        assert NISTFunction.MEASURE in result
        assert NISTCategory.M1 in result[NISTFunction.MAP]
        assert NISTCategory.ME1 in result[NISTFunction.MEASURE]

    # === Edge Cases Tests ===

    def test_fr12_02_11_empty_config(self, mapper):
        """FR-12-02: Empty config returns empty mappings."""
        config = {"enabled_functions": []}
        mappings = mapper.map_trading_functions(config)

        assert len(mappings) == 0

    def test_fr12_02_12_unknown_function_handled(
        self, mapper
    ):
        """FR-12-02: Unknown function names are silently ignored."""
        config = {"enabled_functions": ["kill_switch", "unknown_function_xyz"]}
        mappings = mapper.map_trading_functions(config)

        assert len(mappings) == 1
        assert mappings[0].function_name == "kill_switch"

    def test_fr12_02_13_custom_function_mapping(
        self, mapper
    ):
        """FR-12-02: Custom function mapping is used when provided."""
        custom_mapping = FunctionMapping(
            function_name="custom_trading",
            function_type="trading",
            nist_functions=[NISTFunction.MANAGE],
            nist_categories=[NISTCategory.MA1],
            controls=["AC-1"],
            risk_level="medium"
        )

        config = {
            "enabled_functions": ["custom_trading"],
            "custom_functions": {
                "custom_trading": custom_mapping
            }
        }

        mappings = mapper.map_trading_functions(config)

        assert len(mappings) == 1
        assert mappings[0].function_name == "custom_trading"
        assert mappings[0].risk_level == "medium"

    def test_fr12_02_14_rmf_report_empty_mappings(
        self, mapper
    ):
        """FR-12-02: Report generation with empty mappings."""
        report = mapper.generate_rmf_report([])

        assert report["function_count"] == 0
        assert report["risk_distribution"] == {"critical": 0, "high": 0, "medium": 0, "low": 0}
        assert len(report["controls_required"]) == 0

    def test_fr12_02_15_all_nist_functions_mapped(
        self, mapper, full_system_config
    ):
        """FR-12-02 AC1: All four NIST functions have coverage."""
        mappings = mapper.map_trading_functions(full_system_config)
        report = mapper.generate_rmf_report(mappings)

        by_nist = report["by_nist_function"]

        # All four functions should be represented
        assert len(by_nist["Govern"]) > 0
        assert len(by_nist["Map"]) > 0
        assert len(by_nist["Measure"]) > 0
        assert len(by_nist["Manage"]) > 0

    def test_fr12_02_16_control_families_defined(
        self, mapper
    ):
        """FR-12-02: NIST control families are defined."""
        families = mapper.CONTROL_FAMILIES

        assert "AC" in families  # Access Control
        assert "RA" in families  # Risk Assessment
        assert "AU" in families  # Audit and Accountability
        assert "IR" in families  # Incident Response

    def test_fr12_02_17_controls_are_sorted_unique(
        self, mapper, full_system_config
    ):
        """FR-12-02: Controls returned are sorted and unique."""
        mappings = mapper.map_trading_functions(full_system_config)
        all_controls = mapper.get_govern_controls(mappings)

        # All controls should be unique
        assert len(all_controls) == len(set(all_controls))
        # Should be sorted
        assert all_controls == sorted(all_controls)

    # === Error Cases Tests ===

    def test_fr12_02_18_missing_enabled_functions_key(
        self, mapper
    ):
        """FR-12-02: Missing enabled_functions key handled gracefully."""
        config = {}  # No enabled_functions key
        mappings = mapper.map_trading_functions(config)

        assert len(mappings) == 0

    def test_fr12_02_19_ai_capability_no_functions(
        self, mapper
    ):
        """FR-12-02: AI capability with no functions handled."""
        capability = AICapability(
            capability_id="cap-002",
            name="Empty Capability",
            description="No NIST functions assigned",
            nist_functions=[],
            nist_categories=[]
        )

        result = mapper.map_ai_capability(capability)

        # Should return empty lists for all functions
        assert result[NISTFunction.GOVERN] == []
        assert result[NISTFunction.MAP] == []
        assert result[NISTFunction.MEASURE] == []
        assert result[NISTFunction.MANAGE] == []

    def test_fr12_02_20_function_mapping_notes(
        self, mapper
    ):
        """FR-12-02: Function mappings include notes for audit."""
        config = {"enabled_functions": ["kill_switch"]}
        mappings = mapper.map_trading_functions(config)

        assert mappings[0].notes != ""
        assert len(mappings[0].notes) > 10  # Notes should be descriptive

    def test_fr12_02_21_risk_level_values(
        self, mapper, full_system_config
    ):
        """FR-12-02: Risk levels are valid values."""
        mappings = mapper.map_trading_functions(full_system_config)
        valid_levels = {"critical", "high", "medium", "low"}

        for mapping in mappings:
            assert mapping.risk_level in valid_levels

    def test_fr12_02_22_report_date_is_iso_format(
        self, mapper, full_system_config
    ):
        """FR-12-02: Report date is in ISO format."""
        mappings = mapper.map_trading_functions(full_system_config)
        report = mapper.generate_rmf_report(mappings)

        # Should be parseable as ISO datetime
        from datetime import datetime
        parsed = datetime.fromisoformat(report["report_date"])
        assert parsed is not None

    def test_fr12_02_23_function_type_classification(
        self, mapper
    ):
        """FR-12-02: Functions are classified by type."""
        config = {"enabled_functions": ["order_routing", "kill_switch"]}
        mappings = mapper.map_trading_functions(config)

        for mapping in mappings:
            assert mapping.function_type in ["trading", "risk_management", "oversight"]


class TestNISTFunctionEnum:
    """Test NISTFunction enum values."""

    def test_all_nist_functions_defined(self):
        """FR-12-02: All four NIST AI RMF functions are defined."""
        assert NISTFunction.GOVERN.value == "Govern"
        assert NISTFunction.MAP.value == "Map"
        assert NISTFunction.MEASURE.value == "Measure"
        assert NISTFunction.MANAGE.value == "Manage"


class TestNISTCategoryEnum:
    """Test NISTCategory enum values."""

    def test_govern_categories(self):
        """FR-12-02: GOVERN function categories are defined."""
        gov_categories = [
            NISTCategory.G1, NISTCategory.G2, NISTCategory.G3,
            NISTCategory.G4, NISTCategory.G5
        ]
        assert len(gov_categories) == 5

    def test_map_categories(self):
        """FR-12-02: MAP function categories are defined."""
        map_categories = [
            NISTCategory.M1, NISTCategory.M2, NISTCategory.M3,
            NISTCategory.M4, NISTCategory.M5, NISTCategory.M6
        ]
        assert len(map_categories) == 6

    def test_measure_categories(self):
        """FR-12-02: MEASURE function categories are defined."""
        measure_categories = [
            NISTCategory.ME1, NISTCategory.ME2, NISTCategory.ME3
        ]
        assert len(measure_categories) == 3

    def test_manage_categories(self):
        """FR-12-02: MANAGE function categories are defined."""
        manage_categories = [
            NISTCategory.MA1, NISTCategory.MA2, NISTCategory.MA3
        ]
        assert len(manage_categories) == 3


class TestFunctionMapping:
    """Test FunctionMapping dataclass."""

    def test_function_mapping_creation(self):
        """FR-12-02: FunctionMapping created with all fields."""
        mapping = FunctionMapping(
            function_name="test_function",
            function_type="trading",
            nist_functions=[NISTFunction.GOVERN, NISTFunction.MANAGE],
            nist_categories=[NISTCategory.G1, NISTCategory.MA1],
            controls=["AC-1", "RA-1"],
            risk_level="high",
            notes="Test notes"
        )

        assert mapping.function_name == "test_function"
        assert mapping.function_type == "trading"
        assert len(mapping.nist_functions) == 2
        assert len(mapping.nist_categories) == 2
        assert len(mapping.controls) == 2
        assert mapping.risk_level == "high"
        assert mapping.notes == "Test notes"


class TestAICapability:
    """Test AICapability dataclass."""

    def test_ai_capability_creation(self):
        """FR-12-02: AICapability created with all fields."""
        capability = AICapability(
            capability_id="test-cap",
            name="Test Capability",
            description="A test capability",
            nist_functions=[NISTFunction.MAP],
            nist_categories=[NISTCategory.M1],
            potential_harms=["Harm1"],
            mitigations=["Mit1"],
            performance_metrics={"accuracy": 0.95}
        )

        assert capability.capability_id == "test-cap"
        assert capability.name == "Test Capability"
        assert len(capability.potential_harms) == 1
        assert len(capability.mitigations) == 1
        assert capability.performance_metrics["accuracy"] == 0.95


if __name__ == "__main__":
    pytest.main([__file__, "-v"])