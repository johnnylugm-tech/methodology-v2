# methodology-v2

> Multi-Agent Collaboration Development Methodology v5.4

## 概述

這是一個標準化的多 Agent 協作開發方法論，定義了錯誤分類、開發流程、協作模式、品質把關和監控警報。

整合了三個核心 Skill：
- **ai-agent-toolkit**：工具集
- **multi-agent-toolkit**：協作框架
- **methodology-v2**：方法論核心

---

## 核心原則

- **錯誤分類**：L1-L4 四級分類
- **開發流程**：6 階段標準化
- **協作模式**：Sequential / Parallel / Hierarchical
- **品質把關**：Agent Quality Guard
- **監控警報**：健康評分 + 三級警報
- **工具整合**：Model Router、Quality Guard、Monitor

---

## 使用方式

### 錯誤分類

```python
from methodology import ErrorClassifier

classifier = ErrorClassifier()

# 分類錯誤
level = classifier.classify(error)
# 返回: L1, L2, L3, 或 L4
```

### 任務生命週期

```python
from methodology import TaskLifecycle

lifecycle = TaskLifecycle()

# 執行任務
result = lifecycle.execute(task)
# 經過: 需求 → 規劃 → 執行 → 協調 → 品質 → 完成
```

### Agent 協作

```python
from methodology import Crew, Agent

crew = Crew(
    agents=[dev, reviewer, qa],
    process="sequential"  # 或 "parallel", "hierarchical"
)

result = crew.kickoff()
```

---

## 方法論要點

### L1-L4 錯誤分類

| 等級 | 類型 | 處理 |
|------|------|------|
| L1 | 輸入錯誤 | 立即返回 |
| L2 | 工具錯誤 | 重試 3 次 |
| L3 | 執行錯誤 | 降級處理 |
| L4 | 系統錯誤 | 熔斷 + 警報 |

### 開發流程

```
需求 → 優先級 → 開發 → 品質 → 文檔 → 發布
```

### 發布檢查清單

- [ ] 版本號更新
- [ ] CHANGELOG 記錄
- [ ] README 更新
- [ ] docs/ 同步
- [ ] 測試通過
- [ ] GitHub Release
- [ ] (可選) ClawHub

---

## P0: 正確性與品質保障

### Timeout 規範

> **原則**：確保複雜任務不會因超時中斷

```
最小超時：300 秒（5 分鐘）
計算公式：timeout = 評估時間 × 1.5

任務類型建議：
| 類型 | 範例 | 建議 timeout |
|------|------|--------------|
| 簡單 | 單一檔案修改 | 5-10 分鐘 |
| 中等 | API 實作 | 15-30 分鐘 |
| 複雜 | 多模組系統 | 45-60 分鐘 |
```

**理由**：防止任務中斷導致數據丢失和進度回退

---

### A/B 雙重驗證

> **原則**：防止錯誤設計直接進入實作階段

```
標準流程：

┌─────────────────────────────────────────────┐
│  Agent A 設計產出                            │
│       ↓                                     │
│  [Reflection 自我審查] ← 強制檢查清單       │
│       ↓                                     │
│  交付給 Agent B                              │
│       ↓                                     │
│  [Agent B 預先驗證] ← 設計可行性檢查        │
│       ↓                                     │
│  開始實作                                    │
└─────────────────────────────────────────────┘

Reflection 自我審查清單：
- [ ] 設計完整性：所有需求都有對應方案
- [ ] 技術可行性：現有技術棧可實現
- [ ] 邊界情況：考慮了異常場景
- [ ] 依賴關係：清楚外部依賴
- [ ] 風險評估：標記已知風險

Agent B 預先驗證清單：
- [ ] 設計可行性：技術方案合理
- [ ] 接口一致性：模組接口匹配
- [ ] 資源評估：時間和資源足夠
- [ ] 測試可測性：設計可被驗證
```

**理由**：在實作前發現問題的成本最低

---

### Kickoff 檢查清單

> **原則**：避免專案啟動後才發現基礎設施缺失

