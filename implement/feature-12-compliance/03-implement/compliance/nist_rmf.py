"""NIST AI RMF Function Mapper.

FR-12-02: Maps trading system functions to NIST AI Risk Management Framework
(AI RMF 1.0) functions and categories.

NIST AI RMF Functions:
    - GOVERN ( GOVERN ): Establish and maintain AI risk management processes
    - MAP ( MAP ): Contextualize AI risks based on intended use
    - MEASURE ( MEASURE ): Analyze identified AI risks
    - MANAGE ( MANAGE ): Prioritize and act on AI risks

References:
    - NIST AI RMF v1.0 (NIST AI 100-1)
    - ISO/IEC 42001 (AI MS)
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Optional

# NIST AI RMF Function identifiers
class NISTFunction(Enum):
    """NIST AI RMF core functions."""
    GOVERN = "Govern"
    MAP = "Map"
    MEASURE = "Measure"
    MANAGE = "Manage"


class NISTCategory(Enum):
    """NIST AI RMF categories within each function."""
    # GOVERN categories
    G1 = "Organizational Context"
    G2 = "Leadership and Organizational Structure"
    G3 = "Risk Management Strategy"
    G4 = "AI Inventory"
    G5 = "AI Risk Management Processes"

    # MAP categories
    M1 = "Use Case Context"
    M2 = "Stakeholder Engagement"
    M3 = "AI System Purpose and Scope"
    M4 = "System Description"
    M5 = "Commercial Foundation"
    M6 = "Intended Benefits and Harms"

    # MEASURE categories
    ME1 = "Risk Measurement"
    ME2 = "Risk Analysis"
    ME3 = "AI System Impact"

    # MANAGE categories
    MA1 = "Risk Treatment"
    MA2 = "Incident Management"
    MA3 = "Continuous Monitoring"


@dataclass
class FunctionMapping:
    """Maps a trading function to NIST AI RMF categories."""
    function_name: str
    function_type: str  # e.g., "trading", "risk_management", "oversight"
    nist_functions: list[NISTFunction]
    nist_categories: list[NISTCategory]
    controls: list[str]  # Control identifiers
    risk_level: str  # critical, high, medium, low
    notes: str = ""


@dataclass
class AICapability:
    """Represents an AI system capability mapped to NIST functions."""
    capability_id: str
    name: str
    description: str
    nist_functions: list[NISTFunction]
    nist_categories: list[NISTCategory]
    potential_harms: list[str] = field(default_factory=list)
    mitigations: list[str] = field(default_factory=list)
    performance_metrics: dict[str, float] = field(default_factory=dict)


class NISTRMFMapper:
    """Maps trading system functions to NIST AI RMF structure.

    This mapper provides a standardized way to:
    1. Categorize trading system functions under NIST AI RMF
    2. Identify relevant controls and risk levels
    3. Generate compliance evidence for audits

    Example:
        mapper = NISTRMFMapper()
        mappings = mapper.map_trading_functions(trading_system_config)
        report = mapper.generate_rmf_report(mappings)
    """

    # Pre-defined mappings for common trading functions
    TRADING_FUNCTION_MAPPINGS: dict[str, FunctionMapping] = {
        "order_routing": FunctionMapping(
            function_name="order_routing",
            function_type="trading",
            nist_functions=[NISTFunction.MAP, NISTFunction.MANAGE],
            nist_categories=[NISTCategory.M1, NISTCategory.MA1],
            controls=["AC-1", "AC-2", "RA-1"],
            risk_level="high",
            notes="Direct market access - critical for financial harm mitigation"
        ),
        "position_sizing": FunctionMapping(
            function_name="position_sizing",
            function_type="risk_management",
            nist_functions=[NISTFunction.GOVERN, NISTFunction.MANAGE],
            nist_categories=[NISTCategory.G5, NISTCategory.MA1],
            controls=["RA-1", "RA-3", "ID-1"],
            risk_level="critical",
            notes="Directly affects portfolio risk exposure"
        ),
        "strategy_execution": FunctionMapping(
            function_name="strategy_execution",
            function_type="trading",
            nist_functions=[NISTFunction.MAP, NISTFunction.MEASURE],
            nist_categories=[NISTCategory.M1, NISTCategory.ME2],
            controls=["AC-1", "AC-3", "SI-1"],
            risk_level="high",
            notes="Automated strategy execution requires oversight"
        ),
        "risk_limit_enforcement": FunctionMapping(
            function_name="risk_limit_enforcement",
            function_type="risk_management",
            nist_functions=[NISTFunction.GOVERN, NISTFunction.MANAGE],
            nist_categories=[NISTCategory.G3, NISTCategory.MA1],
            controls=["RA-2", "RA-3", "IR-1"],
            risk_level="critical",
            notes="Core risk control - must be fail-safe"
        ),
        "kill_switch": FunctionMapping(
            function_name="kill_switch",
            function_type="oversight",
            nist_functions=[NISTFunction.MANAGE],
            nist_categories=[NISTCategory.MA1, NISTCategory.MA3],
            controls=["AC-1", "IR-1", "IR-2"],
            risk_level="critical",
            notes="Emergency stop - highest priority control"
        ),
        "human_override": FunctionMapping(
            function_name="human_override",
            function_type="oversight",
            nist_functions=[NISTFunction.GOVERN, NISTFunction.MANAGE],
            nist_categories=[NISTCategory.G5, NISTCategory.MA1],
            controls=["AC-1", "AC-2", "IA-1"],
            risk_level="high",
            notes="Manual intervention capability for Article 14 compliance"
        ),
        "market_data_analysis": FunctionMapping(
            function_name="market_data_analysis",
            function_type="trading",
            nist_functions=[NISTFunction.MAP, NISTFunction.MEASURE],
            nist_categories=[NISTCategory.M1, NISTCategory.ME1],
            controls=["RA-1", "SI-1"],
            risk_level="medium",
            notes="Input processing - impacts decision quality"
        ),
        "portfolio_optimization": FunctionMapping(
            function_name="portfolio_optimization",
            function_type="trading",
            nist_functions=[NISTFunction.MEASURE, NISTFunction.MANAGE],
            nist_categories=[NISTCategory.ME2, NISTCategory.MA1],
            controls=["RA-3", "AC-1"],
            risk_level="high",
            notes="Portfolio-level decisions require governance"
        ),
        "compliance_monitoring": FunctionMapping(
            function_name="compliance_monitoring",
            function_type="oversight",
            nist_functions=[NISTFunction.GOVERN, NISTFunction.MEASURE],
            nist_categories=[NISTCategory.G5, NISTCategory.ME3],
            controls=["AC-2", "AC-3", "RA-1"],
            risk_level="critical",
            notes="Regulatory compliance - requires audit trail"
        ),
        "audit_logging": FunctionMapping(
            function_name="audit_logging",
            function_type="oversight",
            nist_functions=[NISTFunction.GOVERN, NISTFunction.MEASURE],
            nist_categories=[NISTCategory.G5, NISTCategory.ME3],
            controls=["AU-1", "AU-2", "AU-6"],
            risk_level="high",
            notes="Required for regulatory compliance and incident investigation"
        ),
    }

    # NIST AI RMF control families relevant to trading
    CONTROL_FAMILIES = {
        "AC": "Access Control",
        "RA": "Risk Assessment",
        "ID": "Identification and Authentication",
        "IR": "Incident Response",
        "AU": "Audit and Accountability",
        "SI": "System and Information Integrity",
        "MA": "Maintenance",
        "SC": "System and Communications Protection",
        "SI": "System and Information Integrity"
    }

    def __init__(self):
        """Initialize NIST AI RMF mapper."""
        self._custom_mappings: dict[str, FunctionMapping] = {}

    def map_trading_functions(
        self,
        system_config: dict[str, Any]
    ) -> list[FunctionMapping]:
        """Map trading system functions to NIST AI RMF.

        Args:
            system_config: Configuration dict with keys:
                - enabled_functions: list of function names
                - custom_functions: optional dict of custom FunctionMapping

        Returns:
            List of FunctionMapping objects for enabled functions
        """
        enabled = system_config.get("enabled_functions", [])
        custom = system_config.get("custom_functions", {})

        mappings = []

        for func_name in enabled:
            if func_name in self.TRADING_FUNCTION_MAPPINGS:
                mappings.append(self.TRADING_FUNCTION_MAPPINGS[func_name])
            elif func_name in custom:
                # Use custom mapping if provided
                self._custom_mappings[func_name] = custom[func_name]
                mappings.append(custom[func_name])

        return mappings

    def map_ai_capability(
        self,
        capability: AICapability
    ) -> dict[NISTFunction, list[NISTCategory]]:
        """Map an AI capability to NIST functions and categories.

        Args:
            capability: AICapability to map

        Returns:
            Dict mapping each NIST function to relevant categories
        """
        result: dict[NISTFunction, list[NISTCategory]] = {
            NISTFunction.GOVERN: [],
            NISTFunction.MAP: [],
            NISTFunction.MEASURE: [],
            NISTFunction.MANAGE: []
        }

        for func in capability.nist_functions:
            result[func].extend(capability.nist_categories)

        # Remove duplicates per function
        for func in result:
            result[func] = list(set(result[func]))

        return result

    def generate_rmf_report(
        self,
        mappings: list[FunctionMapping]
    ) -> dict[str, Any]:
        """Generate NIST AI RMF compliance report.

        Args:
            mappings: List of function mappings

        Returns:
            Report dict with function categorization and risk summary
        """
        by_function: dict[str, dict] = {}
        by_nist_function: dict[str, list] = {
            "Govern": [],
            "Map": [],
            "Measure": [],
            "Manage": []
        }

        risk_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        all_controls: set[str] = set()

        for mapping in mappings:
            by_function[mapping.function_name] = {
                "type": mapping.function_type,
                "risk_level": mapping.risk_level,
                "nist_functions": [f.value for f in mapping.nist_functions],
                "nist_categories": [c.value for c in mapping.nist_categories],
                "controls": mapping.controls,
                "notes": mapping.notes
            }

            for func in mapping.nist_functions:
                by_nist_function[func.value].append(mapping.function_name)

            risk_counts[mapping.risk_level] += 1
            all_controls.update(mapping.controls)

        return {
            "report_date": datetime.now().isoformat(),
            "function_count": len(mappings),
            "by_function": by_function,
            "by_nist_function": by_nist_function,
            "risk_distribution": risk_counts,
            "controls_required": sorted(list(all_controls)),
            "critical_functions": [
                m.function_name for m in mappings
                if m.risk_level == "critical"
            ]
        }

    def get_govern_controls(
        self,
        mappings: list[FunctionMapping]
    ) -> list[str]:
        """Get all GOVERN function controls from mappings."""
        gov_functions = [NISTFunction.GOVERN]
        controls = []
        for mapping in mappings:
            if any(f in gov_functions for f in mapping.nist_functions):
                controls.extend(mapping.controls)
        return sorted(list(set(controls)))

    def get_manage_controls(
        self,
        mappings: list[FunctionMapping]
    ) -> list[str]:
        """Get all MANAGE function controls from mappings."""
        manage_functions = [NISTFunction.MANAGE]
        controls = []
        for mapping in mappings:
            if any(f in manage_functions for f in mapping.nist_functions):
                controls.extend(mapping.controls)
        return sorted(list(set(controls)))