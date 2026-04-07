# 案例 12：Agent Memory System (agent_memory)

## 概述

Agent Memory System 提供 AI Agent 的長期記憶和上下文管理能力。

---

## 快速開始

```python
from agent_memory import AgentMemory, MemoryStore, ContextManager

# Create memory
memory = AgentMemory(agent_id="coder")

# Store memory
memory.store("user_preference", {"language": "zh-TW"})

# Retrieve
prefs = memory.retrieve("user_preference")

# Context window management
ctx = ContextManager(max_tokens=8000)
context = ctx.build_context(conversation_history)
```

---

## 核心功能

| 功能 | 說明 |
|------|------|
| 長期記憶 | 持久化存儲關鍵資訊 |
| 上下文管理 | 智能構建上下文窗口 |
| 記憶檢索 | 快速檢索相關記憶 |
| 記憶優化 | 自動清理低價值記憶 |

---

## 與現有模組整合

| 模組 | 整合點 |
|------|--------|
| agent_state | 狀態記憶 |
| agent_team | 團隊共享記憶 |
| ContextManager | 上下文窗口 |

---

## CLI 使用

```bash
# 查看 Agent 記憶
python cli.py memory list --agent coder

# 清理記憶
python cli.py memory clean --agent coder --older-than 7d
```

---

## 相關模組

- agent_state.py
- agent_team.py
- observability.py (記憶視覺化)
