# methodology-v2

> Multi-Agent Collaboration Development Methodology v5.56

---

## 📊 版本歷史

| 版本 | 日期 | 說明 |
|------|------|------|
| v5.21 | 2026-03-23 | Constitution 憲章系統 + 標準化專案模板 + Markdown Checklists + 新手上路/客製化/工作流程文檔 |
| v5.22 | 2026-03-23 | **實務驗證**：PolyTrade 專案完整開發記錄 (雙版本對比)、DEVELOPMENT_LOG.md、METHODOLOGY_USAGE.md |
| v5.23 | 2026-03-23 | Anti-Shortcut Framework (6 模組) |
| v5.25 | 2026-03-23 | TDAD Methodology (Mutation Testing, Hidden Tests, Impact Analysis) |
| **v5.26** | **2026-03-23** | **AI Quality Gate + TDD + Multi-Agent + Security Scanner (突破 9.0)** |
| **v5.50** | **2026-03-26** | **Framework Enforcement（Framework 內建）+ Git Enforcement 互補，所有環境皆可觸發** |
| **v5.54** | **2026-03-26** | **Traceability Matrix CLI + Dockerfile/Deployment 模板 + Framework Enforcement 自動化章節** |
| **v5.55** | **2026-03-26** | **TRACEABILITY Matrix 完整整合 FrameworkEnforcer + SPEC vs TRACE 定義 + CLI Constitution 驗證增強** |
| **v5.56** | **2026-03-26** | **Agent Personas 與 sessions_spawn 綁定 + CLI persona 命令** |

---

## v5.26 新模組 (突破 9.0)

| 模組 | 功能 | Quality Gate |
|------|------|---------------|
| ai_quality_gate | AI Code Review | score >= 90 |
| tdd_runner | 自動化測試生成 | coverage >= 80% |
| multi_agent_team | 4 Agent 協作 | 4 steps completed |
| security_scanner | 安全掃描 | score >= 95 |

### 使用方法

```python
# AI Quality Gate
from ai_quality_gate import AIQualityGate
gate = AIQualityGate()
result = gate.scan_directory('src')

# TDD Runner
from tdd_runner import TDDRunner
tdd = TDDRunner()
tdd.generate_test_cases('src')

# Multi-Agent Team
from multi_agent_team import MultiAgentTeam
team = MultiAgentTeam()
team.run_workflow('src')

# Security Scanner
from security_scanner import SecurityScanner
scanner = SecurityScanner()
scanner.scan_directory('src')
```

---

## 實務驗證案例 (v5.22)

### PolyTrade 套利系統

| 項目 | 結果 |
|------|------|
| 開發日期 | 2026-03-23 |
| 開發時間 | 50 分鐘 |
| 程式碼行數 | 754 (新版) vs 2045 (舊版) |
| 測試用例 | 7 個 |
| 通過率 | 100% |

### 兩種開發方式對比

| 維度 | 舊版 (快速) | 新版 (methodology-v2) |
|------|-------------|----------------------|
| 開發時間 | 30 min | 50 min |
| 文件量 | 4 頁 | 20+ 頁 |
| 狀態機 | ❌ | ✅ 4 states |
| 回滾機制 | ❌ | ✅ |
| 單元測試 | ❌ | ✅ |
| 可維護性 | 低 | 高 |

### methodology-v2 使用情況

| 模組 | 狀態 |
|------|------|
| 雙 Agent 協作 | ❌ 未使用 |
| Agent Quality Guard | ❌ 未使用 |
| Reflection | ❌ 未使用 |
| 錯誤分類 L1-L6 | ⚠️ 規格有，未實作 |
| 測試框架 | ✅ 使用 |
| 驗證 Gate | ✅ 使用 |
| Heartbeat | ⚠️ 規格有 |

**完整度：44%**

### Lessons Learned

1. **需要主動提議雙 Agent**：不是用戶要求的時候就該開
2. **記錄開發日誌**：每次開發都要有 timestamp
3. **使用 Agent Quality Guard**：品質把關不可或缺
4. **小型專案也該有基礎文件**：即使不完整也要有

### 產出文件

- `DEVELOPMENT_LOG.md` - 完整時間線
- `METHODOLOGY_USAGE.md` - 模組對照表
- `METHODOLOGY_COMPARISON.md` - 詳細對比報告
- `05-verify/VERIFICATION_REPORT.md` - 驗證報告
| v5.20 | 2026-03-22 | Fault Tolerance 強化：四層架構 (Retry→Fallback→Classification→Checkpoint)、Framework 對照表、上手指南 |
| v5.19 | 2026-03-22 | Human Intervention 人類介入界面（狀態儀表板、介入請求、批准流程） |
| v5.18 | 2026-03-22 | Recovery Controller 災難恢復控制中心 |
| v5.17 | 2026-03-22 | State Persistence 狀態持久化系統（支援 SQLite/Redis/檔案系統） + Checkpoint Manager |
| v5.16 | 2026-03-22 | Knowledge Sync 知識同步系統（對標 Agno 知識庫） |
| v5.15 | 2026-03-22 | Workflow Graph 工作流圖結構視覺化（對標 LangGraph） |
| v5.14 | 2026-03-22 | Async Executor 非同步執行器 |
| v5.13 | 2026-03-22 | ASPICE 實踐：traceability_matrix, verification_gate, work_product |
| v5.12 | 2026-03-22 | 正確性保障：Timeout、A/B雙重驗證、Kickoff檢查；錯誤處理：HITL機制、L1-L6分類、斷點設計；P2P協作 |
| v5.12 | 2026-03-22 | 正確性保障：Timeout、A/B雙重驗證、Kickoff檢查；錯誤處理：HITL機制、L1-L6分類、斷點設計；P2P協作 |
| v5.11 | 2026-03-22 | HITL (Human-in-the-Loop) 系統 |
| v5.10 | 2026-03-22 | Unified Config 統一配置 |
| v5.9 | 2026-03-22 | Hybrid A/B Workflow 混合分流工作流 |
| v5.8 | 2026-03-20 | CrewAI 整合 |
| v5.6 | 2026-03-21 | Three-Phase Executor, Fault Tolerant, Smart Orchestrator |
| v5.4 | 2026-03-20 | 初始版本 |

