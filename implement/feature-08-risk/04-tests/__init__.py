"""
Tests Package for Feature #8: Risk Assessment

This package contains TDD tests for the Risk Assessment Engine
covering all 8 dimensions (D1-D8) and supporting components.

Test Structure:
- test_config.py: Configuration profiles and factory functions
- test_risk_assessment_engine.py: Main engine facade [FR-R-12]
- test_decision_log.py: Decision logging [FR-R-9]
- test_confidence_calibration.py: Confidence calibration [FR-R-10]
- test_effort_tracker.py: Effort tracking [FR-R-11]
- test_alert_manager.py: Alert system [FR-R-13]
- test_uqlm_integration.py: UQLM integration [FR-R-10]
- dimensions/: Individual dimension assessor tests
    - test_privacy.py: D1 - Data Privacy [FR-R-1]
    - test_injection.py: D2 - Injection [FR-R-2]
    - test_cost.py: D3 - Cost/Token [FR-R-3]
    - test_uaf_clap.py: D4 - UAF/CLAP [FR-R-4]
    - test_memory_poisoning.py: D5 - Memory Poisoning [FR-R-5]
    - test_cross_agent_leak.py: D6 - Cross-Agent Leak [FR-R-6]
    - test_latency.py: D7 - Latency/SLO [FR-R-7]
    - test_compliance.py: D8 - Compliance [FR-R-8]

TDD Requirements:
- Coverage: 100% for all assess() methods
- Each assess(): at least 3 test cases (normal, boundary, edge)
- Each class: constructor test + method tests

Run with: pytest tests/ -v
"""

# This file ensures the tests directory is a Python package
