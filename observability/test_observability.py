"""Tests for observability module"""
import pytest
import time
import uuid
from observability import Tracer, MetricsCollector, Observer, DistributedTracer, UnifiedLogger

class TestTracer:
    """Test Tracer"""
    
    def test_tracer_context(self):
        """Test tracer context manager"""
        with Tracer("test_task") as span:
            span.set_tag("key", "value")
        assert span.name == "test_task"
        assert span.tags["key"] == "value"
    
    def test_tracer_error(self):
        """Test tracer error handling"""
        try:
            with Tracer("test_error") as span:
                raise ValueError("test error")
        except ValueError:
            pass
        assert span.status == "error"

class TestMetricsCollector:
    """Test MetricsCollector"""
    
    def test_increment(self):
        """Test increment"""
        collector = MetricsCollector()
        collector.increment("test_counter")
        assert "test_counter" in collector._counters
    
    def test_histogram(self):
        """Test histogram"""
        collector = MetricsCollector()
        collector.histogram("test_hist", 100)
        assert "test_hist" in collector._metrics
    
    def test_gauge(self):
        """Test gauge"""
        collector = MetricsCollector()
        collector.gauge("test_gauge", 50)
        assert collector._gauges["test_gauge"] == 50

class TestObserver:
    """Test Observer"""
    
    def test_log(self):
        """Test logging"""
        observer = Observer()
        observer.log("test_event", {"key": "value"})
        logs = observer.get_logs()
        assert len(logs) > 0
    
    def test_handle_error(self):
        """Test error handling"""
        observer = Observer()
        error = ValueError("test")
        level = observer.handle_error(error, {"context": "test"})
        assert level is not None

class TestDistributedTracer:
    """Test DistributedTracer"""
    
    def test_trace_request(self):
        """Test starting a distributed trace"""
        dt = DistributedTracer()
        request_id = f"test_req_{uuid.uuid4().hex[:8]}"
        span_id = dt.trace_request(request_id, "test_agent", metadata={"task": "test"})
        assert span_id is not None
        assert request_id in dt.list_active_traces()
    
    def test_trace_with_parent(self):
        """Test trace with parent span"""
        dt = DistributedTracer()
        request_id = f"test_req_{uuid.uuid4().hex[:8]}"
        parent_id = dt.trace_request(request_id, "parent_agent")
        child_id = dt.trace_request(request_id, "child_agent", parent_span_id=parent_id)
        assert parent_id != child_id
    
    def test_end_span(self):
        """Test ending a span"""
        dt = DistributedTracer()
        request_id = f"test_req_{uuid.uuid4().hex[:8]}"
        span_id = dt.trace_request(request_id, "test_agent")
        dt.end_span(request_id, span_id, metadata={"status": "done"})
        tree = dt.get_trace_tree(request_id)
        assert tree["request_id"] == request_id
    
    def test_get_trace_tree(self):
        """Test getting trace tree"""
        dt = DistributedTracer()
        request_id = f"test_req_{uuid.uuid4().hex[:8]}"
        dt.trace_request(request_id, "agent_1")
        tree = dt.get_trace_tree(request_id)
        assert "request_id" in tree
        assert tree["request_id"] == request_id


class TestUnifiedLogger:
    """Test UnifiedLogger"""
    
    def test_log_levels(self):
        """Test different log levels"""
        ul = UnifiedLogger()
        ul.debug("agent1", "event1", {"key": "value"})
        ul.info("agent1", "event2", {"key": "value"})
        ul.warn("agent1", "event3", {"key": "value"})
        ul.error("agent1", "event4", {"key": "value"})
        logs = ul.get_logs(agent_id="agent1")
        assert len(logs) >= 4
    
    def test_log_with_request_id(self):
        """Test logging with request_id"""
        ul = UnifiedLogger()
        request_id = f"req_{uuid.uuid4().hex[:8]}"
        ul.info("agent1", "event1", {}, request_id=request_id)
        ul.info("agent2", "event2", {}, request_id=request_id)
        logs = ul.get_logs(request_id=request_id)
        assert len(logs) == 2
    
    def test_level_filter(self):
        """Test log level filtering"""
        ul = UnifiedLogger()
        ul.debug("agent1", "debug_event")
        ul.info("agent1", "info_event")
        ul.error("agent1", "error_event")
        errors = ul.get_logs(level="ERROR")
        for log in errors:
            assert log["level"] == "ERROR"
    
    def test_singleton(self):
        """Test UnifiedLogger is singleton"""
        ul1 = UnifiedLogger()
        ul2 = UnifiedLogger()
        assert ul1 is ul2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