---

## 概述

這是一個標準化的多 Agent 協作開發方法論，定義了錯誤分類、開發流程、協作模式、品質把關和監控警報。

整合了三個核心 Skill：
- **ai-agent-toolkit**：工具集
- **multi-agent-toolkit**：協作框架
- **methodology-v2**：方法論核心

---

## 核心原則

- **錯誤分類**：L1-L6 六級分類（含 HITL）
- **開發流程**：6 階段標準化
- **協作模式**：Sequential / Parallel / Hierarchical / P2P
- **品質把關**：Agent Quality Guard + Quality Gate
- **監控警報**：健康評分 + 三級警報
- **工具整合**：Model Router、Quality Guard、Monitor
- **正確性保障**：Timeout、A/B雙重驗證、Kickoff檢查
- **企業級支援**：ASPICE、Contract Testing、Traceability

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

### 🚀 快速啟動 (Quick Start)

對標 CrewAI 的 minimal boilerplate，5 行啟動 Agent，3 行建立團隊：

```python
from quick_start import create_agent, create_team, quick_start

# Level 1: 5 行啟動一個 Agent
agent = create_agent(name="DevBot", role="Developer", goal="Write code")

# Level 2: 3 行建立團隊
team = create_team("DevTeam", [agent])

# Level 3: 一行執行任務
from quick_start import run_task
result = run_task(team, "Build a login system")
```

#### 預設模板

```python
# 一行建立完整團隊
team = quick_start("full")  # 4 個 Agent: Architect + Dev + Reviewer + Tester

# 開發團隊模板
team = quick_start("dev")   # 2 個 Agent: Developer + Reviewer

# PM 團隊模板
team = quick_start("pm")    # 1 個 Agent: PM
```

#### 互動式 CLI

```bash
python quick_start.py interactive  # 互動式選擇模板
python quick_start.py templates     # 查看可用模板
python quick_start.py quick         # 快速啟動完整團隊
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

---

## 🔒 品質閘道（手動執行）

> **重要**：quality_watch.py daemon 功能已移除。所有檢查都需要手動執行！

### 每個 Phase 結束必須執行的檢查

| Phase | 檢查內容 | 命令 |
|-------|----------|------|
| Phase 1 | ASPICE 文檔檢查 | `python3 quality_gate/doc_checker.py` |
| Phase 1 | Constitution 檢查 | `python3 quality_gate/constitution/runner.py --type srs` |
| Phase 2 | ASPICE 文檔檢查 | `python3 quality_gate/doc_checker.py` |
| Phase 2 | Constitution 檢查 | `python3 quality_gate/constitution/runner.py --type sad` |
| Phase 3 | ASPICE 文檔檢查 | `python3 quality_gate/doc_checker.py` |
| Phase 3 | Constitution 檢查 | `python3 quality_gate/constitution/runner.py` |
| Phase 4 | ASPICE 文檔檢查 | `python3 quality_gate/doc_checker.py` |
| Phase 4 | Constitution 檢查 | `python3 quality_gate/constitution/runner.py --type test_plan` |
| Phase 5-8 | ASPICE 文檔檢查 | `python3 quality_gate/doc_checker.py` |
| Phase 5-8 | Constitution 檢查 | `python3 quality_gate/constitution/runner.py` |

### 規格追蹤整合（v5.49+）

當執行 quality gate 時，額外檢查：

| Phase | 檢查內容 | 命令 |
|-------|----------|------|
| All | SPEC_TRACKING.md 存在性 | 自動檢查 |
| All | 規格意圖分類 | 參考 `spec_intent_classifier.md` |
| All | 決策框架對照 | 參考 `DECISION_FRAMEWORK.md` |
| All | 強化檢查清單 | 使用 `quality_gate/enhanced_checklist.md` |
| All | 規格合規驗證 | `python3 scripts/verify_spec_compliance.py` |

**整合流程**：
1. 檢查 `SPEC_TRACKING.md` 是否存在
2. 若存在，執行 `spec_intent_classifier` 檢查
3. 對照 `DECISION_FRAMEWORK` 確認決策有記錄
4. 使用 `enhanced_checklist.md` 進行檢查
5. 執行 `scripts/verify_spec_compliance.py` 驗證

**CLI 命令**：
```bash
python3 cli.py spec-track init    # 初始化 SPEC_TRACKING.md
python3 cli.py spec-track check   # 檢查規格追蹤完整性
python3 cli.py spec-track report  # 生成規格追蹤報告
```

---

### 檢查命令清單

#### 1. ASPICE 文檔檢查（必需）

```bash
# 檢查當前目錄
python3 quality_gate/doc_checker.py

# 檢查指定目錄
python3 quality_gate/doc_checker.py --path /path/to/project

# JSON 輸出
python3 quality_gate/doc_checker.py --format json
```

**檢查內容**：
- SRS.md（需求規格）
- SAD.md（架構設計）
- TEST_PLAN.md（測試計劃）
- TEST_RESULTS.md（測試結果）
- QUALITY_REPORT.md（品質報告）
- RISK_ASSESSMENT.md（風險評估）
- CONFIG_RECORDS.md（配置記錄）

#### 2. Constitution 品質檢查（必需）

```bash
# 執行 Constitution 檢查
python3 quality_gate/constitution/runner.py

