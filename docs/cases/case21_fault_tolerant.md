# 案例 21：Fault Tolerant - 容錯系統

## 概述

企業級錯誤處理機制，為 AI Agent 提供可靠性保障。

## 核心功能

| 功能 | 說明 |
|------|------|
| **Retry** | 指數退避重試 |
| **Circuit Breaker** | 熔斷機制 |
| **Fallback** | 備援方案 |
| **Timeout** | 逾時保護 |
| **Output Validator** | 檢測 LLM hallucination |

## 使用方式

### 基本重試

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

### 熔斷器

```python
from fault_tolerant import CircuitBreaker, CircuitBreakerConfig

cb = CircuitBreaker("api_service", CircuitBreakerConfig(
    failure_threshold=5,
    timeout=30.0
))
```

### Output Validator (LLM Hallucination 檢測)

```python
from fault_tolerant import OutputValidator

validator = OutputValidator()

# 關鍵字規則
validator.add_keyword_rule(["forbidden", "banned"])

# JSON 結構規則
validator.add_json_structure_rule(["status", "data"])

# 驗證輸出
is_valid, errors = validator.validate(llm_output)
```

## Circuit Breaker 狀態

```
CLOSED → 正常（連續失敗 5 次）
   ↓
OPEN → 熔斷（30 秒後）
   ↓
HALF_OPEN → 測試（2 次成功後關閉）
   ↓
CLOSED → 恢復正常
```

## LLM Hallucination 檢測

```python
# 檢測無意義輸出
validator.add_rule(
    name="meaningful_check",
    check=lambda x: len(str(x)) > 10 and str(x) != "N/A",
    error_message="Output is meaningless"
)

# 檢測事實一致性
validator.add_json_structure_rule(["claim", "source", "confidence"])
```

## 與現有模組整合

| 模組 | 整合點 |
|------|--------|
| parallel_executor | 任務執行錯誤處理 |
| smart_router | API 呼叫重試 |
| auto_quality_gate | 輸出驗證 |

## 相關模組

- failover_manager.py
- auto_quality_gate.py
- smart_orchestrator.py