```
每個專案啟動前必須完成：

| # | 檢查項目 | 確認方式 |
|---|----------|----------|
| 1 | Git 倉庫配置 | git remote -v 成功 |
| 2 | 開發環境就緒 | pip install 成功 |
| 3 | 測試框架建立 | pytest --collect-only 成功 |
| 4 | CI/CD 配置 | .github/workflows 存在 |
| 5 | 安全基線檢查 | 掃描完成 |
| 6 | Quality Gate 標準 | 及格分數 ≥70 |
| 7 | 審批節點定義 | 審批人清單確認 |
| 8 | 通訊渠道設定 | Webhook 測試成功 |

Kickoff 閘門：
[檢查清單] → [全部勾選?] → [正式啟動]
                   ↓
                 否 → 補充後重新檢查
```

**理由**：基礎設施問題會嚴重影響開發效率

---

## P1: 流程嚴謹性

### 狀態區分

> **原則**：明確區分任務的不同階段

```
狀態機：

[待處理] ──[開始]──→ [進行中] ──[完成]──→ [已完成]
                          │
                          ├──[品質檢查]──→ [驗證中]
                          │                    │
                          │                [通過]──→ [已完成]
                          │                    │
                          │                [失敗]──→ [待處理]
                          │
                          └──[異常]──→ [失敗] ──[修復]──→ [待處理]

狀態定義：
| 狀態 | 說明 |
|------|------|
| 待處理 | 任務排入隊列，未開始 |
| 進行中 | 正在執行 |
| 驗證中 | 等待品質檢查 |
| 已完成 | 通過品質檢查 |
| 失敗 | 執行失敗，需修復 |
```

**理由**：避免「做完了」vs「還在驗證」混淆

---

### 流程偏離記錄

> **原則**：確保決策可追溯

```
當偏離標準流程時，必須記錄：

| 欄位 | 說明 |
|------|------|
| 偏離原因 | 為什麼要偏離 |
| 替代方案 | 採用的替代方案 |
| 審批人 | 批准偏離的人 |
| 預期影響 | 對時程/品質的影響 |
| 記錄時間 | 何時做出決定 |

偏離類型：
- 跳過某個階段
- 更改 Agent 協作模式
- 縮短品質檢查
- 延後文檔撰寫

審批權限：
- 小偏離：Agent 自行決定
- 中偏離：需要人類批准
- 大偏離：需要團隊批准
```

**理由**：日後複盤時能理解當初決策

---

## P2: 開發效率

### 增量執行支援

> **原則**：避免重複已完成的工作

```
重新執行時的選項：

模式選擇：
| 模式 | 適用場景 | 行為 |
|------|----------|------|
| 增量模式 | 部分失敗 | 只執行未完成的任務 |
| 全量模式 | 全面重來 | 重新執行所有任務 |

增量模式判斷：
- 檢查上次執行狀態
- 識別未完成/失敗的任務
- 跳過已完成的任務

實現方式：
[選擇模式] → [識別狀態] → [過濾任務] → [執行]
```

**理由**：節省時間，特別是長流程中部分失敗的情況

---

### 智慧 Sub-agent 超時

> **原則**：平衡資源使用和任務完成率

```
動態超時計算因素：

| 因素 | 權重 | 說明 |
|------|------|------|
| 任務複雜度 | 40% | 代碼行數、功能數 |
| 歷史執行時間 | 30% | 同類任務平均時間 |
| Token 消耗速率 | 20% | 目前消耗速度 |
| 系統負載 | 10% | 當前資源使用 |

公式：
timeout = min(max(基礎timeout, 計算值), 上限)

基礎Timeout：
- 簡單任務：300秒
- 中等任務：600秒
- 複雜任務：1800秒

上限：3600秒（1小時）

監控與調整：
- 超時預警：80% timeout 時發出警告
- 自動延長：根據消耗速率自動延長
```

**理由**：避免資源浪費或任務意外中斷

---

## 整合的專案

### 專案狀態

| 專案 | 版本 | 功能數 | GitHub |
|------|------|--------|--------|
| Agent Quality Guard | v1.0.3 | 10+ | ✅ |
| Model Router | v1.0.1 | 12+ | ✅ |
| Agent Monitor v2 | v2.1.0 | 12+ | ✅ |
| Agent Monitor v3 | v3.2.0 | 18+ | ✅ |
| ai-agent-toolkit | v2.1.0 | 6+ | ⏳ |

### 架構

