# methodology-v2 新手上路指南

> 適用對象：新團隊成員、第一次使用 methodology-v2 的開發者
> 版本：v5.12.0
> 更新日期：2026-03-22

---

## 目錄

1. [快速開始](#1-快速開始)
2. [核心概念](#2-核心概念)
3. [新機制總覽](#3-新機制總覽)
4. [任務流程](#4-任務流程)
5. [品質保障](#5-品質保障)
6. [錯誤處理](#6-錯誤處理)
7. [P2P 協作](#7-p2p-協作)
8. [常見問題](#8-常見問題)

---

## 1. 快速開始

### 1.1 安裝

```bash
# 克隆專案
git clone https://github.com/johnnylugm-tech/methodology-v2.git
cd methodology-v2

# 安裝依賴
pip install -r requirements.txt

# 驗證安裝
python -c "from methodology import ErrorClassifier; print('OK')"
```

### 1.2 五分鐘入門

```python
from methodology import ErrorClassifier, Crew, Agent, QualityGate

# 1. 定義任務
task = "開發一個簡單的 API"

# 2. 建立 Agent 團隊
crew = Crew(
    agents=[
        Agent(role="Developer", task=task),
        Agent(role="Reviewer", task="Review code")
    ]
)

# 3. 執行
result = crew.kickoff()

# 4. 品質檢查
gate = QualityGate()
score = gate.evaluate(result)
```

---

## 2. 核心概念

### 2.1 methodology-v2 是什麼？

```
methodology-v2 = 標準化流程 + 錯誤處理 + 品質把關 + 監控
```

| 模組 | 功能 |
|------|------|
| ErrorClassifier | L1-L6 錯誤分類 |
| TaskLifecycle | 任務生命週期 |
| QualityGate | 品質把關 |
| Monitor | 監控與警報 |
| HITLController | 人類介入控制 |
| CheckpointManager | 斷點管理 |

### 2.2 開發流程

```
需求 → 設計 → 實作 → 審查 → 整合 → 品質 → 發布
```

### 2.3 錯誤分類

| 等級 | 類型 | 處理方式 |
|------|------|----------|
| L1 | 輸入錯誤 | 立即返回 |
| L2 | 工具錯誤 | 重試 3 次 |
| L3 | 執行錯誤 | 降級處理 |
| L4 | 系統錯誤 | 熔斷 + 警報 |
| L5 | 認證錯誤 | 請求人工介入 |
| L6 | 臨界錯誤 | 全面停止 + 回滾 |

---

## 3. 新機制總覽

### 3.1 v5.12.0 新增功能

| 功能 | 說明 | 優先級 |
|------|------|--------|
| Timeout 規範 | 最小 5 分鐘，公式 timeout = 評估 × 1.5 | P0 |
| A/B 雙重驗證 | Reflection + 預先驗證 | P0 |
| Kickoff 檢查清單 | 8 項基礎設施檢查 | P0 |
| HITL 節點 | 5 種情況需人工介入 | P0 |
| 斷點設計 | 支援任務中斷/恢復 | P0 |
| P2P 協作 | 對等 Agent 協作模式 | P1 |

---

## 4. 任務流程

### 4.1 標準任務流程

```
[新任務] → [Kickoff 檢查] → [設計] → [驗證] → [實作] → [Quality Gate] → [完成]
              ↓
         檢查清單
```

### 4.2 Kickoff 檢查清單

> 每個專案啟動前必須完成：

| # | 檢查項目 | 確認方式 |
|---|----------|----------|
| 1 | Git 倉庫配置 | `git remote -v` 成功 |
| 2 | 開發環境就緒 | `pip install` 成功 |
| 3 | 測試框架建立 | `pytest --collect-only` 成功 |
| 4 | CI/CD 配置 | `.github/workflows` 存在 |
| 5 | 安全基線檢查 | 掃描完成 |
| 6 | Quality Gate 標準 | 及格分數 ≥70 |
| 7 | 審批節點定義 | 審批人清單確認 |
| 8 | 通訊渠道設定 | Webhook 測試成功 |

### 4.3 A/B 協作流程

```
┌─────────────────────────────────────────────────────┐
│  Agent A (Architect) - 設計階段                     │
│  ├── 職責：架構設計、接口定義                       │
│  ├── 產出：design_spec.md                          │
│  └── 驗證：Reflection 自我審查                      │
│                       ↓                             │
│  [設計交付] ────────────────────────────────────── │
│                       ↓                             │
│  Agent B (Developer) - 實作階段                     │
│  ├── 接收設計 spec                                 │
│  ├── 預先驗證設計可行性                            │
│  ├── 實作                                          │
│  └── Code Review                                    │
└─────────────────────────────────────────────────────┘
```

### 4.4 設計驗證清單

**Agent A 交付前必須完成：**

- [ ] 接口完整：所有模組接口已定義
- [ ] 依賴清晰：外部依賴版本已確認
- [ ] 風險標記：已知風險已記錄
- [ ] 測試策略：單元/集成/端到端已規劃
- [ ] 回滾方案：失敗時可回滾

**Agent B 實作前必須完成：**

- [ ] 設計理解：確認理解所有接口
- [ ] 衝突檢查：與其他 B 無介面衝突
- [ ] 資源評估：時間/Token 評估合理
- [ ] 測試計劃：單元測試已規劃

---

## 5. 品質保障

### 5.1 Quality Gate

```python
from methodology import QualityGate

gate = QualityGate()

# 評估結果
score = gate.evaluate(result)

# 等級判定
if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "D"  # 需要修復
```

### 5.2 評分維度

| 維度 | 權重 | 說明 |
|------|------|------|
| 安全性 | 25% | SQL注入、XSS、權限 |
| 正確性 | 25% | 功能正確、邏輯完整 |
| 可維護性 | 25% | 程式碼結構、命名 |
| 測試覆蓋 | 25% | 單元/集成測試 |

### 5.3 及格標準

| 專案類型 | 最低分數 |
|----------|----------|
| POC/實驗 | 60 |
| 正式專案 | 70 |
| 產品級 | 80 |

---

## 6. 錯誤處理

### 6.1 錯誤發生時的處理

```python
from methodology import ErrorClassifier, ErrorHandler

classifier = ErrorClassifier()
handler = ErrorHandler()

try:
    result = agent.execute(task)
except Exception as e:
    level = classifier.classify(e)
    handler.handle(e, level)
```

### 6.2 需要人工介入的情況 (HITL)

| 錯誤類型 | 觸發條件 |
|----------|----------|
| L5 認證錯誤 | 權限不足、Token 過期 |
| 重大決策 | 涉及財務/安全 |
| 品質不及格 | Quality Gate < 70 |
| 超時過多 | 連續 3 次超時 |
| 未知錯誤 | 無法分類的錯誤 |

### 6.3 斷點與恢復

```python
from methodology import CheckpointManager

checkpoint = CheckpointManager()

# 保存檢查點
checkpoint.save(task_id, phase="design", data={...})

# 恢復任務
state = checkpoint.restore(task_id)
```

---

## 7. P2P 協作

### 7.1 P2P 模式

> 適用場景：多人協作、分散式團隊

```python
from methodology import AgentTeam

team = AgentTeam(mode="peer-to-peer")

# 建立 P2P 實例
dev1 = team.create_p2p_instance("developer", "dev1")
dev2 = team.create_p2p_instance("developer", "dev2")
reviewer = team.create_p2p_instance("reviewer", "reviewer1")

# P2P 訊息傳遞
dev1.send_to(dev2, {"type": "code_complete", "data": {...}})
```

### 7.2 角色與職責

| 角色 | 代號 | 職責 |
|------|------|------|
| Architect | A | 系統架構設計 |
| Developer | B | 功能實作 |
| Reviewer | C | Code Review |
| Integrator | D | 整合測試 |
| QA | E | 品質把關 |

### 7.3 訊息優先級

| 優先級 | 類型 | 處理 |
|--------|------|------|
| P0 | 設計變更 | 立即處理 |
| P1 | 接口更新 | 儘快處理 |
| P2 | 常規溝通 | 排隊處理 |
| P3 | 狀態同步 | 閒置時處理 |

---

## 8. 常見問題

### Q1: 如何決定 timeout 時間？

```
公式：timeout = 評估時間 × 1.5

| 任務類型 | 建議 timeout |
|----------|--------------|
| 簡單 | 5-10 分鐘 |
| 中等 | 15-30 分鐘 |
| 複雜 | 45-60 分鐘 |
```

### Q2: 什麼情況需要 HITL？

```
見「6.2 需要人工介入的情況」
任何 L5-L6 錯誤都需要人工確認
```

### Q3: 如何開始一個新專案？

```
1. 執行 Kickoff 檢查清單（8 項）
2. 確認 Quality Gate 標準
3. 分配 Agent 角色
4. 開始設計階段
```

### Q4: P2P 和 Master-Sub 哪個好？

| 模式 | 適用場景 |
|------|----------|
| P2P | 多人協作、平等溝通 |
| Master-Sub | 簡單分工、階層結構 |

---

## 附錄

### A. 相關資源

| 資源 | 連結 |
|------|------|
| GitHub | https://github.com/johnnylugm-tech/methodology-v2 |
| Releases | https://github.com/johnnylugm-tech/methodology-v2/releases |
| Issues | https://github.com/johnnylugm-tech/methodology-v2/issues |

### B. 版本歷史

| 版本 | 日期 | 變更 |
|------|------|------|
| v5.12.0 | 2026-03-22 | Timeout、A/B 驗證、HITL、P2P 協作 |
| v5.11.0 | 2026-03-22 | HITL 系統 |
| v5.10.0 | 2026-03-22 | Unified Config |

### C. 聯繫

- 有問題？建立 GitHub Issue
- 需要帮助？查看文檔或提問

---

*最後更新：2026-03-22 v5.12.0*
