# 案例 41：Recovery Controller (recovery_controller)

## 概述

災難恢復控制中心，自動偵測失敗並建立恢復計劃。透過智能分類和策略選擇，實現從瞬態錯誤到硬體故障的全方位自動/手動恢復。

---

## 快速開始

```python
from recovery_controller import RecoveryController, FailureType, FailureSeverity

# Initialize controller
def notification_handler(event):
    print(f"Alert: {event}")

controller = RecoveryController(notification_handler=notification_handler)

# Detect and classify failure
try:
    some_operation()
except Exception as e:
    report = controller.detect_failure(
        agent_id="agent-001",
        task_id="task-123",
        exception=e,
        context={"additional_info": "value"}
    )
    print(f"Failure classified as: {report.failure_type.value}")
    
    # Create recovery plan
    plan = controller.create_recovery_plan(report.failure_id)
    print(f"Recovery plan: {plan.plan_id}")
    print(f"Auto-executable: {plan.auto_executable}")
    
    # Execute if auto-executable
    if plan.auto_executable:
        result = controller.execute_recovery(plan.plan_id)
```

---

## 核心功能

| 功能 | 說明 |
|------|------|
| 失敗偵測 | 自動偵測並分類失敗類型 |
| 策略選擇 | 根據失敗類型選擇恢復策略 |
| 計劃生成 | 自動生成多步驟恢復計劃 |
| 人類批准 | 需要人類介入的高風險操作 |
| 歷史追蹤 | 完整的失敗歷史和狀態追蹤 |

---

## 失敗類型分類

| 類型 | 嚴重程度 | 說明 | 自動恢復 |
|------|----------|------|----------|
| TRANSIENT | LOW | 短暫錯誤（網路、限流） | ✅ |
| LLM_RECOVERABLE | MEDIUM | LLM 可恢復 | ✅ |
| USER_FIXABLE | MEDIUM | 用戶可修復 | ❌ |
| SYSTEM_BUG | HIGH | 系統 bug | ❌ |
| HARDWARE | CRITICAL | 硬體故障 | ❌ |
| UNKNOWN | MEDIUM | 未知 | ❌ |

---

## 恢復策略

### 瞬態錯誤 (TRANSIENT)

適用於：網路超時、連接失敗、API 限流

```
等待 5 秒 → 重試操作 → 如果仍然失敗則上報
成功率：80%，預估時間：45 秒
```

### LLM 可恢復 (LLM_RECOVERABLE)

適用於：工具調用失敗、JSON 解析錯誤、輸出格式錯誤

```
記錄錯誤並反饋給 LLM → 讓 LLM 重新生成 → 驗證新輸出
成功率：70%，預估時間：95 秒
```

### 用戶可修復 (USER_FIXABLE)

適用於：缺少輸入、權限不足、需要用戶確認

```
暫停並通知用戶 → 等待用戶提供必要訊息 → 用戶提供後繼續執行
成功率：90%，預估時間：365 秒（需要人類批准）
```

### 系統 Bug (SYSTEM_BUG)

適用於：斷言失敗、屬性錯誤、類型錯誤、數值錯誤

```
記錄詳細錯誤信息 → 回滾到最後穩定狀態 → 通知開發團隊
成功率：60%，預估時間：85 秒（需要人類批准）
```

### 硬體故障 (HARDWARE)

適用於：內存錯誤、磁碟錯誤、CPU 過載、致命錯誤

```
緊急通知 → 保存所有狀態到磁碟 → 等待硬體恢復 → 重新初始化並恢復
成功率：50%，預估時間：905 秒（需要人類批准）
```

---

## API 參考

### RecoveryController

```python
controller = RecoveryController(notification_handler=None)
```

#### detect_failure(agent_id, task_id, exception, context=None)

偵測失敗並自動分類。

**參數：**
- `agent_id` (str): Agent ID
- `task_id` (str): 任務 ID
- `exception` (Exception): 異常對象
- `context` (dict, optional): 額外上下文

**返回：** `FailureReport`

#### create_recovery_plan(failure_id)

為失敗建立恢復計劃。

**參數：**
- `failure_id` (str): 失敗報告 ID

**返回：** `RecoveryPlan` 或 `None`

#### execute_recovery(plan_id, approved=False)

執行恢復計劃。

**參數：**
- `plan_id` (str): 計劃 ID
- `approved` (bool): 是否已獲得批准

**返回：** `dict`

#### get_failure_history(agent_id=None, limit=100)

取得失敗歷史。

**參數：**
- `agent_id` (str, optional): Agent ID 過濾
- `limit` (int): 返回數量限制

**返回：** `List[FailureReport]`

#### get_active_failures()

取得未解決的失敗。

**返回：** `List[FailureReport]`

#### get_recovery_status()

取得恢復狀態摘要。

**返回：** `dict`

---

## 與現有模組整合

| 模組 | 整合點 |
|------|--------|
| agent_debugger | 共享除錯系統 |
| auto_quality_gate | 品質把關觸發 |
| failover_manager | 故障轉移觸發 |
| hitl_controller | 人類批准流程 |
| checkpoint_manager | 狀態快照與回滾 |

---

## CLI 使用

```bash
# 查看恢復狀態
python cli.py recovery status

# 查看失敗歷史
python cli.py recovery history --agent agent-001

# 查看活躍失敗
python cli.py recovery active

# 批准並執行計劃
python cli.py recovery execute --plan-id plan-xxx --approve
```

---

## 通知回調

當失敗需要關注時，系統會透過 `notification_handler` 回調通知：

```python
def notification_handler(event):
    if isinstance(event, FailureReport):
        # 高嚴重性失敗警報
        send_alert(f"Failure {event.failure_id}: {event.message}")
    elif isinstance(event, dict) and event.get("type") == "recovery_plan_requires_approval":
        # 需要人類批准的計劃
        plan = event["plan"]
        failure = event["failure"]
        request_approval(f"Plan {plan.plan_id} requires approval")
```

---

## 相關模組

- recovery_controller.py
- agent_debugger.py
- auto_quality_gate.py
- failover_manager.py
- hitl_controller.py
- checkpoint_manager.py
