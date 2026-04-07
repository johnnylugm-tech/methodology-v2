# Case 31: HITL (Human-in-the-Loop) 人類介入系統

## 概述

HITL (Human-in-the-Loop) 系統讓人類能夠介入 Agent 的工作流程，確保每個 Agent 產出都有負責人把關，實現「AI 做事，人類負責」的協作模式。

## 什麼是 HITL？

HITL 是一種將人類判斷整合到自動化流程中的機制。在 Multi-Agent 系統中，Agent 產出的內容需要經過人類審批才能繼續流程，確保品質和合規性。

### 核心概念

| 概念 | 說明 |
|------|------|
| **Owner (負責人)** | 對特定 Agent 或任務負責的人類 |
| **Output (產出)** | Agent 生成的任何內容、決策或行動 |
| **Review (審批)** | 人類對產出進行的審查和批准 |
| **Escalation (升級)** | 當問題超出處理權限時升級到更高層級 |

## 架構

```
┌─────────────┐
│  Agent 1    │──────┐
└─────────────┘      │
                     ▼
              ┌──────────────┐
              │ HITL         │
              │ Controller   │
              └──────────────┘
                     │
         ┌───────────┼───────────┐
         ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ Owner 1 │ │ Owner 2 │ │ Owner 3 │
    │ (John)  │ │ (Jane)  │ │ (Bob)   │
    └─────────┘ └─────────┘ └─────────┘
         │           │           │
         ▼           ▼           ▼
    ┌─────────┐ ┌─────────┐ ┌─────────┐
    │ Approve │ │ Request │ │ Escalate│
    │  ✅     │ │  Revise │ │  🚨     │
    └─────────┘ └─────────┘ └─────────┘
```

## 產出生命週期

```
┌────────┐    submit    ┌────────────────┐    approve    ┌──────────┐
│ DRAFT  │─────────────▶│ PENDING_REVIEW │─────────────▶│ APPROVED │
└────────┘              └────────────────┘               └──────────┘
     ▲                         │                            │
     │                         │ reject                     │ complete
     │                         ▼                            ▼
     │                  ┌─────────────────┐           ┌──────────┐
     └──────────────────│ REVISION_       │           │ COMPLETED│
                        │ REQUESTED       │           └──────────┘
                        └─────────────────┘
                               ▲
                               │ escalate
                               ▼
                        ┌───────────┐
                        │ ESCALATED │
                        └───────────┘
```

## 使用方式

### 1. 初始化 HITL Controller

```python
from hitl_controller import HITLController, AgentOwner

controller = HITLController()
```

### 2. 註冊負責人

```python
owner = AgentOwner(
    owner_id="owner-1",
    name="John",
    email="john@example.com",
    role="Engineering Manager"
)
controller.register_owner(owner)
```

### 3. 指派 Agent 給負責人

```python
controller.assign_agent_to_owner("agent-dev-1", "owner-1")
controller.assign_agent_to_owner("agent-dev-2", "owner-1")
```

### 4. Agent 產出後提交審批

```python
# Agent 完成任務
output_id = controller.create_output(
    agent_id="agent-dev-1",
    task_id="task-feature-login",
    content={"result": "Login feature implemented"}
)

# 自動提交審批
controller.submit_for_review(output_id)
```

### 5. 負責人審批

```python
# 批准
controller.approve_output(output_id, "owner-1")

# 或要求修改
controller.request_revision(output_id, "owner-1", "Please add unit tests")

# 或升級
controller.escalate_output(output_id, "Needs security review", EscalationLevel.MANAGER)
```

## CLI 命令

### 註冊負責人

```bash
python cli.py hitl register owner-1 --name "John" --email "john@example.com" --role "Manager"
```

### 指派 Agent 給負責人

```bash
python cli.py hitl assign agent-1 --owner-id owner-1
```

### 列出待審批

```bash
python cli.py hitl list pending
python cli.py hitl list pending --owner-filter owner-1
```

### 批准產出

```bash
python cli.py hitl approve output-123 --approver owner-1
```

### 要求修改

```bash
python cli.py hitl reject output-123 --approver owner-1 --feedback "需要添加單元測試"
```

### 查看統計

```bash
python cli.py hitl stats
```

### 生成報告

```bash
python cli.py hitl report
```

## 整合 AgentTeam

```python
from agent_team import AgentTeam
from hitl_controller import HITLController
from hitl_workflow import AgentTeamHITLAdapter

# 初始化
team = AgentTeam()
controller = HITLController()
adapter = AgentTeamHITLAdapter(team, controller)

# 為 Agent 實例指派負責人
adapter.assign_owner_to_agent_instance("agent-instance-1", "owner-1")

# 當任務完成時，自動觸發 HITL 流程
output_id = adapter.on_task_completed("agent-instance-1", "task-123", result)
```

