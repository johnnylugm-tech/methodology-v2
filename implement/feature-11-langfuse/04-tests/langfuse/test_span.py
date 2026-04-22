"""Tests for ml_langfuse.span — Span creation with required fields."""

from __future__ import annotations

import os
import pytest

from opentelemetry import trace
from opentelemetry.trace import StatusCode

from ml_langfuse.span import (
    create_decision_span,
    end_span_with_status,
    end_span_ok,
    end_span_error,
)


class TestCreateDecisionSpan:
    """Tests for create_decision_span()."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        """Ensure a client is initialized before each test."""
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"
        from ml_langfuse.client import get_langfuse_client
        get_langfuse_client()

    def test_span_created_with_all_required_fields(self):
        """create_decision_span should return a valid Span."""
        span = create_decision_span(
            name="phase7.test",
            uaf_score=0.75,
            clap_flag=True,
            risk_score=0.45,
            hitl_gate="review",
            human_decision="approved",
            decided_by="human",
            compliance_tags=["GDPR Art.22"],
        )
        assert span is not None
        assert isinstance(span, trace.Span)

    def test_invalid_hitl_gate_raises(self):
        """Invalid hitl_gate value should raise ValueError."""
        with pytest.raises(ValueError, match="hitl_gate"):
            create_decision_span(
                name="phase7.test",
                uaf_score=0.75,
                clap_flag=True,
                risk_score=0.45,
                hitl_gate="invalid_gate",
                human_decision=None,
                decided_by="agent",
                compliance_tags=[],
            )

    def test_invalid_decided_by_raises(self):
        """Invalid decided_by value should raise ValueError."""
        with pytest.raises(ValueError, match="decided_by"):
            create_decision_span(
                name="phase7.test",
                uaf_score=0.75,
                clap_flag=True,
                risk_score=0.45,
                hitl_gate="pass",
                human_decision=None,
                decided_by="robot",
                compliance_tags=[],
            )

    def test_uaf_score_out_of_range_raises(self):
        """uaf_score outside [0.0, 1.0] should raise ValueError."""
        with pytest.raises(ValueError, match="uaf_score"):
            create_decision_span(
                name="phase7.test",
                uaf_score=1.5,
                clap_flag=True,
                risk_score=0.45,
                hitl_gate="pass",
                human_decision=None,
                decided_by="agent",
                compliance_tags=[],
            )

    def test_risk_score_out_of_range_raises(self):
        """risk_score outside [0.0, 1.0] should raise ValueError."""
        with pytest.raises(ValueError, match="risk_score"):
            create_decision_span(
                name="phase7.test",
                uaf_score=0.75,
                clap_flag=True,
                risk_score=-0.1,
                hitl_gate="pass",
                human_decision=None,
                decided_by="agent",
                compliance_tags=[],
            )

    def test_clap_flag_wrong_type_raises(self):
        """clap_flag must be bool, not e.g. int."""
        with pytest.raises(TypeError, match="clap_flag"):
            create_decision_span(
                name="phase7.test",
                uaf_score=0.75,
                clap_flag=1,  # int instead of bool
                risk_score=0.45,
                hitl_gate="pass",
                human_decision=None,
                decided_by="agent",
                compliance_tags=[],
            )

    def test_compliance_tags_wrong_type_raises(self):
        """compliance_tags must be list[str]."""
        with pytest.raises(TypeError, match="compliance_tags"):
            create_decision_span(
                name="phase7.test",
                uaf_score=0.75,
                clap_flag=True,
                risk_score=0.45,
                hitl_gate="pass",
                human_decision=None,
                decided_by="agent",
                compliance_tags="GDPR Art.22",  # str, not list
            )

    def test_human_decision_wrong_type_raises(self):
        """human_decision must be str or None."""
        with pytest.raises(TypeError, match="human_decision"):
            create_decision_span(
                name="phase7.test",
                uaf_score=0.75,
                clap_flag=True,
                risk_score=0.45,
                hitl_gate="pass",
                human_decision=123,  # int instead of str/None
                decided_by="agent",
                compliance_tags=[],
            )

    def test_all_valid_hitl_gate_values(self):
        """All three valid hitl_gate values should be accepted."""
        for gate in ("pass", "review", "block"):
            span = create_decision_span(
                name="phase7.test",
                uaf_score=0.5,
                clap_flag=False,
                risk_score=0.5,
                hitl_gate=gate,
                human_decision=None,
                decided_by="agent",
                compliance_tags=[],
            )
            assert span is not None

    def test_all_valid_decided_by_values(self):
        """All three valid decided_by values should be accepted."""
        for who in ("agent", "human", "system"):
            span = create_decision_span(
                name="phase7.test",
                uaf_score=0.5,
                clap_flag=False,
                risk_score=0.5,
                hitl_gate="pass",
                human_decision=None,
                decided_by=who,
                compliance_tags=[],
            )
            assert span is not None


class TestEndSpanWithStatus:
    """Tests for end_span_with_status()."""

    @pytest.fixture(autouse=True)
    def setup_client(self):
        """Ensure a client is initialized before each test."""
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"
        from ml_langfuse.client import get_langfuse_client
        get_langfuse_client()

    def test_end_span_ok(self):
        """end_span_ok should end span with StatusCode.OK without raising."""
        span = create_decision_span(
            name="phase7.test",
            uaf_score=0.5,
            clap_flag=False,
            risk_score=0.5,
            hitl_gate="pass",
            human_decision=None,
            decided_by="agent",
            compliance_tags=[],
        )
        end_span_ok(span)  # Should not raise

    def test_end_span_with_status_ok(self):
        """end_span_with_status with OK should not raise."""
        span = create_decision_span(
            name="phase7.test",
            uaf_score=0.5,
            clap_flag=False,
            risk_score=0.5,
            hitl_gate="pass",
            human_decision=None,
            decided_by="agent",
            compliance_tags=[],
        )
        end_span_with_status(span, StatusCode.OK)  # Should not raise

    def test_end_span_with_status_error_and_exception(self):
        """end_span_with_status with ERROR should record exception."""
        span = create_decision_span(
            name="phase7.test",
            uaf_score=0.5,
            clap_flag=False,
            risk_score=0.5,
            hitl_gate="pass",
            human_decision=None,
            decided_by="agent",
            compliance_tags=[],
        )
        exc = ValueError("test error")
        end_span_with_status(span, StatusCode.ERROR, exception=exc)  # Should not raise

    def test_end_span_error(self):
        """end_span_error should end span with ERROR status."""
        span = create_decision_span(
            name="phase7.test",
            uaf_score=0.5,
            clap_flag=False,
            risk_score=0.5,
            hitl_gate="pass",
            human_decision=None,
            decided_by="agent",
            compliance_tags=[],
        )
        end_span_error(span)  # Should not raise
