# P2P + HITL 新團隊上手指南

> 讓新團隊在 30 分鐘內掌握點對點協作與人類介入控制的核心概念

---

## 1️⃣ 什麼是 P2P 和 HITL？

### P2P (Peer-to-Peer Agent Collaboration)

**點對點代理協作** — 多個 Agent 直接互相溝通、分配任務、共享成果，**沒有單一主控者**。

```
┌──────────┐     ┌──────────┐     ┌──────────┐
│ Agent A  │◄───►│ Agent B  │◄───►│ Agent C  │
└──────────┘     └──────────┘     └──────────┘
      │                │                │
      └────────────────┼────────────────┘
                       │
                  點對點溝通
```

**特點：**
- 無中心瓶頸
- 各 Agent 平等協作
- 任務自己協調分配
- 適合複雜、多領域的任務

### HITL (Human-in-the-Loop)

**人類介入控制** — 人類在關鍵節點審批、決策、引導，確保產出符合預期。

```
┌──────────────────┐       ┌──────────────────┐
│   Agent 執行     │ ──→   │  人類審批/決策   │
└──────────────────┘       └──────────────────┘
         ▲                          │
         └──────────────────────────┘
              HITL 介入點
```

**特點：**
- 每個產出都有負責人
- 人類把關關鍵決策
- 避免完全自動化風險
- **所有場景都需要**

---

## 2️⃣ 單一主代理 vs 多主代理對比

> 根據 Johnny 的分析

| 維度 | 單一主代理 | 多主代理 (P2P) |
|------|-----------|----------------|
| **控制權** | 集中在一個 Agent | 分散在多個 Agent |
| **擴展性** | 瓶頸明顯 | 水平擴展簡單 |
| **複雜度** | 低 | 中高 |
| **適用場景** | 簡單任務 | 複雜、多領域任務 |
| **速度** | 串行，較慢 | 並行，快速 |
| **品質** | 依賴單一能力 | 多元能力互補 |
| **單點故障** | 高風險 | 分散風險 |

### 什麼時候用哪種？

```
簡單任務 / 單一領域 / POC
        ↓
   單一主代理
   （夠用就好）
        ↓
        
複雜任務 / 多領域 / 高品質需求
        ↓
   P2P 多主代理
   （協作產生複利）
```

### P2P 的核心優勢

1. **能力互補** — 各 Agent 擅長不同領域
2. **并行處理** — 同時處理多個子任務
3. **去中心化** — 沒有單點故障
4. **自然分工** — 任務自己找到擅長的 Agent

---

## 3️⃣ 什麼時候用 P2P？

### 適合 P2P 的場景

| 場景 | 說明 | 範例 |
|------|------|------|
| **複雜專案** | 任務拆分成多個子領域 | 開發一個 SaaS 系統 |
| **多領域協作** | 需要多種專業能力 | 前端 + 後端 + DevOps |
| **高品質需求** | 單一視角不足 | 需要多角度審查 |
| **大規模並行** | 同時處理多個任務 | 批量處理需求 |
| **風險分散** | 不希望單一 Agent 失敗影響全域 | 關鍵系統開發 |

### P2P 架構範例

```
專案：開發 AI 客服系統

┌─────────────────────────────────────────────────────────┐
│                    AgentTeam (P2P 團隊)                   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────┐   ┌─────────┐   ┌─────────┐   ┌─────────┐ │
│  │Planning │◄─►│Frontend │◄─►│ Backend │◄─►│   QA    │ │
│  │ Agent   │   │ Agent   │   │ Agent   │   │  Agent  │ │
│  └─────────┘   └─────────┘   └─────────┘   └─────────┘ │
│       │              │             │             │      │
│       └──────────────┴─────────────┴─────────────┘     │
│                           │                              │
│                    MessageBus (共享訊息)                  │
└─────────────────────────────────────────────────────────┘
                           │
                    HITL 介入點
                           │
                    ┌──────┴──────┐
                    │  Human Owner │
                    │   (審批)     │
                    └─────────────┘
```

---

## 4️⃣ 什麼時候用 HITL？

### 答案：**所有場景都需要**

HITL 不是「可選項」，而是**必需品**。

### HITL 的三層介入