```
methodology-v2
    │
    ├── ai-agent-toolkit/     (工具集)
    │   ├── Model Router       (智慧路由)
    │   ├── Quality Guard      (品質把關)
    │   └── Monitor            (監控)
    │
    ├── multi-agent-toolkit/   (協作框架)
    │   ├── Planner            (規劃)
    │   ├── Executor           (執行)
    │   └── Communication      (通訊)
    │
    └── methodology.py         (核心)
        ├── ErrorClassifier    (錯誤分類)
        ├── ErrorHandler       (錯誤處理)
        ├── TaskLifecycle      (生命週期)
        ├── QualityGate        (品質把關)
        ├── Crew               (協作)
        ├── Monitor            (監控)
        ├── HITLController     (人類介入)
        └── CheckpointManager  (斷點管理)

---

## P0: 錯誤處理與 HITL 機制

### 錯誤分類細化 (L1-L6)

> **原則**：精確處理各類錯誤

```
現有 L1-L4：
| 等級 | 類型 | 處理 |
|------|------|------|
| L1 | 輸入錯誤 | 立即返回 |
| L2 | 工具錯誤 | 重試 3 次 |
| L3 | 執行錯誤 | 降級處理 |
| L4 | 系統錯誤 | 熔斷 + 警報 |

建議擴展為 L1-L6：
| 等級 | 類型 | 處理 | 日誌 |
|------|------|------|------|
| L1 | 輸入錯誤 | 立即返回 | 不記錄 |
| L2 | 工具錯誤 | 重試 3 次 | 記錄 |
| L3 | 執行錯誤 | 降級處理 | 詳細 |
| L4 | 系統錯誤 | 熔斷 + 警報 | 詳細 + 通知 |
| L5 | 認證錯誤 | HITL | 完整記錄 |
| L6 | 臨界錯誤 | 全面停止 + 回滾 | 完整 + 告警 |
```

### 明確的 HITL 節點

> **原則**：哪些情況需要人工介入

```
哪些情況需要人工介入？

| 錯誤類型 | 觸發條件 | 處理方式 |
|----------|----------|----------|
| L5 認證錯誤 | 權限不足、Token 過期 | 請求人工授權 |
| 重大決策 | 涉及財務/安全 | 人工確認 |
| 品質不及格 | Quality Gate < 70 | 人工複審 |
| 超時過多 | 連續 3 次超時 | 人工干預 |
| 未知錯誤 | 無法分類的錯誤 | 人工診斷 |

HITL 流程：
[錯誤發生] → [分類] → [是 HITL?] → 是 → [請求人工] → [人工處理] → [繼續/終止]
                              ↓
                           否 → [自動處理]

人工介入選項：
- [ ] 批准繼續執行
- [ ] 修改參數後繼續
- [ ] 回滾到上一狀態
- [ ] 終止任務
- [ ] 分配給其他 Agent
```

### 斷點設計 (Checkpoint)

> **原則**：支援任務中斷/恢復

```
任務中斷時的恢復機制：

┌─────────────────────────────────────────────┐
│  任務執行                                    │
│  ├── 階段 1：分析 ✓（已保存）                │
│  ├── 階段 2：設計 ✓（已保存）                │
│  ├── 階段 3：實作 ──[中斷]──→ 保存狀態       │
│  └── 階段 4：測試                            │
└─────────────────────────────────────────────┘

Checkpoint 實現：
- 每個階段完成後保存狀態
- 中斷時保存當前進度
- 恢復時從最後 checkpoint 繼續
- 支持「繼續」或「重來」

保存的狀態：
| 欄位 | 說明 |
|------|------|
| task_id | 任務 ID |
| checkpoint_id | 檢查點 ID |
| phase | 當前階段 |
| progress | 進度百分比 |
| data | 階段數據 |
| timestamp | 時間戳 |
```

---

## P1: 錯誤恢復與診斷

### 錯誤恢復策略

> **原則**：自動從錯誤中恢復

```
錯誤發生時的處理策略：

| 錯誤類型 | 策略 | 說明 |
|----------|------|------|
| 網路超時 | Retry with Backoff | 指數退避重試 |
| API 限流 | Rate Limiting | 排隊等待 |
| 認證失敗 | Token Refresh | 刷新 Token |
| 服務不可用 | Fallback | 切換備用方案 |
| 資料不一致 | Rollback | 回滾到上一狀態 |

錯誤恢復流程：
[錯誤] → [分類] → [選擇策略] → [執行] → [成功?] → 是 → 繼續
                                                          ↓
                                                       否 → 升級
