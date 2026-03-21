# 案例八：OmO + Methodology-v2 整合實戰

## 概述

本案例展示如何使用 Mode C 整合 OmO (oh-my-opencode) 與 Methodology-v2，實現：
- **完全 Decoupling**：兩系統獨立運作
- **事件驅動**：通過 Message Bus 溝通
- **互補增強**：OmO 負責執行，Methodology-v2 負責規範

---

## 架構圖

```
┌─────────────────────────────────────────────────────────┐
│                   OmO (oh-my-opencode)                  │
│                   多模型 Agent 協調                       │
│                   48 Hooks 擴展系統                      │
└──────────────────────────┬──────────────────────────────┘
                           │ Events
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   OmOMethodologyBridge                    │
│                   事件驅動橋接器                          │
│  ┌─────────────────────────────────────────────────┐   │
│  │              Message Bus (Pub/Sub)               │   │
│  └─────────────────────────────────────────────────┘   │
└──────────────────────────┬──────────────────────────────┘
                           │ Events
                           ▼
┌─────────────────────────────────────────────────────────┐
│                   Methodology-v2                         │
│                   流程規範 + 品質把關                      │
└─────────────────────────────────────────────────────────┘
```

---

## 前置需求

### 1. 安裝 Oh My OpenCode

```bash
# 使用 npm 安裝
npm install -g oh-my-opencode

# 驗證安裝
oh-my-opencode --version
# v3.12.3
```

### 2. 設定 API Keys

```bash
# 設定 Anthropic API Key (用於 Claude)
export ANTHROPIC_API_KEY="sk-ant-..."

# 設定 OpenAI API Key (用於 GPT)
export OPENAI_API_KEY="sk-..."
```

---

## 案例 8.1：Mode A - OmO 執行 → v2 品質把關

### 場景

使用 OmO 執行開發任務，完成後自動觸發 Methodology-v2 品質檢查。

### 工作流程

```
1. OmO 執行任務 (如 "開發登入功能")
2. 任務完成 → 發布 om.task.completed 事件
3. Bridge 監聽 → 觸發 v2.quality.check
4. Methodology-v2 執行品質檢查
5. 發布結果到 Message Bus
```

### 程式碼

```python
# mode_a_example.py

import asyncio
from om_bridge import EventBridge, get_bus

async def main():
    # 創建橋接器 (只啟用 Mode A)
    bridge = EventBridge(enable_mode_a=True, enable_mode_b=False)
    
    # 啟動監聽
    await bridge.start()
    
    # 或者：手動發布 OmO 任務完成事件
    bus = get_bus()
    
    await bus.publish(
        "om.task.completed",
        {
            "task_id": "login-feature-001",
            "code": '''
def login(username, password):
    user = db.query("SELECT * FROM users WHERE username = ?", username)
    if user and verify_password(password, user.password):
        return {"success": True, "token": generate_token(user)}
    return {"success": False, "error": "Invalid credentials"}
            ''',
            "language": "python"
        },
        source="om"
    )

asyncio.run(main())
```

### 輸出範例

```
[Mode A] OmO task completed: login-feature-001
[Mode A] Quality check PASSED: score=0.85
```

---

## 案例 8.2：Mode B - v2 規劃 → OmO 多模型執行

### 場景

使用 Methodology-v2 規劃任務，然後調用 OmO 的多模型能力執行。

### 工作流程

```
1. v2 發布 v2.task.planned 事件
2. Bridge 監聽 → 觸發 OmO 執行
3. OmO 選擇最佳模型執行任務
4. 任務完成 → 發布 om.task.completed
5. v2 接收結果
```

### 程式碼

```python
# mode_b_example.py

import asyncio
from om_bridge import EventBridge, get_bus

async def main():
    # 創建橋接器 (只啟用 Mode B)
    bridge = EventBridge(enable_mode_a=False, enable_mode_b=True)
    
    await bridge.start()

asyncio.run(main())
```

```python
# 另一個腳本：發布 v2 任務規劃事件

import asyncio
from om_bridge import get_bus

async def plan_task():
    bus = get_bus()
    
    await bus.publish(
        "v2.task.planned",
        {
            "task_id": "sprint-001-login",
            "instructions": "開發登入功能，包含：用戶名密碼驗證、Token 生成、錯誤處理",
            "preferred_model": "claude-3-opus"  # 指定模型
        },
        source="v2"
    )

asyncio.run(plan_task())
```

### 輸出範例

```
[Mode B] v2 task planned: sprint-001-login
[Mode B] OmO execution SUCCESS: Logged in successfully...
```

---

## 案例 8.3：Mode C - 完整整合 (A + B 同時)

### 場景

兩系統同時運作，根據事件自動協調。

