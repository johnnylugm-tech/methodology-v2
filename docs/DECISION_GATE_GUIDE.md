# Decision Gate - 決策分類閘道指南

> v6.0 - 新團隊完全上手指南

---

## 🎯 什麼是 Decision Gate？

Decision Gate 是 methodology-v2 的**決策分類閘道**，確保所有技術決策都有：
- 明確的風險等級
- 清楚的確認流程
- 完整的決策紀錄

---

## 😰 為什麼需要 Decision Gate？

### 痛點故事：一個價值兩週的重構

```
場景：AI Agent 專案開發到一半

工程師：選 Redis 當 memory store 吧，速度快！
（沒有任何人知道這是個 HIGH 風險決策）

六週後...
產品經理：我們需要複雜查詢，Redis 做不到啊
工程師：😱 那要重構...

代價：2 週重構 + 1 週測試 + 用戶遷移
```

### 問題出在哪？

| 問題 | 結果 |
|------|------|
| ❌ 沒有風險分類標準 | 工程師以為是小決定，實際是大架構 |
| ❌ 沒有確認流程 | 跳過討論直接實作 |
| ❌ 沒有決策紀錄 | 後來的人不知道當初為什麼選 Redis |
| ❌ 決策和品質監控混為一談 | 該擋的沒擋，不該擋的擋了 |

### Decision Gate 解決方案

```
工程師：我想選 Redis 當 memory store
Decision Gate：🔴 HIGH 風險！需要確認！

→ 列出所有選項 + 建議
→ 討論後決定：先用 PostgreSQL，符合長期需求
→ 記錄決策，下次爭執有理有據
```

**代價：30 分鐘討論 vs 2 週重構**

---

## 🔴🟡🔵 三級風險分類標準

### 🔴 HIGH - 架構層級決策

**定義：** 影響系統核心、無法輕易逆轉、替換成本高

**觸發條件（符合任一）：**
- 改變系統核心架構（如：從無狀態變有狀態）
- 選擇或更換外部 API/服務
- 改變資料庫類型或 schema
- 影響安全模型
- 影響效能基線（延遲 >2x 或 記憶體 >2x）

**處理流程：**
```
1. 列出所有選項（至少 3 個）
2. 評估每個選項的優缺點
3. 給出推薦建議
4. 必須用戶確認才能實作
5. 記錄完整的決策理由
```

**常見 HIGH 風險決策：**
- 資料庫選型（PostgreSQL / MongoDB / Redis）
- API Provider 選擇（ElevenLabs / Google TTS / AWS Polly）
- 認證機制（JWT / OAuth / Session）
- 核心演算法邏輯
- 向量資料庫選擇（Pinecone / Weaviate / pgvector）

---

### 🟡 MEDIUM - 配置與工具決策

**定義：** 影響系統行為、有合理預設值、替換成本中等

**觸發條件（符合任一）：**
- 設定預設參數值（如：chunk_size、timeout、max_retries）
- 選擇非核心工具或函式庫
- 配置快取策略
- 調整日誌級別或格式
- 決定錯誤處理策略

**處理流程：**
```
1. 列出 2-3 個可行選項
2. 給出推薦預設值
3. 說明理由
4. 如果用戶無異議，按建議執行
5. 記錄決策（可簡化）
```

**常見 MEDIUM 風險決策：**
- Embedding chunk_size（512 / 800 / 1024）
- API timeout 設定（30s / 60s / 120s）
- 快取 TTL（1h / 24h / 7d）
- 重試次數（3 / 5 / 10）
- 日誌格式（JSON / plaintext）

---

### 🔵 LOW - 執行層級決策

**定義：** 不影響系統行為、可隨時調整、替換成本低

**觸發條件（符合任一）：**
- 檔案 / 目錄命名
- 程式碼結構（module 拆分方式）
- 變數命名
- 程式碼格式（Formatter 設定）
- 註冊使用方法

