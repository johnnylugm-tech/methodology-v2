# Fault Tolerant - 容錯系統

為 AI Agent 提供企業級的錯誤處理機制。

## 核心功能

| 功能 | 說明 |
|------|------|
| **Retry** | 指數退避重試 |
| **Circuit Breaker** | 熔斷機制 |
| **Fallback** | 備援方案 |
| **Timeout** | 逾時保護 |
| **Output Validator** | 輸出驗證（檢測 hallucination）|
| **SLA Tracker** | 任務 SLA 層級追蹤 |

## SLA 等級

| 等級 | 時間閾值 |
|------|----------|
| critical | 1 秒 |
| high | 5 秒 |
| medium | 30 秒 |
| low | 2 分鐘 |

## 使用方式

```python
from fault_tolerant import FaultTolerantExecutor, RetryConfig, SLATracker

executor = FaultTolerantExecutor(
    name="api_call",
    retry_config=RetryConfig(max_attempts=3),
    timeout=30.0,
    fallback=lambda: "backup_result",
    sla_level="high"  # 5 秒 SLA
)

result = await executor.execute(risky_function)
executor.sla_tracker.print_sla_violations()
```

## Circuit Breaker

```python
from fault_tolerant import CircuitBreaker, CircuitBreakerConfig

cb = CircuitBreaker("api_service", CircuitBreakerConfig(failure_threshold=5, timeout=30.0))
```

## Output Validator

```python
from fault_tolerant import OutputValidator

validator = OutputValidator()
validator.add_keyword_rule(["forbidden", "banned"])
validator.add_json_structure_rule(["status", "data"])
```

## SLA Tracker

```python
from fault_tolerant import SLATracker

tracker = SLATracker(default_level="medium")
tracker.track("task_1", "critical")  # 1 秒 SLA
tracker.track("task_2", "high")       # 5 秒 SLA

is_violated, elapsed, sla = tracker.check_sla("task_1")
tracker.print_sla_violations()
```
