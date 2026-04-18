"""Tests for RuntimeMonitor."""
import pytest
import time
from datetime import datetime, timedelta
from implement.hunter.runtime_monitor import RuntimeMonitor, AccessRecord


class TestRuntimeMonitor:
    """Tests for RuntimeMonitor."""

    def setup_method(self):
        self.monitor = RuntimeMonitor()

    def test_validate_read_no_hash_returns_valid(self):
        result = self.monitor.validate_read("agent_1", "memory_source")
        assert result.is_valid is True
        assert result.requires_hitl is False

    def test_validate_read_matching_hash(self):
        source = "test_content"
        hash_val = self.monitor._compute_hash(source)
        result = self.monitor.validate_read("agent_1", source, hash_val)
        assert result.is_valid is True

    def test_validate_read_mismatched_hash(self):
        source = "test_content"
        result = self.monitor.validate_read("agent_1", source, "wrong_hash")
        assert result.is_valid is False

    def test_validate_read_mismatched_hash_with_burst_access_triggers_hitl(self):
        # First populate burst access to trigger anomaly detection
        for i in range(25):
            self.monitor.record_access("agent_1", f"source_{i}")
        # Then mismatched hash with high anomaly score triggers HITL
        result = self.monitor.validate_read("agent_1", "new_source", "wrong_hash")
        assert result.requires_hitl is True
        assert result.anomaly_score >= 0.3

    def test_record_access_single(self):
        self.monitor.record_access("agent_1", "memory_context")
        assert "agent_1" in self.monitor._access_window
        assert len(self.monitor._access_window["agent_1"]) >= 1

    def test_record_access_multiple_same_agent(self):
        self.monitor.record_access("agent_1", "source_a")
        self.monitor.record_access("agent_1", "source_b")
        self.monitor.record_access("agent_1", "source_c")
        assert len(self.monitor._access_window["agent_1"]) >= 3

    def test_record_access_different_agents(self):
        self.monitor.record_access("agent_1", "source_x")
        self.monitor.record_access("agent_2", "source_y")
        assert "agent_1" in self.monitor._access_window
        assert "agent_2" in self.monitor._access_window

    def test_get_access_history_unknown_agent(self):
        history = self.monitor._access_window.get("never_seen_agent", [])
        assert history == []

    def test_anomaly_no_access_returns_zero(self):
        anomaly = self.monitor.detect_anomaly("never_accessed")
        assert anomaly == 0.0

    def test_anomaly_normal_access_returns_zero(self):
        for i in range(5):
            self.monitor.record_access("agent_1", f"source_{i}")
        anomaly = self.monitor.detect_anomaly("agent_1")
        assert anomaly < 0.3

    def test_anomaly_burst_access(self):
        # Record many accesses rapidly
        for i in range(25):
            self.monitor.record_access("agent_1", f"source_{i}")
        anomaly = self.monitor.detect_anomaly("agent_1")
        assert anomaly >= 0.3

    def test_anomaly_burst_access_triggers_hitl(self):
        for i in range(25):
            self.monitor.record_access("agent_1", f"source_{i}")
        result = self.monitor.validate_read("agent_1", "new_source", "wrong_hash")
        assert result.requires_hitl is True

    def test_validate_read_sets_actual_hash(self):
        source = "some_content"
        result = self.monitor.validate_read("agent_1", source)
        assert result.actual_hash == self.monitor._compute_hash(source)
        assert result.source == "some_content"

    def test_validate_read_no_hash_expected_empty(self):
        result = self.monitor.validate_read("agent_1", "source")
        assert result.expected_hash == ""

    def test_hash_computation_deterministic(self):
        content = "test"
        hash1 = self.monitor._compute_hash(content)
        hash2 = self.monitor._compute_hash(content)
        assert hash1 == hash2

    def test_hash_computation_different_content(self):
        hash1 = self.monitor._compute_hash("content_a")
        hash2 = self.monitor._compute_hash("content_b")
        assert hash1 != hash2

    def test_hash_returns_sha256_hex(self):
        hash_val = self.monitor._compute_hash("test")
        assert isinstance(hash_val, str)
        assert len(hash_val) == 64

    def test_access_record_contains_fields(self):
        record = AccessRecord("agent_x", "source_y", datetime.now())
        assert record.agent_id == "agent_x"
        assert record.source == "source_y"
        assert record.accessed_at is not None

    def test_validate_read_valid_preserves_anomaly_score(self):
        result = self.monitor.validate_read("agent_1", "source")
        assert result.anomaly_score == 0.0

    def test_validate_read_invalid_records_anomaly(self):
        # First record burst access
        for i in range(25):
            self.monitor.record_access("agent_1", f"source_{i}")
        # Then validate with wrong hash
        result = self.monitor.validate_read("agent_1", "new_source", "wrong_hash")
        assert result.anomaly_score >= 0.3

    def test_record_access_timestamp_is_reasonable(self):
        before = datetime.now()
        self.monitor.record_access("agent_1", "source")
        after = datetime.now()
        history = self.monitor._access_window["agent_1"]
        assert before <= history[-1].accessed_at <= after

    def test_validate_read_empty_source(self):
        result = self.monitor.validate_read("agent_1", "")
        assert result.is_valid is True
        assert result.source == ""

    def test_record_access_empty_source(self):
        self.monitor.record_access("agent_1", "")
        history = self.monitor._access_window["agent_1"]
        assert len(history) >= 1

    def test_record_access_sliding_window_limit(self):
        # Record more than window_max (1000) accesses
        for i in range(1005):
            self.monitor.record_access("agent_big", f"source_{i}")
        # Should not exceed window_max
        assert len(self.monitor._access_window["agent_big"]) <= self.monitor._window_max