```

### 錯誤日誌與診斷

> **原則**：可追溯問題根源

```
錯誤發生時必須記錄：

| 欄位 | 說明 |
|------|------|
| error_id | 唯一識別碼 |
| error_type | L1-L6 分類 |
| timestamp | 發生時間 |
| location | 檔案:函數:行號 |
| message | 錯誤訊息 |
| stack_trace | 堆疊追蹤 |
| context | 任務/Agent/用戶 ID |
| result | 處理結果 |

日誌級別：
- ERROR: 需要關注的錯誤
- WARNING: 潛在問題
- INFO: 一般資訊
```

---

## P2: 健康檢查與熔斷

### 健康檢查機制

> **原則**：預防勝於治療

```
定期健康檢查：

| 檢查項目 | 頻率 | 異常閾值 |
|----------|------|----------|
| API 響應時間 | 每分鐘 | > 5 秒 |
| 錯誤率 | 每分鐘 | > 10% |
| 超時率 | 每分鐘 | > 20% |
| 資源使用 | 每 5 分鐘 | > 80% |
| Queue 堆積 | 每分鐘 | > 100 |

健康評分：
score = 100 - (error_rate × 50) - (timeout_rate × 30) - (resource × 20)

狀態：
- 綠色: ≥ 80 分
- 黃色: 60-79 分
- 紅色: < 60 分
```

---

## P2P 機制下的任務分工與 A/B 協作

### P2P + A/B 融合架構

> **原則**：P2P 模式下確保設計正確性和品質保障

```
P2P 協作流程：

┌─────────────────────────────────────────────────────┐
│  Agent A (Architect)                                 │
│  ├── 職責：架構設計、接口定義、風險評估              │
│  ├── 產出：design_spec.md                           │
│  └── 驗證：自我 Reflection + 產出審查               │
│                       ↓                              │
│  [P2P 訊息傳遞]                                     │
│                       ↓                              │
│  Agent B1 (Frontend)    Agent B2 (Backend)          │
│  ├── 接收設計 spec     ├── 接收設計 spec           │
│  ├── 預先驗證          ├── 預先驗證                │
│  ├── 實作              ├── 實作                    │
│  └── 介面對接          └── 介面對接                │
│                       ↓                              │
│  [P2P 整合測試]                                     │
│                       ↓                              │
│  Agent C (Integrator)                                │
│  ├── 整合測試                                       │
│  ├── Quality Gate                                   │
│  └── 部署驗證                                       │
└─────────────────────────────────────────────────────┘
```

### 角色定義與職責

```
P2P 團隊角色：

| 角色 | 代號 | 職責 | 權限 |
|------|------|------|------|
| Architect | A | 設計系統架構 | 審批設計 |
| Developer | B | 實作功能 | 提交代碼 |
| Reviewer | C | Code Review | 審批合併 |
| Integrator | D | 整合測試 | 部署權限 |
| QA | E | 品質把關 | Quality Gate |

通訊矩陣：
| 從\到 | A | B | C | D | E |
|-------|---|---|---|---|---|
| A | - | ✓ | ✓ | ✓ | ✓ |
| B | ✓ | - | ✓ | ✓ | - |
| C | ✓ | ✓ | - | ✓ | ✓ |
| D | ✓ | ✓ | ✓ | - | ✓ |
| E | ✓ | - | ✓ | ✓ | - |
```

### 設計驗證清單

```
Agent A 交付前必須完成：

| # | 檢查項 | 說明 |
|---|--------|------|
| 1 | 接口完整 | 所有模組接口已定義 |
| 2 | 依賴清晰 | 外部依賴版本已確認 |
| 3 | 風險標記 | 已知風險已記錄 |
| 4 | 測試策略 | 單元/集成/端到端已規劃 |
| 5 | 回滾方案 | 失敗時可回滾 |

Agent B 實作前必須完成：

| # | 檢查項 | 說明 |
|---|--------|------|
| 1 | 設計理解 | 確認理解所有接口 |
| 2 | 衝突檢查 | 與其他 B 無介面衝突 |
| 3 | 資源評估 | 時間/Token 評估合理 |
| 4 | 測試計劃 | 單元測試已規劃 |
```

### 依賴管理

```
依賴圖譜：