### 工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                        Mode C 完整流程                        │
└─────────────────────────────────────────────────────────────┘

   v2.task.planned ──────────────────────────► OmO 執行
         │                                         │
         │                                         ▼
         │                              om.task.completed
         │                                         │
         │                                         ▼
         │                              v2.quality.check ◄─┘
         │                                         │
         ▼                                         ▼
   OmO 執行另一任務                        品質把關
         │                                         │
         ▼                                         ▼
   om.task.completed ───────────────────► v2.quality.check
```

### 程式碼

```python
# mode_c_example.py

import asyncio
from om_bridge import EventBridge

async def main():
    # 創建橋接器 (同時啟用 Mode A + Mode B)
    bridge = EventBridge(enable_mode_a=True, enable_mode_b=True)
    
    print("Starting OmO + Methodology-v2 Bridge (Mode C)...")
    print("  Mode A: OmO → v2 Quality Check")
    print("  Mode B: v2 → OmO Task Execution")
    
    await bridge.start()

asyncio.run(main())
```

### 輸出範例

```
Starting OmO + Methodology-v2 Bridge (Mode C)...
  Mode A: OmO → v2 Quality Check ✅
  Mode B: v2 → OmO Task Execution ✅

[Mode B] v2 task planned: sprint-001
[Mode B] OmO execution SUCCESS: Task completed...

[Mode A] OmO task completed: sprint-002
[Mode A] Quality check PASSED: score=0.92
```

---

## 案例 8.4：獨立使用模式

### 只使用 OmO

```bash
# 直接使用 OmO 執行任務
oh-my-opencode --task "開發一個排序演算法"
```

### 只使用 Methodology-v2

```bash
# 使用 Methodology-v2 管理專案
cd my-project
python cli.py init
python cli.py task add "排序演算法"
python cli.py sprint create
python cli.py board
```

### 根據場景選擇

| 場景 | 建議 |
|------|------|
| 快速原型驗證 | 只用 OmO |
| 企業級專案 | 只用 Methodology-v2 |
| 需要多模型協調 + 品質把關 | Mode C |
| 研究實驗 | OmO + 選擇性使用 v2 |

---

## 案例 8.5：錯誤處理與監控

### 錯誤分類流程

```python
# error_handling_example.py

import asyncio
from om_bridge import get_bus

async def demo_error_handling():
    bus = get_bus()
    
    # 模擬 OmO 任務失敗
    await bus.publish(
        "om.task.failed",
        {
            "task_id": "task-001",
            "error": "Connection timeout after 30s"
        },
        source="om"
    )
    
    # Bridge 會自動：
    # 1. 監聽 om.task.failed
    # 2. 觸發 v2.error.classified
    # 3. 根據錯誤級別執行對應行動

asyncio.run(demo_error_handling())
```

### L1-L4 錯誤處理

| 等級 | 錯誤類型 | 處理方式 |
|------|---------|---------|
| **L1** | 輸入錯誤 | 立即返回錯誤訊息 |
| **L2** | 工具錯誤 | 重試 3 次，指數退避 |
| **L3** | 執行錯誤 | 降級處理 |
| **L4** | 系統錯誤 | 熔斷，發送警報 |

---

## 事件列表

### OmO 事件

| 事件 | 方向 | 說明 |
|------|------|------|
| `om.task.started` | → Bus | 任務開始 |
| `om.task.completed` | → Bus | 任務完成 |
| `om.task.failed` | → Bus | 任務失敗 |
| `om.agent.status` | → Bus | Agent 狀態 |

### Methodology-v2 事件

| 事件 | 方向 | 說明 |
|------|------|------|
| `v2.task.planned` | → Bus | 任務規劃 |
| `v2.sprint.started` | → Bus | Sprint 開始 |
| `v2.quality.check` | → Bus | 品質檢查結果 |
| `v2.error.classified` | → Bus | 錯誤分類結果 |

---

## 常見問題

### Q1: 如何確認 OmO 已正確安裝？

```python
from om_bridge import OmOAdapter

adapter = OmOAdapter()
status = adapter.get_status()
print(status)
# {'installed': True, 'version': '3.12.3', ...}
```

### Q2: Mode A 和 Mode B 可以同時啟用嗎？

```python
# 是的，預設就是同時啟用 (Mode C)
bridge = EventBridge()  # enable_mode_a=True, enable_mode_b=True
```

### Q3: 如果只想用其中一個模式？

```python
# 只用 Mode A
bridge = EventBridge(enable_mode_a=True, enable_mode_b=False)

# 只用 Mode B
bridge = EventBridge(enable_mode_a=False, enable_mode_b=True)
```

### Q4: OmO 需要 API Key 嗎？

```bash
# 設定環境變數
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
```

---

## 相關功能

| 功能 | 模組 |
|------|------|
| 事件定義 | `om_bridge.events` |
| 事件匯流排 | `om_bridge.message_bus` |
| OmO 適配器 | `om_bridge.om_adapter` |
| v2 適配器 | `om_bridge.v2_adapter` |
| 橋接器 | `om_bridge.bridge` |