## 整合 MessageBus

```python
from message_bus import MessageBus
from hitl_controller import HITLController
from hitl_workflow import MessageBusHITLAdapter

bus = MessageBus()
controller = HITLController()
adapter = MessageBusHITLAdapter(bus, controller)

# HITL 事件會自動發送到 MessageBus
# 主題：hitl.new_output, hitl.approved, hitl.revision_requested, hitl.escalated
```

## 企業表單系統整合

HITL 支援與企業表單系統整合，讓審批流程無縫嵌入企業既有工作流。

### 支援的企業系統

| 系統 | 說明 |
|------|------|
| **Jira** | 建立 Issue 作為審批工單 |
| **ServiceNow** | 企業 IT 服務管理 |
| **SAP** | ERP 系統審批 |
| **Monday.com** | 專案管理平台 |
| **本地/POC** | 預設使用本地儲存 |

### 整合方式

```python
from hitl_controller import HITLController, FormSystemAdapter

# 1. 定義企業 Adapter
class JiraFormAdapter(FormSystemAdapter):
    def __init__(self, jira_client):
        self.jira = jira_client
    
    def create_ticket(self, output, owner):
        """在 Jira 建立審批 Issue"""
        return self.jira.create_issue(
            project="HITL",
            summary=f"[HITL] 產出審批: {output.id}",
            description=f"Agent: {output.agent_id}\nTask: {output.task_id}",
            assignee=owner.email
        )
    
    def notify_approval(self, owner_id, output, action):
        """發送通知"""
        self.jira.notify(owner_id, f"有新審批: {action}")
    
    def get_approval_status(self, ticket_id):
        """查詢審批狀態"""
        return self.jira.get_status(ticket_id)
    
    def update_ticket(self, ticket_id, status, feedback=None):
        """更新工單"""
        self.jira.update(ticket_id, status, comment=feedback)

# 2. 使用自定義 Adapter
controller = HITLController()
controller.set_form_adapter(JiraFormAdapter(jira_client))
```

### 預設本地模式

小型專案或 POC 可使用預設的本地儲存：

```python
# 無需任何設定，預設使用本地儲存
controller = HITLController()

# 手動設定
from hitl_controller import DefaultFormAdapter
controller.set_form_adapter(DefaultFormAdapter())
```

### 何時使用企業整合？

| 場景 | 建議 |
|------|------|
| POC / 快速驗證 | 本地模式（預設） |
| 小型團隊 | 本地模式 |
| 中型企業 | Jira / Monday.com |
| 大型企業 | ServiceNow / SAP |
| 多系統混合 | 多個 Adapter 實作 |

## 最佳實踐

### 1. 清晰的責任歸屬

每個 Agent 都應該有明確的負責人，避免「无人负责」的情況。

### 2. 及時審批

設置合理的審批超時時間，超時後自動升級。

```python
owner = AgentOwner(
    owner_id="owner-1",
    name="John",
    email="john@example.com",
    role="Manager",
    escalation_timeout=3600  # 1 小時
)
```

### 3. 明確的修訂回饋

要求修改時提供具體的回饋，而不是模糊的「不行」。

```python
controller.request_revision(output_id, "owner-1", 
    "需要修改：\n"
    "1. 添加單元測試覆蓋率 > 80%\n"
    "2. 修復 security vulnerability in auth.py\n"
    "3. 更新 README 文件"
)
```

### 4. 分層升級

根據問題嚴重程度升級到不同層級：

| 層級 | 適用場景 |
|------|----------|
| OWNER | 標準審批流程 |
| MANAGER | 跨團隊協調或資源調配 |
| EXECUTIVE | 重大決策或風險規避 |

## 監控指標

| 指標 | 說明 | 目標 |
|------|------|------|
| 待審批數 | 等待審批的產出數量 | < 10 |
| 平均審批時間 | 從提交到批准的時間 | < 1 小時 |
| 修訂率 | 需要修訂的產出比例 | < 30% |
| 升級率 | 升級的產出比例 | < 5% |

## 總結

HITL 系統為 Multi-Agent 協作提供了「人類把關」機制，確保：

1. **品質控制** - 每個產出都經過人類審查
2. **責任明確** - 每個 Agent 都有負責人
3. **風險管理** - 問題能夠被及時發現和升級
4. **可追溯性** - 所有決策都有記錄

在自動化日益普及的今天，HITL 確保了人類始終保持對 AI 系統的控制和監督。
