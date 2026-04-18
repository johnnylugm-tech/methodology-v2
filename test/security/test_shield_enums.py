"""Tests for shield_enums: Verdict, PatternMatch, ScanResult."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "implement"))

from security.shield_enums import Verdict, PatternMatch, ScanResult


class TestVerdictEnum:
    """Test Verdict enum values and behaviors."""

    def test_verdict_pass_value(self):
        assert Verdict.PASS.value == "pass"

    def test_verdict_flag_value(self):
        assert Verdict.FLAG.value == "flag"

    def test_verdict_block_value(self):
        assert Verdict.BLOCK.value == "block"

    def test_verdict_is_enum(self):
        assert isinstance(Verdict.PASS, Verdict)
        assert isinstance(Verdict.FLAG, Verdict)
        assert isinstance(Verdict.BLOCK, Verdict)

    def test_verdict_from_string(self):
        assert Verdict("pass") == Verdict.PASS
        assert Verdict("flag") == Verdict.FLAG
        assert Verdict("block") == Verdict.BLOCK


class TestPatternMatchDataclass:
    """Test PatternMatch dataclass."""

    def test_pattern_match_creation(self):
        pm = PatternMatch(
            pattern_name=r"ignore\s*previous\s*instructions?",
            mode="direct_override",
            matched_text="ignore previous instructions",
            position=(0, 25),
            confidence=0.85,
        )
        assert pm.pattern_name == r"ignore\s*previous\s*instructions?"
        assert pm.mode == "direct_override"
        assert pm.matched_text == "ignore previous instructions"
        assert pm.position == (0, 25)
        assert pm.confidence == 0.85

    def test_pattern_match_position_is_tuple(self):
        pm = PatternMatch(
            pattern_name="test",
            mode="direct_override",
            matched_text="test",
            position=(10, 20),
            confidence=0.9,
        )
        assert isinstance(pm.position, tuple)
        assert pm.position[0] == 10
        assert pm.position[1] == 20

    def test_pattern_match_default_confidence(self):
        # confidence must be provided explicitly
        pm = PatternMatch(
            pattern_name="test",
            mode="role_hijack",
            matched_text="test",
            position=(0, 4),
            confidence=0.75,
        )
        assert pm.confidence == 0.75


class TestScanResultDataclass:
    """Test ScanResult dataclass."""

    def test_scan_result_pass(self):
        result = ScanResult(
            verdict=Verdict.PASS,
            confidence=1.0,
        )
        assert result.verdict == Verdict.PASS
        assert result.confidence == 1.0
        assert result.matched_patterns == []
        assert result.error is None

    def test_scan_result_block_with_matches(self):
        pm = PatternMatch(
            pattern_name=r"ignore",
            mode="direct_override",
            matched_text="ignore",
            position=(0, 6),
            confidence=0.90,
        )
        result = ScanResult(
            verdict=Verdict.BLOCK,
            confidence=0.90,
            matched_patterns=[pm],
            latency_ms=12.5,
            scanner="detection_modes",
            input_hash="abc123",
        )
        assert result.verdict == Verdict.BLOCK
        assert result.confidence == 0.90
        assert len(result.matched_patterns) == 1
        assert result.matched_patterns[0].matched_text == "ignore"
        assert result.latency_ms == 12.5
        assert result.scanner == "detection_modes"
        assert result.input_hash == "abc123"

    def test_scan_result_flag_with_error(self):
        result = ScanResult(
            verdict=Verdict.FLAG,
            confidence=0.78,
            error="Scanner timeout",
        )
        assert result.verdict == Verdict.FLAG
        assert result.confidence == 0.78
        assert result.error == "Scanner timeout"

    def test_scan_result_defaults(self):
        result = ScanResult(verdict=Verdict.PASS, confidence=1.0)
        assert result.matched_patterns == []
        assert result.latency_ms == 0.0
        assert result.scanner == "unknown"
        assert result.input_hash == ""
        assert result.error is None
