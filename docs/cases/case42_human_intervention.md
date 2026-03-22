# Case 42: Human Intervention - 人類介入界面

## 問題背景

在 AI Agent 執行關鍵任務時，系統難免會遇到需要人類判斷的情況：
- 代理嘗試執行不可逆轉的危險操作（如刪除資料、發送外部請求）
- Agent 陷入失敗重試循環，需要人類介入指導
- 任務執行偏離預期，需要人類確認修正方向
- 系統檢測到高風險行為，需要人類批准後才能繼續

沒有統一的人類介入機制，Agent 只能：
1. 暂停等待（時間成本）
2. 自行假設處理（風險極高）
3. 完全放棄任務（任務失敗）

## 傳統方案

```python
# 傳統方式：簡單的標記和輪詢
class OldInterventionSystem:
    def __init__(self):
        self.pending = []
        self.approved = []
    
    def request_approval(self, agent_id, action):
        # 只簡單記錄，沒有結構化狀態
        self.pending.append({
            "agent": agent_id,
            "action": action,
            "status": "pending"
        })
    
    def poll_approval(self, agent_id):
        # 返回簡單的 True/False
        for item in self.pending:
            if item["agent"] == agent_id:
                return item["status"] == "approved"
        return False
```

**痛點：**
- 沒有優先級管理，緊急請求可能被淹沒
- 沒有時間追蹤，無法計算解決速度
- 沒有狀態儀表板，人類無法快速了解全局
- 沒有整合Checkpoint，無法了解請求時的系統狀態
- 通知機制缺失，人類可能遺漏請求

## AI-Native 方案

```python
from human_intervention import (
    HumanIntervention,
    InterventionType,
    InterventionStatus,
    StatusDashboard
)

# 初始化人類介入系統
def notification_handler(event):
    """自定義通知處理"""
    print(f"[通知] {event['type']}: {event}")

hi = HumanIntervention(notification_handler=notification_handler)

# ========== 1. 請求介入 ==========

# 場景1: 需要批准的高風險操作
request_id = hi.request_intervention(
    agent_id="dev_agent_001",
    task_id="deploy_to_production",
    intervention_type=InterventionType.APPROVAL,
    reason="即將部署到生產環境，需要人類確認",
    current_state={
        "changes": ["user_auth.py", "database.py"],
        "test_coverage": 78,
        "risk_level": "high"
    },
    suggested_actions=[
        "確認部署計劃",
        "檢查測試覆蓋率",
        "準備回滾方案"
    ],
    priority=5  # 最高優先級
)

# 場景2: 需要修正的錯誤情況
request_id = hi.request_intervention(
    agent_id="dev_agent_002",
    task_id="data_migration",
    intervention_type=InterventionType.CORRECTION,
    reason="資料遷移發現預期外的 schema 差異",
    current_state={
        "source_schema": {...},
        "target_schema": {...},
        "incompatible_fields": ["user.preferences", "order.history"]
    },
    suggested_actions=[
        "跳過不相容欄位",
        "手動對應欄位",
        "中止遷移程序"
    ],
    priority=4
)

# 場景3: 需要升級的系統錯誤
request_id = hi.request_intervention(
    agent_id="dev_agent_003",
    task_id="api_integration",
    intervention_type=InterventionType.ESCALATION,
    reason="API 限流導致任務失敗，已重試 10 次",
    current_state={
        "api_calls": 150,
        "success_rate": 0.3,
        "error_codes": ["429", "429", "429"]
    },
    priority=3
)

# 場景4: 僅通知
request_id = hi.request_intervention(
    agent_id="dev_agent_004",
    task_id="report_generation",
    intervention_type=InterventionType.NOTIFICATION,
    reason="任務完成，但有些非關鍵警告",
    current_state={
        "warnings": ["API rate limit警告", "部分cache未命中"]
    },
    priority=1
)

# ========== 2. 查看狀態儀表板 ==========

from checkpoint_manager import CheckpointManager

cm = CheckpointManager(storage_path="./checkpoints")

# 獲取特定 Agent 的狀態儀表板
dashboard = hi.show_status(
    agent_id="dev_agent_001",
    task_id="deploy_to_production",
    checkpoint_manager=cm
)

# 導出為文字格式方便顯示
print(hi.export_dashboard_text(dashboard))
```

輸出範例：
```
============================================================
Agent Status Dashboard
============================================================
Agent ID: dev_agent_001
Task ID: deploy_to_production
Generated: 2026-03-22T15:30:00.123456

Last Checkpoint:
  ID: ckpt-a1b2c3d4e5f6
  Created: 2026-03-22T15:29:45

Active Failures (0):

Pending Interventions (1):
  - [5] approval: 即將部署到生產環境，需要人類確認
```

## 核心功能

### 1. 介入類型 (InterventionType)

| 類型 | 說明 | 使用場景 |
|------|------|----------|
| `APPROVAL` | 需要批准 | 高風險操作：刪除、部署、發送 |
| `CORRECTION` | 需要修正 | 錯誤需要人類判斷正確方向 |
| `ESCALATION` | 需要升級 | 系統無法處理，需要專家介入 |
| `NOTIFICATION` | 僅通知 | 完成通知、警告通知 |