**處理流程：**
```
→ Agent 可自主決定
→ 不需要記錄
→ 如果不確定，可標記為 MEDIUM 請求確認
```

---

## 🔄 與 Quality Gate 的區別

| 維度 | Decision Gate | Quality Gate |
|------|---------------|--------------|
| **目標** | 決策品質 | 程式碼品質 |
| **時機** | 決策前 | 決策後 |
| **焦點** | 做對的事 | 把事做對 |
| **阻擋** | 阻止高風險決策未經討論就實作 | 阻止壞程式碼進入專案 |
| **觸發** | 任何技術決策 | 檔案存檔、Commit、PR |
| **關注點** | 選項評估、風險分類 | Lint、測試覆蓋、ASPICE 文檔 |
| **例子** | 「該用 PostgreSQL 還是 MongoDB？」 | 「這個 function 有沒有 type hint？」 |

### 什麼時候用哪個？

```
開始新專案或新功能
       ↓
Decision Gate：這個架構選型合理嗎？
       ↓
Coding...
       ↓
Quality Gate：你的程式碼符合標準嗎？
       ↓
存檔
       ↓
Quality Gate：文檔齊全嗎？ASPICE 合規嗎？
```

**比喻：**
- Decision Gate = 建築師（決定蓋什麼樣的房子）
- Quality Gate = 監工（確保房子按圖紙施工、品質過關）

---

## 📊 決策風險矩陣

| 風險級別 | 決策類型 | 處理方式 | 確認需求 | 紀錄詳略 |
| -------- | -------- | -------- | -------- | -------- |
| 🔴 HIGH | 架構、API、核心演算法、資料庫 | 必須照 spec | 用戶確認 | 完整 |
| 🟡 MEDIUM | 預設值、工具選型、配置 | 列出選項 + 建議 | 可選確認 | 簡化 |
| 🔵 LOW | 目錄結構、檔案命名、格式 | 可自主決定 | 不需要 | 不需要 |

---

## 🚀 Step-by-Step 流程圖

### 完整決策流程

```
新技術決策出現
       ↓
┌─────────────────────────────────────┐
│  這個決策影響什麼？                    │
├─────────────────────────────────────┤
│  🔴 HIGH                             │
│  ├─ 改變核心架構？                    │
│  ├─ 更換外部 API？                   │
│  ├─ 改變資料庫？                     │
│  └─ 影響安全模型？                    │
│      → 🔴 HIGH，等級確認            │
├─────────────────────────────────────┤
│  🟡 MEDIUM                           │
│  ├─ 調整預設參數？                   │
│  ├─ 選擇工具/函式庫？                │
│  └─ 配置非核心功能？                  │
│      → 🟡 MEDIUM，列出選項          │
├─────────────────────────────────────┤
│  🔵 LOW                              │
│  ├─ 命名、格式、程式碼結構？          │
│      → 🔵 LOW，自主決定              │
└─────────────────────────────────────┘
```

### 🔴 HIGH 風險決策流程

```
🔴 HIGH 風險決策
       ↓
列出所有選項（至少 3 個）
       ↓
評估每個選項
┌─────────────────────────────────────┐
│  選項 A  |  優點：... | 缺點：...    │
│  選項 B  |  優點：... | 缺點：...    │
│  選項 C  |  優點：... | 缺點：...    │
└─────────────────────────────────────┘
       ↓
給出推薦建議 + 理由
       ↓
請求用戶確認
       ↓
用戶確認 ✅ → 記錄決策 → 實作
用戶否決 ❌ → 重新評估 → 迭代
```

### 🟡 MEDIUM 風險決策流程

```
🟡 MEDIUM 風險決策
       ↓
列出 2-3 個可行選項
       ↓
給出推薦預設值 + 理由
       ↓
┌─────────────────────────────────────┐
│  if (用戶無異議)                     │
│      → 按建議執行                    │
│  else                                │
│      → 討論後調整                   │
└─────────────────────────────────────┘
       ↓
記錄決策（簡化格式）
```

---

## 🚀 快速開始