# 指定類型檢查
python3 quality_gate/constitution/runner.py --type srs      # 需求規格
python3 quality_gate/constitution/runner.py --type sad      # 架構設計
python3 quality_gate/constitution/runner.py --type test_plan # 測試計劃
python3 quality_gate/constitution/runner.py --type all       # 全部
```

**檢查維度**：
| 維度 | 目標 | 權重 |
|------|------|------|
| 正確性 | 100% | 25% |
| 安全性 | 100% | 25% |
| 可維護性 | >70% | 25% |
| 測試覆蓋率 | >80% | 25% |

#### 3. Decision Gate（推薦）

```bash
# 檢查風險決策是否已確認
python3 .methodology/decisions/check_decisions.py
```

**用途**：確保所有 MEDIUM/HIGH 風險決策都已確認

#### 4. Phase Enforcer（推薦）

```bash
# 確保 Phase 依賴順序正確
python3 quality_gate/phase_artifact_enforcer.py
```

**用途**：檢查 Phase 1 必須在 Phase 2 之前完成

#### 5. Unified Gate（可選）

```bash
# 一次執行全部檢查
python3 quality_gate/unified_gate.py
```

**用途**：整合 ASPICE + Constitution + Phase Enforcer 一次執行

---

### 驗證要求

每次執行檢查後，**必須**：

1. **記錄輸出**：將檢查結果複製到 `DEVELOPMENT_LOG.md`
2. **確認通過**：檢查 `passed=True` 或 `Compliance Rate > 80%` 才能進入下一 Phase
3. **禁止假裝**：必須有實際命令輸出，不能只寫「已檢查」

#### 正確範例

```markdown
### Phase 1 Quality Gate 結果

執行命令：
python3 quality_gate/doc_checker.py

結果：
- Compliance Rate: 87.5%
- Passed: 7/8 phases

### Phase 1 Constitution 結果

執行命令：
python3 quality_gate/constitution/runner.py --type srs

結果：
- 正確性: 100%
- 安全性: 100%
- 可維護性: 75%
- 覆蓋率: 85%
```

#### 錯誤範例（禁止）

```markdown
### Phase 1 Quality Gate
✅ 已通過
```

> ⚠️ **Enforcement 觸發**：執行 `methodology quality` 時，Framework Enforcement 會自動執行。請參閱 [Enforcement（Framework 內建）](#enforcementframework-內建) 章節。

---

### 🚫 已移除的功能

| 功能 | 原因 | 替代方案 |
|------|------|----------|
| `quality_watch.py start` (daemon) | 依賴 watchdog 套件，常失效 | 手動執行命令 |
| 自動檔案監控 | 環境限制 | 每 Phase 手動檢查 |
| Git commit hook | 需要設定 | 手動檢查後再 commit |

---

## Enforcement（Framework 內建）

> 任何環境都能觸發，不依賴 Git Hook

### 執行方式

```bash
methodology quality
```

### 等級與檢查項目

| 等級 | 檢查項目 | 觸發條件 | 失敗行為 |
|------|----------|----------|----------|
| 🔴 BLOCK | SPEC_TRACKING.md 存在 | 每次 quality 執行 | 阻擋 |
| 🔴 BLOCK | 規格完整性 > 90% | 每次 quality 執行 | 阻擋 |
| 🔴 BLOCK | Constitution Score > 60% | 每次 quality 執行 | 阻擋 |
| 🟡 WARN | Decision Framework 存在 | 每次 quality 執行 | 警告 |
| 🟡 WARN | enhanced_checklist.md 更新 | 每次 quality 執行 | 警告 |

### 流程

```
1. 執行 methodology quality
2. 自動觸發 Framework Enforcement
3. 依序檢查所有 BLOCK 項目
4. 若有 BLOCK 失敗 → 顯示錯誤並阻擋
5. 若有 WARN → 顯示警告
6. 全部通過 → 繼續流程
```

### 與 Git Enforcement 的關係

| 類型 | 觸發時機 | 環境依賴 |
|------|----------|----------|
| **Framework Enforcement** | 執行 `methodology quality` | 無（任何環境）|
| **Git Enforcement** | commit/push/pr | Git + CI/CD |

兩者互補，都需要開啟。

### 範例輸出

```
🔴 [BLOCK] SPEC_TRACKING.md 不存在
   請執行: methodology spec-track init

🟡 [WARN] Decision Framework 未建立
   建議建立 DECISION_FRAMEWORK.md

✅ Framework Enforcement 通過
```

### Python 實作（可選）

如需要，可呼叫 `quality_gate/spec_tracking_checker.py` 的 `SpecTrackingChecker`

---

## Framework Enforcement（自動化）

> 透過 SKILL.md 定義，所有執行 `methodology` 命令的環境都會自動遵守

### 自動執行點

當執行以下命令時，會自動觸發對應檢查：

| 命令 | 觸發檢查 |
|------|----------|
| `methodology quality-gate check` | SPEC_TRACKING + Constitution + ASPICE |
| `methodology enforce --level BLOCK` | 所有 BLOCK 檢查 |
| `methodology spec-track check` | 規格完整性 ≥90% |
| `methodology constitution check` | Constitution Score ≥60% |

### SPEC_TRACKING vs TRACEABILITY Matrix

#### 兩個文件的區別

| 維度 | SPEC_TRACKING.md | TRACEABILITY_MATRIX.md |
|------|------------------|----------------------|
| 用途 | 規格書對照 | 需求追蹤 |
| 起點 | PDF 規格書 | 使用者需求 |
| 追蹤 | 規格 → 實作 | 需求 → 實作 → 測試 |
| 使用時機 | 有外部規格書時 | 任何專案 |

#### 選擇方式

```
有 PDF 規格書 → 使用 SPEC_TRACKING + TRACEABILITY
沒有規格書 → 只使用 TRACEABILITY
```

#### 建議

新專案應該同時建立兩個文件：
- `SPEC_TRACKING.md` - 對照外部規格
- `TRACEABILITY_MATRIX.md` - 內部需求追蹤

### 專案初始化時

```bash
# 初始化專案（自動建立追蹤矩陣）
methodology init