┌──────────┐     ┌──────────┐
│  Agent A  │────→│  Agent B1 │
│  (Design) │     │   (FE)   │
└──────────┘     └──────────┘
       │               │
       ↓               ↓
┌──────────┐     ┌──────────┐
│  Agent C  │     │  Agent B2 │
│  (Review) │     │   (BE)   │
└──────────┘     └──────────┘
       │               │
       └───────┬───────┘
               ↓
        ┌──────────┐
        │  Agent D │
        │(Integrate)│
        └──────────┘

依賴規則：
- A 完成後，B1/B2 才能開始
- B1/B2 完成後，D 才能開始
- C 可在任何階段介入 Review
```

### 衝突處理

```
P2P 衝突類型：

| 類型 | 說明 | 處理方式 |
|------|------|----------|
| 接口衝突 | 兩人定義同一接口 | 提交給 A 仲裁 |
| 資源衝突 | 搶佔同一資源 | 排隊機制 |
| 依賴衝突 | 循環依賴 | 重新設計依賴 |

衝突解決流程：
[衝突檢測] → [暫停任務] → [仲裁] → [解決] → [繼續]
```

### P2P 訊息優先級

```
訊息優先級：

| 優先級 | 類型 | 處理 |
|--------|------|------|
| P0 | 設計變更 | 立即處理，暫停所有相關任務 |
| P1 | 接口更新 | 儘快處理，影響的任務暫停 |
| P2 | 常規溝通 | 排隊處理 |
| P3 | 狀態同步 | 閒置時處理 |

訊息格式：
{
  "type": "design_change",
  "priority": "P0",
  "from": "Agent A",
  "to": ["Agent B1", "Agent B2"],
  "content": {...},
  "requires_ack": true
}
```

### 智慧任務分配

```
分配策略：

| 因素 | 權重 | 說明 |
|------|------|------|
| Agent 負載 | 30% | 當前任務數 |
| 技能匹配 | 30% | 與任務需求的匹配度 |
| 歷史表現 | 20% | 成功率 |
| 可用性 | 20% | 線上/忙碌 |

分配流程：
[新任務] → [評估需求] → [計算分數] → [選擇最佳] → [分配]
```

---

### 熔斷與降級

> **原則**：防止系統崩潰

```
熔斷器模式：

┌─────────────────────────────────────────────┐
│  CLOSED（正常）→ 失敗計數                    │
│       ↓ 失敗超過閾值                         │
│  OPEN（熔斷）→ 請求直接返回                   │
│       ↓ 過渡期結束                           │
│  HALF_OPEN（測試）→ 允許部分請求             │
│       ↓ 成功                                 │
│  CLOSED（恢復）                              │
└─────────────────────────────────────────────┘

降級策略：
| 服務 | 降級方案 |
|------|----------|
| LLM API | 切換備用模型 |
| 搜尋服務 | 使用本地快取 |
| 資料庫 | 使用記憶體緩存 |
| 第三方 API | 返回預設值 |
```

---

## P3: 智慧重試

### 重試策略配置

> **原則**：優化資源使用

```
| 錯誤類型 | 最大重試 | 退避策略 | jitter |
|----------|----------|----------|--------|
| 網路錯誤 | 3 | 指數 | 是 |
| API 限流 | 5 | 線性 | 是 |
| 認證錯誤 | 2 | 常數 | 否 |
| 伺服器錯誤 | 3 | 指數 | 是 |
| 超時 | 3 | 指數 | 是 |

退避公式：
delay = base_delay × (backoff ^ attempt) + random(0, jitter)

Example:
base_delay = 1s, backoff = 2, jitter = 0.5
- 重試 1: 1s + 0-0.5s
- 重試 2: 2s + 0-1s
- 重試 3: 4s + 0-2s
```
```

---

## 使用的 Skills (單獨維護)

這三個核心 Skill 會單獨維護，methodology-v2 的專案運作會使用它們：

| Skill | GitHub | 用途 |
|-------|---------|------|
| **Model Router** (v1.0.2) | johnnylugm-tech/model-router-v2 | 智慧模型路由 + M2.7 |
| **Agent Monitor** | johnnylugm-tech/agent-dashboard-v3 | 監控儀表板 |
| **Agent Quality Guard** | johnnylugm-tech/Agent-Quality-Guard | 品質把關 |

---

## 整合的 Skills

