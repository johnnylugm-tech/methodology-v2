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

*最後更新：2026-03-23*
