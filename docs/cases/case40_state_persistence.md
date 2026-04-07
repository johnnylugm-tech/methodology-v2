# Case 40: State Persistence - 狀態持久化系統

## 問題背景

在多 Agent 系統中，每個 Agent 的執行狀態、對話歷史、中間結果需要持久化儲存，以便：
- 系統重啟後能恢復狀態
- 多個 Agent 共享同一 Session 的狀態
- 實現併發控制（鎖定機制）
- 追蹤和管理長時間運行的任務

沒有統一的状态持久化系統，開發者需要自行處理各種存儲後端，增加複雜度和出錯風險。

## 傳統方案

```python
# 傳統方式：手動管理狀態
import json
import sqlite3
import os

class OldSessionManager:
    def __init__(self):
        self.db_path = "./sessions.db"
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                state TEXT
            )
        """)
        conn.commit()
        conn.close()
    
    def save(self, session_id, state):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO sessions VALUES (?, ?)",
            (session_id, json.dumps(state))
        )
        conn.commit()
        conn.close()
    
    def load(self, session_id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT state FROM sessions WHERE session_id = ?", (session_id,))
        row = cursor.fetchone()
        conn.close()
        return json.loads(row[0]) if row else None
```

**痛點：**
- 只支援單一後端（SQLite）
- 沒有併發鎖定機制
- 沒有統一的 Session 資料結構
- 不支援 Redis 或檔案系統後端
- 難以擴展新後端

## AI-Native 方案

```python
from state_persistence import StatePersistence, StorageBackend

# 選擇後端：SQLite / Redis / File / Memory
persistence = StatePersistence(
    backend=StorageBackend.SQLITE,
    config={"db_path": "./data/sessions.db"}
)

# 儲存 Session 狀態
session_id = "agent_001_session_20260322"
persistence.save_state(
    session_id=session_id,
    agent_id="agent_001",
    state={
        "conversation_history": [...],
        "current_task": "分析市場趨勢",
        "progress": 45,
        "context": {...}
    },
    metadata={"user_id": "user_123", "priority": "high"}
)

# 載入 Session 狀態
state = persistence.load_state(session_id)
print(state["current_task"])  # "分析市場趨勢"

# 鎖定 Session（併發控制）
success = persistence.lock_session(session_id, owner="agent_002", timeout=300)
if success:
    # 進行需要獨占的操作
    update_session_state(session_id)
    persistence.unlock_session(session_id, owner="agent_002")
```

## 支援的後端

| 後端 | 適用場景 | 配置 |
|------|----------|------|
| `MEMORY` | 開發/測試 | 無需配置 |
| `SQLITE` | 單機部署 | `db_path` |
| `REDIS` | 分散式部署 | `redis_host`, `redis_port` |
| `FILE` | 簡單部署 | `storage_path` |

## 核心功能

### 1. Session 狀態儲存

```python
# 儲存狀態
persistence.save_state(
    session_id="session_001",
    agent_id="agent_001",
    state={"key": "value"},
    metadata={"source": "user_input"}
)

# 自動更新：如果 session 已存在，會更新狀態
persistence.save_state(
    session_id="session_001",
    agent_id="agent_001", 
    state={"key": "new_value"},  # 覆蓋
    metadata={"source": "agent_processing"}
)
```

### 2. 併發鎖定

```python
# 鎖定 Session（預設 300 秒超時）
locked = persistence.lock_session(
    session_id="session_001",
    owner="agent_002",
    timeout=300  # 5 分鐘
)

if locked:
    # 執行需要獨占的操作
    do_exclusive_work()
    persistence.unlock_session(session_id, owner="agent_002")
else:
    # 被其他人鎖定，等待或跳過
    print("Session 已被鎖定")
```

### 3. Session 查詢

```python
# 列出所有 Sessions
all_sessions = persistence.list_sessions()

# 按 Agent 篩選
agent_sessions = persistence.list_sessions(agent_id="agent_001")

# 按狀態篩選
active_sessions = persistence.list_sessions(status="active")
locked_sessions = persistence.list_sessions(status="locked")
```

### 4. Session 刪除

```python
# 刪除 Session
deleted = persistence.delete_session(session_id)
print(f"已刪除: {deleted}")
```

### 5. 狀態查詢

```python
# 取得系統狀態
status = persistence.get_status()
print(status)
# {
#     "backend": "sqlite", 
#     "total_sessions": 10,
#     "active_sessions": 8,
#     "locked_sessions": 2
# }
```

## 使用場景

### 場景一：系統重啟後恢復

```python
# 系統啟動時初始化
persistence = StatePersistence(backend=StorageBackend.SQLITE)

# 恢復所有活躍的 Sessions
active = persistence.list_sessions(status="active")
for session in active:
    state = persistence.load_state(session.session_id)
    restore_agent_state(session.agent_id, state)
```

### 場景二：分散式 Agent 協作

```python
# 使用 Redis 後端實現跨進程共享
persistence = StatePersistence(
    backend=StorageBackend.REDIS,
    config={"redis_host": "10.0.0.1", "redis_port": 6379}
)

# Agent A 鎖定 Session
persistence.lock_session("shared_task", owner="agent_a")

# Agent B 嘗試鎖定（失敗）
if not persistence.lock_session("shared_task", owner="agent_b"):
    # 等待或分配其他任務
    pass
```

### 場景三：簡單部署（檔案系統）

```python
# 不需要 Redis 或 SQLite，直接用檔案系統
persistence = StatePersistence(
    backend=StorageBackend.FILE,
    config={"storage_path": "/tmp/agent_sessions"}
)
```

## 與 Checkpoint Manager 的差異

| 維度 | Checkpoint Manager | State Persistence |
|------|-------------------|------------------|
| 用途 | 狀態快照/回滾 | 持續狀態追蹤 |
| 頻率 | 離散時間點 | 持續更新 |
| 鎖定 | 無 | 有（併發控制） |
| 後端 | 檔案系統 | 多種後端 |
| 典型用途 | 任務恢復、分支探索 | Session 管理、狀態共享 |

## 傳統方案對比

| 維度 | 傳統方案 | StatePersistence |
|------|----------|------------------|
| 後端支援 | 單一 | 四種後端 |
| 鎖定機制 | 無 | 有（超時、持有者） |
| Session 結構 | 手動定義 | 統一 dataclass |
| 查詢能力 | 基本 | 多維度篩選 |
| 配置方式 | 硬編碼 | 統一 config |
| 程式碼量 | ~50 行 | 封裝好，直接用 |

## 整合建議

```python
# 與 Agent 框架整合
class AgentWithPersistence:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.persistence = StatePersistence(backend=StorageBackend.SQLITE)
        self.current_session = None
    
    def start_session(self, session_id):
        self.current_session = session_id
        self.persistence.save_state(
            session_id=session_id,
            agent_id=self.agent_id,
            state={"status": "started"},
            metadata={"start_time": datetime.now().isoformat()}
        )
    
    def update_state(self, state_update):
        current = self.persistence.load_state(self.current_session)
        current.update(state_update)
        self.persistence.save_state(
            session_id=self.current_session,
            agent_id=self.agent_id,
            state=current
        )
```

---

**適用範圍：** 需要 Session 狀態持久化、併發控制、跨進程狀態共享的多 Agent 系統