# 這會自動：
# 1. 建立 TRACABILITY_MATRIX.md
# 2. 建立 SPEC_TRACKING.md
# 3. 建立 Phase 目錄結構
```

### 每日開發時

```bash
# 每次完成任務
methodology task complete <task-id>

# 這會自動：
# 1. 更新 TRACABILITY_MATRIX.md
# 2. 檢查 Constitution 狀態
```

### CI-free Enforcement

> 不需要 GitHub Actions 等外部 CI

Enforcement 透過以下方式保證：

1. **CLI 入口把關**：`methodology quality-gate check` 失敗無法繼續
2. **Git Hook 可選**：如需，在 `.git/hooks/pre-commit` 加入：
   ```bash
   #!/bin/bash
   methodology enforce --level BLOCK
   ```
3. **團隊協定**：約定每次 commit 前執行 `methodology enforce`

這種方式的優點：
- 不依賴外部服務
- 任何 Git 主機都適用
- 可離線工作

---

### 📋 完整開發流程

```
1. Phase 1: 功能規格
   ├── 撰寫 SRS.md
   ├── 執行 quality_gate/doc_checker.py
   ├── 執行 quality_gate/constitution/runner.py --type srs
   └── 記錄結果到 DEVELOPMENT_LOG.md

2. Phase 2: 架構設計
   ├── 撰寫 SAD.md
   ├── 執行 quality_gate/doc_checker.py
   ├── 執行 quality_gate/constitution/runner.py --type sad
   └── 記錄結果到 DEVELOPMENT_LOG.md

3. Phase 3: 代碼實現
   ├── 撰寫程式碼
   ├── 撰寫單元測試
   ├── 執行 quality_gate/doc_checker.py
   ├── 執行 quality_gate/constitution/runner.py
   └── 記錄結果到 DEVELOPMENT_LOG.md

4. Phase 4: 測試
   ├── 撰寫 TEST_PLAN.md
   ├── 執行 quality_gate/doc_checker.py
   ├── 執行 quality_gate/constitution/runner.py --type test_plan
   └── 記錄結果到 DEVELOPMENT_LOG.md

5-8. Phase 5-8: 驗證/交付/品質/風險/配置
   ├── 補齊缺失文檔
   ├── 執行 quality_gate/doc_checker.py
   ├── 執行 quality_gate/constitution/runner.py
   └── 記錄結果到 DEVELOPMENT_LOG.md
```

---


---

### 📝 Phase 4-8 文檔模板（內容框架）

#### TEST_PLAN.md 模板（Phase 4）

```markdown
# Test Plan - [專案名稱]

## 1. 測試目標
[描述測試的主要目標和範圍]

## 2. 測試範圍
- 單元測試覆蓋範圍
- 整合測試範圍
- 系統測試範圍

## 3. 測試策略
| 類型 | 方法 | 工具 |
|------|------|------|
| 單元測試 | White-box | pytest/unittest |
| 整合測試 | Black-box | requests |
| E2E測試 | User story | Selenium |

## 4. 測試環境
- 硬體規格
- 軟體版本
- 網路配置

## 5. 測試案例清單
| ID | 案例名稱 | 優先級 | 狀態 |
|----|----------|--------|------|
| TC-001 | 登入成功 | P0 | ✅ |
| TC-002 | 密碼錯誤 | P0 | ✅ |

## 6. 風險與緩解
| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 環境不穩定 | 高 | 容器化部署 |
```

#### TEST_RESULTS.md 模板（Phase 4）

```markdown
# Test Results - [專案名稱]

## 執行摘要
- 總測試數：XX
- 通過：XX
- 失敗：XX
- 通過率：XX%

## 詳細結果
| ID | 測試案例 | 結果 | 備註 |
|----|----------|------|------|
| TC-001 | 登入成功 | ✅ PASS | |
| TC-002 | 密碼錯誤 | ✅ PASS | |

## 失敗案例分析
[失敗測試的原因和修復記錄]

## 覆蓋率報告
- 程式碼覆蓋率：XX%
- 分支覆蓋率：XX%
```

#### QUALITY_REPORT.md 模板（Phase 5-7）

```markdown
# Quality Report - [專案名稱]

## 1. 品質指標
| 指標 | 目標 | 實際 | 狀態 |
|------|------|------|------|
| 正確性 | 100% | XX% | ✅/❌ |
| 安全性 | 100% | XX% | ✅/❌ |
| 可維護性 | >70% | XX% | ✅/❌ |

## 2. ASPICE 合規性
- Phase 1 (SRS): 合規率 XX%
- Phase 2 (SAD): 合規率 XX%
- Phase 3 (Code): 合規率 XX%
- Phase 4 (Test): 合規率 XX%

## 3. 問題清單
| 嚴重性 | 描述 | 狀態 | 修復記錄 |
|--------|------|------|----------|
| High | [問題描述] | Open | [修復方式] |

## 4. 改進建議
[品質改進的具體建議]
```

#### RISK_ASSESSMENT.md 模板（Phase 5-7）

```markdown
# Risk Assessment - [專案名稱]