| Skill | 用途 | 整合方式 |
|-------|------|----------|
| **dispatching-parallel-agents** | 任務分配 | 方法論引用 |
| **sessions_spawn** | 建立子 Agent | OpenClawAdapter |
| **sessions_send** | 跨 Agent 溝通 | OpenClawAdapter |
| **verification-before-completion** | 交付前驗證 | AutoQualityGate |
| **requesting-code-review** | 程式碼審查 | 品質把關 |
| **agent-task-manager** | 任務管理 | 整合到 TaskSplitter |
| **long-term-memory** | 長期記憶 | 可與 Storage 搭配 |
| **executing-plans** | 執行計劃 | TaskLifecycle 引用 |
| **planning-with-files** | 規劃管理 | 任務規劃參考 |
| **finishing-a-development-branch** | 開發分支完成 | 發布流程參考 |

---

## 安裝

```bash
# 方式 1: 直接使用
pip install ai-agent-toolkit

# 方式 2: 開發模式
cd skills/methodology-v2
pip install -e .
```

---

## 範例

### 標準錯誤處理

```python
from methodology import ErrorHandler

handler = ErrorHandler()

try:
    result = agent.execute(task)
except Exception as e:
    level = handler.classify(e)
    handler.handle(e, level)
```

### 品質把關

```python
from methodology import QualityGate

gate = QualityGate()

if gate.check(result):
    return result
else:
    return gate.fix(result)
```

### 完整工作流

```python
from methodology import ErrorClassifier, Crew, Monitor, QualityGate

# 1. 錯誤處理
classifier = ErrorClassifier()

# 2. Agent 協作
crew = Crew(agents, process="sequential")
result = crew.kickoff()

# 3. 品質把關
gate = QualityGate()
if not gate.check(result):
    result = gate.fix(result)

# 4. 監控
monitor = Monitor()
monitor.register_agent(agent)
health = monitor.get_health_score(agent.id)
```

### Auto Quality Gate

自動運行 Agent Quality Guard 檢查並修復問題。

```python
from auto_quality_gate import AutoQualityGate

# 預設：自動修復開啟
gate = AutoQualityGate()  # auto_fix=True

# 關閉自動修復（需手動執行）
gate = AutoQualityGate(auto_fix=False)

# 1. 掃描 (如果 auto_fix=True，會自動修復)
report = gate.scan("your_code.py")
print(f"Score: {report.score}/100")

# 2. 手動修復 (auto_fix=False 時使用)
result = gate.fix(report)
print(f"Fixed: {result['success']}/{result['total']}")

# 3. 生成報告
print(gate.generate_report("markdown"))
```

#### 開關說明

| 設置 | 行為 |
|------|------|
| `auto_fix=True` (預設) | 掃描後自動修復可解決問題 |
| `auto_fix=False` | 僅掃描，需手動執行 `gate.fix(report)` |

---

### Agent Output Validator

結構化輸出驗證 + 自動修復，支援 JSON Schema / Pydantic / 自訂規則。

```python
from agent_output_validator import AgentOutputValidator, create_output_schema

# 初始化
validator = AgentOutputValidator()

# 建立 JSON Schema
schema = create_output_schema(
    "user_info",
    {
        "id": {"type": "integer"},
        "name": {"type": "string"},
        "email": {"type": "string", "pattern": r"^[\w.-]+@[\w.-]+\.\w+$"},
        "role": {"type": "string", "enum": ["admin", "user", "guest"]},
    },
    required=["id", "email"]
)

# 驗證輸出
report = validator.validate(
    {"id": 123, "name": "John", "email": "john@example.com"},
    schema
)
print(f"Valid: {report.valid}")

# 自動修復
fixed, fix_report = validator.auto_fix(
    {"id": "not_an_int", "email": "invalid"},
    schema
)
print(f"Fixes applied: {fix_report.fix_applied}")
```

#### 驗證類型

| 類型 | 說明 |
|------|------|
| JSON Schema | 標準 JSON Schema Draft-07 |
| Pydantic | BaseModel 子類驗證 |
| 自訂規則 | List[Dict] 定義的規則 |

#### 自訂規則範例

```python
rules = [
    {"field": "id", "check": "required"},
    {"field": "score", "check": "range", "min": 0, "max": 100},
    {"field": "email", "check": "pattern", "pattern": r"^[\w.-]+@[\w.-]+\.\w+$"},
    {"field": "status", "check": "enum", "values": ["active", "inactive"]},
]
```

