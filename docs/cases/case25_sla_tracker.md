# Case 25: SLA Tracker - SLA 層級追蹤

## 情境

需要追蹤 Agent 任務的響應時間，確保符合 SLA 協議。

## 解決方案

```python
from fault_tolerant import SLATracker, SLALevel

tracker = SLATracker()

# 追蹤任務
tracker.track("task-123", SLALevel.HIGH)

# 檢查 SLA
is_violated, elapsed, limit = tracker.check_sla("task-123")
if is_violated:
    print(f"SLA 違規: {elapsed:.2f}s > {limit}s")

# 查詢違規
violations = tracker.get_violation_summary()
```

## SLA 等級

| 等級 | 時間限制 | 適用場景 |
|------|---------|---------|
| CRITICAL | 1 秒 | 核心交易 |
| HIGH | 5 秒 | 即時響應 |
| MEDIUM | 30 秒 | 一般任務 |
| LOW | 120 秒 | 後台任務 |

## 與 FaultTolerantExecutor 整合

```python
executor = FaultTolerantExecutor(sla_level="high")
result = await executor.execute(task)  # 自動追蹤 SLA
```

## CLI

```bash
python fault_tolerant.py --sla-status
python fault_tolerant.py --test-sla --sla-level critical
```

## Related

- fault_tolerant.py
- SLATracker
