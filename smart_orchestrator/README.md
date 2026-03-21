# Smart Orchestrator - 智能任務協調器

協調多個 AI Agent 協作完成複雜任務。

## 核心功能

| 功能 | 說明 |
|------|------|
| **任務規劃** | 自動分解複雜任務 |
| **Agent 調度** | 智慧分配任務給 Agent |
| **依賴管理** | 處理任務間依賴關係 |
| **負載均衡** | 避免 Agent 過載 |
| **狀態追蹤** | 實時監控執行狀態 |

## 概念

```
┌─────────────────────────────────────────────┐
│           Smart Orchestrator                 │
│                                             │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐    │
│  │Research │→ │ Analyze │→ │  Write  │    │
│  │  Agent  │  │  Agent  │  │  Agent  │    │
│  └─────────┘  └─────────┘  └─────────┘    │
└─────────────────────────────────────────────┘
```

## 使用方式

```python
from smart_orchestrator import SmartOrchestrator

# 創建協調器
orchestrator = SmartOrchestrator(max_concurrent=3)

# 註冊 Agents
orchestrator.register_agent("researcher", "研究 Agent", "research")
orchestrator.register_agent("analyst", "分析 Agent", "analysis")

# 建立任務
task1 = orchestrator.create_task("研究", "研究任務", "research")
task2 = orchestrator.create_task("分析", "分析任務", "analysis", dependencies=[task1])

# 執行
result = await orchestrator.execute()
print(f"完成: {result.completed_tasks}/{result.total_tasks}")
```

## 整合

可與 fault_tolerant 整合：

```python
from smart_orchestrator import SmartOrchestrator
from fault_tolerant import FaultTolerantExecutor

orchestrator = SmartOrchestrator()
# 每個任務包裝容錯
```
