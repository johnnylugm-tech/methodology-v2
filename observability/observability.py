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

# =============================================================================
# Distributed Tracing - Cross-Agent Request Tracking
# =============================================================================

DT_TRACE_FILE = Path("/tmp/distributed_traces.jsonl")

class DistributedTracer:
    """分散式追蹤 - 跨 Agent 請求追蹤
    
    用於追蹤單一請求在多個 Agent 之間的流轉，構成完整呼叫鏈。
    所有追蹤資料寫入同一位置（/tmp/distributed_traces.jsonl），
    供 get_trace_tree() 重建完整呼叫樹。
    """
    
    def __init__(self):
        self._active_traces: dict[str, dict] = {}
    
    def trace_request(self, request_id: str, agent_id: str, parent_span_id: str = None, metadata: dict = None) -> str:
        """開始追蹤一個跨 Agent 請求
        
        Args:
            request_id: 請求唯一識別碼（由調用方生成）
            agent_id: 當前 Agent 的識別碼
            parent_span_id: 父 span ID（可選，用於巢狀追蹤）
            metadata: 額外元資料
        
        Returns:
            span_id: 當前 span 的 ID
        """
        if request_id not in self._active_traces:
            self._active_traces[request_id] = {
                "request_id": request_id,
                "start_time": time.time(),
                "spans": []
            }
        
        span_id = uuid.uuid4().hex[:12]
        span = {
            "span_id": span_id,
            "agent_id": agent_id,
            "parent_span_id": parent_span_id,
            "start_time": time.time(),
            "end_time": None,
            "duration_ms": None,
            "metadata": metadata or {}
        }
        
        self._active_traces[request_id]["spans"].append(span)
        self._save_trace_event(request_id, "span_start", span)
        return span_id
    
    def end_span(self, request_id: str, span_id: str, metadata: dict = None):
        """結束一個 span
        
        Args:
            request_id: 請求 ID
            span_id: 要結束的 span ID
            metadata: 額外元資料
        """
        if request_id not in self._active_traces:
            return
        
        trace = self._active_traces[request_id]
        for span in trace["spans"]:
            if span["span_id"] == span_id:
                span["end_time"] = time.time()
                span["duration_ms"] = (span["end_time"] - span["start_time"]) * 1000
                if metadata:
                    span["metadata"].update(metadata)
                self._save_trace_event(request_id, "span_end", span)
                break
        
        # 如果所有 span 都結束，標記請求完成
        all_done = all(s["end_time"] is not None for s in trace["spans"])
        if all_done:
            trace["end_time"] = time.time()
            trace["total_duration_ms"] = (trace["end_time"] - trace["start_time"]) * 1000
            self._save_trace_event(request_id, "request_complete", trace)
    
    def get_trace_tree(self, request_id: str) -> dict:
        """取得完整呼叫鏈（呼叫樹）
        
        Args:
            request_id: 請求 ID
        
        Returns:
            呼叫樹結構，包含所有 span 的父子關係
        """
        if request_id not in self._active_traces:
            # 嘗試從檔案讀取
            return self._load_trace_from_file(request_id)
        
        trace = self._active_traces[request_id]
        return self._build_tree(trace)
    
    def _build_tree(self, trace: dict) -> dict:
        """從 spans 列表構建呼叫樹"""
        spans = trace["spans"]
        span_map = {s["span_id"]: s for s in spans}
        
        # 建立父子關係
        root_spans = []
        for span in spans:
            if span["parent_span_id"] is None:
                root_spans.append(span)
            else:
                parent = span_map.get(span["parent_span_id"])
                if parent:
                    if "children" not in parent:
                        parent["children"] = []
                    parent["children"].append(span)
        
        return {
            "request_id": trace["request_id"],
            "start_time": trace["start_time"],
            "end_time": trace.get("end_time"),
            "total_duration_ms": trace.get("total_duration_ms"),
            "root_spans": root_spans,
            "span_count": len(spans)
        }
    
    def _save_trace_event(self, request_id: str, event_type: str, data: dict):
        """寫入追蹤事件到統一檔案"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "request_id": request_id,
            "event_type": event_type,
            **data
        }
        with open(DT_TRACE_FILE, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def _load_trace_from_file(self, request_id: str) -> dict:
        """從檔案載入追蹤記錄並重建呼叫樹"""
        if not DT_TRACE_FILE.exists():
            return {"error": f"No trace found for request_id: {request_id}"}
        
        spans = []
        with open(DT_TRACE_FILE, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if entry.get("request_id") == request_id and entry.get("event_type") == "span_start":
                        spans.append(entry)
                except json.JSONDecodeError:
                    continue
        
        if not spans:
            return {"error": f"No trace found for request_id: {request_id}"}
        
        trace = {
            "request_id": request_id,
            "start_time": spans[0].get("start_time"),
            "spans": spans
        }
        return self._build_tree(trace)
    
    def list_active_traces(self) -> list[str]:
        """列出所有活躍追蹤的 request_id"""
        return list(self._active_traces.keys())


# =============================================================================
# Unified Logger - 統一日誌格式
# =============================================================================

UL_LOG_FILE = Path("/tmp/unified_logs.jsonl")

class UnifiedLogger:
    """統一日誌格式 - 所有 Agent 的日誌輸出到同一位置
    
    統一格式：
    {
        "timestamp": "ISO8601",
        "level": "INFO|WARN|ERROR|DEBUG",
        "agent_id": "agent_name",
        "event": "event_name",
        "metadata": {...},
        "request_id": "可選的跨請求追蹤ID"
    }
    """
    
    _instance = None
    _levels = ["DEBUG", "INFO", "WARN", "ERROR"]
    
    def __new__(cls):
        """Singleton 確保只有一個 UnifiedLogger 實例"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._logs = []
            cls._instance._min_level = "INFO"
        return cls._instance
    
    def __init__(self):
        self._logs = []
        self._min_level = "INFO"
    
    def set_min_level(self, level: str):
        """設定最小日誌等級，低於此等級的日誌會被忽略"""
        if level.upper() in self._levels:
            self._min_level = level.upper()
    
    def log(self, level: str, agent_id: str, event: str, metadata: dict = None, request_id: str = None):
        """寫入統一日誌
        
        Args:
            level: 日誌等級（DEBUG, INFO, WARN, ERROR）
            agent_id: 當前 Agent 的識別碼
            event: 事件名稱（例：agent_start, tool_call, error）
            metadata: 事件相關的額外資料
            request_id: 可選的請求追蹤 ID（用於關聯分散式追蹤）
        """
        level = level.upper()
        if level not in self._levels:
            level = "INFO"
        
        # 等級過濾
        level_order = {l: i for i, l in enumerate(self._levels)}
        if level_order.get(level, 0) < level_order.get(self._min_level, 1):
            return
        
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "agent_id": agent_id,
            "event": event,
            "metadata": metadata or {},
            "request_id": request_id
        }
        
        self._logs.append(entry)
        self._write_to_file(entry)
    
    def debug(self, agent_id: str, event: str, metadata: dict = None, request_id: str = None):
        self.log("DEBUG", agent_id, event, metadata, request_id)
    
    def info(self, agent_id: str, event: str, metadata: dict = None, request_id: str = None):
        self.log("INFO", agent_id, event, metadata, request_id)
    
    def warn(self, agent_id: str, event: str, metadata: dict = None, request_id: str = None):
        self.log("WARN", agent_id, event, metadata, request_id)
    
    def error(self, agent_id: str, event: str, metadata: dict = None, request_id: str = None):
        self.log("ERROR", agent_id, event, metadata, request_id)
    
    def _write_to_file(self, entry: dict):
        """寫入到統一日誌檔案"""
        with open(UL_LOG_FILE, "a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    
    def get_logs(self, agent_id: str = None, event: str = None, level: str = None, request_id: str = None, limit: int = 100) -> list:
        """查詢日誌
        
        Args:
            agent_id: 依 Agent ID 過濾
            event: 依事件名稱過濾
            level: 依等級過濾
            request_id: 依請求 ID 過濾
            limit: 返回最多多少筆
        
        Returns:
            過濾後的日誌列表
        """
        results = self._logs
        
        if agent_id:
            results = [r for r in results if r["agent_id"] == agent_id]
        if event:
            results = [r for r in results if r["event"] == event]
        if level:
            results = [r for r in results if r["level"] == level.upper()]
        if request_id:
            results = [r for r in results if r.get("request_id") == request_id]
        
        return results[-limit:]
    
    def read_logs_from_file(self, since: datetime = None, until: datetime = None, limit: int = 1000) -> list:
        """從檔案讀取日誌（可用於重啟後恢復）
        
        Args:
            since: 只讀取此時間之後的日誌
            until: 只讀取此時間之前的日誌
            limit: 最多讀取多少行
        
        Returns:
            日誌列表
        """
        if not UL_LOG_FILE.exists():
            return []
        
        results = []
        with open(UL_LOG_FILE, "r") as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    ts = datetime.fromisoformat(entry["timestamp"])
                    if since and ts < since:
                        continue
                    if until and ts > until:
                        continue
                    results.append(entry)
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return results[-limit:]


# =============================================================================
# Demo
# =============================================================================

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
