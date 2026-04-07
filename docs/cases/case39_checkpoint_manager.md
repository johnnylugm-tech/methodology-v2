# Case 39: Checkpoint Manager - 狀態快照管理

## 問題背景

Agent 在執行長期任務時，可能會遇到中斷、失敗或需要回滾的情況。沒有狀態快照機制，每次失敗都意味著從頭開始，造成重複運算和時間浪費。

## 傳統方案

```python
# 傳統方式：手動保存狀態
import pickle
import os

class OldAgent:
    def __init__(self):
        self.state = {}
        self.checkpoint_dir = "./checkpoints"
    
    def save_checkpoint(self, task_id, step):
        os.makedirs(self.checkpoint_dir, exist_ok=True)
        with open(f"{self.checkpoint_dir}/{task_id}_step{step}.pkl", "wb") as f:
            pickle.dump(self.state, f)
    
    def load_checkpoint(self, task_id):
        # 需要自己實現查找邏輯
        files = [f for f in os.listdir(self.checkpoint_dir) if f.startswith(task_id)]
        if not files:
            return None
        latest = sorted(files)[-1]
        with open(f"{self.checkpoint_dir}/{latest}", "rb") as f:
            return pickle.load(f)
```

**痛點：**
- 沒有統一的快照狀態管理
- 手動管理容易遺漏或錯誤
- 沒有自動清理機制
- 難以查詢和比較歷史快照

## AI-Native 方案

```python
from checkpoint_manager import CheckpointManager

# 初始化管理器
cm = CheckpointManager(
    storage_path="./agent_checkpoints",
    max_checkpoints=50
)

# 執行任務前保存快照
initial_state = {
    "conversation_history": [...],
    "current_task": "分析市場趨勢",
    "progress": 0,
    "context": {...}
}
ckpt_id = cm.save(
    agent_id="agent_001",
    task_id="market_analysis_q1",
    state=initial_state,
    checkpoint_type="manual"
)

# 任務中定期自動快照
progress_state = {
    "conversation_history": [...],
    "current_task": "分析市場趨勢",
    "progress": 50,
    "context": {...},
    "partial_results": {...}
}
cm.save(
    agent_id="agent_001",
    task_id="market_analysis_q1",
    state=progress_state,
    checkpoint_type="auto",
    metadata={"step": 5, "tokens_used": 12000}
)

# 任務完成後保存完成快照
completed_state = {
    "conversation_history": [...],
    "current_task": "分析市場趨勢",
    "progress": 100,
    "context": {...},
    "final_results": {...}
}
cm.save(
    agent_id="agent_001",
    task_id="market_analysis_q1",
    state=completed_state,
    checkpoint_type="on_complete"
)
```

## 核心功能

### 1. 快照儲存（記憶體 + 磁碟）

```python
# 雙重儲存：記憶體快速訪問 + 磁碟持久化
# 記憶體緩存加速查詢
# 磁碟確保重啟後不丟失
```

### 2. 快照恢復

```python
# 從快照 ID 恢復
state = cm.load("ckpt-a1b2c3d4e5f6")

# 取得最新快照
latest = cm.get_latest("agent_001")
if latest:
    state = latest.state
```

### 3. 快照查詢

```python
# 查看 Agent 的所有快照
checkpoints = cm.list_checkpoints("agent_001")
for cp in checkpoints:
    print(f"{cp.checkpoint_id} - {cp.created_at} - {cp.status}")

# 查看特定任務的快照
task_checkpoints = cm.list_task_checkpoints("market_analysis_q1")

# 查看狀態摘要
status = cm.get_status("agent_001")
print(status)
# {'agent_id': 'agent_001', 'total_checkpoints': 12, 'latest': 'ckpt-xxx', ...}
```

### 4. 自動清理

```python
# 超過 max_checkpoints 自動刪除最舊的
# 預設保留 100 個快照
# 可調整：CheckpointManager(max_checkpoints=50)
```

## 使用場景

### 場景一：任務中斷恢復

```python
try:
    result = agent.execute_complex_task()
except Exception as e:
    # 取得最後一個快照恢復
    latest = cm.get_latest(agent.id)
    if latest:
        restored_state = latest.state
        # 從恢復的狀態繼續
        agent.resume(restored_state)
```

### 場景二：分支探索

```python
# 任務開始時保存基準快照
base_ckpt = cm.save(agent_id="agent_001", task_id="explore", state=initial_state)

# 嘗試路徑 A
explore_path_a(state)

# 比較結果，如果不好則回滾
cm.load(base_ckpt)  # 恢復到基準點
explore_path_b(state)
```

### 場景三：導出/導入

```python
# 導出快照供其他系統使用
json_str = cm.export_checkpoint("ckpt-xxx")

# 或從其他系統導入
new_id = cm.import_checkpoint(json_str)
```

## 快照類型

| 類型 | 說明 | 使用時機 |
|------|------|----------|
| `auto` | 自動快照 | 定期保存、狀態變化時 |
| `manual` | 手動快照 | 用戶主動保存 |
| `on_complete` | 完成快照 | 任務成功完成時 |

## 快照狀態

| 狀態 | 說明 |
|------|------|
| `active` | 活躍快照 |
| `committed` | 已提交的快照 |
| `obsolete` | 已廢棄的快照 |

## 與傳統方案對比

| 維度 | 傳統方案 | CheckpointManager |
|------|----------|-------------------|
| 儲存方式 | 單一磁碟 | 記憶體 + 磁碟 |
| 查詢 | 需自己實現 | 內建索引 |
| 清理 | 手動管理 | 自動清理 |
| 類型 | 無 | 三種類型 |
| 導出導入 | 無 | 支援 |
| 程式碼量 | ~50 行 | 封裝好，直接用 |

## 整合建議

```python
# 與 Agent 框架整合示例
class AgentWithCheckpoint:
    def __init__(self, agent_id, task_id):
        self.id = agent_id
        self.task_id = task_id
        self.state = {}
        self.cm = CheckpointManager()
        self.auto_save_interval = 10  # 每 10 步自動保存
    
    def step(self, action):
        self.state = self.reduce(self.state, action)
        self.step_count += 1
        
        # 自動快照
        if self.step_count % self.auto_save_interval == 0:
            self.cm.save(self.id, self.task_id, self.state, "auto")
        
        return self.state
    
    def complete(self):
        self.cm.save(self.id, self.task_id, self.state, "on_complete")
```

---

**適用範圍：** 需要長期運行、可能中斷、或需要回滾能力的 Agent 任務