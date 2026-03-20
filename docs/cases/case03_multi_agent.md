# 案例三：Multi-Agent 協作

## 情境描述

需要讓多個 Agent 协同完成複雜任務，包括定義角色、通訊協調、狀態共享、錯誤處理。

---

## 案例 3.1：Hierarchical 協作模式

### 背景
大型專案需要一個 Coordinator Agent 協調多個 Worker Agent。

### 使用方式

```python
from methodology import (
    MethodologyCore,
    AgentTeam, AgentRole, AgentDefinition, AgentCapability, AgentPermission,
    MessageBus, MessageType,
    WorkflowGraph
)

core = MethodologyCore()

# 1. 建立 Agent 團隊
team = AgentTeam(name="電商系統開發團隊")

# Coordinator
coordinator = AgentDefinition(
    name="Project Coordinator",
    role=AgentRole.ARCHITECT,
    capabilities=[AgentCapability.PLANNING, AgentCapability.DECISION],
    permissions=[AgentPermission.MANAGE_TASKS, AgentPermission.VIEW_ALL]
)

# Workers
dev = AgentDefinition(
    name="Backend Developer",
    role=AgentRole.DEVELOPER,
    capabilities=[AgentCapability.CODING, AgentCapability.API_DESIGN],
    permissions=[AgentPermission.READ_CODE, AgentPermission.WRITE_CODE]
)

tester = AgentDefinition(
    name="QA Engineer",
    role=AgentRole.TESTER,
    capabilities=[AgentCapability.TESTING, AgentCapability.BUG_REPORT],
    permissions=[AgentPermission.READ_CODE, AgentPermission.EXECUTE_TESTS]
)

team.register(coordinator)
team.register(dev)
team.register(tester)

# 2. 建立工作流
wf = core.workflow
wf.add_node("coordinate", "協調任務分配", role=AgentRole.ARCHITECT)
wf.add_node("develop", "實作功能", role=AgentRole.DEVELOPER)
wf.add_node("test", "測試驗證", role=AgentRole.TESTER)
wf.add_node("review", "最終審查", role=AgentRole.REVIEWER)

wf.add_edge("coordinate", "develop")
wf.add_edge("develop", "test")
wf.add_edge("test", "review")

# 3. 執行工作流
result = wf.execute()
print(f"執行結果: {result['status']}")
print(f"總任務數: {result['total_tasks']}")
```

### 輸出範例
```
執行結果: completed
總任務數: 4
```

---

## 案例 3.2：Agent 間通訊

### 背景
當一個 Agent 完成任務後，需要通知其他 Agent 並傳遞結果。

### 使用方式

```python
from methodology import MessageBus, MessageType, AgentMessage

bus = MessageBus()

# Agent A 發送訊息給 Agent B
msg = AgentMessage(
    sender="dev-agent",
    recipient="test-agent",
    type=MessageType.HANDOFF,
    content={
        "task_id": "task-123",
        "artifacts": ["login_module.py", "auth_api.py"],
        "status": "completed",
        "next_action": "run_unit_tests"
    }
)

bus.send(msg)

# Agent B 接收訊息
inbox = bus.get_messages("test-agent")
print(f"收到 {len(inbox)} 條訊息")

for m in inbox:
    print(f"\n來自: {m.sender}")
    print(f"類型: {m.type.value}")
    print(f"內容: {m.content}")

# 發送回應
response = AgentMessage(
    sender="test-agent",
    recipient="dev-agent",
    type=MessageType.RESPONSE,
    content={
        "task_id": "task-123",
        "test_result": "passed",
        "coverage": "85%"
    }
)
bus.send(response)
```

### 輸出範例
```
收到 1 條訊息

來自: dev-agent
類型: HANDOFF
內容: {'task_id': 'task-123', 'artifacts': [...], 'status': 'completed'}
```

---

## 案例 3.3：共享狀態管理

### 背景
多個 Agent 需要共享上下文和狀態，確保資訊一致性。

### 使用方式

```python
from methodology import AgentState, AgentStateManager

# 建立共享狀態管理器
manager = AgentStateManager()

# 初始化專案狀態
manager.init_state("project-1", {
    "phase": "development",
    "current_sprint": 3,
    "completed_features": ["login", "logout"],
    "pending_features": ["payment", "shipping"]
})

# Agent A 更新狀態
manager.update("project-1", {
    "agent": "dev-agent",
    "action": "complete_feature",
    "feature": "payment"
})

# Agent B 讀取狀態
state = manager.get_state("project-1")
print(f"目前階段: {state['phase']}")
print(f"已完成的功能: {', '.join(state['completed_features'])}")
print(f"待完成: {', '.join(state['pending_features'])}")

# 監控狀態變化
history = manager.get_history("project-1")
print(f"\n狀態變化記錄: {len(history)} 筆")
```

### 輸出範例
```
目前階段: development
已完成的功能: login, logout, payment
待完成: shipping

狀態變化記錄: 3 筆
```

---

## 相關功能

| 功能 | 模組 |
|------|------|
| Agent 定義 | `AgentTeam`, `AgentDefinition` |
| 通訊協議 | `MessageBus`, `AgentCommunication` |
| 狀態管理 | `AgentState`, `AgentStateManager` |
| 工作流引擎 | `WorkflowGraph` |
| 審批流程 | `ApprovalFlow` |
