"""
Tests for deidentify(), verify_evidence(), auto_detect_and_deidentify()
Covering acceptance criteria in SPEC.md Section 4.3
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "implement"))

import pytest
from implement.mcp.data_perimeter import (
    PerimeterLevel,
    DeidentifiedPayload,
    deidentify,
    verify_evidence,
    auto_detect_and_deidentify,
    _compute_evidence_hash,
    _detect_pii_fields,
    _generate_schema,
)


class TestDeidentifyL1:
    """FR-3.1: L1 deidentification - raw data for Planner"""

    def test_deidentify_l1_returns_raw(self):
        """FR-3.1: L1 returns original data (Planner only)"""
        payload = {"name": "Johnny", "email": "johnny@example.com", "age": 30}
        result = deidentify(payload, level=PerimeterLevel.L1_RAW)
        assert result.raw_present is True
        assert result.perimeter_level == "L1"
        # L1 should not have deidentified_fields
        assert len(result.deidentified_fields) == 0

    def test_deidentify_l1_with_nested_data(self):
        """L1 with nested structures"""
        payload = {"user": {"name": "Johnny", "ssn": "123-45-6789"}}
        result = deidentify(payload, level=PerimeterLevel.L1_RAW)
        assert result.raw_present is True


class TestDeidentifyL2:
    """FR-3.2: L2 deidentification - intent + schema for Critic/DA"""

    def test_deidentify_l2_returns_intent_and_schema(self):
        """FR-3.2: L2 returns intent + schema + evidence_hash, no raw values"""
        payload = {"name": "Johnny", "email": "johnny@example.com", "age": 30}
        result = deidentify(payload, level=PerimeterLevel.L2_SCHEMA, intent="process_user_request")
        assert result.raw_present is False
        assert result.perimeter_level == "L2"
        assert result.intent == "process_user_request"
        assert result.schema is not None
        assert result.evidence_hash is not None
        # Schema should have type info, not values
        assert result.schema["name"] == "string"
        assert result.schema["email"] == "string"
        assert result.schema["age"] == "integer"

    def test_deidentify_l2_generates_evidence_hash(self):
        """FR-3.2: L2 generates evidence hash for verification"""
        payload = {"query": "台北天氣", "user_id": 123}
        result = deidentify(payload, level=PerimeterLevel.L2_SCHEMA)
        assert result.evidence_hash is not None
        assert len(result.evidence_hash) == 64  # SHA256 hex

    def test_deidentify_l2_detects_pii_fields(self):
        """FR-3.5: L2 detects and reports PII fields"""
        payload = {
            "name": "Johnny",
            "email": "johnny@example.com",
            "ssn": "123-45-6789",
            "phone": "+1234567890",
        }
        result = deidentify(payload, level=PerimeterLevel.L2_SCHEMA)
        assert "email" in result.deidentified_fields
        assert "ssn" in result.deidentified_fields
        assert "phone" in result.deidentified_fields

    def test_deidentify_l2_default_intent(self):
        """L2 uses default intent when not provided"""
        payload = {"data": "test"}
        result = deidentify(payload, level=PerimeterLevel.L2_SCHEMA)
        assert result.intent is not None  # Should have some default
        assert result.schema is not None


class TestDeidentifyL3:
    """FR-3.3: L3 deidentification - evidence hash only for Judge"""

    def test_deidentify_l3_returns_only_hash(self):
        """FR-3.3: L3 returns only evidence_hash (Judge verification)"""
        payload = {"sensitive": "data", "value": 42}
        result = deidentify(payload, level=PerimeterLevel.L3_HASH)
        assert result.evidence_hash is not None
        assert result.intent is None
        assert result.schema is None
        assert result.raw_present is False

    def test_deidentify_l3_no_deidentified_fields(self):
        """L3 should not track deidentified fields"""
        payload = {"data": "sensitive"}
        result = deidentify(payload, level=PerimeterLevel.L3_HASH)
        assert len(result.deidentified_fields) == 0

    def test_deidentify_l3_evidence_hash_valid(self):
        """L3 evidence_hash can be verified"""
        payload = {"original": "data"}
        result = deidentify(payload, level=PerimeterLevel.L3_HASH)
        assert verify_evidence(payload, result.evidence_hash)


class TestVerifyEvidence:
    """FR-3.6: Evidence hash verification"""

    def test_verify_evidence_valid(self):
        """FR-3.6: verify_evidence returns True for matching data"""
        original = {"name": "Johnny", "email": "johnny@example.com"}
        hash_val = _compute_evidence_hash(original)
        assert verify_evidence(original, hash_val) is True

    def test_verify_evidence_invalid(self):
        """verify_evidence returns False for non-matching data"""
        original = {"name": "Johnny"}
        hash_val = _compute_evidence_hash(original)
        tampered = {"name": "Johnny", "tampered": True}
        assert verify_evidence(tampered, hash_val) is False

    def test_verify_evidence_string(self):
        """verify_evidence works with string input"""
        original = "台北天氣"
        hash_val = _compute_evidence_hash(original)
        assert verify_evidence("台北天氣", hash_val) is True
        assert verify_evidence("different string", hash_val) is False

    def test_verify_evidence_empty(self):
        """verify_evidence works with empty data"""
        original = {}
        hash_val = _compute_evidence_hash(original)
        assert verify_evidence({}, hash_val) is True

    def test_verify_evidence_nested(self):
        """verify_evidence works with nested structures"""
        original = {"user": {"name": "Johnny", "data": [1, 2, 3]}}
        hash_val = _compute_evidence_hash(original)
        assert verify_evidence(original, hash_val) is True


class TestAutoDetectAndDeidentify:
    """FR-3.5: Automatic PII detection and deidentification"""

    def test_auto_detect_ssn(self):
        """FR-3.5: SSN triggers L2 deidentification"""
        payload = {"name": "Johnny", "ssn": "123-45-6789"}
        result = auto_detect_and_deidentify(payload)
        assert result.perimeter_level == "L2"
        assert result.evidence_hash is not None
        assert "ssn" in result.deidentified_fields

    def test_auto_detect_email(self):
        """FR-3.5: Email triggers L2 deidentification"""
        payload = {"contact": "user@example.com", "message": "hello"}
        result = auto_detect_and_deidentify(payload)
        assert result.perimeter_level == "L2"
        assert "contact" in result.deidentified_fields

    def test_auto_detect_phone(self):
        """FR-3.5: Phone number triggers L2 deidentification"""
        payload = {"phone": "+123456789012345", "query": "台北天氣"}
        result = auto_detect_and_deidentify(payload)
        assert result.perimeter_level == "L2"
        assert "phone" in result.deidentified_fields

    def test_auto_detect_credit_card(self):
        """FR-3.5: Credit card triggers L2 deidentification"""
        payload = {"card": "1234-5678-9012-3456", "amount": 100}
        result = auto_detect_and_deidentify(payload)
        assert result.perimeter_level == "L2"
        assert "card" in result.deidentified_fields

    def test_auto_detect_ip_address(self):
        """FR-3.5: IP address triggers L2 deidentification"""
        payload = {"ip": "192.168.1.100", "action": "login"}
        result = auto_detect_and_deidentify(payload)
        assert result.perimeter_level == "L2"
        assert "ip" in result.deidentified_fields

    def test_auto_detect_no_pii(self):
        """No PII detected applies requested level or default L2"""
        payload = {"query": "台北天氣", "language": "zh"}
        result = auto_detect_and_deidentify(payload)
        assert result.perimeter_level == "L2"
        assert len(result.deidentified_fields) == 0

    def test_auto_detect_overrides_l1_to_l2(self):
        """FR-3.5: PII overrides L1 to L2"""
        payload = {"name": "Johnny", "ssn": "123-45-6789"}
        result = auto_detect_and_deidentify(payload, level=PerimeterLevel.L1_RAW)
        # L1 with PII should be elevated to L2
        assert result.perimeter_level == "L2"

    def test_auto_detect_with_explicit_level(self):
        """Explicit level is respected when no PII detected"""
        payload = {"query": "台北天氣"}
        result = auto_detect_and_deidentify(payload, level=PerimeterLevel.L3_HASH)
        assert result.perimeter_level == "L3"


class TestHelperFunctions:
    """Tests for internal helper functions"""

    def test_detect_pii_fields_ssn(self):
        """SSN pattern detection"""
        data = {"ssn": "123-45-6789", "name": "Johnny"}
        detected = _detect_pii_fields(data)
        assert "ssn" in detected

    def test_detect_pii_fields_email(self):
        """Email pattern detection"""
        data = {"email": "test@example.com"}
        detected = _detect_pii_fields(data)
        assert "email" in detected

    def test_detect_pii_fields_phone(self):
        """Phone pattern detection"""
        data = {"phone": "+1234567890"}
        detected = _detect_pii_fields(data)
        assert "phone" in detected

    def test_detect_pii_fields_no_match(self):
        """No PII detected in clean data"""
        data = {"query": "台北天氣", "count": 42}
        detected = _detect_pii_fields(data)
        assert len(detected) == 0

    def test_generate_schema_types(self):
        """Schema generation preserves type information"""
        data = {
            "name": "Johnny",      # string
            "age": 30,             # integer
            "active": True,        # boolean
            "score": 3.14,         # float
        }
        schema = _generate_schema(data)
        assert schema["name"] == "string"
        assert schema["age"] == "integer"
        assert schema["active"] == "integer"  # bool is subclass of int in Python
        assert schema["score"] == "float"

    def test_generate_schema_nested(self):
        """Schema handles nested objects"""
        data = {"user": {"name": "Johnny", "age": 30}}
        schema = _generate_schema(data)
        assert schema["user"]["type"] == "object"

    def test_compute_evidence_hash_deterministic(self):
        """Evidence hash is deterministic"""
        data = {"key": "value"}
        hash1 = _compute_evidence_hash(data)
        hash2 = _compute_evidence_hash(data)
        assert hash1 == hash2

    def test_compute_evidence_hash_different_for_different_data(self):
        """Different data produces different hashes"""
        hash1 = _compute_evidence_hash({"a": 1})
        hash2 = _compute_evidence_hash({"a": 2})
        assert hash1 != hash2