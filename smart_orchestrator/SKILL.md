# SKILL.md - Smart Orchestrator

## Metadata

```yaml
name: smart-orchestrator
description: 智能任務協調器。當需要協調多個 AI Agent 協作，或需要負載均衡時使用。
```

## When to Use

- 多個 Agent 需要協作完成任務
- 需要自動任務分配
- 需要避免 Agent 過載
- 需要實時狀態追蹤

## Quick Start

```python
from smart_orchestrator import SmartOrchestrator

orchestrator = SmartOrchestrator(max_concurrent=3)

# 註冊 Agents
orchestrator.register_agent("dev", "開發 Agent", "coding")
orchestrator.register_agent("qa", "測試 Agent", "testing")

# 建立任務
task1 = orchestrator.create_task("開發", "寫代碼", "coding")
task2 = orchestrator.create_task("測試", "測試代碼", "testing", dependencies=[task1])

# 執行
result = await orchestrator.execute()
print(f"完成: {result.completed_tasks}/{result.total_tasks}")
```

## Key Concepts

| Feature | Description |
|---------|-------------|
| 任務規劃 | 自動分解複雜任務 |
| Agent 調度 | 根據類型分配任務 |
| 負載均衡 | 選擇最低負載 Agent |
| 狀態追蹤 | 實時監控執行 |

## Integration

```python
# 與 fault_tolerant 整合
orchestrator.use_fault_tolerant(True)

# 與 three_phase_executor 整合
orchestrator.set_executor(ThreePhaseExecutor())
```

## Related

- agent_team.py
- three_phase_executor.py
- fault_tolerant.py