## 1. 風險矩陣
| ID | 風險描述 | 機率 | 影響 | 等級 | 緩解措施 |
|----|----------|------|------|------|----------|
| R1 | 技術債務過高 | 高 | 高 | 🔴 | 重構關鍵模組 |

## 2. 技術風險
- [風險描述]: [緩解方案]
- [風險描述]: [緩解方案]

## 3. 商業風險
- [風險描述]: [緩解方案]

## 4. 監控計畫
[持續監控風險的計畫]
```

#### CONFIG_RECORDS.md 模板（Phase 8）

```markdown
# Configuration Records - [專案名稱]


#### TEST_RESULTS.md 模板（Phase 5）

```markdown
# Test Results - [專案名稱]

## 1. 執行摘要
- 總測試數：XX
- 通過：XX
- 失敗：XX
- 通過率：XX%
- 執行時間：YYYY-MM-DD HH:MM

## 2. 測試結果詳細
| ID | 測試案例 | 預期結果 | 實際結果 | 狀態 |
|----|----------|----------|----------|------|
| TC-001 | 登入成功 | 返回 token | 返回 token | ✅ PASS |

## 3. 失敗案例分析
### TC-XXX: [失敗測試名稱]
- **原因**: [根本原因]
- **修復方式**: [修復方案]
- **狀態**: 已修復/待修復

## 4. 覆蓋率報告
| 類型 | 覆蓋率 | 備註 |
|------|--------|------|
| 程式碼覆蓋率 | XX% | |
| 分支覆蓋率 | XX% | |

## 5. 回歸測試
[之前失敗的測試是否通過]
```

#### BASELINE.md 模板（Phase 5）

```markdown
# Baseline - [專案名稱]

## 1. 基線概述
| 項目 | 內容 |
|------|------|
| 基線版本 | v1.0.0 |
| 建立日期 | YYYY-MM-DD |
| 階段 | Phase 5 (驗證與交付) |
| 狀態 | APPROVED |

## 2. 功能基線
| 功能 ID | 功能名稱 | 狀態 | 驗證方式 |
|---------|----------|------|----------|
| FR01 | 文字輸入 | ✅ 已實現 | 單元測試 |
| FR02 | 語音合成 | ✅ 已實現 | 整合測試 |

## 3. 品質基線
| 指標 | 目標 | 實際 | 狀態 |
|------|------|------|------|
| 正確性 | 100% | 100% | ✅ |
| 安全性 | 100% | 100% | ✅ |
| 可維護性 | >70% | XX% | ✅/❌ |

## 4. 風險基線
| 風險 ID | 風險描述 | 等級 | 狀態 |
|---------|----------|------|------|
| R1 | 網路不穩定 | 中 | 監控中 |

## 5. 變更記錄
| 日期 | 變更內容 | 變更者 | 批准人 |
|------|----------|--------|--------|
| YYYY-MM-DD | 初始基線 | Agent | PM |

## 6. 驗收簽收
| 角色 | 簽名 | 日期 |
|------|------|------|
| PM | [簽名] | YYYY-MM-DD |
| QA | [簽名] | YYYY-MM-DD |
```

#### RISK_REGISTER.md 模板（Phase 7）

```markdown
# Risk Register - [專案名稱]

## 1. 風險概覽
| 總風險數 | 高風險 | 中風險 | 低風險 | 已關閉 |
|---------|--------|--------|--------|--------|
| XX | X | X | X | X |

## 2. 風險登錄表
| ID | 風險描述 | 類別 | 等級 | 機率 | 影響 | 狀態 | 緩解措施 | 負責人 |
|----|----------|------|------|------|------|------|----------|--------|
| R1 | 網路中斷導致合成失敗 | 技術 | 🔴 高 | 中 | 高 | Open | 重試機制 | Dev |
| R2 | API 配額限制 | 技術 | 🟡 中 | 高 | 中 | Closed | 快取機制 | Dev |

## 3. 風險應對計畫
### R1: 網路中斷導致合成失敗
- **觸發條件**: 網路連線失敗超過 30 秒
- **應對策略**: 重試 3 次 → 降級處理 → 返回錯誤訊息
- **復原時間**: < 5 分鐘
- **演練頻率**: 每月一次

## 4. 風險監控記錄
| 日期 | 風險 ID | 事件 | 處理結果 |
|------|---------|------|----------|
| YYYY-MM-DD | R1 | 網路閃斷 | 自動重試成功 |

## 5. 風險關閉條件
- 緩解措施已實施並驗證
- 連續 30 天無觸發事件
- 經 PM 批准


## 1. 版本資訊
| 元件 | 版本 | 日期 | 備註 |
|------|------|------|------|
| Core | v1.0.0 | YYYY-MM-DD | 初始發布 |

## 2. 環境配置
### 開發環境
- Node.js: v20.x
- Python: 3.11
- Database: PostgreSQL 15

### 生產環境
- [配置詳情]

## 3. 依賴管理
| 套件 | 版本 | 用途 |
|------|------|------|
| axios | ^1.6.0 | HTTP Client |

## 4. 部署記錄
| 日期 | 版本 | 部署環境 | 變更內容 |
|------|------|----------|----------|
| YYYY-MM-DD | v1.0.0 | Production | 初始發布 |
```

### 🎯 目標

| 指標 | 目標 |
|------|------|
| ASPICE 合規率 | > 80% |
| Constitution 總分 | > 70/100 |
| 檢查執行率 | 100% (每 Phase 都要) |

---

### 📁 文件位置

| 功能 | 路徑 |
|------|------|
| Quality Gate | `quality_gate/doc_checker.py` |
| Constitution | `quality_gate/constitution/runner.py` |
| Decision Gate | `.methodology/decisions/` |
| Phase Enforcer | `quality_gate/phase_artifact_enforcer.py` |
| Unified Gate | `quality_gate/unified_gate.py` |

