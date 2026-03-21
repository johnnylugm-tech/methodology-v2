"""Enhanced Observability Module for methodology-v2
Refactored with proper framework integration
"""
import json, time, uuid
from datetime import datetime
from pathlib import Path

# Framework integration via direct import
try:
    import sys
    sys.path.insert(0, '/workspace/methodology-v2')
    
    # Try importing from methodology package
    from methodology import ErrorClassifier, ErrorLevel
    FRAMEWORK_AVAILABLE = True
except ImportError:
    # Fallback: define compatible interfaces
    FRAMEWORK_AVAILABLE = False
    
    class ErrorLevel:
        L1 = "L1"
        L2 = "L2"
        L3 = "L3"
        L4 = "L4"
    
    class ErrorClassifier:
        """Fallback classifier when framework not available"""
        TRANSIENT_KEYWORDS = ["timeout", "network", "503", "429"]
        
        def classify(self, error):
            error_str = str(error).lower()
            if any(kw in error_str for kw in self.TRANSIENT_KEYWORDS):
                return ErrorLevel.L1
            return ErrorLevel.L2

# Storage
TRACE_DIR = Path("/tmp/traces")
TRACE_DIR.mkdir(exist_ok=True)

class Span:
    """Trace span with framework integration"""
    def __init__(self, trace_id: str, name: str, task_id: str = None):
        self.trace_id = trace_id
        self.span_id = uuid.uuid4().hex[:8]
        self.name = name
        self.task_id = task_id
        self.start_time = time.time()
        self.end_time = None
        self.tags = {}
        self.status = "started"
        self.error = None
        self._lifecycle = None
    
    def set_lifecycle(self, lifecycle):
        """Integrate with TaskLifecycle"""
        self._lifecycle = lifecycle
    
    def finish(self):
        self.end_time = time.time()
        self.status = "completed"
        if self._lifecycle:
            self._lifecycle.complete_task()
    
    def set_tag(self, key: str, value: str):
        self.tags[key] = value
    
    def set_error(self, error: Exception):
        self.error = error
        self.status = "error"
        if self._lifecycle:
            classifier = ErrorClassifier()
            level = classifier.classify(error)
            self._lifecycle.fail_task(str(error), level)
    
    def to_dict(self):
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "name": self.name,
            "task_id": self.task_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.end_time - self.start_time if self.end_time else None,
            "tags": self.tags,
            "status": self.status,
            "error": str(self.error) if self.error else None,
            "framework_integrated": FRAMEWORK_AVAILABLE
        }

class Tracer:
    """Distributed tracing with framework integration"""
    
    def __init__(self, name: str, task_id: str = None):
        self.name = name
        self.task_id = task_id or str(uuid.uuid4())
        self.trace_id = uuid.uuid4().hex[:16]
        self.current_span: Span = None
        
        # Try to use framework's TaskLifecycle
        self._lifecycle = None
        if FRAMEWORK_AVAILABLE:
            try:
                from methodology import TaskLifecycle
                self._lifecycle = TaskLifecycle(task_id=self.task_id)
            except ImportError:
                pass  # Framework not available, use fallback
    
    def __enter__(self) -> Span:
        span = Span(self.trace_id, self.name, self.task_id)
        if self._lifecycle:
            span.set_lifecycle(self._lifecycle)
            self._lifecycle.start_task(self.name)
        self.current_span = span
        return span
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.current_span:
            if exc_val:
                self.current_span.set_error(exc_val)
            else:
                self.current_span.finish()
            self._save_span(self.current_span)
            self.current_span = None
    
    def _save_span(self, span: Span):
        filename = TRACE_DIR / f"{span.trace_id}.jsonl"
        with open(filename, "a") as f:
            f.write(json.dumps(span.to_dict()) + "\n")

class MetricsCollector:
    """Metrics collection with framework Monitor integration"""
    
    def __init__(self):
        self._metrics = {}
        self._counters = {}
        self._gauges = {}
        
        # Try to use framework Monitor
        self._monitor = None
        if FRAMEWORK_AVAILABLE:
            try:
                from methodology import Monitor
                self._monitor = Monitor()
            except ImportError:
                pass  # Framework not available
    
    def increment(self, name: str, value: int = 1):
        self._counters[name] = self._counters.get(name, 0) + value
        if self._monitor:
            self._monitor.track_metric(name, self._counters[name])
    
    def gauge(self, name: str, value: float):
        self._gauges[name] = value
        if self._monitor:
            self._monitor.track_metric(name, value)
    
    def histogram(self, name: str, value: float):
        if name not in self._metrics:
            self._metrics[name] = []
        self._metrics[name].append(value)
        if self._monitor:
            self._monitor.track_metric(name, value)
    
    def record(self, name: str, value: float):
        self.histogram(name, value)
    
    def get_stats(self, name: str) -> dict:
        values = self._metrics.get(name, [])
        if not values:
            return {"count": 0}
        return {
            "count": len(values),
            "min": min(values),
            "max": max(values),
            "avg": sum(values) / len(values)
        }
    
    def get_all(self) -> dict:
        return {
            "counters": self._counters.copy(),
            "gauges": self._gauges.copy(),
            "histograms": {k: self.get_stats(k) for k in self._metrics},
            "framework_integrated": FRAMEWORK_AVAILABLE
        }

class Observer:
    """Structured logging with framework ErrorHandler integration"""
    
    def __init__(self):
        self._logs = []
        
        # Try to use framework ErrorHandler
        self._error_handler = None
        if FRAMEWORK_AVAILABLE:
            try:
                from methodology import ErrorHandler
                self._error_handler = ErrorHandler()
            except ImportError:
                pass  # Framework not available
    
    def log(self, event: str, data: dict):
        entry = {
            "timestamp": datetime.now().isoformat(),
            "event": event,
            "data": data,
            "framework_integrated": FRAMEWORK_AVAILABLE
        }
        self._logs.append(entry)
# # #         print(f"[{event}] {json.dumps(data, ensure_ascii=False)}")
    
    def handle_error(self, error: Exception, context: dict = None) -> str:
        """Handle error using framework if available"""
        if self._error_handler:
            level = self._error_handler.handle_error(error, context)
            return level.value if hasattr(level, 'value') else str(level)
        else:
            # Fallback to local classifier
            classifier = ErrorClassifier()
            level = classifier.classify(error)
            self.log("error", {
                "error": str(error),
                "level": level,
                "context": context or {}
            })
            return str(level)
    
    def get_logs(self, event: str = None) -> list:
        if event:
            return [l for l in self._logs if l["event"] == event]
        return self._logs

# Demo
if __name__ == "__main__":
# # #     print("=== Observability with Framework Integration ===")
# # #     print(f"Framework Available: {FRAMEWORK_AVAILABLE}")
    
    # Trace example with lifecycle
    with Tracer("agent_execution", task_id="task_001") as span:
        span.set_tag("agent", "coder")
        span.set_tag("task", "debug")
        time.sleep(0.1)
    
    # Metrics
    metrics = MetricsCollector()
    metrics.increment("requests")
    metrics.histogram("latency_ms", 150)
    metrics.gauge("active_agents", 5)
# # #     print(f"\nMetrics: {json.dumps(metrics.get_all(), indent=2)}")
    
    # Error handling
    observer = Observer()
    try:
        raise Exception("network timeout")
    except Exception as e:
        level = observer.handle_error(e, {"task": "test"})
# # #         print(f"\nHandled error level: {level}")
    
# # #     print("\n✅ Observability (with framework integration) ready!")