### Step 1: 分類一個決策

```bash
python3 cli.py decision classify chunk_size "Embedding chunk size"
```

**輸出範例：**
```
✅ Decision classified:
   ID: D-A1B2C3
   Risk: 🟡 MEDIUM
   Type: config_default
   ⚠️  Requires user confirmation!
   Options: 512, 800, 1024
   Recommendation: 800
```

### Step 2: 列出所有決策

```bash
python3 cli.py decision list
```

### Step 3: 確認 HIGH 風險決策

```bash
python3 cli.py decision confirm D-A1B2C3 "800"
```

---

## 📁 決策紀錄

所有決策都記錄在：
```
.methodology/decisions/
    └── decision_log.json
```

### 完整決策紀錄格式

```json
{
  "id": "D-A1B2C3",
  "timestamp": "2026-03-24T21:00:00",
  "item": "database",
  "description": "Database for agent memory",
  "risk": "HIGH",
  "options": ["PostgreSQL", "MongoDB", "Redis"],
  "recommendation": "PostgreSQL",
  "confirmed": true,
  "confirmed_by": "user",
  "reason": "PostgreSQL 支持复杂查询，符合长期需求",
  "alternatives_rejected": {
    "MongoDB": "不需要 document store 的灵活性",
    "Redis": "不支持复杂查询"
  }
}
```

### 簡化決策紀錄格式（MEDIUM）

```json
{
  "id": "D-X1Y2Z3",
  "timestamp": "2026-03-24T21:05:00",
  "item": "chunk_size",
  "risk": "MEDIUM",
  "decision": "800",
  "reason": "平衡上下文长度和语义完整性"
}
```

---

## 🤔 常見問題

### Q: 為什麼要分類決策？

A: 避免在開發過程中「隨機」決定重大事項，導致後期重構成本高。30 分鐘的討論可以省下 2 週的重構。

### Q: LOW 風險決策需要記錄嗎？

A: 不需要，Decision Gate 自動分類，只記錄 MEDIUM 和 HIGH。

### Q: 如果 spec 沒有規定的決策？

A: 視為 MEDIUM 或 HIGH 風險，需要與用戶確認。

### Q: 可以跳過 Decision Gate 直接實作嗎？

A: 不建議。HIGH 風險決策會被 Quality Gate 或 Enforcement 阻擋。刻意繞過會留下紀錄。

### Q: 決策後發現選錯了怎麼辦？

A: 記錄為「reconsidered」，說明新資訊和新的共識。決策紀錄是學習的資料，不是秋後算帳的工具。

### Q: Decision Gate 和 Quality Gate 哪個先觸發？

A: Decision Gate 在决策前，Quality Gate 在编码时和存档后。先想清楚要做什麼，再想辦法做好。

---

## 📚 相關文件

| 文件 | 內容 |
|------|------|
| [WORKFLOW.md](./WORKFLOW.md) | 完整工作流程 |
| [QUALITY_WATCH_GUIDE.md](./QUALITY_WATCH_GUIDE.md) | 持續監控 |
| [DECISION_EXAMPLES.md](./DECISION_EXAMPLES.md) | 常見決策範例 |
| [ENFORCEMENT_HANDBOOK.md](./ENFORCEMENT_HANDBOOK.md) | Enforcement 完整手冊 |

---

## 📋 快速參考卡

```
┌─────────────────────────────────────────────────────────┐
│                    Decision Gate 速查                    │
├─────────────────────────────────────────────────────────┤
│  🔴 HIGH → 架構、API、資料庫、安全模型                    │
│           → 用戶確認、完整紀錄                            │
│                                                         │
│  🟡 MEDIUM → 預設值、工具選型、配置                      │
│            → 列出選項、簡化紀錄                          │
│                                                         │
│  🔵 LOW → 命名、格式、程式碼結構                         │
│          → 自主決定、不需紀錄                            │
└─────────────────────────────────────────────────────────┘
```

---

*最後更新：2026-03-24*
