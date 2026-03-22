# 🛡️ Fault Tolerance 完整指南

> 給新團隊的錯誤處理與災難復原上手指南

---

## 1️⃣ 什麼是 Fault Tolerance？

Fault Tolerance（容錯）是指系統在遇到錯誤或故障時，能夠：

- 繼續正常運作
- 或優雅地降級
- 並在災難後恢復

---

## 2️⃣ 四層 Fault Tolerance 架構

```
┌─────────────────────────────────────────────────────────────┐
│                    L4: Checkpoint Recovery                     │
│           (遇到系統崩潰？從快照恢復！)                          │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                    L3: Error Classification                    │
│           (錯誤分類？不同錯誤不同處理！)                         │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                    L2: Model Fallback                         │
│           (模型當機？自動切換備用模型！)                        │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
┌─────────────────────────────────────────────────────────────┐
│                    L1: Retry with Backoff                     │
│           (網路瞬斷？等一下再試！)                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3️⃣ 快速上手

### 第一步：理解你的錯誤

| 錯誤類型 | 說明 | 處理方式 |
|---------|------|---------|
| **Transient** | 網路瞬斷、API 限流 | 重試 |
| **LLM Recoverable** | 工具執行失敗、解析錯誤 | 讓 LLM 重新生成 |
| **User Fixable** | 缺少輸入資訊 | 暫停等待用戶 |
| **System Bug** | 程式碼邏輯錯誤 | 回滾並通知 |
| **Hardware** | 硬體故障、電力中斷 | 保存狀態等待恢復 |

### 第二步：選擇正確的工具

| 場景 | 使用工具 |
|------|---------|
| 任務做到一半斷電 | `CheckpointManager` |
| Agent 崩潰需要恢復 | `RecoveryController` |
| 需要人類審批決策 | `HumanIntervention` |
| 跨 session 保持狀態 | `StatePersistence` |

### 第三步：實作最簡範例

```python
from checkpoint_manager import CheckpointManager
from state_persistence import StatePersistence, StorageBackend
from recovery_controller import RecoveryController
from human_intervention import HumanIntervention

# 1. 初始化
checkpoint = CheckpointManager()
persistence = StatePersistence(backend=StorageBackend.SQLITE)
recovery = RecoveryController()
intervention = HumanIntervention()

# 2. 執行任務並定期儲存快照
def execute_task(agent_id, task):
    # 執行任務
    result = agent.execute(task)

    # 儲存快照（每個步驟後）
    checkpoint.save(agent_id, task.id, {
        "result": result,
        "step": task.current_step,
    })

    return result

# 3. 如果系統崩潰，從快照恢復
def recover(agent_id):
    latest = checkpoint.get_latest(agent_id)
    if latest:
        return latest.state
    return None
```

---

## 4️⃣ 災難場景演練

### 場景 1: 電力中斷 💡

**問題**：任務執行到一半，伺服器突然斷電

**解決流程**：
```
1. 電力恢復
2. 系統啟動
3. CheckpointManager 自動載入最後快照
4. RecoveryController 偵測中斷
5. 任務從快照點繼續執行
6. 人類收到通知：「任務已從 checkpoint 恢復」
```

**關鍵程式碼**：
```python
# 電力恢復後
manager = CheckpointManager()
latest = manager.get_latest("agent-1")
if latest:
    print(f"恢復到: {latest.checkpoint_id}")
    print(f"時間: {latest.created_at}")
    state = latest.state
    # 繼續執行
```

### 場景 2: Agent 崩潰 💥

**問題**：某個 Agent 在執行中突然崩潰

**解決流程**：
```
1. RecoveryController 偵測到失敗
2. 分類失敗類型
3. 如果是 LLM recoverable → 嘗試自動恢復
4. 如果需要人類介入 → 發送通知
5. 人類可以在 HumanIntervention 查看狀態
6. 人類批准後，系統繼續執行
```

**關鍵程式碼**：
```python
# 偵測並分類失敗
report = recovery.detect_failure(
    agent_id="agent-1",
    task_id="task-1",
    exception=e,
    context={"retry_count": 3}
)