### 發布檢查清單

- [ ] 版本號更新
- [ ] CHANGELOG 記錄
- [ ] README 更新
- [ ] docs/ 同步
- [ ] 測試通過
- [ ] GitHub Release
- [ ] (可選) ClawHub

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
        └── Monitor            (監控)
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

---

## 工作產品 (Work Products)

結構化追蹤 Agent 產出，確保每個產出都有明確的類型、擁有者和驗證狀態。

### 基本使用

```python
from work_product import WorkProductRegistry, ProductType, register_product

# 初始化
registry = WorkProductRegistry()

# 快速註冊
product = register_product(
    name="用戶認證模組",
    product_type=ProductType.CODE,
    owner_agent_id="agent-dev-001",
    content="def authenticate(user, passwd): ...",
    metadata={"language": "python"}
)

# 驗證
product.verify("reviewer-001")

# 查詢
summary = registry.get_verification_summary()
print(f"驗證率: {summary['verification_rate']}")
```

### 產品類型

| 類型 | 說明 |
|------|------|
| CODE | 代碼產出 |
| DOCUMENT | 文檔資料 |
| REPORT | 報告分析 |
| TEST_RESULT | 測試結果 |
| CONFIG | 配置檔案 |
| MODEL | 模型檔案 |
| DATA | 資料檔案 |

### 驗證狀態

| 狀態 | 說明 |
|------|------|
| UNVERIFIED | 待驗證 |
| VERIFIED | 已驗證 |
| FAILED | 驗證失敗 |

### 查詢方式

```python
# 依 Agent 查詢
registry.get_by_agent("agent-dev-001")

# 依類型查詢
registry.get_by_type(ProductType.CODE)

---

## 附錄：正確的模組使用方式

### Fault Tolerant

```python
from fault_tolerant import CircuitBreaker, FaultTolerantExecutor

# 初始化（需要 name 參數）
cb = CircuitBreaker(name="my-circuit")
executor = FaultTolerantExecutor(name="my-executor")

# 使用裝飾器
@with_fault_tolerance(max_retries=3, backoff=2.0)
async def my_function():
    pass
```

### Governance

```python
from governance.governance_agent import GovernanceAgent

agent = GovernanceAgent()
```

### Error Classification

```python
from methodology_base import ErrorClassifier, ErrorLevel

classifier = ErrorClassifier()
level = classifier.classify(ValueError("test"))
# 返回: ErrorLevel.L1, L2, L3, L4, L5, L6
```

# 取得未驗證產品
registry.get_unverified()

# 驗證摘要
registry.get_verification_summary()
```

詳細案例：請參考 `docs/cases/case33_work_products.md`

---

### Async Executor

對標 AutoGen 的 async/await 支援，提供 asyncio 原生的並發任務執行能力。

```python
from async_executor import AsyncExecutor, run_async, run_parallel

# 使用 executor
executor = AsyncExecutor(max_concurrency=5)

async def my_task(name):
    await asyncio.sleep(1)
    return f"{name} done"

# 創建任務
executor.create_task("task1", my_task("A"))
executor.create_task("task2", my_task("B"))

# 執行並取得結果
results = await executor.execute_all()

# 便捷函數
result = await run_async(agent.execute("task"), timeout=30.0)
results = await run_parallel(task1(), task2(), task3(), max_concurrency=10)
```

| 功能 | 說明 |
|------|------|
| 並發執行 | 控制最大並發數，避免資源耗盡 |
| 超時控制 | 支援任務級別的超時設定 |
| 錯誤處理 | 單一任務失敗不影響其他任務 |
| 結果收集 | 統一收集所有任務結果 |

詳細案例：請參考 `docs/cases/case37_async_executor.md`

---

### Checkpoint Manager

狀態快照管理，支援 Agent 狀態的定期快照、恢復和查詢。

```python
from checkpoint_manager import CheckpointManager, CheckpointStatus

# 初始化
cm = CheckpointManager(
    storage_path="./checkpoints",
    max_checkpoints=100
)

# 保存快照
ckpt_id = cm.save(
    agent_id="agent_001",
    task_id="task_001",
    state={"progress": 50, "data": {...}},
    checkpoint_type="auto",  # auto, manual, on_complete
    metadata={"step": 5}
)

# 恢復快照
state = cm.load(ckpt_id)

# 取得最新快照
latest = cm.get_latest("agent_001")

# 列出所有快照
checkpoints = cm.list_checkpoints("agent_001")

# 刪除快照
cm.delete(ckpt_id)

# 導出/導入
json_str = cm.export_checkpoint(ckpt_id)
new_id = cm.import_checkpoint(json_str)
```

| 功能 | 說明 |
|------|------|
| 雙重儲存 | 記憶體快速訪問 + 磁碟持久化 |
| 自動清理 | 超過上限自動刪除最舊快照 |
| 快照類型 | auto, manual, on_complete |
| 快照狀態 | active, committed, obsolete |
| 導出導入 | JSON 格式跨系統共享 |

詳細案例：請參考 `docs/cases/case39_checkpoint_manager.md`

---

## State Persistence (狀態持久化)

Session 狀態持久化系統，支援多種後端。

```python
from state_persistence import StatePersistence, StorageBackend

# SQLite 後端（單機）
persistence = StatePersistence(backend=StorageBackend.SQLITE)

# Redis 後端（分散式）
persistence = StatePersistence(
    backend=StorageBackend.REDIS,
    config={"redis_host": "localhost", "redis_port": 6379}
)

# 儲存 Session
persistence.save_state(session_id, agent_id, state)

# 載入 Session
state = persistence.load_state(session_id)

# 併發鎖定
persistence.lock_session(session_id, owner="agent_002")
persistence.unlock_session(session_id, owner="agent_002")
```