```
┌─────────────────────────────────────────────────────────┐
│ Layer 1: 任務設定 (Planning HITL)                       │
│ ─────────────────────────────────────────────────────── │
│ • 確認需求理解正確                                       │
│ • 審批任務拆分                                           │
│ • 設定品質標準                                           │
├─────────────────────────────────────────────────────────┤
│ Layer 2: 過程監控 (Execution HITL)                      │
│ ─────────────────────────────────────────────────────── │
│ • 關鍵節點審批                                           │
│ • 進度檢查                                               │
│ • 方向調整                                               │
├─────────────────────────────────────────────────────────┤
│ Layer 3: 交付把關 (Delivery HITL)                       │
│ ─────────────────────────────────────────────────────── │
│ • 最終產出審批                                           │
│ • 上線確認                                               │
│ • 驗收通過                                               │
└─────────────────────────────────────────────────────────┘
```

### 為什麼所有場景都需要 HITL？

| 原因 | 說明 |
|------|------|
| **責任歸屬** | 每個產出都有明確負責人 |
| **品質把關** | 人類視角確保符合預期 |
| **風險控制** | 避免完全自動化的失控風險 |
| **上下文判斷** | 人類理解商業邏輯，Agent 不一定懂 |
| **例外處理** | 特殊情況需要人類決策 |

### HITL Owner 職責

```
┌─────────────────────────────────────────────────────────┐
│                    HITL Owner                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ✓ 設定任務目標與品質標準                               │
│  ✓ 審批每個階段的產出                                   │
│  ✓ 做出最終交付決定                                     │
│  ✓ 對結果負責                                           │
│  ✓ 在關鍵節點介入                                       │
│                                                         │
│  ✗ 不要：微觀管理每個步驟                               │
│  ✗ 不要：完全放任 Agent 自主                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 5️⃣ 實作範例

### 5.1 設定 P2P 團隊

```python
from methodology import AgentTeam, MessageBus

# 建立 P2P 團隊
team = AgentTeam(
    name="ai客服系統開發",
    topology="p2p",  # 點對點模式
    members=[
        {"role": "planner", "model": "claude-3-5-sonnet"},
        {"role": "frontend", "model": "gpt-4o"},
        {"role": "backend", "model": "claude-3-5-sonnet"},
        {"role": "qa", "model": "gpt-4o-mini"},
    ]
)

# 啟動 MessageBus 讓各 Agent 直接溝通
bus = MessageBus(topology="p2p")

# Planner 發布任務
bus.publish("task:分解", {
    "goal": "開發 AI 客服系統",
    "subtasks": ["前端介面", "對話引擎", "知識庫", "測試"]
})

# 前端 Agent 接收並處理
@bus.subscribe("task:前端介面")
def handle_frontend(task):
    # ... 實作前端
    bus.publish("result:前端介面", {"status": "done", "output": "..."})

# 後端 Agent 接收並處理
@bus.subscribe("task:對話引擎")
def handle_backend(task):
    # ... 實作後端
    bus.publish("result:對話引擎", {"status": "done", "output": "..."})

# QA Agent 收集結果
@bus.publish("result:*")
def collect_results(topic, data):
    # 彙整所有產出
    pass
```

### 5.2 設定 HITL Owner

```python
from methodology import HITLController, ApprovalStage

# 建立 HITL 控制
hitl = HITLController(
    owner="human_pm",  # 人類 Owner
    stages=[
        ApprovalStage(
            name="planning",
            trigger="after_task_split",
            approver="human_pm",
            auto_approve=False  # 必須人工審批
        ),
        ApprovalStage(
            name="milestone",
            trigger="after_milestone",
            approver="human_pm",
            auto_approve=False
        ),
        ApprovalStage(
            name="delivery",
            trigger="before_delivery",
            approver="human_pm",
            auto_approve=False  # 最終交付必須審批
        )
    ]
)

# 任務執行中
@hitl.intercept("planning")
def on_planning_complete(plan):
    # 人類審批任務計畫
    print(f"任務計畫：{plan}")
    approval = input("批准這個計畫？(y/n): ")
    if approval.lower() != "y":
        raise RejectedException("計畫需要修改")
    return True

@hitl.intercept("delivery")
def on_delivery(result):
    # 人類最終驗收
    print(f"交付產出：{result}")
    approval = input("通過驗收？(y/n): ")
    if approval.lower() != "y":
        raise RejectedException("需要修改")
    return True
```

### 5.3 產出審批流程

```python
from methodology import ApprovalFlow, OutputQuality

