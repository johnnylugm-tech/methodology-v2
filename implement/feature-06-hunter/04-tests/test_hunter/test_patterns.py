"""Tests for Hunter Agent detection patterns."""
import pytest
from implement.hunter.patterns import (
    TAMPER_PATTERNS,
    FABRICATION_KEYWORDS,
    PATTERN_SEVERITY,
)
from implement.hunter.enums import TamperPattern, Severity


class TestTAMPER_PATTERNS:
    """Tests for TAMPER_PATTERNS dictionary."""

    def test_all_patterns_defined(self):
        for pattern in TamperPattern:
            assert pattern in TAMPER_PATTERNS

    def test_pattern_count(self):
        assert len(TAMPER_PATTERNS) == 5

    def test_direct_override_has_regexes(self):
        assert TamperPattern.DIRECT_OVERRIDE in TAMPER_PATTERNS
        assert len(TAMPER_PATTERNS[TamperPattern.DIRECT_OVERRIDE]) > 0

    def test_role_hijack_has_regexes(self):
        assert TamperPattern.ROLE_HIJACK in TAMPER_PATTERNS
        assert len(TAMPER_PATTERNS[TamperPattern.ROLE_HIJACK]) > 0

    def test_permission_escalation_has_regexes(self):
        assert TamperPattern.PERMISSION_ESCALATION in TAMPER_PATTERNS
        assert len(TAMPER_PATTERNS[TamperPattern.PERMISSION_ESCALATION]) > 0

    def test_rule_modification_has_regexes(self):
        assert TamperPattern.RULE_MODIFICATION in TAMPER_PATTERNS
        assert len(TAMPER_PATTERNS[TamperPattern.RULE_MODIFICATION]) > 0

    def test_context_injection_has_regexes(self):
        assert TamperPattern.CONTEXT_INJECTION in TAMPER_PATTERNS
        assert len(TAMPER_PATTERNS[TamperPattern.CONTEXT_INJECTION]) > 0

    def test_all_pattern_values_are_strings(self):
        for pattern_type, regexes in TAMPER_PATTERNS.items():
            assert isinstance(regexes, list)
            for regex in regexes:
                assert isinstance(regex, str)
                assert len(regex) > 0

    def test_all_regexes_are_valid(self):
        import re
        for pattern_type, regexes in TAMPER_PATTERNS.items():
            for regex in regexes:
                # Should not raise
                compiled = re.compile(regex, re.IGNORECASE)
                assert compiled is not None


class TestFABRICATION_KEYWORDS:
    """Tests for FABRICATION_KEYWORDS list."""

    def test_keywords_not_empty(self):
        assert len(FABRICATION_KEYWORDS) >= 10

    def test_keywords_are_strings(self):
        for keyword in FABRICATION_KEYWORDS:
            assert isinstance(keyword, str)

    def test_keywords_are_not_empty(self):
        for keyword in FABRICATION_KEYWORDS:
            assert len(keyword) > 0

    def test_all_keywords_lowercase_have_spaces(self):
        # These are phrase keywords, should contain spaces
        for keyword in FABRICATION_KEYWORDS:
            assert " " in keyword, f"'{keyword}' should contain a space"

    def test_contains_as_i_said_earlier(self):
        assert "as I said earlier" in FABRICATION_KEYWORDS

    def test_contains_as_you_told_me(self):
        assert "as you told me" in FABRICATION_KEYWORDS

    def test_contains_per_your_request(self):
        assert "per your request" in FABRICATION_KEYWORDS


class TestPATTERN_SEVERITY:
    """Tests for PATTERN_SEVERITY mapping."""

    def test_all_patterns_mapped(self):
        for pattern in TamperPattern:
            assert pattern in PATTERN_SEVERITY

    def test_pattern_count_matches(self):
        assert len(PATTERN_SEVERITY) == len(TamperPattern)

    def test_direct_override_is_critical(self):
        assert PATTERN_SEVERITY[TamperPattern.DIRECT_OVERRIDE] == Severity.CRITICAL

    def test_role_hijack_is_critical(self):
        assert PATTERN_SEVERITY[TamperPattern.ROLE_HIJACK] == Severity.CRITICAL

    def test_permission_escalation_is_high(self):
        assert PATTERN_SEVERITY[TamperPattern.PERMISSION_ESCALATION] == Severity.HIGH

    def test_rule_modification_is_high(self):
        assert PATTERN_SEVERITY[TamperPattern.RULE_MODIFICATION] == Severity.HIGH

    def test_context_injection_is_medium(self):
        assert PATTERN_SEVERITY[TamperPattern.CONTEXT_INJECTION] == Severity.MEDIUM

    def test_all_mapped_values_are_severity_enum(self):
        for pattern, severity in PATTERN_SEVERITY.items():
            assert isinstance(severity, Severity)

    def test_no_low_severity_in_tamper_patterns(self):
        severities = list(PATTERN_SEVERITY.values())
        # Tamper patterns should not be LOW severity
        for sev in severities:
            assert sev != Severity.LOW

    def test_critical_count(self):
        critical = [p for p, s in PATTERN_SEVERITY.items() if s == Severity.CRITICAL]
        assert len(critical) == 2

    def test_high_count(self):
        high = [p for p, s in PATTERN_SEVERITY.items() if s == Severity.HIGH]
        assert len(high) == 2

    def test_medium_count(self):
        medium = [p for p, s in PATTERN_SEVERITY.items() if s == Severity.MEDIUM]
        assert len(medium) == 1

    def test_low_count_in_pattern_severity(self):
        low = [p for p, s in PATTERN_SEVERITY.items() if s == Severity.LOW]
        assert len(low) == 0
