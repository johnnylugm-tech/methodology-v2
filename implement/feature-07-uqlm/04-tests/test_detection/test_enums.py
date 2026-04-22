"""Tests for detection/enums.py."""

from detection.enums import Decision, GapSeverity, GapType, ProbeType


class TestGapType:
    def test_enum_values(self):
        assert GapType.BASE64_VS_AES.value == "base64_vs_aes"
        assert GapType.TEST_TODO_FLOOD.value == "test_todo_flood"
        assert GapType.EMPTY_CATCH.value == "empty_catch"
        assert GapType.HARDCODED_SECRETS.value == "hardcoded_secrets"

    def test_enum_count(self):
        assert len(GapType) == 4

    def test_enum_from_value(self):
        assert GapType("base64_vs_aes") == GapType.BASE64_VS_AES
        assert GapType("test_todo_flood") == GapType.TEST_TODO_FLOOD


class TestGapSeverity:
    def test_enum_values(self):
        assert GapSeverity.CRITICAL.value == "CRITICAL"
        assert GapSeverity.HIGH.value == "HIGH"
        assert GapSeverity.MEDIUM.value == "MEDIUM"
        assert GapSeverity.LOW.value == "LOW"

    def test_enum_count(self):
        assert len(GapSeverity) == 4


class TestDecision:
    def test_enum_values(self):
        assert Decision.PASS.value == "PASS"
        assert Decision.ROUND_2.value == "ROUND_2"
        assert Decision.HITL.value == "HITL"

    def test_enum_count(self):
        assert len(Decision) == 3


class TestProbeType:
    def test_enum_values(self):
        assert ProbeType.LOGISTIC_REGRESSION.value == "logistic_regression"
        assert ProbeType.LINEAR.value == "linear"
        assert ProbeType.MLP.value == "mlp"
        assert ProbeType.TINYLORA.value == "tinylora"

    def test_enum_count(self):
        assert len(ProbeType) == 4
