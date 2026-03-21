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

## 使用方式

```python
from fault_tolerant import FaultTolerantExecutor, RetryConfig

executor = FaultTolerantExecutor(
    name="api_call",
    retry_config=RetryConfig(max_attempts=3),
    timeout=30.0,
    fallback=lambda: "backup_result"
)

result = await executor.execute(risky_function)
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
