"""
Tests for EffortTracker [FR-R-11]

Covers effort tracking, metrics collection, aggregation, and efficiency scoring.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "03-implement"))

from effort_tracker import EffortTracker, EffortMetrics


class TestEffortMetrics:
    """Test EffortMetrics dataclass."""

    def test_constructor_defaults(self):
        """Test default values."""
        metrics = EffortMetrics(
            tracking_id="track-001",
            agent_id="planner",
            task_id="task-123"
        )
        assert metrics.tracking_id == "track-001"
        assert metrics.agent_id == "planner"
        assert metrics.task_id == "task-123"
        assert metrics.time_spent_minutes == 0.0
        assert metrics.tool_calls == 0
        assert metrics.tokens_consumed == 0
        assert metrics.iteration_count == 0
        assert metrics.ab_round_triggered is False
        assert metrics.output_quality_score is None
        assert metrics.error_count == 0

    def test_constructor_generates_tracking_id(self):
        """Test auto-generation of tracking ID."""
        metrics = EffortMetrics()
        assert metrics.tracking_id != ""
        assert len(metrics.tracking_id) <= 8

    def test_duration_seconds_empty(self):
        """Test duration when not completed."""
        metrics = EffortMetrics()
        assert metrics.duration_seconds == 0.0

    def test_duration_seconds_calculation(self):
        """Test duration calculation."""
        metrics = EffortMetrics(
            started_at="2024-01-01T10:00:00",
            completed_at="2024-01-01T10:05:00"
        )
        assert metrics.duration_seconds == 300.0

    def test_to_dict(self):
        """Test serialization to dict."""
        metrics = EffortMetrics(
            tracking_id="track-001",
            agent_id="planner",
            task_id="task-123",
            tool_calls=5,
            tokens_consumed=1000
        )
        d = metrics.to_dict()

        assert d["tracking_id"] == "track-001"
        assert d["agent_id"] == "planner"
        assert d["task_id"] == "task-123"
        assert d["tool_calls"] == 5
        assert d["tokens_consumed"] == 1000


class TestEffortTrackerConstructor:
    """Test EffortTracker constructor."""

    def test_constructor_default_enabled(self):
        """Test default enabled state."""
        tracker = EffortTracker()
        assert tracker.enabled is True

    def test_constructor_with_config(self):
        """Test constructor with config."""
        tracker = EffortTracker(config={
            "enabled": False,
            "track_detailed": False,
            "quality_threshold": 0.8
        })
        assert tracker.enabled is False
        assert tracker._track_detailed is False
        assert tracker._quality_threshold == 0.8


class TestEffortTrackerStartTracking:
    """Test tracking start."""

    def test_start_tracking_disabled(self):
        """Test disabled tracker returns empty string."""
        tracker = EffortTracker(config={"enabled": False})
        tracking_id = tracker.start_tracking("planner", "task-001")
        assert tracking_id == ""

    def test_start_tracking_generates_id(self):
        """Test start_tracking generates unique ID."""
        tracker = EffortTracker()
        id1 = tracker.start_tracking("planner", "task-001")
        id2 = tracker.start_tracking("coder", "task-002")

        assert id1 != ""
        assert id2 != ""
        assert id1 != id2

    def test_start_tracking_creates_metrics(self):
        """Test start_tracking creates metrics object."""
        tracker = EffortTracker()
        tracking_id = tracker.start_tracking("planner", "task-001")

        assert tracking_id in tracker._active_tracking
        metrics = tracker._active_tracking[tracking_id]
        assert metrics.agent_id == "planner"
        assert metrics.task_id == "task-001"


class TestEffortTrackerRecordToolCall:
    """Test tool call recording."""

    def test_record_tool_call(self):
        """Test recording a tool call."""
        tracker = EffortTracker()
        tracking_id = tracker.start_tracking("planner", "task-001")

        tracker.record_tool_call(tracking_id, "web_search", 100, True)

        assert tracker._active_tracking[tracking_id].tool_calls == 1

    def test_record_tool_call_failure_increments_error(self):
        """Test failed tool call increments error count."""
        tracker = EffortTracker()
        tracking_id = tracker.start_tracking("planner", "task-001")

        tracker.record_tool_call(tracking_id, "web_search", 100, False, "Timeout")

        assert tracker._active_tracking[tracking_id].error_count == 1

    def test_record_tool_call_disabled(self):
        """Test disabled tracker ignores tool calls."""
        tracker = EffortTracker(config={"enabled": False})
        tracking_id = tracker.start_tracking("planner", "task-001")

        # When disabled, start_tracking returns empty string
        assert tracking_id == ""


class TestEffortTrackerRecordTokenUsage:
    """Test token usage recording."""

    def test_record_token_usage(self):
        """Test recording token usage."""
        tracker = EffortTracker()
        tracking_id = tracker.start_tracking("planner", "task-001")

        tracker.record_token_usage(tracking_id, input_tokens=100, output_tokens=50)

        assert tracker._active_tracking[tracking_id].tokens_consumed == 150

    def test_record_token_usage_accumulates(self):
        """Test token usage accumulates."""
        tracker = EffortTracker()
        tracking_id = tracker.start_tracking("planner", "task-001")

        tracker.record_token_usage(tracking_id, input_tokens=100, output_tokens=50)
        tracker.record_token_usage(tracking_id, input_tokens=200, output_tokens=100)

        assert tracker._active_tracking[tracking_id].tokens_consumed == 450


class TestEffortTrackerOtherRecordings:
    """Test other recording methods."""

    def test_record_iteration(self):
        """Test iteration recording."""
        tracker = EffortTracker()
        tracking_id = tracker.start_tracking("planner", "task-001")

        tracker.record_iteration(tracking_id)
        tracker.record_iteration(tracking_id)

        assert tracker._active_tracking[tracking_id].iteration_count == 2

    def test_record_ab_round(self):
        """Test AB round recording."""
        tracker = EffortTracker()
        tracking_id = tracker.start_tracking("planner", "task-001")

        tracker.record_ab_round(tracking_id)

        assert tracker._active_tracking[tracking_id].ab_round_triggered is True

    def test_record_memory_reference(self):
        """Test memory reference recording."""
        tracker = EffortTracker()
        tracking_id = tracker.start_tracking("planner", "task-001")

        tracker.record_memory_reference(tracking_id)
        tracker.record_memory_reference(tracking_id)
        tracker.record_memory_reference(tracking_id)

        assert tracker._active_tracking[tracking_id].memory_references == 3

    def test_record_retry(self):
        """Test retry recording."""
        tracker = EffortTracker()
        tracking_id = tracker.start_tracking("planner", "task-001")

        tracker.record_retry(tracking_id)
        tracker.record_retry(tracking_id)

        assert tracker._active_tracking[tracking_id].retry_count == 2

    def test_update_context_usage(self):
        """Test context usage update."""
        tracker = EffortTracker()
        tracking_id = tracker.start_tracking("planner", "task-001")

        tracker.update_context_usage(tracking_id, 75.5)

        assert tracker._active_tracking[tracking_id].context_window_usage == 75.5


class TestEffortTrackerFinishTracking:
    """Test tracking finish."""

    def test_finish_tracking_nonexistent(self):
        """Test finishing non-existent tracking."""
        tracker = EffortTracker()
        result = tracker.finish_tracking("nonexistent")
        assert result is None

    def test_finish_tracking_returns_metrics(self):
        """Test finish returns completed metrics."""
        tracker = EffortTracker()
        tracking_id = tracker.start_tracking("planner", "task-001")
        tracker.record_tool_call(tracking_id, "search", 100, True)
        tracker.record_token_usage(tracking_id, 100, 50)

        metrics = tracker.finish_tracking(tracking_id)

        assert metrics is not None
        assert metrics.tool_calls == 1
        assert metrics.tokens_consumed == 150
        assert metrics.completed_at != ""

    def test_finish_tracking_with_quality(self):
        """Test finish with quality score."""
        tracker = EffortTracker()
        tracking_id = tracker.start_tracking("planner", "task-001")

        metrics = tracker.finish_tracking(tracking_id, quality_score=0.85)

        assert metrics.output_quality_score == 0.85

    def test_finish_tracking_moves_to_completed(self):
        """Test finish moves tracking to completed."""
        tracker = EffortTracker()
        tracking_id = tracker.start_tracking("planner", "task-001")

        tracker.finish_tracking(tracking_id)

        assert tracking_id not in tracker._active_tracking
        assert len(tracker._completed_metrics) == 1


class TestEffortTrackerGetMetrics:
    """Test metrics retrieval."""

    def test_get_metrics_active(self):
        """Test getting metrics for active tracking."""
        tracker = EffortTracker()
        tracking_id = tracker.start_tracking("planner", "task-001")
        tracker.record_tool_call(tracking_id, "search", 100, True)

        metrics = tracker.get_metrics(tracking_id)

        assert metrics is not None
        assert metrics["tool_calls"] == 1

    def test_get_metrics_completed(self):
        """Test getting metrics for completed tracking."""
        tracker = EffortTracker()
        tracking_id = tracker.start_tracking("planner", "task-001")
        tracker.record_tool_call(tracking_id, "search", 100, True)
        tracker.finish_tracking(tracking_id)

        metrics = tracker.get_metrics(tracking_id)

        assert metrics is not None
        assert metrics["tool_calls"] == 1

    def test_get_metrics_nonexistent(self):
        """Test getting metrics for non-existent tracking."""
        tracker = EffortTracker()
        metrics = tracker.get_metrics("nonexistent")
        assert metrics is None

    def test_get_active_tracking(self):
        """Test getting active tracking IDs."""
        tracker = EffortTracker()
        id1 = tracker.start_tracking("planner", "task-001")
        id2 = tracker.start_tracking("coder", "task-002")

        active = tracker.get_active_tracking()

        assert id1 in active
        assert id2 in active


class TestEffortTrackerAggregate:
    """Test aggregation methods."""

    def test_aggregate_task_metrics_empty(self):
        """Test aggregation for task with no metrics."""
        tracker = EffortTracker()
        agg = tracker.aggregate_task_metrics("nonexistent-task")

        assert agg["task_id"] == "nonexistent-task"
        assert agg["total_time_minutes"] == 0.0
        assert agg["total_tool_calls"] == 0

    def test_aggregate_task_metrics(self):
        """Test aggregation for task."""
        tracker = EffortTracker()

        id1 = tracker.start_tracking("planner", "task-001")
        tracker.record_tool_call(id1, "search", 100, True)
        tracker.finish_tracking(id1)

        id2 = tracker.start_tracking("coder", "task-001")
        tracker.record_tool_call(id2, "edit", 200, True)
        tracker.finish_tracking(id2)

        agg = tracker.aggregate_task_metrics("task-001")

        assert agg["total_tool_calls"] == 2
        assert "planner" in agg["agents_involved"]
        assert "coder" in agg["agents_involved"]


class TestEffortTrackerEfficiency:
    """Test efficiency scoring."""

    def test_get_efficiency_score(self):
        """Test efficiency score calculation."""
        tracker = EffortTracker()
        tracking_id = tracker.start_tracking("planner", "task-001")

        tracker.record_token_usage(tracking_id, 1000, 500)
        tracker.finish_tracking(tracking_id, quality_score=0.8)

        score = tracker.get_efficiency_score(tracking_id)

        assert score is not None
        assert 0.0 <= score <= 1.0

    def test_get_efficiency_score_nonexistent(self):
        """Test efficiency for non-existent tracking."""
        tracker = EffortTracker()
        score = tracker.get_efficiency_score("nonexistent")
        assert score is None


class TestEffortTrackerAgentSummary:
    """Test agent summary."""

    def test_get_agent_summary_empty(self):
        """Test summary for agent with no metrics."""
        tracker = EffortTracker()
        summary = tracker.get_agent_summary("unknown-agent")

        assert summary["agent_id"] == "unknown-agent"
        assert summary["session_count"] == 0

    def test_get_agent_summary(self):
        """Test summary for agent."""
        tracker = EffortTracker()

        id1 = tracker.start_tracking("planner", "task-001")
        tracker.record_tool_call(id1, "search", 100, True)
        tracker.finish_tracking(id1, quality_score=0.8)

        id2 = tracker.start_tracking("planner", "task-002")
        tracker.record_tool_call(id2, "edit", 200, True)
        tracker.finish_tracking(id2, quality_score=0.9)

        summary = tracker.get_agent_summary("planner")

        assert summary["session_count"] == 2
        assert summary["total_tool_calls"] == 2
        assert summary["avg_quality_score"] is not None


class TestEffortTrackerExport:
    """Test export methods."""

    def test_export_metrics(self):
        """Test metrics export."""
        tracker = EffortTracker()
        id1 = tracker.start_tracking("planner", "task-001")
        tracker.finish_tracking(id1)

        exported = tracker.export_metrics()

        assert len(exported) >= 1
        assert all(isinstance(m, dict) for m in exported)


class TestEffortTrackerStatistics:
    """Test statistics retrieval."""

    def test_get_statistics(self):
        """Test statistics retrieval."""
        tracker = EffortTracker()
        id1 = tracker.start_tracking("planner", "task-001")
        tracker.record_tool_call(id1, "search", 100, True)
        tracker.finish_tracking(id1)

        stats = tracker.get_statistics()

        assert stats["enabled"] is True
        assert stats["active_sessions"] == 0
        assert stats["total_completed"] == 1
        assert stats["total_tool_calls"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])