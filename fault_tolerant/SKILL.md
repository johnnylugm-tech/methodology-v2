# SKILL.md - Fault Tolerant

## Metadata

```yaml
name: fault-tolerant
description: 容錯系統。當需要錯誤處理、重試機制、熔斷器，或檢測 LLM hallucination 時使用。
```

## When to Use

- API 呼叫可能失敗
- LLM 輸出需要驗證
- 需要熔斷機制
- 需要備援方案
- 需要 SLA 追蹤

## Quick Start

```python
from fault_tolerant import FaultTolerantExecutor, RetryConfig, OutputValidator, SLATracker

# 基本重試
executor = FaultTolerantExecutor(
    retry_config=RetryConfig(max_attempts=3),
    timeout=30.0,
    fallback=lambda: "backup_result"
)
result = await executor.execute(risky_function)

# Output Validator (LLM Hallucination 檢測)
validator = OutputValidator()
validator.add_keyword_rule(["forbidden", "banned"])
validator.add_json_structure_rule(["status", "data"])
is_valid, errors = validator.validate(llm_output)

# SLA 追蹤
executor = FaultTolerantExecutor(name="api_call", sla_level="high")  # 5秒 SLA
result = await executor.execute(risky_function)
executor.sla_tracker.print_sla_violations()
```

## Key Concepts

| Feature | Description |
|---------|-------------|
| Retry | 指數退避重試 |
| Circuit Breaker | 熔斷機制 |
| Fallback | 備援方案 |
| Output Validator | LLM hallucination 檢測 |
| SLA Tracker | 任務 SLA 層級追蹤 |

## SLA Levels

| Level | Threshold |
|-------|-----------|
| critical | 1 秒 |
| high | 5 秒 |
| medium | 30 秒 |
| low | 2 分鐘 |

## CLI

```bash
# 測試熔斷器
python fault_tolerant.py --test-circuit

# 測試 SLA 追蹤
python fault_tolerant.py --test-sla --sla-level high

# 查看 SLA 狀態
python fault_tolerant.py --sla-status
```

## Integration

```python
# 與 smart_orchestrator 整合
orchestrator.use_fault_tolerant(True)
```

## Related

- failover_manager.py
- auto_quality_gate.py
- smart_orchestrator.py
