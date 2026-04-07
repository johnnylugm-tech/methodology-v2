"""
Unit tests for severity.py — covers all 25 matrix combinations.
"""

import pytest
from feedback.severity import (
    SEVERITY_MATRIX,
    calculate_severity,
    severity_to_numeric,
    _to_level,
)


class Test_to_level:
    def test_clamps_low(self):
        assert _to_level(0.0) == 1
        assert _to_level(-5.0) == 1

    def test_clamps_high(self):
        assert _to_level(6.0) == 5
        assert _to_level(100.0) == 5

    def test_rounds_bankers_rounding(self):
        # Python round() uses banker's rounding (round half to even)
        assert _to_level(2.4) == 2
        assert _to_level(2.5) == 2   # banker's: 2 is even
        assert _to_level(2.6) == 3
        assert _to_level(1.5) == 2   # banker's: 2 is even
        assert _to_level(3.5) == 4   # banker's: 4 is even
        assert _to_level(4.5) == 4   # banker's: 4 is even

    def test_exact_values(self):
        assert _to_level(1.0) == 1
        assert _to_level(2.0) == 2
        assert _to_level(3.0) == 3
        assert _to_level(4.0) == 4
        assert _to_level(5.0) == 5


class TestSeverityMatrixShape:
    def test_5x5_matrix(self):
        assert len(SEVERITY_MATRIX) == 5
        for row in SEVERITY_MATRIX:
            assert len(row) == 5

    def test_all_cells_non_empty(self):
        for row in SEVERITY_MATRIX:
            for cell in row:
                assert cell in ("info", "low", "medium", "high", "critical")


class TestCalculateSeverity:
    """Cover all 25 (impact, urgency) combinations in the 5x5 matrix."""

    @pytest.mark.parametrize("impact", [1, 2, 3, 4, 5])
    @pytest.mark.parametrize("urgency", [1, 2, 3, 4, 5])
    def test_all_25_combinations(self, impact, urgency):
        result = calculate_severity(float(impact), float(urgency))
        assert result in SEVERITY_MATRIX[impact - 1]
        assert result == SEVERITY_MATRIX[impact - 1][urgency - 1]

    def test_critical_at_max_impact_and_urgency(self):
        assert calculate_severity(5.0, 5.0) == "critical"

    def test_info_at_min_impact_and_urgency(self):
        assert calculate_severity(1.0, 1.0) == "info"

    def test_fractional_inputs_clamps_correctly(self):
        # impact=5.8 -> level 6 -> clamped to 5
        assert calculate_severity(5.8, 1.2) == SEVERITY_MATRIX[4][0]
        # urgency=0.3 -> clamped to 1
        assert calculate_severity(3.0, 0.3) == SEVERITY_MATRIX[2][0]


class TestSeverityToNumeric:
    def test_known_levels(self):
        assert severity_to_numeric("info") == 0
        assert severity_to_numeric("low") == 1
        assert severity_to_numeric("medium") == 2
        assert severity_to_numeric("high") == 3
        assert severity_to_numeric("critical") == 4

    def test_unknown_level(self):
        assert severity_to_numeric("unknown") == -1
        assert severity_to_numeric("") == -1