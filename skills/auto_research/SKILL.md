# AutoResearch Skill

> **Version**: v1.0.0
> **Date**: 2026-04-09
> **Author**: Musk Agent
> **Purpose**: 自動品質改進系統 - 迭代式優化軟體品質

---

## 1. Concept & Vision

**AutoResearch** 是基於 Karpathy AutoResearch 概念的自動品質改進系統。給定一個專案，它會自動運行多輪品質評估，識別最低分維度，用 AI Agent 分析並修復問題，驗證改進效果，直到達標或達到最大迭代次數。

**核心理念**：
- 不依賴主觀假設，用數據說話
- 迭代式改進，每次小前進
- 保護機制：無改善則回滾

---

## 2. 9 維度品質模型

### 2.1 維度權重

| 維度 | 權重 | Tool-Driven | 目標分數 |
|------|------|-------------|----------|
| D1 Linting | 10% | ✅ ruff | ≥85% |
| D2 Type Safety | 15% | ✅ mypy | ≥90% |
| D3 Test Coverage | 20% | ✅ pytest-cov | ≥70% |
| D4 Security | 15% | ✅ bandit/semgrep | ≥90% |
| D5 Complexity | 10% | ✅ lizard | ≥80% |
| D6 Architecture | 10% | ⚠️ radon + agent | ≥70% |
| D7 Readability | 10% | ⚠️ agent | ≥70% |
| D8 Error Handling | 5% | ⚠️ agent | ≥60% |
| D9 Documentation | 5% | ⚠️ agent | ≥70% |

### 2.2 維度詳細說明

#### D1 Linting
- **工具**: ruff, flake8, pylint
- **測量**: error count, warning count
- **評分**: `100 - errors × 5`
- **常見問題**: 未使用 import (F401), 行太長 (E501)

#### D2 Type Safety
- **工具**: mypy, pyright
- **測量**: type error count, implicit any count
- **評分**: `100 - type_errors × 10`
- **常見問題**: 缺少 return type, implicit any

#### D3 Test Coverage
- **工具**: pytest-cov, coverage.py
- **測量**: statement %, branch %, function %
- **評分**: 直接覆蓋率百分比
- **常見問題**: 未測試的函數、低覆蓋率分支

#### D4 Security
- **工具**: bandit, semgrep, snyk
- **測量**: HIGH/MEDIUM/LOW severity issues
- **評分**: `100 - HIGH×20 - MEDIUM×10`
- **常見問題**: 硬編碼密鑰、SQL injection、XSS

#### D5 Complexity
- **工具**: lizard (cyclomatic complexity)
- **測量**: CC per function, avg CC
- **評分**: `100 - avg_CC × 5`
- **閾值**: CC > 15 為高複雜度

#### D6 Architecture
- **工具**: radon, designite
- **測量**: SOLID compliance, coupling, cohesion
- **評分**: 結構評估（主觀 + 工具）
- **注意**: 與 Error Handling 有 trade-off

#### D7 Readability
- **工具**: agent (agent-driven)
- **測量**: 命名清晰度、註釋品質、結構組織
- **評分**: agent 主觀 1-10 × 10%

#### D8 Error Handling
- **工具**: agent + 靜態分析
- **測量**: try-except 完整性、錯誤訊息清晰度
- **評分**: 模式檢測 + agent 分析
- **注意**: 與 Complexity 有 trade-off

#### D9 Documentation
- **工具**: agent + docstring detection
- **測量**: docstring 存在率、覆蓋率、清晰度
- **評分**: `(doc_files / total_files) × 100`

---

## 3. Quality Dashboard

### 3.1 Dashboard 功能

```
quality_dashboard/
├── dashboard.py          # 9維度評估引擎
├── auto_research_loop.py # AutoResearch 主循環
└── agent_auto_research.py # Agent驅動版（推薦）
```

### 3.2 使用方式

```bash
# 基本評估
python3 quality_dashboard/dashboard.py --project /path/to/project

# 生成 HTML 報告
python3 quality_dashboard/dashboard.py --project /path/to/project --html

# 顯示進化報告
python3 quality_dashboard/dashboard.py --project /path/to/project --report

# 顯示趨勢圖
python3 quality_dashboard/dashboard.py --project /path/to/project --trend
```

### 3.3 Agent-Driven AutoResearch（推薦）

```bash
# 使用 AI Agent 進行 3 輪自動改進
python3 quality_dashboard/agent_auto_research.py --project /path/to/project --iterations 3
```

---

## 4. AutoResearch Loop 流程

### 4.1 標準流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 評估                                                  │
│    python3 dashboard.py --project /path                  │
│    ↓                                                     │
│ 2. 識別最低分維度（< 70%）                              │
│    ↓                                                     │
│ 3. 分析問題根源                                          │
│    ↓                                                     │
│ 4. 執行修復                                              │
│    ↓                                                     │
│ 5. 重新評估                                              │
│    ↓                                                     │
│ 6. 如果改善 → 保留                                       │
│    如果未改善 → 回滾 + 繼續下一個維度                     │
│    ↓                                                     │
│ 7. 重複直到達標或達到最大迭代                            │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 保護機制

| 機制 | 觸發條件 | 行為 |
|------|----------|------|
| 迭代上限 | 達到 max_iterations | 停止並報告 |
| 回滾機制 | 無改善 | 回復原始代碼 |
| 無改善停止 | 連續 2 次無改善 | 停止該維度 |
| 分數上限 | 達到 100% | 跳過該維度 |

### 4.3 迭代參數

| 參數 | 預設值 | 說明 |
|------|--------|------|
| max_iterations | 5 | 最大迭代次數 |
| target_score | 85.0% | 目標總分 |
| min_dim_score | 70% | 最低維度分數門檻 |