#### 整合 StructuredOutputEngine

```python
from structured_output import StructuredOutputEngine

engine = StructuredOutputEngine()

# 驗證輸出（含自動修復）
result = engine.validate_output(
    output=data,
    schema="user_info",
    auto_fix=True
)

# 完整流程：Validator + QualityGate
result = engine.validate_and_fix_with_quality_gate(
    output=data,
    schema="user_info",
    quality_gate=quality_gate_instance,
    file_path="agent_output.py"
)
```

---

### Smart Router

基於 Model Router 的智慧路由，根據任務自動選擇最適合的 LLM。

```python
from smart_router import SmartRouter, TaskType, BudgetLevel

# 初始化 (預設 medium 預算)
router = SmartRouter()

# 或指定預算
router = SmartRouter(budget="low")   # 低成本
router = SmartRouter(budget="high")  # 高品質

# 路由任務
result = router.route("幫我寫一個 Python 函數")
print(f"Model: {result.model}")
print(f"Provider: {result.provider}")
print(f"Est. Cost: ${result.estimated_cost}")

# 強制使用模型
result = router.route(task, force_model="gpt-4")

# 列出可用模型
models = router.list_models()
```

#### 任務類型

| 類型 | 關鍵詞 |
|------|--------|
| CODING | code, program, function, debug |
| REVIEW | review, critique, check |
| WRITING | write, draft, compose |
| ANALYSIS | analyze, compare, evaluate |
| TRANSLATION | translate, convert |
| CREATIVE | idea, brainstorm, creative |

#### 預算等級

| 等級 | 說明 |
|------|------|
| LOW | 低成本模型 |
| MEDIUM | 平衡成本與品質 |
| HIGH | 高品質模型 |

#### 配置開關

```python
from smart_router import SmartRouter

# 預設：自動路由開啟
router = SmartRouter()  # auto_route=True

# 關閉自動路由（使用預設模型）
router = SmartRouter(auto_route=False)

# 自定義配置
router = SmartRouter(config={
    "auto_route": False,
    "default_model": "claude-3-sonnet",
    "budget": "high",
    "fallback_model": "gpt-3.5-turbo"
})
```

#### 預設配置

```python
DEFAULT_CONFIG = {
    "auto_route": True,       # 自動路由（預設開）
    "default_model": "gemini-pro",  # 預設模型
    "budget": "medium",       # 預算等級
    "fallback_model": "gpt-3.5-turbo",  # 備用模型
}
```

| 設置 | 說明 |
|------|------|
| auto_route=True (預設) | 根據任務自動選擇模型 |
| auto_route=False | 使用 default_model 設定 |

#### 命令列

```bash
# 掃描
python auto_quality_gate.py scan your_code.py

# 自動修復
python auto_quality_gate.py fix your_code.py

# 生成報告
python auto_quality_gate.py report
```

---

### 統一 Dashboard

#### 方式 1: 命令列

```bash
# 輕量版 (v2)
python dashboard.py light
python dashboard.py v2

# 完整版 (v3，預設)
python dashboard.py full
python dashboard.py v3

# 從配置文件啟動
python dashboard.py --config config.json

# 訪問 http://localhost:8080
```

#### 預設配置

```python
DEFAULT_CONFIG = {
    "version": "full",     # 版本：light (v2) / full (v3)
    "port": 8080,
    "auto_start": True,
}
```

#### 方式 2: Python API

```python
from methodology import Dashboard

# 預設：完整版 (v3)
dashboard = Dashboard()

# 輕量版 (v2)
dashboard = Dashboard(mode="light")
dashboard = Dashboard(mode="v2")

# 完整版 (v3)
dashboard = Dashboard(mode="full")
dashboard = Dashboard(mode="v3")

# 自定義配置
dashboard = Dashboard(config={
    "version": "light",
    "port": 9000,
    "auto_start": True
})
```

功能：
- 📡 Model Router 指標（請求、成本、快取命中率）
- 🤖 Agent Monitor 指標（健康、任務、警報）
- 📈 趨勢圖表（ECharts）
- 🔄 統一介面封裝 v2/v3 功能

---

*這個方法論幫助團隊標準化多 Agent 協作開發流程*
