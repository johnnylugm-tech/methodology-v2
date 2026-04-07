# HITL Controller

> Human-in-the-Loop 控制中心 - 為每個 Agent 產出提供人類把關

## 快速開始

```python
from hitl_controller import HITLController, AgentOwner, OutputStatus

# 初始化
controller = HITLController()

# 註冊負責人
owner = AgentOwner(
    owner_id="owner-1",
    name="John",
    email="john@example.com",
    role="Manager"
)
controller.register_owner(owner)

# 指派 Agent
controller.assign_agent_to_owner("agent-dev-1", "owner-1")

# 建立並提交產出
output_id = controller.create_output("agent-dev-1", "task-1", {"result": "data"})
controller.submit_for_review(output_id)

# 批准
controller.approve_output(output_id, "owner-1")
```

## 核心概念

### Owner (負責人)

對特定 Agent 或任務負責的人類。

```python
owner = AgentOwner(
    owner_id="owner-1",
    name="John",
    email="john@example.com",
    role="Manager",
    agents=["agent-1", "agent-2"],  # 負責的 Agents
    escalation_timeout=3600  # 秒，超時後升級
)
```

### Output (產出)

Agent 生成的任何內容。

```python
output = Output(
    id="output-abc123",
    agent_id="agent-1",
    owner_id="owner-1",
    task_id="task-1",
    status=OutputStatus.PENDING_REVIEW,
    created_at=datetime.now()
)
```

### 狀態流

```
DRAFT → PENDING_REVIEW → APPROVED → COMPLETED
                ↓
        REVISION_REQUESTED → (回到 DRAFT)
                ↓
           ESCALATED
```

## API 參考

### Owner 管理

| 方法 | 說明 |
|------|------|
| `register_owner(owner)` | 註冊負責人 |
| `get_owner(owner_id)` | 取得負責人 |
| `list_owners()` | 列出所有負責人 |
| `assign_agent_to_owner(agent_id, owner_id)` | 指派 Agent 給負責人 |
| `get_owner_for_agent(agent_id)` | 取得 Agent 的負責人 |

### 產出管理

| 方法 | 說明 |
|------|------|
| `create_output(agent_id, task_id, content)` | 建立產出 |
| `submit_for_review(output_id)` | 提交審批 |
| `approve_output(output_id, owner_id)` | 批准產出 |
| `request_revision(output_id, owner_id, feedback)` | 要求修改 |
| `complete_output(output_id)` | 完成產出 |
| `escalate_output(output_id, reason, level)` | 升級產出 |

### 查詢

| 方法 | 說明 |
|------|------|
| `get_output(output_id)` | 取得產出 |
| `get_outputs_by_agent(agent_id)` | 取得 Agent 的產出 |
| `get_outputs_by_owner(owner_id)` | 取得負責人的產出 |
| `get_pending_reviews(owner_id)` | 取得待審批列表 |
| `get_statistics()` | 取得統計 |
| `generate_report()` | 生成報告 |

## CLI 使用

```bash
# 註冊負責人
python cli.py hitl register owner-1 --name "John" --email "john@example.com" --role "Manager"

# 指派 Agent
python cli.py hitl assign agent-1 --agent-id agent-1 --owner-id owner-1

# 列出待審批
python cli.py hitl list pending

# 批准產出
python cli.py hitl approve output-123 --approver owner-1

# 要求修改
python cli.py hitl reject output-123 --approver owner-1 --feedback "需要修改..."

# 查看統計
python cli.py hitl stats

# 生成報告
python cli.py hitl report
```

## 整合

### AgentTeam 整合

```python
from agent_team import AgentTeam
from hitl_controller import HITLController
from hitl_workflow import AgentTeamHITLAdapter

team = AgentTeam()
controller = HITLController()
adapter = AgentTeamHITLAdapter(team, controller)

# 為 Agent 實例指派負責人
adapter.assign_owner_to_agent_instance("instance-1", "owner-1")

# 任務完成時自動觸發 HITL
output_id = adapter.on_task_completed("instance-1", "task-123", result)
```

### MessageBus 整合

```python
from message_bus import MessageBus
from hitl_controller import HITLController
from hitl_workflow import MessageBusHITLAdapter

bus = MessageBus()
controller = HITLController()
adapter = MessageBusHITLAdapter(bus, controller)
```

## 持久化

```python
# 自動保存到檔案
controller = HITLController(storage_path=".hitl_state.json")

# 狀態會自動在變更時保存
controller.register_owner(owner)
# -> 保存到 .hitl_state.json

# 重啟後自動載入
controller = HITLController(storage_path=".hitl_state.json")
# -> 從 .hitl_state.json 載入狀態
```

## 統計指標

```python
stats = controller.get_statistics()
# {
#     "total_outputs": 42,
#     "by_status": {
#         "draft": 5,
#         "pending_review": 3,
#         "approved": 28,
#         ...
#     },
#     "total_owners": 5,
#     "total_agents_assigned": 12,
#     "pending_reviews": 3,
#     "avg_revision_count": 0.5
# }
```

---

*這個 Skill 為 methodology-v2 提供了完整的人類介入機制*