---

## 5. 應用場景

### 5.1 專案級評估

```bash
# 評估整個專案
python3 quality_dashboard/dashboard.py --project /path/to/project

# 使用 Agent 自動改進（3輪）
python3 quality_dashboard/agent_auto_research.py --project /path/to/project --iterations 3
```

### 5.2 模組級評估

```bash
# 只評估特定模組
python3 quality_dashboard/dashboard.py --project /path/to/project/lib/module

# 指定模組並限制範圍
cd /path/to/project
python3 -c "
import sys
sys.path.insert(0, 'quality_dashboard')
from dashboard import QualityDashboard
d = QualityDashboard('lib/module')
d.run_evaluation()
"
```

### 5.3 單一檔案評估

```bash
# 只評估單一檔案
python3 quality_dashboard/dashboard.py --project /path/to/file.py

# 或直接使用工具
ruff check /path/to/file.py
mypy /path/to/file.py
```

---

## 6. 整合進 methodology-v2

### 6.1 Phase 3 整合

在 Phase 3（代碼實作）的 Pre-flight 加入 AutoResearch：

```
Phase 3 Pre-flight
    │
    ├─→ Constitution 檢查（靜態）
    │
    └─→ AutoResearch 評估（動態）
         │
         ├─→ D1-D5 工具檢查 → 立即發現問題
         │
         ├─→ D6-D9 Agent 分析 → 深度發現問題
         │
         └─→ 生成修復建議
```

### 6.2 Phase 4 整合

在 Phase 4（測試生成）確保 Coverage 達標：

```
Phase 4 Gate
    │
    ├─→ AutoResearch Coverage 檢查
    │    └─→ Coverage < 70% → BLOCK
    │
    └─→ Constitution 測試覆蓋檢查
```

### 6.3 持續監控

設定 Cron Job 定期運行：

```bash
# 每天 22:00 評估
0 22 * * * python3 /path/to/quality_dashboard/dashboard.py --project /path

# 每週生成報告
0 9 * * 0 python3 /path/to/quality_dashboard/dashboard.py --project /path --html
```

---

## 7. LLM 品質基準測試

### 7.1 應用場景

AutoResearch 可作為 LLM 品質的客觀量化標準：

| 用途 | 做法 |
|------|------|
| **LLM 比較** | 同一代碼庫，用不同 LLM 生成 → 測量品質差異 |
| **Prompt 版本比較** | Prompt V1 vs V2 → 對照實驗 |
| **Framework 版本比較** | methodology-v2 v5 vs v6 → 量化改進 |
| **Model Routing** | 根據維度分數自動選擇最佳 LLM |

### 7.2 實驗設計

```
實驗：比較 Claude 3.5 vs GPT-4o 產出品質

控制組：
- 同一個代碼庫
- 同一個任務

實驗組：
- Agent A（Claude 3.5）→ AutoResearch 測量
- Agent B（GPT-4o）→ AutoResearch 測量

結果：客觀量化差異
```

---

## 8. 限制與 Trade-off

### 8.1 維度上限

| 維度 | 上限 | 限制原因 |
|------|------|----------|
| D6 Architecture | 70% | try-except 增加 CC，trade-off |
| D8 Error Handling | ~80% | 與 Complexity 矛盾 |

### 8.2 問題分級

| 分級 | 分佈 | AutoResearch 能力 |
|------|------|------------------|
| 🔴 Critical（Runtime） | ~20-30% | ✅ 能發現 |
| 🟡 Moderate | ~20-30% | ⚠️ 部分 |
| 🟢 Minor | ~40-60% | ✅ 最常發現 |

### 8.3 與 Phase 2 的關係

- Phase 2 規格品質更高 → Phase 3 問題更少
- 但 AutoResearch 仍需要：用於處理 Phase 2 無法預見的問題
- **兩者互補，不是競爭**

---

## 9. 維度加強方向

### 9.1 新增維度

| 新維度 | 對應問題 | 工具/方法 |
|--------|----------|-----------|
| **Logic Coverage** | 條件分支覆蓋 | 分支覆蓋率測試 |
| **Security Audit** | 深度安全分析 | Semgrep + Agent 推理 |
| **Edge Case Detection** | 邊緣案例 | Fuzzing + Agent 分析 |
| **Data Integrity** | 資料一致性 | Property-based testing |

### 9.2 Critical 問題分層

| 層次 | 問題類型 | 當前能力 |
|------|----------|----------|
| L1 | 空 try-except | ✅ 能發現 |
| L2 | 邏輯錯誤 | ❌ 不能 |
| L3 | 安全漏洞 | ⚠️ 只能找到表面的 |
| L4 | Race conditions | ❌ 不能 |
| L5 | 商業邏輯缺陷 | ❌ 不能 |

---

## 10. 檔案結構

```
quality_dashboard/
├── SKILL.md                    # 本檔案
├── dashboard.py               # 9維度評估引擎
├── auto_research_loop.py      # 標準 AutoResearch
├── agent_auto_research.py     # Agent驅動版（推薦）
└── programs/                  # 維度program模板
    ├── D3_Coverage.md
    ├── D8_ErrorHandling.md
    └── ...
```

---

## 11. Quick Reference

```bash
# 1. 基本評估
python3 quality_dashboard/dashboard.py --project /path/to/project

# 2. 生成 HTML 報告
python3 quality_dashboard/dashboard.py --project /path --html

# 3. AutoResearch 3輪改進
python3 quality_dashboard/agent_auto_research.py --project /path --iterations 3

# 4. 查看進化報告
python3 quality_dashboard/dashboard.py --project /path --report

# 5. 查看技術債趨勢
python3 quality_dashboard/dashboard.py --project /path --trend
```

---

*最後更新: 2026-04-09*