### 2. 優先級系統

- **P1-P5**: 數字越大優先級越高
- 系統自動按優先級排序，高優先級請求會被優先處理
- 預設為 P1（最低）

### 3. 狀態管理

```python
# 查看所有待處理請求
pending = hi.get_pending_requests()
# [<InterventionRequest>, ...]

# 按優先級過濾
urgent = hi.get_pending_requests(priority=4)
# 只返回 P4 和 P5 的請求

# 查看特定 Agent 的請求
agent_requests = hi.get_pending_requests(agent_id="dev_agent_001")

# 查看介入歷史
history = hi.get_intervention_history(limit=50)

# 獲取介入摘要
summary = hi.get_intervention_summary()
# {
#     "total_pending": 3,
#     "by_type": {"approval": 1, "correction": 1, "escalation": 1, "notification": 0},
#     "by_priority": {"p1": 0, "p2": 0, "p3": 1, "p4": 1, "p5": 1},
#     "avg_resolution_time": 4.5
# }
```

### 4. 批准/拒絕行動

```python
# 批准請求
success = hi.approve_action(
    request_id="intv-a1b2c3d4e5f6",
    approver="johnny",
    comments="確認部署，已檢查回滾方案"
)

# 拒絕請求
success = hi.reject_action(
    request_id="intv-a1b2c3d4e5f6",
    rejector="johnny",
    reason="測試覆蓋率太低，需要先提升至 90% 以上"
)

# 解決並繼續（自定義解決方案）
success = hi.resolve_and_continue(
    request_id="intv-a1b2c3d4e5f6",
    resolution="手動修正 schema 對應後繼續",
    continuator="johnny"
)
```

### 5. 狀態覆寫

```python
# 人類直接覆寫 Agent 狀態
hi.override_state(
    agent_id="dev_agent_001",
    new_state={
        "task": "deploy_to_production",
        "step": "rollback",
        "target_version": "v1.2.3"
    },
    override_by="johnny",
    reason="部署失敗，需要回滾到上一版本"
)
```

### 6. 整合 CheckpointManager

```python
from checkpoint_manager import CheckpointManager

cm = CheckpointManager()

# 請求介入時自動保存當前狀態
request_id = hi.request_intervention(
    agent_id="agent_001",
    task_id="complex_task",
    intervention_type=InterventionType.ESCALATION,
    reason="複雜錯誤需要人類處理",
    current_state=cm.get_latest("agent_001").state if cm.get_latest("agent_001") else {}
)

# 查看狀態時整合 checkpoint 資訊
dashboard = hi.show_status(
    agent_id="agent_001",
    checkpoint_manager=cm
)
# dashboard.last_checkpoint 包含最新快照資訊
# dashboard.current_state 包含快照時的狀態
```

## 整合範例

### 整合 Fault Tolerant

```python
from fault_tolerant import FaultTolerantExecutor, RetryConfig
from human_intervention import HumanIntervention, InterventionType

hi = HumanIntervention()

executor = FaultTolerantExecutor(
    max_retries=3,
    on_retry_failure=lambda ctx: hi.request_intervention(
        agent_id=ctx.get("agent_id", "unknown"),
        task_id=ctx.get("task_id", "unknown"),
        intervention_type=InterventionType.ESCALATION,
        reason=f"重試失敗次數過多: {ctx.get('retry_count', 0)}",
        current_state=ctx,
        priority=4
    )
)
```

### 整合 HITL Workflow

```python
from hitl_workflow import HITLWorkflow

hi = HumanIntervention()

workflow = HITLWorkflow(
    human_intervention=hi,
    auto_proceed_types=[InterventionType.NOTIFICATION],  # 通知類型自動繼續
    require_approval_types=[InterventionType.APPROVAL],  # 批准類型需要明確批准
)

# 執行工作流，自動處理人類介入
result = workflow.execute(task)
```

## 最佳實踐

### 1. 及時響應

- 高優先級請求（P4-P5）應在 5 分鐘內響應
- 設置通知機制確保人類能及時收到請求

### 2. 完整上下文

請求介入時，提供足夠的 `current_state` 和 `suggested_actions`，幫助人類快速做出判斷

### 3. 記錄解決方案

使用 `resolve_and_continue` 而非簡單批准，可以記錄解決方案供日後參考

### 4. 定期回顧

定期查看 `get_intervention_summary()` 的 `avg_resolution_time`，優化流程

## 總結

Human Intervention 模組提供了：

- ✅ **統一界面** - 單一介面處理所有類型的人類介入
- ✅ **優先級管理** - 不會遺漏緊急請求
- ✅ **狀態儀表板** - 人類可快速了解全局狀態
- ✅ **Checkpoint 整合** - 請求時自動保存上下文
- ✅ **通知機制** - 異步通知確保及時響應
- ✅ **歷史追蹤** - 所有介入都有記錄可查