詳細案例：請參考 `docs/cases/case40_state_persistence.md`

---

## Human Intervention (人類介入界面)

人類介入系統，讓人類可以查看狀態、請求介入、批准行動。

```python
from human_intervention import (
    HumanIntervention,
    InterventionType,
    InterventionStatus
)

# 初始化人類介入系統
hi = HumanIntervention()

# 請求介入
request_id = hi.request_intervention(
    agent_id="dev_agent_001",
    task_id="deploy_to_production",
    intervention_type=InterventionType.APPROVAL,
    reason="即將部署到生產環境，需要人類確認",
    current_state={"changes": ["user_auth.py"], "risk_level": "high"},
    suggested_actions=["確認部署", "檢查測試覆蓋率"],
    priority=5
)

# 批准請求
hi.approve_action(request_id, approver="johnny", comments="確認部署")

# 拒絕請求
hi.reject_action(request_id, rejector="johnny", reason="測試覆蓋率不足")

# 查看狀態儀表板
dashboard = hi.show_status(agent_id="dev_agent_001")
print(hi.export_dashboard_text(dashboard))

# 獲取待處理請求
pending = hi.get_pending_requests(priority=4)

# 獲取介入摘要
summary = hi.get_intervention_summary()
```

### 介入類型

| 類型 | 說明 |
|------|------|
| `APPROVAL` | 需要批准（高風險操作） |
| `CORRECTION` | 需要修正（錯誤處理） |
| `ESCALATION` | 需要升級（專家介入） |
| `NOTIFICATION` | 僅通知 |

詳細案例：請參考 `docs/cases/case42_human_intervention.md`

---

## Fault Tolerance（容錯與災難復原）

Methodology-v2 提供完整的 Fault Tolerance 方案，透過四層架構確保系統在遇到錯誤或故障時能繼續運作或優雅降級。

### 四層架構

| 層級 | 功能 | 說明 |
|------|------|------|
| **L1: Retry with Backoff** | 自動重試 | 網路瞬斷、API 限流時等一下再試 |
| **L2: Model Fallback** | 模型切換 | 主模型當機時自動切換備用模型 |
| **L3: Error Classification** | 錯誤分類 | 不同錯誤類型不同處理方式 |
| **L4: Checkpoint Recovery** | 快照恢復 | 系統崩潰後從快照恢復 |

### 四大核心工具

| 工具 | 模組 | 功能 |
|------|------|------|
| `CheckpointManager` | `checkpoint_manager.py` | 任務執行中定期快照，中斷後恢復 |
| `StatePersistence` | `state_persistence.py` | 跨 session 保持狀態（SQLite/Redis） |
| `RecoveryController` | `recovery_controller.py` | 失敗自動分類 + 建立恢復計劃 |
| `HumanIntervention` | `human_intervention.py` | 危險操作前或連續失敗時需要人類審批 |

### 推薦組合

| 專案規模 | 組合 |
|---------|------|
| 小型（單機） | `CheckpointManager` |
| 中型（單機 + DB） | `CheckpointManager` + `StatePersistence` + `RecoveryController` |
| 大型（分散式） | 全部四個工具 + 通知系統（Slack/Email） |

📖 **詳細上手指南：** [docs/FAULT_TOLERANCE_GUIDE.md](docs/FAULT_TOLERANCE_GUIDE.md)
📖 **案例文檔：**
- [Checkpoint Manager](docs/cases/case39_checkpoint_manager.md)
- [State Persistence](docs/cases/case40_state_persistence.md)
- [Recovery Controller](docs/cases/case41_recovery_controller.md)
- [Human Intervention](docs/cases/case42_human_intervention.md)

---

## 統一角色定義 (Agent Role)

對標 CrewAI 的 Role-based Agent 概念，實現統一的角色定義系統。

```python
from agent_role import (
    AgentRole, 
    RoleType, 
    Permission, 
    Skill,
    RoleRegistry
)

# 建立角色
dev_role = AgentRole(
    role_id="role-dev-001",
    name="Developer",
    role_type=RoleType.DEVELOPER,
    goals="Write high-quality code",
    backstory="Experienced software engineer",
    permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE],
    skills=[Skill("coding", 5), Skill("debugging", 4)]
)

# 檢查權限
dev_role.has_permission(Permission.WRITE)  # True

# 使用角色註冊表
registry = RoleRegistry()
registry.register(dev_role)
role = registry.get("role-dev-001")
```

### 預設角色

| 角色 | ID | 權限 |
|------|-----|------|
| Developer | role-dev | read, write, execute |
| Code Reviewer | role-review | read, approve |
| Project Manager | role-pm | read, write, approve, delete |

詳細案例：請參考 `docs/cases/case34_agent_role.md`

---

## Agent Persona（預設套用）

### 概念

Agent Persona 為每個 Agent 賦予豐富的角色內涵，不僅是 role 名稱，還包括：
- **Goal**: Agent 的目標
- **Backstory**: Agent 的背景故事
- **Personality**: Agent 的人格特徵

### 預設人格類型

| 人格 | 適用場景 |
|------|----------|
| `architect` | Phase 1-2 需求分析、架構設計 |
| `developer` | Phase 3 代碼實作 |
| `reviewer` | 代碼審查、安全審查 |
| `qa` | Phase 4 測試、邊界 case |
| `pm` | 需求管理、優先級排序 |
| `devops` | Phase 5-8 部署、CI/CD |

### 使用方式

