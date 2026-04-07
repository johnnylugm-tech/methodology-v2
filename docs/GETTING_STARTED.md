# methodology-v2 新手上路指南

> 適用於新團隊快速上手 methodology-v2

---

## 🚨 開始之前必讀

**新團隊請先完成 [CHECKLIST.md](../CHECKLIST.md)（前置檢查清單）！**

這份清單告訴你：
- 環境需求
- 安裝步驟
- 設定檢查
- 常見問題

---

## 📋 快速概述

| 問題 | 答案 |
|------|------|
| 這是什麼？ | Multi-Agent 協作開發方法論 |
| 解決什麼？ | 多 Agent 協作時的錯誤處理、品質把關、驗證追蹤 |
| 適合誰？ | 使用 AI Agent 開發軟體的團隊 |

---

## 🎯 核心概念

### 1. 錯誤分類（L1-L6）

| 等級 | 類型 | 範例 | 處理方式 |
|------|------|------|----------|
| L1 | 配置錯誤 | API Key 缺失 | 不允許啟動 |
| L2 | API 錯誤 | Timeout、Rate Limit | 重試 + Fallback |
| L3 | 業務錯誤 | 驗證失敗 | 記錄 + 降級 |
| L4 | 預期異常 | 網路波動 | 記錄 + 忽略 |
| L5 | 環境錯誤 | 磁碟滿 | 告警 + 人工介入 |
| L6 | 災難錯誤 | 資料損毀 | 進入災難復原模式 |

### 2. 驗證關卡（Verification Gates）

```
任務開始 → Gate 1: 語法檢查 → Gate 2: 單元測試 → Gate 3: Quality Gate → 完成
```

### 3. 品質標準（Quality Gate）

| 維度 | 閾值 | 權重 |
|------|------|------|
| 正確性 | >= 80% | 30% |
| 安全性 | >= 100% | 25% |
| 可維護性 | >= 70% | 20% |
| 效能 | >= 80% | 15% |
| 覆蓋率 | >= 80% | 10% |

> **v5.45 更新**：Quality Gate 改為手動執行模式。進入每個 Phase 前，請手動執行：
> `python3 cli.py quality-gate check` 或 `python3 quality_gate/doc_checker.py`

---

## 🚀 快速開始

### 步驟 1：安裝

```bash
pip install methodology-v2
```

### 步驟 2：初始化專案結構

```
your-project/
├── constitution/          # 團隊憲章
│   └── CONSTITUTION.md
├── src/                   # 程式碼
├── tests/                 # 測試
└── docs/                 # 文檔
```

### 步驟 3：設定 Quality Gate

```python
from quality_gate import QualityGate

gate = QualityGate(thresholds={
    "correctness": 80,
    "security": 100,
    "maintainability": 70,
    "performance": 80,
    "coverage": 80
})

# 檢查你的程式碼
result = gate.check("./src")
print(f"Score: {result['score']}/100")
```

###步驟 4：設定 Fault Tolerance

```python
from fault_tolerant import FaultTolerant

@FaultTolerant.retry(max_attempts=3, backoff="exponential")
def call_api():
    # 可能會失敗的 API 呼叫
    return api.request()
```

---

## 📚 學習路徑

### 第一天：基礎概念

1. 閱讀本指南
2. 理解 L1-L6 錯誤分類
3. 運行第一個範例

### 第二天：核心功能

1. 設定 Quality Gate
2. 設定 Fault Tolerance
3. 使用 Verification Gates

### 第三天：進階功能

1. 設定 P2P 協作
2. 設定 HITL（人類介入）
3. 客製化 Constitution

---

## 🔧 常見使用場景

### 場景 1：API 開發

```python
from methodology import Agent, QualityGate

# 建立 Agent
agent = Agent(name="api-developer")

# 定義任務
task = """
建立一個用戶認證 API
- POST /login
- POST /register
- GET /profile
"""

# 執行（自動品質把關）
result = agent.execute(task, quality_gate=True)
```

### 場景 2：Bug 修復

```python
from fault_tolerant import FaultTolerant

@FaultTolerant.retry(max_attempts=3)
def fix_bug():
    # 修復邏輯
    pass

# 自動錯誤分類
result = classify_error(exception)
print(f"Error Level: L{result['level']}")
```

---

## 📞 獲取幫助

| 資源 | 連結 |
|------|------|
| GitHub | https://github.com/johnnylugm-tech/methodology-v2 |
| 問題回報 | GitHub Issues |
| 文檔 | /docs |

---

## 進階：自訂憲章

根據團隊需求調整 methodology-v2：

- [CUSTOMIZATION_GUIDE.md](CUSTOMIZATION_GUIDE.md) - 調整品質閾值、錯誤分類
- [Constitution](../constitution/CONSTITUTION.md) - 團隊憲章核心原則
- [PROJECT_STRUCTURE.md](../templates/PROJECT_STRUCTURE.md) - 標準化專案結構

使用 Constitution CLI 查看：
```bash
python3 cli.py constitution view      # 查看憲章
python3 cli.py constitution thresholds # 查看品質閾值
python3 cli.py constitution errors     # 查看錯誤等級
```

---

---

## 🔴🟡🔵 Decision Gate（決策分類閘道）

在技術決策時使用 Decision Gate 追蹤所有重大選擇，HIGH 風險決策需確認後才能執行。

### 基本用法

```bash
# 新增技術決策並自動分類
python3 cli.py decision classify "遷移到 PostgreSQL" "將資料庫從 MySQL 遷移到 PostgreSQL"

# 列出所有決策
python3 cli.py decision list

# 查看待確認的 HIGH 風險決策
python3 cli.py decision pending

# 確認決策（提供具體採用的值）
python3 cli.py decision confirm <id> "PostgreSQL 15.3 + pgvector"

# 產生決策報告
python3 cli.py decision report
```

### 風險等級

| 等級 | 意義 | 需要確認 |
|------|------|----------|
| HIGH | 重大架構變更、不可逆決策 | ✅ 需要 |
| MEDIUM | 中等影響、局部變更 | ❌ 不需要 |
| LOW | 小調整、純粹實施細節 | ❌ 不需要 |

詳見：[DECISION_GATE_GUIDE.md](DECISION_GATE_GUIDE.md)

---

*最後更新：2026-03-24*
