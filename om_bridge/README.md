# OmO + Methodology-v2 Bridge (Mode C)

> 事件驅動的 decoupled 整合方案

---

## 概述

Mode C 是 OmO (oh-my-opencode) 與 Methodology-v2 的事件驅動橋接器，實現：
- **完全 Decoupling**：兩系統獨立運作
- **事件驅動**：通過 Message Bus 溝通
- **彈性最大**：可單獨使用任一方

---

## 架構

```
┌─────────────────────────────────────────────────────────┐
│                    OmO (oh-my-opencode)                 │
│                    多模型 Agent 協調                      │
│                    48 Hooks 擴展系統                      │
└──────────────────────────┬──────────────────────────────┘
                           │ Events
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   OmOMethodologyBridge                   │
│                   事件驅動橋接器                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Message Bus (Pub/Sub)               │   │
│  └─────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────┘
                           │ Events
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   Methodology-v2                        │
│                   流程規範 + 品質把關                      │
└─────────────────────────────────────────────────────────┘
```

---

## 目錄結構

```
om_bridge/
├── __init__.py
├── events.py          # 事件定義
├── message_bus.py      # 事件匯流排
├── bridge.py          # 橋接器核心
├── om_adapter.py      # OmO 適配器
├── v2_adapter.py       # Methodology-v2 適配器
└── examples/
    ├── mode_a_usage.py   # OmO → v2 模式
    └── mode_b_usage.py   # v2 → OmO 模式
```

---

## 快速開始

### 1. 初始化橋接器

```python
from om_bridge import EventBridge

# 創建橋接器
bridge = EventBridge()

# 啟動監聽
bridge.start()
```

### 2. Mode A：OmO 任務完成 → v2 品質把關

```python
# 發布 OmO 任務完成事件
bridge.bus.publish("om.task.completed", {
    "task_id": "task-001",
    "code": "def hello(): print('world')",
    "language": "python"
})

# Bridge 自動觸發：
# 1. 訂閱 om.task.completed
# 2. 調用 Methodology-v2 QualityGate
# 3. 發布 v2.quality.check 事件（可選）
```

### 3. Mode B：v2 任務規劃 → OmO 多模型執行

```python
# 發布 v2 任務規劃事件
bridge.bus.publish("v2.task.planned", {
    "task_id": "task-002",
    "instructions": "開發登入功能",
    "preferred_model": "claude-3-opus"
})

# Bridge 自動觸發：
# 1. 訂閱 v2.task.planned
# 2. 調用 OmO AgentPool 執行任務
# 3. 發布 om.task.completed 事件
```

---

## 事件列表

### OmO 事件 (發布)

| 事件 | 說明 | 資料 |
|------|------|------|
| `om.task.started` | 任務開始 | `{task_id, instructions}` |
| `om.task.completed` | 任務完成 | `{task_id, code, result}` |
| `om.task.failed` | 任務失敗 | `{task_id, error}` |
| `om.agent.status` | Agent 狀態 | `{agent_id, status}` |

### Methodology-v2 事件 (發布)

| 事件 | 說明 | 資料 |
|------|------|------|
| `v2.task.planned` | 任務規劃 | `{task_id, instructions, preferred_model}` |
| `v2.sprint.started` | Sprint 開始 | `{sprint_id, tasks}` |
| `v2.quality.check` | 品質檢查 | `{task_id, report}` |
| `v2.error.classified` | 錯誤分類 | `{error, level, action}` |

---

## 設定

```python
# config.py
OM_CONFIG = {
    "api_key": os.getenv("ANTHROPIC_API_KEY"),
    "preferred_models": ["claude-3-opus", "claude-3-sonnet"],
    "timeout": 30
}

V2_CONFIG = {
    "quality_threshold": 0.8,
    "sprint_capacity": 40,
    "error_levels": ["L1", "L2", "L3", "L4"]
}

BRIDGE_CONFIG = {
    "log_level": "INFO",
    "enable_mode_a": True,
    "enable_mode_b": True,
    "event_history_size": 1000
}
```

---

## 獨立使用

### 只使用 OmO

```bash
oh-my-opencode --task "開發登入功能"
```

### 只使用 Methodology-v2

```bash
cd /path/to/methodology-v2
python cli.py init my-project
python cli.py task add "登入功能"
python cli.py sprint create
```

### 同時使用（Mode C）

```bash
# 啟動橋接器
python -m om_bridge.bridge

# 在另一終端使用 OmO
oh-my-opencode --task "開發登入功能"

# Bridge 自動：
# 1. 捕獲 OmO 任務事件
# 2. 觸發 Methodology-v2 品質把關
# 3. 發布結果到 Message Bus
```

---

## License

MIT + Methodology-v2 License