```python
# 方式 1: 自動套用（根據 role）
from agent_spawner import spawn_with_persona
session = spawn_with_persona(role="developer", task="實作登入功能")

# 方式 2: 明確指定人格
session = spawn_with_persona(
    role="developer",
    persona_type="architect",
    task="設計系統架構"
)
```

### CLI 命令

```bash
# 列出所有人格
methodology persona list

# 套用到當前任務
methodology persona apply developer
```

---

## Agent 執行框架（完整版）

### 角色定位

**極度嚴謹的軟體工程架構師**

- 專精於 methodology-v2 skill 規範
- 核心使命：依據 methodology-v2 規範進行規格實作與方法論驗證
- 開發目標：零偏差將規格書轉化為符合規範的代碼

### 執行黃金準則

#### 100% 強制落實

以下項目必須完全、無例外地符合 methodology-v2 定義：
- 架構分層
- 模組解耦邏輯
- 命名規則（Naming Convention）
- 錯誤處理機制（Error Handling）

#### 衝突處理原則

若規格書與 methodology-v2 產生衝突：
1. **禁止私自妥協**
2. **優先選擇符合 methodology-v2 的實作方式**
3. 在開發日誌中詳細記錄該衝突點（Conflict Log）

#### 禁止幻覺

> 不得引入任何不屬於 methodology-v2 或規格書外的第三方框架或私有習慣。

---

### 交付成果格式

每次執行任務時，必須依序交付以下內容：

#### A. 開發日誌（Development Log）

```markdown
## 開發日誌

### 步驟 1: [動作]
- 開發步驟 → 決策邏輯 → 對應規範條文

### 衝突記錄（若有）
| 衝突點 | 規格建議 | methodology-v2 選擇 | 理由 |
|--------|----------|---------------------|------|
```

#### B. 完整原始碼（Production-Ready Code）

要求：
- 單元測試覆蓋率 100%
- 代碼註解標注對應規範條文

```python
class TTSEngine:
    """
    TTS 引擎 - 語音合成核心
    
    對應 methodology-v2 規範：
    - SKILL.md - Core Modules
    - SKILL.md - Error Handling
    """
```

#### C. 合規矩陣（Compliance Matrix）

```markdown
| 功能模組 | 對應 methodology-v2 檔案/規範 | 執行狀態 | 備註 |
|----------|-------------------------------|----------|------|
| TTSEngine | SKILL.md - Core Modules | 100% 落實 | 無 |
| TextProcessor | SKILL.md - Data Processing | 100% 落實 | 無 |
```

#### D. 回饋報告（Refinement Report）

```markdown
## 方法論實戰回饋

### 有效性評估
| 規範 | 效果（⭐）| 說明 |
|------|----------|------|
| 分層設計 | ⭐⭐⭐⭐⭐ | 顯著提升架構品質 |

### 修正建議
| 問題 | 建議 |
|------|------|
```

---

### 快速使用

```markdown
## 使用方式

當你提供規格書給 Agent 時，只需說：

「請依據 methodology-v2 規範執行此任務」

Agent 會自動：
1. 套用「極度嚴謹的軟體工程架構師」人格
2. 遵循執行黃金準則
3. 按交付成果格式提供完整產出
```

---

*這個方法論幫助團隊標準化多 Agent 協作開發流程*

---

## 2026-03-27 改善方案：強制使用 A/B 協作機制

### 問題診斷

| 問題 | 原因 |
|------|------|
| 只有 1 個 Agent | 沒用 quick_start() |
| 沒人審查 code | 沒用 Agent Evaluator |
| 失敗還繼續 | 沒用 Hybrid Workflow |
| 品質爛 | 沒分工，沒人把關 |

### 解決方案：直接使用現有機制

#### 1. 啟動 Multi-Agent 協作

```python
from methodology import quick_start

# 2 Agent: Developer + Reviewer（推薦）
team = quick_start("dev")

# 或 4 Agent: Architect + Dev + Reviewer + Tester
team = quick_start("full")
```

#### 2. 強制 A/B 審查

```python
from agent_evaluator import AgentEvaluator

evaluator = AgentEvaluator()

# 每次 commit 前都要 A/B 評估
result = evaluator.evaluate(code_a, code_b)
if not result.approved:
    # 阻止 commit
    raise Exception("Code not approved")
```

#### 3. Hybrid Workflow 模式

```python
from hybrid_workflow import HybridWorkflow

# OFF: 直接執行
# HYBRID: 簡單直接，複雜 A/B
# ON: 強制 A/B 審查
workflow = HybridWorkflow(mode="ON")  # 強制
```

#### 4. 角色分工

| 角色 | 職責 |
|------|------|
| Developer | 寫代碼 |
| Code Reviewer | 審查代碼（不能是同一人） |
| Tester | 實際執行測試 |
| Architect | 確認架構 |

#### 5. 檢查清單（每次 commit 前）

- [ ] Developer 寫完 code
- [ ] Code Reviewer 審查並 approve
- [ ] Tester 執行 pytest 通過
- [ ] Architect 確認架構 OK
- [ ] Hybrid Workflow mode = ON

### 禁止事項

| 禁止 | 原因 |
|------|------|
| ❌ 只有 1 個 Agent | 必須用 quick_start("dev") |
| ❌ 自己寫自己審 | 必須不同人審查 |
| ❌ 不跑測試就 commit | Tester 必須實際執行 |
| ❌ QG 失敗還繼續 | 失敗就停止，不能給藉口 |

### 驗證命令

```bash
# 確認有 2+ Agent 運行
team.list_agents()

# 確認 Hybrid Workflow 模式
workflow.mode  # 應該是 "ON"

# 執行 A/B 評估
python -m agent_evaluator --check
```

---

*改善方案日期: 2026-03-27*
