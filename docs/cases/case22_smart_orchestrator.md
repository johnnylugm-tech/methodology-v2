# 案例 22：Smart Orchestrator - 智能任務協調器

## 概述

協調多個 AI Agent 協作完成複雜任務，具有任務規劃、負載均衡和狀態追蹤功能。

## 核心功能

| 功能 | 說明 |
|------|------|
| **任務規劃** | 自動分解複雜任務 |
| **Agent 調度** | 智慧分配任務給 Agent |
| **依賴管理** | 處理任務間依賴關係 |
| **負載均衡** | 避免 Agent 過載 |
| **狀態追蹤** | 實時監控執行狀態 |

## 架構圖

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
orchestrator.register_agent("writer", "寫作 Agent", "writing")

# 建立任務
task1 = orchestrator.create_task("研究", "研究任務", "research")
task2 = orchestrator.create_task("分析", "分析任務", "analysis", dependencies=[task1])
task3 = orchestrator.create_task("寫作", "寫作任務", "writing", dependencies=[task2])

# 執行
result = await orchestrator.execute()
print(f"完成: {result.completed_tasks}/{result.total_tasks}")
```

## 負載均衡

```python
# 選擇負載最低的可用 Agent
available = orchestrator.get_available_agent("research")
# → 返回負載最低的 researcher
```

## 與 FaultTolerant 整合

```python
from smart_orchestrator import SmartOrchestrator
from fault_tolerant import FaultTolerantExecutor

orchestrator = SmartOrchestrator()

# 每個任務包裝容錯
orchestrator.use_fault_tolerant(True)
```

## 與現有模組整合

| 模組 | 整合點 |
|------|--------|
| agent_team | Agent 註冊與管理 |
| three_phase_executor | 任務執行協調 |
| fault_tolerant | 錯誤處理 |

## 執行流程

```
任務建立
    ↓
依賴檢查
    ↓
選擇可用 Agent（負載最低）
    ↓
執行（可並行）
    ↓
結果聚合
    ↓
完成/失敗追蹤
```

## 相關模組

- agent_team.py
- three_phase_executor.py
- fault_tolerant.py