# 建立審批流程
flow = ApprovalFlow(
    name="code_review_approval",
    stages=[
        {
            "name": "self_review",
            "actor": "agent",
            "criteria": ["lint_pass", "test_pass", "no_security_issue"]
        },
        {
            "name": "peer_review", 
            "actor": "peer_agent",
            "criteria": ["logic_correct", "follows_convention"]
        },
        {
            "name": "human_approval",
            "actor": "human_owner",
            "criteria": ["meets_requirements", "production_ready"]
        }
    ]
)

# 提交產出審批
result = flow.submit(
    artifact=generated_code,
    context={"task": "user_login", "priority": "high"}
)

print(f"審批狀態: {result.status}")
# Output: 審批狀態: pending_human_approval

# 人類 Owner 審批
if result.needs_human_decision:
    decision = input(f"審查這段代碼:\n{generated_code}\n\n批准？(y/n): ")
    flow.respond(decision=decision.lower() == "y", comments="...")
```

### 5.4 完整 P2P + HITL 範例

```python
from methodology import AgentTeam, HITLController, MessageBus

# 初始化
team = AgentTeam(name="p2p_hitl_project", topology="p2p")
hitl = HITLController(owner="johnny_pm")
bus = MessageBus()

# 定義團隊成員
team.add_member(role="architect", model="claude-3-5-sonnet")
team.add_member(role="developer", model="gpt-4o")
team.add_member(role="tester", model="gpt-4o-mini")

# P2P 協作流程
@bus.subscribe("task:design_complete")
def on_design_done(design):
    # HITL: 設計階段審批
    hitl.approve_or_reject(
        stage="design",
        output=design,
        owner="johnny_pm"
    )
    # 繼續分配開發任務
    bus.publish("task:implement", design)

@bus.subscribe("task:implement_complete")
def on_implement_done(code):
    # 自動測試
    test_result = tester.run_tests(code)
    if test_result.passed:
        bus.publish("task:review", code)
    else:
        bus.publish("task:fix", {"code": code, "errors": test_result.errors})

@bus.subscribe("task:review_complete")
def on_review_done(code):
    # HITL: 最終交付審批
    hitl.approve_or_reject(
        stage="delivery",
        output=code,
        owner="johnny_pm"
    )

# 啟動專案
bus.publish("task:start", {"goal": "開發用戶管理模組"})
```

---

## 6️⃣ 快速開始

### Step 1: 選擇架構

```
簡單任務 / POC → 單一主代理（不需要 P2P）
複雜任務 / 多領域 → P2P 多主代理
```

### Step 2: 設定 HITL Owner

```python
from methodology import HITLController

# 必填：指定人類 Owner
hitl = HITLController(owner="YOUR_NAME")
```

### Step 3: 定義審批點

```python
# 至少設定這些節點
approval_stages = ["planning", "milestone", "delivery"]

for stage in approval_stages:
    hitl.add_stage(stage, auto_approve=False)
```

### Step 4: 啟動 P2P 團隊（如需要）

```python
from methodology import AgentTeam

team = AgentTeam(
    name="my_project",
    topology="p2p",  # 點對點
    members=[
        {"role": "developer"},
        {"role": "reviewer"},
    ]
)

team.start()
```

### Step 5: 執行並審批

```
Agent 執行 → HITL 審批 → 通過 → 下一階段
                ↓
           駁回 → Agent 修正 → 重新審批
```

---

## 📋 P2P + HITL 檢查清單

### 專案開始前

- [ ] 確認使用 P2P 還是單一代理
- [ ] 指定 HITL Owner（必須）
- [ ] 定義審批節點
- [ ] 設定品質標準

### 執行中

- [ ] 每個階段按時審批
- [ ] 記錄審批決定和意見
- [ ] 追蹤產出品質

### 交付前

- [ ] 最終產出人類審批
- [ ] 確認責任歸屬
- [ ] 記錄經驗教訓

---

## 🔗 相關資源

| 資源 | 連結 |
|------|------|
| Hybrid Workflow | [HYBRID_WORKFLOW_GUIDE.md](HYBRID_WORKFLOW_GUIDE.md) |
| 完整介紹 | [NEW_TEAM_GUIDE.md](NEW_TEAM_GUIDE.md) |
| 實作案例 | [docs/cases/README.md](cases/README.md) |
| Model Router | [model-router-v2](https://github.com/johnnylugm-tech/model-router-v2) |

---

## 🎯 一句話總結

> **P2P 讓複雜任務並行處理，HITL 讓每個產出都有負責人。兩者結合 = 速度 + 品質 + 責任。**
