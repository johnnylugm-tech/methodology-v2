"""Tests for observability module"""
import pytest
import time
from observability import Tracer, MetricsCollector, Observer

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

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
