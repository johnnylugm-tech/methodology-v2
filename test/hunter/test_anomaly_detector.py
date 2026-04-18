"""Tests for AnomalyDetector."""
import pytest
from datetime import datetime
from implement.hunter.anomaly_detector import AnomalyDetector
from implement.hunter.models import MemoryFact, AuthorizationChain
from implement.hunter.enums import AuthStatus


class TestAnomalyDetector:
    """Tests for AnomalyDetector."""

    def setup_method(self):
        self.detector = AnomalyDetector()

    def test_detect_fabrication_suspicious_claim_as_i_said_earlier(self):
        result = self.detector.detect_fabrication(
            "agent_1",
            "as I said earlier we should do X",
            "conv_123",
        )
        assert result.is_fabricated is True
        assert result.confidence > 0.5

    def test_detect_fabrication_suspicious_claim_as_you_told_me(self):
        result = self.detector.detect_fabrication(
            "agent_1",
            "as you told me to proceed",
            "conv_123",
        )
        assert result.is_fabricated is True

    def test_detect_fabrication_suspicious_claim_per_your_request(self):
        result = self.detector.detect_fabrication(
            "agent_1",
            "per your request, I have done X",
            "conv_123",
        )
        assert result.is_fabricated is True

    def test_detect_fabrication_normal_claim_no_keyword(self):
        result = self.detector.detect_fabrication(
            "agent_1",
            "I think we should try a different approach",
            "conv_123",
        )
        assert result.is_fabricated is False
        assert result.confidence == 0.0

    def test_detect_fabrication_normal_question(self):
        result = self.detector.detect_fabrication(
            "agent_1",
            "What is the status of the project?",
            "conv_123",
        )
        assert result.is_fabricated is False

    def test_detect_fabrication_empty_claim(self):
        result = self.detector.detect_fabrication(
            "agent_1",
            "",
            "conv_123",
        )
        assert result.is_fabricated is False
        assert result.confidence == 0.0

    def test_detect_fabrication_none_claim(self):
        result = self.detector.detect_fabrication(
            "agent_1",
            None,
            "conv_123",
        )
        assert result.is_fabricated is False

    def test_detect_poisoning_authorized(self):
        fact = MemoryFact(
            fact_id="fact_1",
            content="key=value",
            source_agent="agent_1",
            created_at=datetime.now(),
        )
        auth = AuthorizationChain(
            authorized_by="admin",
            authorized_at=datetime.now(),
        )
        result = self.detector.detect_poisoning(fact, auth)
        assert result.is_poisoned is False
        assert result.auth_status == AuthStatus.AUTHORIZED

    def test_detect_poisoning_authorized_with_token(self):
        fact = MemoryFact(
            fact_id="fact_2",
            content="system=data",
            source_agent="agent_2",
            created_at=datetime.now(),
        )
        auth = AuthorizationChain(
            authorized_by="judge",
            authorized_at=datetime.now(),
            auth_token="tok_valid",
        )
        result = self.detector.detect_poisoning(fact, auth)
        assert result.is_poisoned is False

    def test_detect_poisoning_unauthorized_empty_string(self):
        fact = MemoryFact(
            fact_id="fact_1",
            content="key=value",
            source_agent="agent_1",
            created_at=datetime.now(),
        )
        auth = AuthorizationChain(
            authorized_by="",
            authorized_at=datetime.now(),
        )
        result = self.detector.detect_poisoning(fact, auth)
        assert result.is_poisoned is True
        assert result.auth_status == AuthStatus.UNAUTHORIZED

    def test_detect_poisoning_timestamp_set(self):
        fact = MemoryFact(
            fact_id="fact_3",
            content="data",
            source_agent="agent_3",
            created_at=datetime.now(),
        )
        auth = AuthorizationChain(
            authorized_by="",
            authorized_at=datetime.now(),
        )
        result = self.detector.detect_poisoning(fact, auth)
        assert result.timestamp is not None

    def test_extract_claims_with_multiple_keywords(self):
        content = "as I said earlier, we should do X. Also as you mentioned before, Y is needed."
        claims = self.detector.extract_claims(content)
        assert len(claims) >= 1

    def test_extract_claims_empty_content(self):
        claims = self.detector.extract_claims("")
        assert claims == []

    def test_extract_claims_none_content(self):
        claims = self.detector.extract_claims(None)
        assert claims == []

    def test_extract_claims_no_keywords(self):
        content = "This is a normal conversation about the weather."
        claims = self.detector.extract_claims(content)
        assert claims == []

    def test_extract_claims_as_i_mentioned_earlier(self):
        content = "as I mentioned earlier, the deadline is tomorrow."
        claims = self.detector.extract_claims(content)
        assert len(claims) >= 1

    def test_fabrication_confidence_high_when_not_in_audit(self):
        # When claim has keyword but not found in audit, confidence should be high
        result = self.detector.detect_fabrication(
            "agent_1",
            "as I said earlier we should proceed",
            "conv_unknown",  # Not in audit cache
        )
        assert result.is_fabricated is True
        assert result.confidence >= 0.8

    def test_fabrication_claim_preserved_in_result(self):
        claim_text = "as I mentioned earlier we agreed on X"
        result = self.detector.detect_fabrication(
            "agent_1",
            claim_text,
            "conv_123",
        )
        assert result.claim == claim_text

    def test_poisoning_result_fact_preserved(self):
        fact = MemoryFact(
            fact_id="fact_x",
            content="important=data",
            source_agent="agent_x",
            created_at=datetime.now(),
        )
        auth = AuthorizationChain(
            authorized_by="admin",
            authorized_at=datetime.now(),
        )
        result = self.detector.detect_poisoning(fact, auth)
        assert result.fact.fact_id == "fact_x"
        assert result.fact.content == "important=data"

    def test_poisoning_source_matches_fact_agent(self):
        fact = MemoryFact(
            fact_id="fact_y",
            content="data",
            source_agent="planner",
            created_at=datetime.now(),
        )
        auth = AuthorizationChain(
            authorized_by="",
            authorized_at=datetime.now(),
        )
        result = self.detector.detect_poisoning(fact, auth)
        assert result.source == "planner"