# 建立恢復計劃
plan = recovery.create_recovery_plan(report.failure_id)
print(f"失敗類型: {report.failure_type}")
print(f"嚴重程度: {report.severity}")
print(f"計劃: {[s.description for s in plan.steps]}")
```

### 場景 3: 網路中斷 📶

**問題**：網路不穩定，API 呼叫超時

**解決流程**：
```
1. fault_tolerant.py 偵測到超時
2. 自動重試（Exponential Backoff）
3. 如果超過重試次數，切換到備用模型
4. StatePersistence 保存當前狀態
5. 網路恢復後從快照繼續
```

---

## 5️⃣ 人類介入時機

### 何時需要人類介入？

| 情況 | 是否介入 |
|------|---------|
| 簡單的 API 超時 | ❌ 自動處理 |
| 需要修正輸入內容 | ⚠️ 介入審批 |
| 涉及金額/刪除操作 | ⚠️ 介入審批 |
| 系統嚴重錯誤 | ✅ 必須介入 |
| 連續多次失敗 | ✅ 必須介入 |

### 如何介入？

```python
# 1. 查看狀態
dashboard = intervention.show_status("agent-1")
print(intervention.export_dashboard_text(dashboard))

# 2. 請求介入
request_id = intervention.request_intervention(
    agent_id="agent-1",
    task_id="task-1",
    intervention_type=InterventionType.APPROVAL,
    reason="涉及刪除操作，需要人類確認",
    priority=5
)

# 3. 批准行動
intervention.approve_action(request_id, approver="admin")
```

---

## 6️⃣ 工具對照表

| 工具 | 功能 | 何時使用 | 範例 |
|------|------|---------|------|
| `CheckpointManager` | 快照管理 | 任務中斷 | 每完成一個步驟就快照 |
| `StatePersistence` | 狀態持久化 | 跨 session | 使用 SQLite/Redis |
| `RecoveryController` | 災難恢復 | 失敗處理 | 自動分類 + 計劃 |
| `HumanIntervention` | 人類介入 | 需要審批 | 危險操作前 |

---

## 7️⃣ 推薦的組合使用

### 小型專案（單機）
```python
checkpoint = CheckpointManager()  # 記憶體 + 檔案
```

### 中型專案（單機 + 資料庫）
```python
checkpoint = CheckpointManager()
persistence = StatePersistence(backend=StorageBackend.SQLITE)
recovery = RecoveryController()
```

### 大型專案（分散式）
```python
checkpoint = CheckpointManager()
persistence = StatePersistence(backend=StorageBackend.REDIS,
                                 config={"host": "redis-server"})
recovery = RecoveryController(notification_handler=slack_notify)
intervention = HumanIntervention(notification_handler=slack_notify)
```

---

## 8️⃣ 常見問題

**Q: 快照會佔用很多磁碟空間嗎？**
A: CheckpointManager 預設保留 100 個快照，舊的會自動清理。

**Q: 可以手動建立快照嗎？**
A: 可以，呼叫 `checkpoint.save(agent_id, task_id, state, checkpoint_type="manual")`

**Q: 人類介入可以遠端操作嗎？**
A: 可以，HumanIntervention 支援任何 notification_handler（Slack、Email 等）。

**Q: 失敗了會自動恢復嗎？**
A: 看失敗類型：
- Transient → 自動重試
- LLM Recoverable → 自動重新生成
- User Fixable → 需要人類介入
- System Bug → 回滾 + 通知

---

## 9️⃣ 下一個步驟

1. 閱讀案例文檔：
   - [Checkpoint Manager 案例](cases/case39_checkpoint_manager.md)
   - [State Persistence 案例](cases/case40_state_persistence.md)
   - [Recovery Controller 案例](cases/case41_recovery_controller.md)
   - [Human Intervention 案例](cases/case42_human_intervention.md)

2. 整合進你的專案：
   ```python
   from checkpoint_manager import CheckpointManager
   # 開始使用
   ```

3. 設定通知：
   ```python
   recovery = RecoveryController(notification_handler=my_slack_notify)
   ```
