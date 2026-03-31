# methodology-v2

> Multi-Agent Collaboration Development Methodology v6.02.0

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
| **v5.59** | **2026-03-29** | **Ralph Mode - 任務長時監控模組（狀態持久化、階段狀態機、進度追蹤）** |
| **v5.85** | **2026-03-29** | **Ralph Mode 預設啟動 - Agent 建立新專案時自動啟動 Ralph Mode 監控** |
| **v5.86** | **2026-03-29** | **整合 Agent Quality Guard 到 PhaseEnforcer (L3)** |
| **v5.87** | **2026-03-29** | **整合 Phase1_Plan_5W1H_AB.md 精華：DEVELOPMENT_LOG 格式、A/B 審查模板、附錄章節** |
| **v5.88** | **2026-03-29** | **整合 Phase2_Plan_5W1H_AB.md 精華：SAD.md 最低要求、A/B 架構審查清單、Conflict Log 格式** |
| **v5.89** | **2026-03-29** | **整合 Phase3_Plan_5W1H_AB.md 精華：代碼規範、單元測試三類、集成測試模板、同行邏輯審查對話、合規矩陣** |
| **v5.90** | **2026-03-29** | **整合 Phase4_Plan_5W1H_AB.md 精華：TEST_PLAN/TEST_RESULTS 完整規格、兩次 A/B 審查流程、Tester≠Developer 角色分離原則、失敗案例根本原因分析** |
| **v5.93** | **2026-03-29** | **Phase1-8 5W1H 整合審計修正（P0-P3）：Phase 1 新增獨立 5W1H 章節、Phase 1 退出條件補齊 SPEC_TRACKING 完整性檢查、Phase 4 補充 WHEN/WHERE/WHY/HOW、Phase 3 加入 phase_artifact_enforcer.py、Phase 6-7 加入 session_id 記錄要求、Phase 7 加入邏輯正確性閾值、Phase 8 統一監控時段定義** |
| **v5.94** | **2026-03-29** | **Phase 1-8 5W1H 審計修正（P1-P2）：Phase 4 WHERE 加入 spec_logic_checker.py、Phase 4 退出條件代碼覆蓋率明確為單元測試、Phase 3 退出條件加入代碼覆蓋率 ≥ 70%、Phase 6 進入條件加入測試通過率 = 100%、Phase 7 前置條件加入驗證測試通過率 = 100%、Phase 8 新增 SUP.8 配置管理說明** |
| **v5.95** | **2026-03-29** | **Core Test Suite: 4 個測試檔案（spec_logic_checker, unified_gate, phase_enforcer, constitution_runner）、Ralph Mode smoke test、CHANGELOG v5.82-v5.95 更新** |
| **v5.96** | **2026-03-29** | **PhaseEnforcer 獨立 smoke test、UnifiedGate 覆蓋矩陣** |
| **v5.97** | **2026-03-30** | **VERSION_SOP.md、COVERAGE_MATRIX.md** |
| **v5.98** | **2026-03-30** | **Phase enum 擴展 6→9 phases、FrameworkEnforcer ASPICE mapping** |
| **v5.99** | **2026-03-30** | **BUG-001 + BUG-002 修復** |
| **v6.00** | **2026-03-31** | **版本統一** |
| **v6.02** | **2026-03-31** | **Integrity Tracker + Constitution 整合** |
| **v5.92** | **2026-03-29** | **整合 Phase5+7+8_Plan_5W1H_AB.md 精華：Phase 5 兩次 A/B 審查 + BASELINE 完整規格 + MONITORING_PLAN；Phase 7 五維度風險識別 + Decision Gate + 四層緩解措施；Phase 8 CONFIG_RECORDS 8 章節 + 七區塊發布清單 + 方法論閉環確認** |

---

## v5.59 新模組：Ralph Mode

| 模組 | 功能 | Quality Gate |
|------|------|---------------|
| ralph_mode | 任務長時監控 | 任務狀態持久化到 JSON |
| task_persistence | TaskState 類別 | save/load JSON |
| scheduler | 定時輪詢 | 間隔可配置 |
| state_machine | 階段狀態機 | 6 階段轉換 |
| progress_tracker | 進度追蹤 | PROGRESS.md |

### Ralph Mode 功能說明

**核心目標**：為長時運行的批次任務提供狀態持久化、定時監控和進度追蹤。

**階段流程**：
```
init → run_batch → extract → eval → report → done
```

**CLI 命令**：

```bash
# 初始化任務
methodology ralph init task-001

# 啟動監控
methodology ralph start task-001 --interval 60 --background

# 查看狀態
methodology ralph status task-001

# 列出所有任務
methodology ralph list --status running

# 停止監控
methodology ralph stop task-001

# 推進階段
methodology ralph advance task-001 --to eval
```

**Python API**：

```python
from ralph_mode import (
    TaskState,
    TaskPersistence,
    RalphScheduler,
    PhaseStateMachine,
    RalphProgressTracker,
)

# 任務持久化
persistence = TaskPersistence()
state = TaskState(task_id="task-001", status="running", current_phase="init")
persistence.save_state(state)

# 進度追蹤
tracker = RalphProgressTracker("task-001")
tracker.update_progress("run_batch", 50.0)

# 狀態機
sm = PhaseStateMachine()
sm.start()
sm.advance()  # 推進到下一階段
```

**獨立 CLI**：

```bash
# 也可以直接使用 ralph_mode/cli.py
python -m ralph_mode.cli start task-001
python -m ralph_mode.cli status task-001
python -m ralph_mode.cli list
```

---

## v5.85: Ralph Mode 預設啟動

| 模組 | 功能 | Quality Gate |
|------|------|---------------|
| ralph_mode | 預設啟動監控 | 自動初始化 Ralph Mode |
| RalphScheduler | 後台定時監控 | 每 5 分鐘檢查 Phase |
| PhaseStateMachine | 階段狀態追蹤 | init → run_batch → extract → eval → report → done |

### 啟動觸發條件

當 Agent 建立新專案或啟動 develop 工作流程時，自動：
1. 執行 `python -m ralph_mode init <project_id>`
2. 啟動 RalphScheduler 後台監控
3. 每 5 分鐘檢查 Phase 進度

### 使用範例

```python
# 使用 Ralph Mode
from ralph_mode import RalphMode

ralph = RalphMode()
ralph.start(task_id="my-project", daemon=True)

# 取得狀態
status = ralph.get_status()
print(f"Current phase: {status['current_phase']}")

# 推進下一階段
ralph.advance()
```

### CLI 命令

```bash
# 初始化任務（自動在新專案建立時觸發）
methodology ralph init <task_id>

# 啟動監控
methodology ralph start

# 查看進度
methodology ralph status

# 推進下一階段
methodology ralph advance
```

### 自動整合（方案 C）

在 `cli.py` 的 `cmd_init` 函數中，專案建立後自動啟動 Ralph Mode：

```python
def cmd_init(self, args):
    """初始化專案"""
    project_name = args.name or "my-project"
    
    # ... 現有初始化邏輯 ...
    
    # ========================================
    # Ralph Mode 自動啟動（v5.85 新增）
    # ========================================
    try:
        from ralph_mode import RalphScheduler, TaskPersistence
        from ralph_mode.task_persistence import TaskState
        
        # 初始化任務狀態
        persistence = TaskPersistence()
        state = TaskState(
            task_id=project_name,
            status="running",
            current_phase="init"
        )
        persistence.save_state(state)
        
        # 啟動 RalphScheduler 後台監控（5 分鐘輪詢）
        scheduler = RalphScheduler(
            task_id=project_name,
            interval_seconds=300,  # 5 分鐘
            daemon=True
        )
        scheduler.start()
        
        print(f"🚀 Ralph Mode started (interval: 5min)")
    except ImportError as e:
        print(f"⚠️ Ralph Mode not available: {e}")
    
    print(f"✅ Initialized: {project_name}")
    
    return 0
```

### 實作位置

- **Hook 點**: `cli.py` → `cmd_init()` 函數
- ** Ralph Mode 模組**: `ralph_mode/`
- **排程配置**: `SchedulerConfig.interval_seconds = 300` (5 分鐘)

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
   - 分數閾值：≥ 90 分
   - 等級要求：A
   - **邏輯正確性檢查**：自動發現輸出>輸入、分支不一致、Lazy check 缺失
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
| Phase 2 | 前置條件確認 | `python3 quality_gate/phase_artifact_enforcer.py` |
| Phase 2 | ASPICE 文檔檢查 | `python3 quality_gate/doc_checker.py` |
| Phase 2 | Constitution 檢查 | `python3 quality_gate/constitution/runner.py --type sad` |
| Phase 2 | TRACEABILITY 更新確認 | `python3 cli.py spec-track check` |
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

#### 6. PhaseEnforcer（推薦，2026-03-29 新增）

```bash
# 檢查特定 Phase
python -m quality_gate.cli quality check-phase 1

# 嚴格模式檢查
python -m quality_gate.cli quality check-phase 2 --strict

# 檢查所有 Phase
python -m quality_gate.cli quality check-all

# 阻擋模式（失敗時退出）
python -m quality_gate.cli quality check-phase 3 --block

# 使用 unified gate 整合
python -m quality_gate.cli quality check-phase 4 --unified
```

**用途**：自動化 Phase 檢查，確保每個 Phase 結束時自動執行檢查，阻止進入下一個 Phase 直到通過。

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

## Phase 自動化檢查（v5.84+）

> 確保每個 Phase 結束時自動執行檢查，阻止進入下一個 Phase 直到通過

### PhaseEnforcer 模組

| 模組 | 功能 | Quality Gate |
|------|------|---------------|
| phase_enforcer | Phase 自動化檢查 | gate_score >= 80 |
| folder_structure_checker | 資料夾結構檢查 | Phase 1-8 完整支援 |
| quality.py (CLI) | 命令列介面 | check-phase, check-all |

### 整合架構

```
PhaseEnforcer
    ├── folder_structure_checker (strict_mode=True)
    │   ├── 結構檢查（目錄、檔案）
    │   └── 內容檢查（章節完整性）
    └── unified_gate（可選整合）
        ├── Constitution 檢查
        ├── FR-ID 追蹤
        └── 其他 Quality Gate 工具
```

### 使用方式

#### Python API

```python
from quality_gate.phase_enforcer import PhaseEnforcer, enforce_phase

# 方式 1: 使用類別
enforcer = PhaseEnforcer("/path/to/project", strict_mode=True)
result = enforcer.enforce_phase(1)

if not result.can_proceed:
    print(f"Blocked! Issues: {result.blocker_issues}")

# 方式 2: 快速函式
result = enforce_phase("/path/to/project", phase=1)
print(result.print_summary())

# 方式 3: 檢查是否可以進入下一個 Phase
from quality_gate.phase_enforcer import check_can_proceed
if check_can_proceed("/path/to/project", current_phase=1):
    print("可以進入 Phase 2")
else:
    print("Phase 1 尚未通過，不能進入 Phase 2")

# 方式 4: 生成完整報告
from quality_gate.phase_enforcer import generate_full_report
report = generate_full_report("/path/to/project")
print(f"Overall Score: {report['summary']['overall_score']:.2f}%")
```

#### CLI 命令

```bash
# 檢查 Phase 1
python -m quality_gate.cli quality check-phase 1

# 嚴格模式檢查
python -m quality_gate.cli quality check-phase 2 --strict

# 檢查所有 Phase
python -m quality_gate.cli quality check-all

# 阻擋模式（失敗時退出，適用於 CI/CD）
python -m quality_gate.cli quality check-phase 3 --block

# 使用 unified gate 整合
python -m quality_gate.cli quality check-phase 4 --unified

# 單獨執行 PhaseEnforcer
python quality_gate/phase_enforcer.py /path/to/project 1 --strict
```

#### 輸出格式

```json
{
  "phase": 1,
  "passed": true,
  "structure_check": {
    "score": 100.0,
    "missing": [],
    "passed": true
  },
  "content_check": {
    "score": 85.0,
    "missing_sections": ["Overview", "Functional Requirements"],
    "passed": false
  },
  "gate_score": 92.5,
  "can_proceed": true,
  "blocker_issues": ["Missing section: Overview", "Missing section: Functional Requirements"]
}
```

### 每個 Phase 結束時

1. **執行 `PhaseEnforcer.enforce_phase(N)`**
2. **檢查 `gate_score >= 80`（可自訂閾值）**
3. **通過後才能進入 Phase N+1**
4. **記錄結果到 DEVELOPMENT_LOG.md**

### 閾值配置

```python
# 自訂閾值（預設 80）
enforcer = PhaseEnforcer(
    "/path/to/project",
    strict_mode=True,
    gate_threshold=90  # 更嚴格的閾值
)
```

### 整合 unified_gate

```python
from quality_gate.unified_gate import UnifiedGate

gate = UnifiedGate("/path/to/project")
result = gate.check_all(
    phase=1,
    strict_mode=True,
    phase_enforcement=True  # 啟用 PhaseEnforcer 整合
)

print(f"Combined Score: {result.overall_score}%")
print(f"Combined Passed: {result.passed}")
```

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
   ├── Agent A（Architect）設計 SAD.md
   ├── Agent B（Senior Dev/Reviewer）架構審查
   ├── 執行 quality_gate/doc_checker.py
   ├── 執行 quality_gate/constitution/runner.py --type sad
   ├── 更新 TRACEABILITY_MATRIX.md（FR → 模組）
   └── 記錄結果到 DEVELOPMENT_LOG.md

3. Phase 3: 代碼實現
   ├── 領域知識確認（實作前查閱領域知識清單）
   ├── 邏輯正確性自我檢查（輸出≤輸入、分支一致、Lazy check）
   ├── 撰寫程式碼
   ├── 撰寫單元測試（含邊界測試和負面測試）
   ├── 執行 quality_gate/doc_checker.py
   ├── 執行 quality_gate/constitution/runner.py
   └── 記錄結果到 DEVELOPMENT_LOG.md

   ### 3.x 邏輯正確性檢查（強制）
   
   #### 3.x.1 領域知識確認
   實作前必須查閱領域知識清單，確認以下要點：
   
   **TTS 領域**：
   - [ ] 標點是否保留？（刪除會破壞停頓）
   - [ ] 合併後是否多於原文？
   - [ ] 單一檔案格式是否與多檔案一致？
   - [ ] ffmpeg 初始化是否 lazy check？
   
   **通用領域**：
   - [ ] 輸出是否多於輸入？（字串操作）
   - [ ] 單一情况是否與多情况一致？（分支邏輯）
   - [ ] 外部依賴是否 lazy check？（初始化）
   
   #### 3.x.2 Spec Logic Mapping（強制度）
   每個 SRS 需求都必須填寫「邏輯驗證方法」：
   
   | SRS ID | 需求描述 | 實作函數 | 邏輯驗證方法 |
   |--------|---------|---------|-------------|
   | FR-05 | 按標點分段，保留標點 | split() | 輸出長度 ≤ 輸入長度 |
   | FR-07 | 分段不超過 800 字 | _merge_chunks() | 輸出不插入多餘字符 |
   | FR-19 | 多分段合併為單一輸出 | merge() | 單一檔案與多檔案格式一致 |
   
   #### 3.x.3 邊界測試要求
   Test Plan 必須包含負面測試：
   
   **文字處理**：
   - [ ] 空白輸入 → 應回傳空陣列
   - [ ] 超過 chunk_size 的單一句子 → 應正確分割
   - [ ] **合併後檢查：輸出是否多於原文？**
   
   **音訊處理**：
   - [ ] 不存在的檔案 → 應拋出 FileNotFoundError
   - [ ] **單一檔案 vs 多檔案：格式是否一致？**
   
   **網路處理**：
   - [ ] timeout → 應拋出 TimeoutError
   - [ ] 連續失敗 → 熔斷器是否觸發？
   - [ ] 無效設定 → 建構時是否驗證？

   #### 3.x.4 同行邏輯審查機制（強制）
   
   在 Phase 3 完成後，進行「邏輯審查對話」：
   
   ```markdown
   ## 邏輯審查對話（Phase 3 完成後）
   
   ### Developer 回答（必須）
   1. 我的假設是：______
      - [ ] 標點處理邏輯
      - [ ] 輸出不超過輸入
      - [ ] 分支一致性
      - [ ] Lazy check
   
   2. 輸出預期：______
      - [ ] 沒有插入額外字符
      - [ ] 格式與多情況一致
   
   3. 領域知識應用：______
      - [ ] TTS：標點=停頓
      - [ ] 網路：timeout、重試、熔斷
      - [ ] 通用：輸出≤輸入
   
   ### Architect 確認（必須）
   - [ ] 假設合理
   - [ ] 邏輯正確
   - [ ] 領域知識已應用
   - [ ] 通過審查
   ```
   
- **記錄**：將審查結果記錄到 DEVELOPMENT_LOG.md

### Phase 2 A/B 架構審查紀錄模板（v5.88 新增）

```markdown
## Phase 2 A/B 架構審查紀錄

### 審查維度 1：需求覆蓋完整性
- [ ] 所有 FR 在 SAD 中有對應模組
- [ ] 所有 NFR 有架構級別的保障機制
- 說明：______

### 審查維度 2：模組設計品質
- [ ] 模組邊界清晰，無職責重疊
- [ ] 依賴方向單向（無循環依賴）
- [ ] 每個模組可獨立測試
- 說明：______

### 審查維度 3：錯誤處理完整性
- [ ] L1-L6 分類已明確對應到模組
- [ ] Retry / Fallback 策略有具體參數（次數、間隔）
- [ ] Circuit Breaker 觸發條件已定義
- 說明：______

### 審查維度 4：技術選型合理性
- [ ] 所有技術選型都有 ADR 記錄
- [ ] 無引入規格書外的第三方框架
- [ ] 外部依賴均有 Lazy Init 設計
- 說明：______

### 審查維度 5：實作可行性
- [ ] Phase 3 開發者能直接從 SAD 開始實作
- [ ] 無「設計上優美但無法測試」的模組
- 說明：______

### 審查結論
- [ ] ✅ APPROVE — 進入 Quality Gate
- [ ] ❌ REJECT — 返回 Agent A（原因：______）

### Conflict Log（若有）
| 衝突點 | 規格書建議 | methodology-v2 選擇 | 理由 |
|--------|------------|---------------------|------|
|        |            |                     |      |

### Agent B 簽名：______  Session ID：______
### 日期：______
```

---

4. Phase 4: 測試
   ├── 撰寫 TEST_PLAN.md
   ├── 執行 quality_gate/doc_checker.py
   ├── 執行 quality_gate/constitution/runner.py --type test_plan
   └── 記錄結果到 DEVELOPMENT_LOG.md

---

## Phase 3 詳細說明（v5.91 新增）

> 基於 Phase3_Plan_5W1H_AB.md，詳細定義 Phase 3 代碼實現的 A/B 協作流程。

### Phase 3 WHO — A/B 角色分工

| 角色 | Persona | 職責 | 禁止事項 |
|------|---------|------|----------|
| Agent A（Developer）| `developer` | 代碼實作、單元測試、填寫邏輯審查對話 Developer 部分 | 引入第三方框架、自行通過 Quality Gate |
| Agent B（Code Reviewer）| `reviewer` | 同行邏輯審查、填寫 Architect 確認部分、測試完整性確認 | 代替 Agent A 修改代碼、跳過 AgentEvaluator |

**強制原則**：A/B 必須是不同 Agent，禁止自寫自審。每個模組完成即觸發 A/B 審查。

### Phase 3 代碼規範要求

每個模組必須包含規範標注：

```python
class TTSEngine:
    """
    TTS 引擎 - 語音合成核心

    對應 methodology-v2 規範：
    - SKILL.md - Core Modules
    - SKILL.md - Error Handling (L1-L6)
    - SAD.md FR-01, FR-05

    邏輯約束：
    - 輸出長度 ≤ 輸入長度（Spec Logic Mapping FR-01）
    - 外部依賴使用 Lazy Init（避免初始化崩潰）
    """

    def __init__(self):
        self._engine = None  # Lazy Init：不在 __init__ 直接呼叫

    def _get_engine(self):
        """Lazy Init：實際需要時才初始化外部依賴"""
        if self._engine is None:
            self._engine = ExternalTTSSDK()
        return self._engine
```

### 單元測試三類要求

每個模組的測試必須覆蓋以下三類：

| 類型 | 說明 | 範例 |
|------|------|------|
| 正向測試（Happy Path）| 正常輸入的預期行為 | 正常文字分段 |
| 邊界測試（Boundary）| 邊界條件處理 | 空白輸入、超長輸入 |
| 負面測試（Negative）| 邏輯約束驗證 | 合併後字符數 ≤ 原文 |

### Phase 3 A/B 代碼審查清單（Agent B 逐項確認）

**邏輯正確性**
- [ ] 所有字串操作：輸出長度 ≤ 輸入長度
- [ ] 分支邏輯：`if len(x)==1` 與一般情況結果一致
- [ ] 外部依賴：全部使用 Lazy Init，`__init__` 不直接呼叫
- [ ] 標點處理（TTS 領域）：標點有保留，未被刪除

**測試完整性**
- [ ] 正向測試覆蓋所有 Happy Path
- [ ] 邊界測試：空輸入、超長輸入、單一元素
- [ ] 負面測試：合併後字符數驗證、格式一致性驗證
- [ ] 集成測試覆蓋跨模組邏輯
- [ ] 單元測試覆蓋率 ≥ 80%（Constitution 門檻）

**規範符合度**
- [ ] 代碼命名符合 methodology-v2 命名規則
- [ ] 錯誤處理對應 L1-L6 分類
- [ ] 代碼註解標注對應規範條文
- [ ] 無引入 SAD.md 外的第三方框架

### Phase 3 同行邏輯審查對話模板

```markdown
## 邏輯審查對話 — [模組名稱]（Phase 3）

### Developer 回答（Agent A 必須填寫）

**1. 我的假設是：**
- [ ] 標點處理邏輯：______
- [ ] 輸出不超過輸入：______
- [ ] 分支一致性：______
- [ ] Lazy Init：______

**2. 輸出預期：**
- [ ] 沒有插入額外字符
- [ ] 格式與多情況一致

**3. 領域知識應用：**
- [ ] TTS：標點 = 停頓，已保留
- [ ] 網路：timeout、重試、熔斷
- [ ] 通用：輸出 ≤ 輸入

### Architect 確認（Agent B 必須填寫）

**審查結果：**
- [ ] 假設合理
- [ ] 邏輯正確
- [ ] 領域知識已正確應用
- [ ] 負面測試覆蓋關鍵約束

**審查結論：**
- [ ] ✅ 通過 — 繼續下一模組
- [ ] ❌ 不通過 — 返回 Agent A 修改
```

### Phase 3 合規矩陣格式

```markdown
## 合規矩陣（Compliance Matrix）— Phase 3

| 功能模組 | 對應 methodology-v2 規範 | 對應 SRS ID | 執行狀態 | 備註 |
|----------|--------------------------|-------------|----------|------|
| TTSEngine | SKILL.md - Core Modules | FR-01,FR-02 | 100% 落實 | 無 |
| TextProcessor | SKILL.md - Data Processing | FR-05,FR-07 | 100% 落實 | 無 |
| AudioMerger | SKILL.md - Error Handling | FR-19 | 100% 落實 | 無 |
```

### Phase 3 進入條件（全部必須為 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| Phase 2 已完成 | phase_artifact_enforcer 通過 | Framework Enforcement |
| ASPICE 文檔合規率 | > 80% | Quality Gate doc_checker |
| Constitution 正確性 | = 100% | Constitution Runner |
| Constitution 測試覆蓋率 | > 80% | Constitution Runner |
| 單元測試全部通過 | 通過率 100% | pytest |
| 集成測試全部通過 | 通過率 100% | pytest |
| 每個模組都有同行邏輯審查記錄 | 無遺漏 | Agent B 確認 |
| AgentEvaluator 評分 | ≥ 90 分 | AgentEvaluator |

---

## Phase 4 詳細說明（v5.90 新增）

> 基於 Phase4_Plan_5W1H_AB.md，詳細定義 Phase 4 測試的 A/B 協作流程。

### Phase 4 WHO — A/B 角色分工

| 角色 | Persona | 職責 | 禁止事項 |
|------|---------|------|----------|
| Agent A（Tester）| `qa` | 設計 TEST_PLAN、執行測試、記錄 TEST_RESULTS | 查看 Phase 3 代碼設計測試案例、自行判定測試通過 |
| Agent B（QA Reviewer）| `reviewer` | 審查 TEST_PLAN 完整性、審查 TEST_RESULTS 真實性 | 幫 Agent A 補寫測試案例、接受手動確認 |

**核心原則**：Tester 必須與 Phase 3 Developer **不同 Agent**，確保測試從需求出發而非從代碼出發。

### Phase 4 兩次 A/B 審查流程

**第一次：TEST_PLAN 計劃審查（執行測試前）**
- 確認每條 SRS FR 都有對應 TC
- 確認 P0 需求有三類測試（正向 + 邊界 + 負面）
- 確認 Mock 策略已定義
- 確認預期結果可量化

**第二次：TEST_RESULTS 結果審查（執行測試後）**
- 確認所有 TC 有 pytest 實際輸出
- 確認失敗案例有具體根本原因分析（到代碼行）
- 確認覆蓋率由工具自動生成
- 確認 SRS FR 覆蓋率 = 100%

### Phase 4 TEST_PLAN.md 完整規格

```markdown
# Test Plan - [專案名稱]

## 1. 測試目標
- 驗證所有 SRS FR 的功能行為符合預期
- 確認邊界條件與異常情況的處理正確
- 驗證跨模組集成行為無迴歸

## 2. 測試範圍
### 納入範圍
- 所有 SRS 功能需求（FR-01 ~ FR-XX）
- 非功能需求中可測試項目（效能、錯誤恢復）
- 跨模組集成點

## 3. 測試策略
| 類型 | 方法 | 工具 | 覆蓋目標 |
|------|------|------|----------|
| 單元測試 | White-box | pytest | ≥ 80% |
| 集成測試 | Black-box | pytest | 所有跨模組介面 |
| 負面測試 | Fault Injection | pytest | 所有 L1-L6 錯誤路徑 |

## 4. 測試環境
| 項目 | 規格 |
|------|------|
| OS | Ubuntu 24 / macOS |
| Python | 3.11 |
| 測試框架 | pytest 8.x |

## 5. 測試案例清單
| TC ID | 對應 SRS ID | 測試案例名稱 | 測試類型 | 優先級 |
|-------|-------------|-------------|----------|--------|
| TC-001 | FR-01 | 正常文字分段 | 正向 | P0 |
| TC-002 | FR-01 | 空白輸入分段 | 邊界 | P0 |
| TC-003 | FR-01 | 合併後不多於原文 | 負面 | P0 |
```

### Phase 4 TEST_RESULTS.md 完整規格

```markdown
# Test Results - [專案名稱]

## 執行摘要
| 項目 | 數值 |
|------|------|
| 執行日期 | YYYY-MM-DD HH:MM |
| 總測試數 | XX |
| 通過 | XX |
| 失敗 | XX |
| 通過率 | XX% |
| 代碼覆蓋率 | XX% |

## 詳細結果
| TC ID | 測試案例 | 預期結果 | 實際結果 | 狀態 |
|-------|----------|----------|----------|------|
| TC-001 | 正常文字分段 | 回傳 3 段 | 回傳 3 段 | ✅ PASS |

## 失敗案例分析
### TC-XXX：[失敗案例名稱]
- **根本原因**：[具體技術原因，不能只說「邏輯錯誤」]
- **修復方式**：[具體代碼修改說明]
- **修復驗證**：[重新執行後的結果]
```

### Phase 4 失敗案例根本原因分析要求

模糊的根本原因 = 無法防止再次發生：

```
❌ 差：根本原因「邏輯錯誤」
✅ 好：根本原因「TextProcessor.split() 在處理含有多個連續標點（。！？）
        的輸入時，錯誤地將標點作為分割點，導致輸出陣列長度超過預期。
        問題位於 module.py 第 47 行，需改用 regex 分割。」
```

### Phase 4 進入條件（全部必須為 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| TEST_PLAN A/B 審查通過 | APPROVE | AgentEvaluator |
| Constitution test_plan | 正確性 100%、可維護性 > 70% | Constitution Runner |
| pytest 全部測試通過 | 通過率 = 100% | pytest 實際輸出 |
| 代碼覆蓋率 | ≥ 80% | pytest-cov 實際輸出 |
| SRS FR 覆蓋率 | = 100% | Agent B 確認 |
| 失敗案例全數修復 | 0 個 open 失敗 | TEST_RESULTS.md |
| TEST_RESULTS A/B 審查通過 | APPROVE | AgentEvaluator |

---

## Phase 5-8: 驗證/交付/品質/風險/配置
   ├── 領域知識確認（實作前查閱領域知識清單）
   ├── 邏輯正確性自我檢查（輸出≤輸入、分支一致、Lazy check）
   ├── 補齊缺失文檔
   ├── 執行 quality_gate/doc_checker.py
   ├── 執行 quality_gate/constitution/runner.py
   ├── 執行 scripts/spec_logic_checker.py（邏輯正確性檢查）
   └── 記錄結果到 DEVELOPMENT_LOG.md

---

### Phase 4 WHEN — 何時執行？

Phase 3 完成後

**進入條件**：Phase 3 sign-off + 代碼 APPROVE

**退出條件**：

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| TEST_PLAN A/B 審查通過（計劃前）| APPROVE | AgentEvaluator |
| Constitution test_plan 正確性 | = 100% | `constitution/runner.py --type test_plan` |
| pytest 全部測試通過 | = 100% | pytest 實際輸出 |
| 代碼覆蓋率 | ≥ 80%（單元測試）| pytest-cov 實際輸出 |
| SRS FR 覆蓋率 | = 100% | Agent B 確認 |
| TEST_RESULTS A/B 審查通過（結果後）| APPROVE | AgentEvaluator |

### Phase 4 WHERE — 在哪裡執行？

| 項目 | 內容 |
|------|------|
| 目錄 | `04-testing/`, `tests/` |
| 工具 | `pytest` |
| 工具 | `pytest-cov` |
| 工具 | `quality_gate/constitution/runner.py --type test_plan` |
| 工具 | `scripts/spec_logic_checker.py`（邏輯正確性驗證，≥ 90 分）|

### Phase 4 WHY — 為什麼這樣做？

> Phase 3 的測試是「開發者自測」，Phase 4 是「獨立驗證」——視角不同，發現不同缺陷。

| 測試類型 | 視角 | 發現的問題 |
|----------|------|------------|
| Phase 3（自測）| Developer 視角 | 確認偏誤：認為代碼正確 |
| Phase 4（獨立）| 外部視角 | 發現開發者忽略的邊界條件 |

### Phase 4 HOW — 如何執行？

1. **Agent A（Tester）從 SRS 推導 TC**（不看代碼）
   - 每條 FR 對應至少 1 個 TC
   - P0 需求必須有正向 + 邊界 + 負面三類測試

2. **第一次 A/B 審查（TEST_PLAN）**
   - Agent B 審查計畫完整性
   - 確認從 SRS 而非代碼推導

3. **執行測試**
   - pytest 實際執行
   - pytest-cov 產生覆蓋率報告

4. **第二次 A/B 審查（TEST_RESULTS）**
   - Agent B 審查結果真實性
   - 失敗案例根本原因分析到代碼行

### Phase 4 進入 Phase 5 前置條件（全部 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| 測試通過率 | = 100% | pytest 實際輸出 |
| 代碼覆蓋率 | ≥ 80% | pytest-cov 實際輸出 |
| SRS FR 覆蓋率 | = 100% | Agent B 確認 |
| TEST_RESULTS A/B 審查通過 | APPROVE | AgentEvaluator |

---

## Phase 5 詳細說明（v5.92 新增）

> 基於 Phase5_Plan_5W1H_AB.md，詳細定義 Phase 5 驗證與交付的 A/B 協作流程。

### Phase 5 WHO — A/B 角色分工

| 角色 | Persona | 職責 | 禁止事項 |
|------|---------|------|----------|
| Agent A（DevOps / Delivery）| `devops` | 建立 BASELINE.md、執行驗收測試、啟動 A/B 持續監控、記錄 TEST_RESULTS（Phase 5）| 自行宣告基線通過；在監控數據不足時強行進入 Phase 6 |
| Agent B（Architect / Senior QA）| `architect` 或 `reviewer` | 審查 BASELINE.md 完整性、確認 A/B 監控閾值、審查 VERIFICATION_REPORT.md | 跳過監控數據直接 APPROVE；接受基線版本中有「待修復」的已知缺陷 |

**核心原則**：驗證必須獨立於開發。Agent A 不能是 Phase 3 的 Developer；基線建立必須經 Agent B 確認，不能自簽。

### Phase 5 必要交付物

| 交付物 | 負責方 | 驗證方 | 位置 |
|--------|--------|--------|------|
| `BASELINE.md`（7 章節）| Agent A | Agent B + Quality Gate | `05-verify/` |
| `TEST_RESULTS.md`（Phase 5 驗收版）| Agent A | Agent B | `05-verify/` |
| `VERIFICATION_REPORT.md` | Agent A | Agent B | `05-verify/` |
| `MONITORING_PLAN.md`（A/B 監控）| Agent A | Agent B | 專案根目錄 |
| `QUALITY_REPORT.md`（初版）| Agent A | Agent B | `05-verify/` |

### Phase 5 BASELINE.md 核心規格

```markdown
# Baseline - [專案名稱] v[版本號]

## 1. 基線概述（建立人/審查人/session_id）
## 2. 功能基線（對應 SRS FR，100% ✅）
## 3. 品質基線（Constitution≥80%、覆蓋率≥80%、邏輯≥90分）
## 4. 效能基線（A/B 監控基準：回應時間、記憶體、錯誤率、熔斷器）
## 5. 已知問題登錄（HIGH 嚴重性 = 0 才能建立基線）
## 6. 變更記錄
## 7. 驗收簽收（雙方 session_id + 日期）
```

### Phase 5 MONITORING_PLAN.md 四個閾值

| 監控項目 | 閾值 | 觸發動作 |
|----------|------|----------|
| 邏輯正確性分數 | ≥ 90 分 | 低於閾值 → 停止部署 |
| 回應時間 | 與基線偏差 < 10% | 超出 → 警告 + 人工確認 |
| 熔斷器觸發 | 不觸發 | 觸發 → 立即回滾 |
| 錯誤率 | < 1% | 超出 → 停止流量 |

### Phase 5 兩次 A/B 審查流程

| 審查次數 | 時機 | 審查內容 | 模板位置 |
|----------|------|----------|----------|
| 第一次 | 部署**前**（基線審查）| BASELINE + QUALITY_REPORT + MONITORING_PLAN | Phase5_Plan_5W1H_AB.md |
| 第二次 | 部署**後**（驗收報告審查）| VERIFICATION_REPORT + 監控初次結果 | Phase5_Plan_5W1H_AB.md |

### Phase 5 進入 Phase 6 前置條件（全部 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| 邏輯正確性分數 | ≥ 90 分 | spec_logic_checker.py 實際輸出 |
| Constitution 總分 | ≥ 80% | Constitution Runner |
| ASPICE 合規率 | > 80% | doc_checker.py |
| BASELINE 功能驗收 | 100% ✅（無任何 ❌）| Agent B 確認 |
| 已知問題 HIGH 嚴重性 | = 0 個 | BASELINE.md 問題登錄 |
| 第一次 A/B 審查（基線）| APPROVE | AgentEvaluator |
| 第二次 A/B 審查（驗收）| APPROVE | AgentEvaluator |

### Phase 5 邏輯正確性複查（Phase 5 重做，非 Phase 3）

| Phase | 審查方式 | 門檻 |
|-------|----------|------|
| Phase 3 | 定性（對話審查）| 依賴人工判斷 |
| Phase 5 | 量化（spec_logic_checker.py）| ≥ 90 分 |

重做理由：Phase 4 修復可能引入新邏輯問題；需要 `devops` 人格的新鮮視角。

### Phase 5 DEVELOPMENT_LOG 記錄格式

```markdown
## Phase 5 Quality Gate 結果（YYYY-MM-DD HH:MM）

### 前置確認
執行命令：python3 quality_gate/phase_artifact_enforcer.py
結果：Phase 4 完成 ✅

### 邏輯正確性複查
執行命令：python3 scripts/spec_logic_checker.py
結果：
- 邏輯正確性分數：XX/100（目標 ≥ 90）
- 輸出 ≤ 輸入約束：✅
- 分支一致性：✅
- Lazy Init 完整：✅

### Constitution 全面檢查
執行命令：python3 quality_gate/constitution/runner.py
結果：總分 XX%（目標 ≥ 80%）✅

### 第一次 A/B 審查（基線審查）
- Agent A（DevOps）：session_id ______
- Agent B（Architect）：session_id ______
- 審查結論：APPROVE ✅

### A/B 持續監控首次結果
- 邏輯正確性：XX/100 ✅
- 回應時間偏差：X%（< 10%）✅
- 熔斷器觸發：0 次 ✅
- 錯誤率：X%（< 1%）✅

### 第二次 A/B 審查（驗收報告審查）
- 審查結論：APPROVE ✅

### Phase 5 結論
- [ ] ✅ 通過，BASELINE v1.0.0 建立，進入 Phase 6
```

> ❌ **禁止空泛記錄**：`✅ 基線建立完成`（必須有實際命令輸出）

### Phase 5 監控異常 SOP

| 異常 | 動作 |
|------|------|
| 熔斷器觸發 | 立即回滾 → 診斷根本原因 → Phase 3 修復 → 重新 Phase 4/5 |
| 錯誤率 ≥ 1% | 停止流量 → 分析日誌 → 修復 → 重新部署 |
| 回應時間偏差 ≥ 10% | 警告 + 人工確認 → 判斷是否可接受 |
| 邏輯分數 < 90 | 停止部署 → 邏輯複查 → 修復 |

**原則**：任何 HIGH 異常都優先回滾，不嘗試帶著異常繼續。

### Phase 5 在整體架構的位置

```
Phase 1 需求 → Phase 2 設計 → Phase 3 開發 → Phase 4 測試
                                                           │
                                                           ▼
Phase 8 配置 ←── Phase 7 風險 ←── Phase 6 品質 ←── Phase 5 驗收
                                                             （建立基線）
                                                                   ↑
                                                            轉折點：
                                                            從「建構」轉為「保障」
```

---

## Phase 6 詳細說明（v5.91 新增）

> 基於 Phase6_Plan_5W1H_AB.md，詳細定義 Phase 6 品質保證的 A/B 協作流程。

### Phase 6 WHO — A/B 角色分工

| 角色 | Persona | 職責 | 禁止事項 |
|------|---------|------|----------|
| Agent A（QA Lead）| `qa` | 品質深度分析、完成 QUALITY_REPORT 完整版、持續執行 A/B 監控 | 只描述問題不分析根源、在監控數據不穩定時宣告品質通過 |
| Agent B（Architect / PM）| `architect` 或 `pm` | 審查品質報告深度、確認改進建議可行性 | 接受只有數字沒有分析的品質報告、跳過改進建議的可行性確認 |

**核心原則**：品質分析必須跨越所有 Phase 的數據，不能只看 Phase 5 的快照。

### Phase 6 Constitution ≥ 80% 全面檢查

Phase 6 要求整體總分 ≥ 80%，代表所有維度加權後的系統性品質水準：

```bash
# 執行全面檢查（不加 --type）
python3 quality_gate/constitution/runner.py

# 門檻：≥ 80%
```

| 維度 | 目標 | Phase 6 要求 |
|------|------|--------------|
| 正確性 | 100% | 模組級別細化分析 |
| 安全性 | 100% | 具體掃描項目結果 |
| 可維護性 | >70% | 有具體問題描述 |
| 測試覆蓋率 | >80% | 有未覆蓋區域的模組/函數 |

### Phase 6 品質問題根源分析（Layer 1-3）

```markdown
分析流程（三層遞進）：

Layer 1：問題識別
  → 從 Phase 1-5 的 DEVELOPMENT_LOG 提取所有「REJECT」、「失敗」、「未通過」記錄

Layer 2：分類彙整
  → 依問題類型分類：邏輯錯誤 / 文檔缺失 / 測試遺漏 / 架構偏離

Layer 3：根源 Phase 定位
  → 對每類問題，追溯「最早應該被攔截的 Phase」
  → 識別該 Phase 哪個步驟、哪個門檻沒有發揮作用
```

### Phase 6 改進建議格式（P0/P1/P2 + 目標指標）

| 優先級 | 改進項目 | 對應根源 Phase | 具體動作 | 負責角色 | 目標指標 |
|--------|----------|---------------|----------|----------|----------|
| P0 | Spec Logic Mapping 強化 | Phase 3 | 每條 FR 必須有量化驗證方法 | Developer | 邏輯分數 ≥ 95 |
| P1 | Quality Gate 執行率 | Phase 1-4 | 每 Phase 結束前強制執行 | 所有 Agent | 執行率 100% |
| P2 | 負面測試覆蓋率 | Phase 4 | P0 需求強制三類測試 | Tester | FR 負面覆蓋 100% |

### Phase 6 A/B 監控數據分析

Phase 6 期間持續監控，記錄到 MONITORING_PLAN.md：

| 日期 | 邏輯分數 | 回應時間偏差 | 錯誤率 | 熔斷器 | 結論 |
|------|----------|-------------|--------|--------|------|
| YYYY-MM-DD | XX/100 | X% | X% | 0 | ✅ |

**監控閾值**：
- 邏輯正確性：≥ 90 分
- 回應時間偏差：< 10%
- 錯誤率：< 1%
- 熔斷器觸發：0 次

### Phase 6 記錄確認

| 項目 | 說明 |
|------|------|
| 雙方 session_id 記錄 | 每個 Phase 結束時，Agent A + Agent B 的 session_id 都必須記錄到 DEVELOPMENT_LOG.md |
| 用途 | 可追溯、誰審查、誰負責 |

### Phase 6 A/B 審查清單（Agent B 逐項確認）

- [ ] Constitution 總分 ≥ 80%
- [ ] ASPICE 合規率 > 80%
- [ ] 邏輯正確性分數 ≥ 90 分
- [ ] QUALITY_REPORT.md 七個章節完整
- [ ] 品質問題根源分析到位
- [ ] 改進建議 P0 有目標指標
- [ ] 雙方 session_id 已記錄（可追溯）
- [ ] Agent B APPROVE

### Phase 6 QUALITY_REPORT.md 完整版（7 章節）

```markdown
# Quality Report - [專案名稱]（完整版）

## 1. 品質指標全覽
| 指標 | 目標 | Phase 5 快照 | Phase 6 驗證 | 趨勢 | 狀態 |
|------|------|-------------|-------------|------|------|

## 2. ASPICE 各 Phase 合規性分析
| Phase | 文件 | 合規率 | 主要缺失 | 根源分析 |

## 3. Constitution 四維度深度分析
### 3.1 正確性
### 3.2 安全性
### 3.3 可維護性
### 3.4 測試覆蓋率

## 4. 品質問題根源分析（系統性）
### 4.1 問題分類彙整
### 4.2 根源 Phase 分布

## 5. 改進建議（具體可執行）
| 優先級 | 改進項目 | 對應根源 Phase | 具體動作 | 負責角色 | 目標指標 |

## 6. A/B 監控數據分析（Phase 6 期間）

## 7. 品質目標達成摘要
```

### Phase 6 持續監控維持

A/B 監控在 Phase 6 全程維持，每日執行：

```bash
# 每日監控（Phase 6 全程）
python3 scripts/spec_logic_checker.py      # ≥ 90 分
python3 scripts/performance_check.py       # < 10% 偏差
python3 scripts/circuit_breaker_check.py   # 0 次觸發
```

### Phase 6 進入條件（全部必須為 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| Constitution 總分 | ≥ 80% | Constitution Runner 實際輸出 |
| ASPICE 合規率 | > 80% | doc_checker.py 實際輸出 |
| 邏輯正確性分數 | ≥ 90 分 | spec_logic_checker.py 實際輸出 |
| 測試通過率 | = 100%（所有 TC 必須通過）| pytest 實際輸出 |
| A/B 監控：Phase 6 全程穩定 | 熔斷 0 次、錯誤率 < 1% | MONITORING_PLAN.md 連續記錄 |
| QUALITY_REPORT.md 完整版 | 七個章節全部完成 | Agent B 審查確認 |
| 品質問題根源分析 | 有根源 Phase 定位 | Agent B 審查確認 |
| 改進建議 P0 全部有目標指標 | 可量化 | Agent B 審查確認 |
| Agent B APPROVE | AgentEvaluator 輸出 | AgentEvaluator |

---

## Phase 7 詳細說明（v5.92 新增）

> 基於 Phase7_Plan_5W1H_AB.md，詳細定義 Phase 7 風險評估的 A/B 協作流程。

### Phase 7 WHO — A/B 角色分工

| 角色 | Persona | 職責 | 禁止事項 |
|------|---------|------|----------|
| Agent A（Risk Analyst）| `qa` 或 `devops` | 五維度風險識別、建立 RISK_REGISTER.md、制定演練計劃、提交 Decision Gate 確認 | 以「機率低」為由跳過 HIGH 影響風險；緩解措施寫「加強注意」等無法量化的文字 |
| Agent B（PM / Architect）| `pm` 或 `architect` | 確認風險識別無重大遺漏；緩解措施切實可行；所有 MEDIUM/HIGH 風險有決策記錄 | 接受「持續監控」作為唯一緩解措施；跳過 Decision Gate |

**核心原則**：風險評估必須保持悲觀視角。Agent A 的任務是「盡可能找出更多風險」，而不是「證明系統安全」。

### Phase 7 風險識別五個維度

| 維度 | 來源 | 典型風險 |
|------|------|----------|
| 技術風險 | Phase 6 QUALITY_REPORT | Constitution 低分維度對應的技術債 |
| 依賴風險 | SAD.md ADR | 外部 API/SDK 版本鎖定與棄用 |
| 操作風險 | BASELINE.md 效能基線 | 超出效能基線 10% 的降級場景 |
| 商業風險 | SRS.md NFR | 核心功能不可用的業務衝擊 |
| 迭代風險 | Phase 6 改進建議 | 技術債累積的長期退化 |

### Phase 7 必要交付物

| 交付物 | 負責方 | 驗證方 | 位置 |
|--------|--------|--------|------|
| `RISK_ASSESSMENT.md`（風險矩陣）| Agent A | Agent B + Quality Gate | `07-risk/` |
| `RISK_REGISTER.md`（完整版）| Agent A | Agent B | `07-risk/` |
| `.methodology/decisions/` 風險決策記錄 | Agent A + Agent B | Decision Gate | `.methodology/decisions/` |
| `MONITORING_PLAN.md`（Phase 7 更新）| Agent A | Agent B | 專案根目錄 |

### Phase 7 四層緩解措施

每個 HIGH/MEDIUM 風險必須同時具備四層：

| 層次 | 定義 | 例 |
|------|------|-----|
| 預防（Prevent）| 降低風險發生機率 | Retry、版本鎖定、輸入驗證 |
| 偵測（Detect）| 快速發現風險已發生 | 監控告警、熔斷器、錯誤率追蹤 |
| 應對（Respond）| 風險發生後的自動處置 | Fallback、降級模式、自動恢復 |
| 升級（Escalate）| 自動處置不足時的人工介入 | HITL 通知、on-call 流程 |

> ❌ **無效的緩解措施**：`持續監控`（只是發現問題更快，不是防止或應對問題）

### Phase 7 Decision Gate 確認流程

| 步驟 | 動作 | 負責方 |
|------|------|--------|
| 1 | 為每個 MEDIUM/HIGH 風險建立決策記錄（`R*_decision.md`）| Agent A |
| 2 | Agent B 逐一確認每個決策（含 session_id 與日期）| Agent B |
| 3 | 執行 `check_decisions.py` → 0 個未確認 | 工具驗證 |
| 4 | A/B 風險審查（Decision Gate 完成後才執行）| Agent A → Agent B |

**Decision Gate 記錄格式**：

```markdown
# Decision Record - [風險 ID] - [YYYY-MM-DD]

| 項目 | 內容 |
|------|------|
| 風險 ID | R1 |
| 風險等級 | 🔴 HIGH |
| 決策類型 | 接受 / 轉移 / 緩解 / 消除 |
| 決策日期 | YYYY-MM-DD |

## 殘餘風險
- 殘餘風險等級：🟡 中
- 可接受理由：[說明]

## 確認記錄
| 角色 | Session ID | 日期 | 確認 |
|------|------------|------|------|
| Risk Analyst | ______ | YYYY-MM-DD | ✅ 提交 |
| PM / Architect | ______ | YYYY-MM-DD | ✅ 確認 |
```

### Phase 7 風險演練要求

| 要求 | 標準 |
|------|------|
| 演練對象 | 至少 1 個 HIGH 風險 |
| 演練頻率 | HIGH ≤ 每月一次 |
| 演練場景 | 具體（「模擬網路中斷 30 秒」而非「測試網路」）|
| RTO 驗證 | 演練時量測實際 RTO 是否達標 |
| 記錄內容 | 觸發條件 → 觀察 → 結果 → RTO 達成 |

**演練記錄格式**：

```markdown
## 演練記錄 - [風險 ID]（YYYY-MM-DD）

### 演練場景
[具體模擬步驟]

### 實際結果
- Retry 執行：✅/❌（間隔：____ms）
- 熔斷器觸發：✅/❌
- Fallback 切換：✅/❌（時間：____ms）
- HITL 通知：✅/❌（延遲：____s）

### RTO 達成
- 聲明 RTO：< X 分鐘
- 實際 RTO：____分____秒
- 達成：✅/❌

### 結論
- [ ] ✅ 通過——緩解措施有效
- [ ] ❌ 未通過（修正後重新演練）
```

### Phase 7 進入 Phase 8 前置條件（全部 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| 五維度風險識別完整 | 每個維度至少 1 個風險 | Agent B 確認 |
| HIGH 風險數量 | ≥ 1 個 | Agent B 主觀判斷 |
| HIGH/MEDIUM 風險緩解措施 | 四層 + Plan B + RTO | Agent B 確認 |
| 邏輯正確性分數 | ≥ 90 分 | spec_logic_checker.py |
| 驗證測試通過率 | = 100%（所有 TC 必須通過）| pytest 實際輸出 |
| Decision Gate | 所有決策已確認 | `check_decisions.py` 0 個未確認 |
| 至少 1 個 HIGH 風險演練 | 演練通過 | 演練記錄 |
| 雙方 session_id 已記錄 | 可追溯 | DEVELOPMENT_LOG.md |
| Agent B APPROVE | AgentEvaluator 輸出 | AgentEvaluator |
| Constitution 總分 | ≥ 80% | Constitution Runner |

### Phase 7 記錄確認

| 項目 | 說明 |
|------|------|
| 雙方 session_id 記錄 | 每個 Phase 結束時，Agent A + Agent B 的 session_id 都必須記錄到 DEVELOPMENT_LOG.md |
| 用途 | 可追溯、誰審查、誰負責 |

### Phase 7 A/B 審查清單（Agent B 逐項確認）

- [ ] 五維度風險識別完整（每個維度至少 1 個風險）
- [ ] HIGH 風險數量 ≥ 1 個
- [ ] HIGH/MEDIUM 風險緩解措施：四層 + Plan B + RTO
- [ ] 邏輯正確性分數 ≥ 90 分
- [ ] Decision Gate：所有決策已確認（`check_decisions.py` 0 個未確認）
- [ ] 至少 1 個 HIGH 風險演練通過
- [ ] 雙方 session_id 已記錄（可追溯）
- [ ] Agent B APPROVE

### Phase 7 在整體架構的位置

```
Phase 6（品質分析）→ Phase 7（風險管理）→ Phase 8（配置管理）
    ↑                      ↑                      ↑
「現有問題」          「未來威脅」             「版本控制」
  回顧視角              前瞻視角               治理視角

Phase 7 輸出服務：
  → Phase 8：風險等級影響配置管理嚴格程度
  → 下個版本 Phase 1：迭代風險轉化為新版本需求約束
```

---

## Phase 8 詳細說明（v5.92 新增）

> 基於 Phase8_Plan_5W1H_AB.md，詳細定義 Phase 8 配置管理的 A/B 協作流程。

### Phase 8 WHO — A/B 角色分工

| 角色 | Persona | 職責 | 禁止事項 |
|------|---------|------|----------|
| Agent A（DevOps / Config Manager）| `devops` | 建立 CONFIG_RECORDS.md、執行發布清單、編製 A/B 監控最終報告、封版前確認所有 Phase 產出完整 | 使用「最新版」等模糊版本描述；在 A/B 監控異常未解除前封版 |
| Agent B（PM / Architect）| `pm` 或 `architect` | 確認版本配置完整可重現；發布清單無遺漏；A/B 監控最終狀態健康 | 在監控最終報告顯示異常時 APPROVE 封版 |

**核心原則**：配置管理是「治理行為」，不是「技術行為」。重點是「所有配置都有記錄、可被審計、可被重現」。

### Phase 8 配置管理（SUP.8）

> ASPICE SUP.8 要求：所有配置項（Configuration Items）必須明確識別、版本控制、變更管理。

**SUP.8 配置項識別清單**：

| 配置項類別 | 具體項目 | 管理方式 |
|------------|----------|----------|
| 需求文件 | SRS.md、SRS.pdf 版本 | 版本標籤 |
| 架構設計 | SAD.md、SAD.pdf 版本 | 版本標籤 |
| 代碼 | `03-development/` 目錄、Git Commit | Git Tag |
| 測試 | TEST_PLAN.md、TEST_RESULTS.md | 版本對應 |
| 部署 | Docker Image、Config 檔 | Image Tag |
| 環境 | 環境變數、第三方依賴 | pip/npm lock |

**SUP.8 變更控制流程**：

```
1. 識別變更需求（Change Request）
2. 評估影響範圍（Impact Analysis）
3. 獲得批准（Approval）
4. 實施變更（Implementation）
5. 驗證變更（Verification）
6. 更新配置記錄（Update CONFIG_RECORDS.md）
```

### Phase 8 必要交付物

| 交付物 | 負責方 | 驗證方 | 位置 |
|--------|--------|--------|------|
| `CONFIG_RECORDS.md`（完整版，8 章節）| Agent A | Agent B + Quality Gate | `08-config/` |
| 發布清單（七個區塊）確認記錄 | Agent A + Agent B | 雙方逐項確認 | `DEVELOPMENT_LOG.md` |
| A/B 監控最終報告 | Agent A | Agent B | `MONITORING_PLAN.md`（最終段落）|
| 版本封存記錄（Git Tag）| Agent A | Agent B | Git |
| `DEVELOPMENT_LOG.md`（Phase 8 + 方法論閉環）| Agent A | Agent B | 專案根目錄 |

### Phase 8 CONFIG_RECORDS.md 八章節

```markdown
# Configuration Records - [專案名稱]

## 1. 版本資訊（Git Commit Hash 必填）
## 2. 執行環境配置（開發環境 + 生產環境）
## 3. 依賴套件清單（pip freeze / npm lock 快照，無省略）
## 4. 環境變數與配置（secret 類型只記名稱）
## 5. 部署記錄（日期 + 版本 + 方式 + 執行人）
## 6. 配置變更記錄（Phase 5 至今所有配置調整）
## 7. 回滾 SOP（觸發條件 + 命令列步驟 + 後續必做）
## 8. 配置合規性確認（對應 Phase 7 風險緩解措施）
```

### Phase 8 回滾 SOP

**觸發條件**：

| 條件 | 閾值 |
|------|------|
| 錯誤率突增 | > 5%（持續 5 分鐘）|
| 熔斷器觸發 | 任何一次觸發 |
| A/B 邏輯分數下降 | < 85 分（預警）/ < 80 分（立即回滾）|

**回滾步驟**：

```bash
# 1. 確認回滾目標版本
git log --oneline -5

# 2. 執行回滾
git checkout [previous_stable_tag]
docker-compose down && docker-compose up -d

# 3. 驗證回滾成功
python3 scripts/spec_logic_checker.py  # ≥ 90 分
python3 scripts/circuit_breaker_check.py  # 0 觸發

# 4. 通知相關人員
# 5. 記錄回滾原因到 CONFIG_RECORDS.md
```

### Phase 8 發布清單（七個區塊）

Agent A 執行，Agent B 見證。**任何 ❌ 阻止封版**：

```markdown
# Release Checklist - v[版本號] - [YYYY-MM-DD]

## 一、版本準備
- [ ] 版本號已更新（`__version__`, `package.json`）
- [ ] CHANGELOG.md 已記錄所有變更
- [ ] README.md 已同步
- [ ] `docs/` 文檔已同步

## 二、文檔完整性（Phase 1-8 全部完成）
- [ ] SRS.md（Phase 1）/ SAD.md（Phase 2）/ BASELINE.md（Phase 5）
- [ ] TEST_PLAN + TEST_RESULTS（Phase 4）/ QUALITY_REPORT（Phase 6）
- [ ] RISK_ASSESSMENT + RISK_REGISTER（Phase 7）/ CONFIG_RECORDS（Phase 8）
- [ ] TRACEABILITY_MATRIX 四欄完整（FR→設計→代碼→測試）

## 三、品質確認
- [ ] 測試通過率 = 100%（`pytest` 最後輸出）
- [ ] 代碼覆蓋率 ≥ 80%（`pytest-cov` 輸出）
- [ ] Constitution 總分 ≥ 80%（`constitution/runner.py` 輸出）
- [ ] 邏輯正確性 ≥ 90 分（`spec_logic_checker.py` 輸出）

## 四、A/B 監控最終狀態（Phase 5 至今）
- [ ] 邏輯分數平均 ≥ 90 分
- [ ] 回應時間偏差 < 10%
- [ ] 熔斷器觸發（Phase 5 至今）= 0 次
- [ ] 錯誤率 < 1%

## 五、風險管理確認
- [ ] `check_decisions.py`：0 個未確認決策
- [ ] 所有 HIGH 風險有演練記錄
- [ ] 回滾 SOP 已寫入 CONFIG_RECORDS.md

## 六、配置管理確認
- [ ] 所有依賴版本精確（無「最新版」模糊描述）
- [ ] Git Tag 已建立（`v[Major.Minor.Patch]`）
- [ ] CHANGELOG.md 有本版本記錄

## 七、封版確認
- [ ] Agent A 確認：所有項目已逐一執行 ✅
- [ ] Agent B 確認：所有項目已逐一審查 ✅
- [ ] 封版決策：APPROVE 正式發布

Agent A：______（session_id：______）日期：______
Agent B：______（session_id：______）日期：______
```

### Phase 8 封版前置條件（Phase 5 至 Phase 8 全程監控健康）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| A/B 監控（Phase 5 至 Phase 8 全程）邏輯分數 | 平均 ≥ 90 分 | MONITORING_PLAN.md |
| A/B 監控熔斷器（Phase 5 至今）| = 0 次 | MONITORING_PLAN.md |
| 發布清單七個區塊 | 全部 ✅ | 雙方逐項確認 |
| CONFIG_RECORDS.md 完整 | 八章節完整 | Agent B 審查 |
| Constitution 最終總分 | ≥ 80% | Constitution Runner |
| Git Tag 建立 | `v[Major.Minor.Patch]` | git log --tags |
| Agent B APPROVE | AgentEvaluator | AgentEvaluator |

### Phase 8 A/B 監控最終報告

```markdown
# A/B 監控最終報告 - [專案名稱] v[版本號]

## 監控期間概覽
| 項目 | 內容 |
|------|------|
| 監控起始日 | Phase 5 啟動日 |
| 監控截止日 | Phase 8 封版日 |
| 總監控天數 | XX 天 |

## 各監控指標最終統計
| 指標 | 閾值 | 最低值 | 最高值 | 平均值 | 達標天數 | 最終狀態 |
|------|------|--------|--------|--------|----------|----------|
| 邏輯正確性分數 | ≥ 90 | XX | XX | XX | XX | ✅ |
| 回應時間偏差 | < 10% | X% | X% | X% | XX | ✅ |
| 熔斷器觸發 | 0 次 | — | — | — | XX | ✅ |
| 錯誤率 | < 1% | X% | X% | X% | XX | ✅ |

## 異常事件記錄（Phase 5 至今）
（無異常）✅

## 最終結論
| 項目 | 結論 |
|------|------|
| 整體監控穩定性 | ✅ 穩定（熔斷 0 次）|
| 可封版 | ✅ |
```

### Phase 8 方法論閉環確認

```markdown
### 方法論閉環記錄

| Phase | 完成日期 | Agent A | Agent B | 最終狀態 |
|-------|----------|---------|---------|----------|
| Phase 1 | YYYY-MM-DD | ______ | ______ | ✅ Sign-off |
| Phase 2 | YYYY-MM-DD | ______ | ______ | ✅ Sign-off |
| Phase 3 | YYYY-MM-DD | ______ | ______ | ✅ Sign-off |
| Phase 4 | YYYY-MM-DD | ______ | ______ | ✅ Sign-off |
| Phase 5 | YYYY-MM-DD | ______ | ______ | ✅ Sign-off |
| Phase 6 | YYYY-MM-DD | ______ | ______ | ✅ Sign-off |
| Phase 7 | YYYY-MM-DD | ______ | ______ | ✅ Sign-off |
| Phase 8 | YYYY-MM-DD | ______ | ______ | ✅ Sign-off |

**methodology-v2 v5.92 完整閉環達成 🎉**
```

### Phase 8 在整體架構的位置

```
版本週期完整地圖：

Phase 1 需求    → SRS.md + SPEC_TRACKING + TRACEABILITY（建立 FR）
Phase 2 設計    → SAD.md + ADR（FR → 模組）
Phase 3 實作    → 代碼 + 單元測試（模組 → 函數）
Phase 4 測試    → TEST_PLAN + TEST_RESULTS（函數 → TC）
                  ↓ TRACEABILITY 四欄全滿
Phase 5 驗收    → BASELINE + MONITORING 啟動
Phase 6 品質    → QUALITY_REPORT 完整版（回顧）
Phase 7 風險    → RISK_REGISTER + Decision Gate（前瞻）
Phase 8 配置    → CONFIG_RECORDS + 封版（治理）

每個 Phase 都有：
✅ A/B 雙 Agent 協作（不同 Persona）
✅ HybridWorkflow mode=ON
✅ AgentEvaluator 評估
✅ Quality Gate（ASPICE + Constitution）
✅ DEVELOPMENT_LOG 實際輸出記錄
✅ 雙方 session_id 可追溯
```

---

## Phase 1 詳細說明（v5.93 新增）

> 基於 Phase1_Plan_5W1H_AB.md，詳細定義 Phase 1 需求規格的 A/B 協作流程。

### Phase 1 WHO — A/B 角色分工

| 角色 | Persona | 職責 | 禁止事項 |
|------|---------|------|----------|
| Agent A（Architect）| `architect` | 撰寫 SRS.md、建立 SPEC_TRACKING.md、更新 TRACEABILITY_MATRIX.md | 省略任何 FR 的邏輯驗證方法、跳過 Constitution 檢查 |
| Agent B（Reviewer）| `reviewer` | 審查 FR 完整性、A/B 評估、給出 APPROVE/REJECT | 自寫自審、跳過 AgentEvaluator |

### Phase 1 WHAT — 交付物

| 交付物 | 格式 | 位置 |
|--------|------|------|
| SRS.md（功能需求）| Markdown，FR-01~FR-XX | `01-requirements/` |
| SPEC_TRACKING.md（規格追蹤）| Markdown，追蹤外部規格 → 內部實作 | `01-requirements/` |
| TRACEABILITY_MATRIX.md（初始化）| Markdown，四欄（FR→設計→代碼→測試）| `01-requirements/` |

### Phase 1 WHEN — 時序門檻

**進入條件**：專案啟動

**退出條件**（全部必須為 ✅）：

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| ASPICE 文檔合規率 | > 80% | `quality_gate/doc_checker.py` |
| Constitution SRS 正確性 | = 100% | `constitution/runner.py --type srs` |
| SPEC_TRACKING.md 存在 | 必須存在 | Framework Enforcement（BLOCK）|
| SPEC_TRACKING.md 完整性檢查 | 通過 | `python3 cli.py spec-track check` |
| 規格完整性 | ≥ 90% | Agent B 確認 |
| 每條 FR 有邏輯驗證方法 | 100% | Agent B 逐條確認 |
| Agent B APPROVE | AgentEvaluator | AgentEvaluator |

### Phase 1 WHERE — 路徑工具

| 項目 | 內容 |
|------|------|
| 目錄 | `01-requirements/` |
| 工具 | `quality_gate/doc_checker.py` |
| 工具 | `constitution/runner.py --type srs` |
| 工具 | `python3 cli.py spec-track init` |
| 工具 | `python3 cli.py spec-track check` |

### Phase 1 WHY — 設計理由

> 建立需求基線，防止規格漂移。

**核心原則**：Phase 1 缺陷到 Phase 3 才發現，修復成本 ×10。

| 問題階段 | 修復成本 | 說明 |
|----------|----------|------|
| Phase 1 發現 | ×1 | 規格階段修復 |
| Phase 2 發現 | ×3 | 設計階段變更 |
| Phase 3 發現 | ×10 | 實作後重構 |
| Phase 4+ 發現 | ×100+ | 測試/部署後變更 |

### Phase 1 HOW — SOP + A/B 審查清單

**SOP（標準作業流程）**：
1. Agent A 撰寫 SRS.md（FR-01~FR-XX）
2. Agent A 初始化 SPEC_TRACKING.md
3. Agent A 初始化 TRACEABILITY_MATRIX.md（四欄空表）
4. Agent A 自檢：每條 FR 都有邏輯驗證方法
5. Agent B A/B 審查（7 項清單）
6. 執行 Quality Gate（ASPICE + Constitution）
7. Agent B 給出 APPROVE/REJECT

**A/B 審查清單（7 項）**：

| # | 檢查項 | 說明 |
|----|--------|------|
| 1 | SRS.md 完整性 | 所有 SRS FR 都有對應章節 |
| 2 | FR 邏輯驗證方法 | 每條 FR 都有量化驗證方法（非「待確認」）|
| 3 | NFR 可測試性 | 非功能需求可量化驗證 |
| 4 | SPEC_TRACKING 對應 | 外部規格 → 內部 FR 映射完整 |
| 5 | Constitution 合規 | 正確性 = 100%、安全性 = 100% |
| 6 | Traceability 可追蹤 | FR → 實作可追蹤 |
| 7 | AgentEvaluator 分數 | ≥ 80 分 |

### Phase 1 DEVELOPMENT_LOG 格式

```markdown
## Phase 1 Quality Gate 結果（YYYY-MM-DD HH:MM）

### 前置確認
執行命令：python3 quality_gate/doc_checker.py
結果：Compliance Rate XX% ✅/❌

執行命令：python3 quality_gate/constitution/runner.py --type srs
結果：正確性 XX%（目標 100%）✅/❌

執行命令：python3 cli.py spec-track check
結果：完整性檢查 ✅/❌

### FR 邏輯驗證方法確認
- [ ] FR-01：______
- [ ] FR-02：______
（每條 FR 逐一確認）

### A/B 審查結果
- Agent A（Architect）：session_id ______
- Agent B（Reviewer）：session_id ______
- 審查結論：APPROVE ✅ / REJECT ❌

### Phase 1 結論
- [ ] ✅ 通過，進入 Phase 2
- [ ] ❌ 未通過（原因：______）
```

---

## Phase 2 詳細說明（v5.88 新增）

> 基於 Phase2_Plan_5W1H_AB.md，詳細定義 Phase 2 架構設計的 A/B 協作流程。

### Phase 2 WHO — A/B 角色分工

| 角色 | Persona | 職責 | 禁止事項 |
|------|---------|------|----------|
| Agent A（Architect）| `architect` | 設計 SAD.md、定義模組邊界、決定技術選型、記錄 ADR | 引入第三方框架、偷偷妥協衝突 |
| Agent B（Senior Dev/Reviewer）| `reviewer` 或 `developer`（資深）| 從實作可行性角度審查架構設計 | 代替 Agent A 重寫、跳過 AgentEvaluator |

**強制原則**：A/B 必須是不同 Agent，禁止自寫自審。架構設計比需求更需要對抗性審查。

### Phase 2 WHAT — SAD.md 最低內容要求

SAD.md 必須包含以下章節，與 Phase 1 的 SRS.md 要求對齊：

```markdown
# SAD - [專案名稱]

## 1. 架構概覽
- 系統邊界圖
- 核心模組清單

## 2. 模組設計
| 模組名稱 | 職責 | 對應 SRS FR | 依賴模組 |
|----------|------|-------------|----------|
| ModuleA  | ...  | FR-01, FR-02 | ModuleB |

## 3. 介面定義
- 模組間 API 合約
- 資料流向圖

## 4. 錯誤處理機制
- L1-L6 分類對應（參照 methodology-v2）
- Retry / Fallback / Circuit Breaker 設計

## 5. 技術選型決策（ADR）
| 決策 | 選擇 | 理由 | 替代方案 | 捨棄原因 |
|------|------|------|----------|----------|

## 6. 架構合規矩陣
| 模組 | 對應 methodology-v2 規範 | 執行狀態 | 備註 |
|------|--------------------------|----------|------|
```

### Phase 2 A/B 架構審查清單（Agent B 逐項確認）

- [ ] SAD 模組列表完整對應所有 SRS FR 編號（無遺漏）
- [ ] 模組間耦合度合理（低耦合、高內聚）
- [ ] 每個外部依賴都有 Lazy Init 設計
- [ ] 錯誤處理明確對應 L1-L6 分類
- [ ] Retry / Fallback / Circuit Breaker 已設計
- [ ] 技術選型決策（ADR）已記錄，無「幻覺框架」
- [ ] 架構可直接指導 Phase 3 實作（無模糊地帶）
- [ ] TRACEABILITY_MATRIX.md 已從 FR → 模組 更新

### Phase 2 Conflict Log 格式

當架構設計與 methodology-v2 規範衝突時，記錄到 DEVELOPMENT_LOG.md：

```markdown
| 衝突點 | 規格書建議 | methodology-v2 選擇 | 理由 |
|--------|------------|---------------------|------|
| 快取機制 | Redis Cluster | 單機 Redis（符合架構分層規範）| 規格書未說明分散式需求 |
```

**衝突處理原則**：
1. **禁止私自妥協** — 不能悄悄選其中一個
2. **優先選擇符合 methodology-v2 的方式**
3. **詳細記錄到 Conflict Log**

### Phase 2 進入條件（全部必須為 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| Phase 1 已完成 | phase_artifact_enforcer 通過 | Framework Enforcement |
| SPEC_TRACKING.md 存在 | 必須存在 | Framework Enforcement（BLOCK）|
| Constitution SRS 分數 | 正確性 = 100% | constitution runner --type srs |

### Phase 2 退出條件（全部必須為 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| ASPICE 文檔合規率 | > 80% | quality_gate/doc_checker.py |
| Constitution SAD 分數：正確性 | = 100% | constitution runner --type sad |
| Constitution SAD 分數：可維護性 | > 70% | constitution runner --type sad |
| AgentEvaluator Score | ≥ 80/100 | AgentEvaluator |
| TRACEABILITY_MATRIX 已更新 | FR → 模組 欄位完整 | Agent B 人工確認 |
| A/B 審查結論 | APPROVE | Agent B |
| DEVELOPMENT_LOG 有實際輸出 | 非空泛文字 | Agent B 人工確認 |

---

## Phase 3 詳細說明（v5.90 新增）

### Phase 3 WHO — A/B 角色分工

#### Agent A（Developer）—— 代碼實作者

| 屬性 | 內容 |
|------|------|
| Persona | `developer` |
| Goal | 將 SAD.md 模組設計轉化為生產就緒代碼，單元測試覆蓋率 100% |
| 職責 | 實作所有模組、撰寫單元測試（含三類）、填寫同行邏輯審查對話 |
| 黃金準則 | 代碼註解標注對應規範條文；命名規則 100% 符合 methodology-v2 |
| 禁止 | 引入 SAD.md 外的第三方框架；自行通過 Quality Gate；跳過同行審查 |

#### Agent B（Code Reviewer）—— 代碼審查者

| 屬性 | 內容 |
|------|------|
| Persona | `reviewer` |
| Goal | 發現 Agent A 實作中的邏輯錯誤、覆蓋率漏洞、規範偏離 |
| 職責 | 同行邏輯審查、A/B 代碼評估、確認測試完整性 |
| 核心問題 | 「輸出是否可能多於輸入？」「單一與多情況邏輯一致？」「Lazy Init 有沒有落實？」|
| 禁止 | 代替 Agent A 修改代碼；跳過 AgentEvaluator；僅看代碼不看測試 |

> ⚠️ **雙重禁止**：①禁止自寫自審；②禁止跳過同行邏輯審查對話。

---

### Phase 3 WHAT — 代碼規範要求

每個模組必須包含規範標注：

```python
class TTSEngine:
    """
    TTS 引擎 - 語音合成核心

    對應 methodology-v2 規範：
    - SKILL.md - Core Modules
    - SKILL.md - Error Handling (L1-L6)
    - SAD.md FR-01, FR-05

    邏輯約束：
    - 輸出長度 ≤ 輸入長度（Spec Logic Mapping FR-01）
    - 外部依賴使用 Lazy Init（避免初始化崩潰）
    """

    def __init__(self):
        self._engine = None  # Lazy Init：不在 __init__ 直接呼叫

    def _get_engine(self):
        """Lazy Init：實際需要時才初始化外部依賴"""
        if self._engine is None:
            self._engine = ExternalTTSSDK()
        return self._engine
```

---

### Phase 3 WHAT — 單元測試三類要求

每個模組的測試必須覆蓋以下三類：

```python
# ── 類型 1：正向測試（Happy Path）─────────────────
def test_split_normal_text(self):
    """正常文字分段"""
    text = "大家好。我是導引員。今天天氣好。"
    result = processor.split(text)
    assert len(result) > 0

# ── 類型 2：邊界測試（Boundary）──────────────────
def test_split_empty_input(self):
    """空白輸入 → 應回傳空陣列"""
    assert processor.split("") == []

def test_split_single_sentence_exceeds_chunk_size(self):
    """超過 chunk_size 的單一句子 → 應正確分割"""
    long_sentence = "A" * 1000
    result = processor.split(long_sentence)
    assert all(len(chunk) <= CHUNK_SIZE for chunk in result)

# ── 類型 3：負面測試（Negative）──────────────────
def test_output_not_exceed_input(self):
    """邏輯約束：合併後字符數不應多於原文"""
    text = "大家好。我是導引員。今天天氣好。"
    chunks = processor.split(text)
    merged = ''.join(chunks)
    assert len(merged) <= len(text), \
        f"輸出多於原文！merged={len(merged)}, input={len(text)}"

def test_single_vs_multi_format_consistency(self):
    """單一檔案與多檔案格式必須一致"""
    single = merger.merge(["a.mp3"], "out.mp3")
    multi  = merger.merge(["a.mp3", "b.mp3"], "out.mp3")
    assert get_format(single) == get_format(multi), \
        "單一與多檔案格式不一致！"
```

---

### Phase 3 WHAT — 集成測試模板（端到端）

```python
# tests/test_integration.py

class TestIntegration:
    """端到端集成測試——覆蓋跨模組邏輯"""

    def test_full_pipeline(self):
        """完整流程：文字 → 最終輸出"""
        text = "大家好。我是導引員。"
        result = pipeline.process(text)
        assert result.success
        assert result.output_file.exists()

    def test_output_not_exceed_input(self):
        """跨模組約束：輸出不應比輸入多字符"""
        text = "大家好。我是導引員。今天天氣好。"
        chunks = processor.split(text)
        merged = ''.join(chunks)
        assert len(merged) <= len(text)

    def test_single_file_format_consistency(self):
        """單一檔案 vs 多檔案：格式一致"""
        s = merger.merge(["a.mp3"], "s.mp3")
        m = merger.merge(["a.mp3", "b.mp3"], "m.mp3")
        assert get_format(s) == get_format(m)

    def test_error_recovery(self):
        """錯誤復原：失敗後可重新執行"""
        with pytest.raises(ExpectedError):
            pipeline.process(invalid_input)
        result = pipeline.process(valid_input)
        assert result.success
```

---

### Phase 3 WHAT — 同行邏輯審查對話模板

#### Developer 部分（Agent A 填寫）

```markdown
## 邏輯審查對話 — [模組名稱]（Phase 3）

### Developer 回答（Agent A 必須填寫）

**1. 我的假設是：**
- [ ] 標點處理邏輯：______（例：標點已保留，未被刪除）
- [ ] 輸出不超過輸入：______（例：split() 不插入額外字符）
- [ ] 分支一致性：______（例：單一元素與多元素走同一邏輯路徑）
- [ ] Lazy Init：______（例：_engine 在 _get_engine() 中初始化）

**2. 輸出預期：**
- [ ] 沒有插入額外字符（說明：______）
- [ ] 格式與多情況一致（說明：______）

**3. 領域知識應用：**
- [ ] TTS：標點 = 停頓，已保留
- [ ] 網路：timeout=30s、retry=3 次、熔斷在 5 次失敗後觸發
- [ ] 通用：輸出 ≤ 輸入，已有負面測試驗證

Agent A 簽名：______  Session ID：______
```

#### Architect 確認部分（Agent B 填寫）

```markdown
### Architect 確認（Agent B 必須填寫）

**審查結果：**
- [ ] 假設合理（說明：______）
- [ ] 邏輯正確（說明：______）
- [ ] 領域知識已正確應用（說明：______）
- [ ] 負面測試覆蓋關鍵約束（說明：______）

**發現問題（若有）：**
| 問題描述 | 嚴重性 | 建議修改方式 |
|----------|--------|-------------|
|          |        |             |

**審查結論：**
- [ ] ✅ 通過 — 繼續下一模組
- [ ] ❌ 不通過 — 返回 Agent A 修改（原因：______）

Agent B 簽名：______  Session ID：______
```

---

### Phase 3 WHAT — 合規矩陣格式

```markdown
## 合規矩陣（Compliance Matrix）— Phase 3

| 功能模組 | 對應 methodology-v2 規範 | 對應 SRS ID | 執行狀態 | 備註 |
|----------|--------------------------|-------------|----------|------|
| TTSEngine | SKILL.md - Core Modules | FR-01,FR-02 | 100% 落實 | 無 |
| TextProcessor | SKILL.md - Data Processing | FR-05,FR-07 | 100% 落實 | 無 |
| AudioMerger | SKILL.md - Error Handling | FR-19 | 100% 落實 | 無 |
| ErrorHandler | SKILL.md - L1-L6 分類 | NFR-02 | 100% 落實 | 無 |
```

---

### Phase 3 A/B 代碼審查清單（Agent B 逐項確認）

**邏輯正確性**
- [ ] 所有字串操作：輸出長度 ≤ 輸入長度
- [ ] 分支邏輯：`if len(x)==1` 與一般情況結果一致
- [ ] 外部依賴：全部使用 Lazy Init，`__init__` 不直接呼叫
- [ ] 標點處理：標點有保留，未被刪除

**測試完整性**
- [ ] 正向測試覆蓋所有 Happy Path
- [ ] 邊界測試：空輸入、超長輸入、單一元素
- [ ] 負面測試：合併後字符數驗證、格式一致性驗證
- [ ] 集成測試覆蓋跨模組邏輯
- [ ] 單元測試覆蓋率 ≥ 80%

**規範符合度**
- [ ] 代碼命名符合 methodology-v2 命名規則
- [ ] 錯誤處理對應 L1-L6 分類
- [ ] 代碼註解標注對應規範條文
- [ ] 無引入 SAD.md 外的第三方框架

**合規矩陣完整性**
- [ ] 每個模組都在合規矩陣中有記錄
- [ ] 合規矩陣執行狀態均為「100% 落實」或有說明

---

### Phase 3 進入條件（全部必須為 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| Phase 2 已完成 | phase_artifact_enforcer 通過 | Framework Enforcement |
| SAD.md 存在 | 必須存在 | Framework Enforcement（BLOCK）|
| Constitution SAD 分數 | 正確性 = 100% | constitution runner --type sad |

---

### Phase 3 退出條件（全部必須為 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| Phase 2 已完成 | phase_artifact_enforcer 通過 | Framework Enforcement |
| `python3 quality_gate/phase_artifact_enforcer.py` 通過 | Phase 2 完成確認 | 工具驗證 |
| ASPICE 文檔合規率 | > 80% | quality_gate/doc_checker.py |
| Constitution 代碼分數 | 正確性 = 100%、覆蓋率 > 80% | constitution runner（不加 --type）|
| 代碼覆蓋率 | ≥ 70%（單元測試）| pytest-cov 實際輸出 |
| 單元測試全部通過 | 通過率 100% | pytest |
| 集成測試全部通過 | 通過率 100% | pytest |
| 每個模組都有同行邏輯審查記錄 | 無遺漏 | Agent B 確認 |
| AgentEvaluator Score | ≥ 90/100 | AgentEvaluator |
| 合規矩陣完整 | 每個模組有記錄 | Agent B 確認 |
| A/B 審查結論 | APPROVE | Agent B |

> ⚠️ **核心原則**：A/B 審查以**模組為單位**觸發，不是等全部代碼完成才審。

---

## Phase 4 詳細說明（v5.90 新增）

### Phase 4 WHO — A/B 角色分工（Tester ≠ Developer）

> ⚠️ **Phase 4 核心原則**：Tester（Agent A）必須與 Phase 3 的 Developer **不同 Agent**。
> 讓寫代碼的人設計測試，等同於讓人自己出題自己改卷。

#### Agent A（Tester）—— 測試設計 & 執行者

| 屬性 | 內容 |
|------|------|
| Persona | `qa` |
| Goal | 從**使用者需求**角度驗證系統行為，而非從「代碼實作」角度驗證 |
| 職責 | 撰寫 TEST_PLAN.md、設計測試案例、執行測試、記錄 TEST_RESULTS.md |
| 核心心態 | 「這個功能**應該**怎麼運作？」而不是「這段代碼**能不能**跑過？」|
| 禁止 | 查看 Phase 3 代碼再設計測試案例（避免確認偏誤）；自行判定測試通過 |

#### Agent B（QA Reviewer）—— 測試審查者

| 屬性 | 內容 |
|------|------|
| Persona | `reviewer` |
| Goal | 確保測試計劃覆蓋所有 SRS 需求；測試結果真實可信 |
| 職責 | 審查 TEST_PLAN（計劃完整性）、審查 TEST_RESULTS（結果真實性）|
| 核心問題 | 「測試案例是從 SRS 推導的嗎？」「失敗案例的根本原因分析夠深嗎？」|
| 禁止 | 幫 Agent A 補寫測試案例；接受「已手動確認」等無法重現的測試記錄 |

---

### Phase 4 WHAT — TEST_PLAN.md 完整規格

```markdown
# Test Plan - [專案名稱]

## 1. 測試目標
- 驗證所有 SRS FR 的功能行為符合預期
- 確認邊界條件與異常情況的處理正確
- 驗證跨模組集成行為無迴歸

## 2. 測試範圍

### 納入範圍
- 所有 SRS 功能需求（FR-01 ~ FR-XX）
- 非功能需求中可測試項目（效能、錯誤恢復）
- 跨模組集成點

### 排除範圍
- [明確說明哪些場景不在本次測試]

## 3. 測試策略

| 類型 | 方法 | 工具 | 覆蓋目標 |
|------|------|------|----------|
| 單元測試 | White-box | pytest | ≥ 80% |
| 集成測試 | Black-box | pytest / requests | 所有跨模組介面 |
| 系統測試 | End-to-End | 自動化腳本 | 所有 FR |
| 負面測試 | Fault Injection | pytest | 所有 L1-L6 錯誤路徑 |

## 4. 測試環境
| 項目 | 規格 |
|------|------|
| OS | Ubuntu 24 / macOS |
| Python | 3.11 |
| 測試框架 | pytest 8.x |
| 覆蓋率工具 | pytest-cov |

## 5. 測試案例清單（從 SRS 直接推導）

| TC ID | 對應 SRS ID | 測試案例名稱 | 測試類型 | 優先級 | 狀態 |
|-------|-------------|-------------|----------|--------|------|
| TC-001 | FR-01 | 正常文字分段 | 正向 | P0 | 待執行 |
| TC-002 | FR-01 | 空白輸入分段 | 邊界 | P0 | 待執行 |
| TC-003 | FR-01 | 合併後不多於原文 | 負面 | P0 | 待執行 |
| TC-004 | FR-05 | 單一 vs 多檔案格式一致 | 負面 | P0 | 待執行 |

## 6. 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 測試環境不穩定 | 高 | 容器化隔離 |
| 外部 API 不可用 | 中 | Mock 替代 |
```

---

### Phase 4 WHAT — TEST_RESULTS.md 完整規格

```markdown
# Test Results - [專案名稱]

## 執行摘要

| 項目 | 數值 |
|------|------|
| 執行日期 | YYYY-MM-DD HH:MM |
| 總測試數 | XX |
| 通過 | XX |
| 失敗 | XX |
| 略過 | XX |
| 通過率 | XX% |
| 代碼覆蓋率 | XX% |

## 詳細結果

| TC ID | 測試案例 | 預期結果 | 實際結果 | 狀態 | 備註 |
|-------|----------|----------|----------|------|------|
| TC-001 | 正常文字分段 | 回傳 3 段 | 回傳 3 段 | ✅ PASS | |
| TC-003 | 合併後不多於原文 | len ≤ 原文 | len ≤ 原文 | ✅ PASS | |

## 失敗案例分析

### TC-XXX：[失敗案例名稱]
- **根本原因**：[具體技術原因，不能只說「邏輯錯誤」]
- **影響範圍**：[影響哪些 SRS FR]
- **修復方式**：[具體代碼修改說明]
- **修復驗證**：[重新執行後的結果]
- **狀態**：已修復 / 待修復 / 已知問題

## 覆蓋率報告

| 類型 | 覆蓋率 | 目標 | 狀態 |
|------|--------|------|------|
| 代碼覆蓋率 | XX% | ≥ 80% | ✅/❌ |
| 分支覆蓋率 | XX% | ≥ 70% | ✅/❌ |
| SRS FR 覆蓋率 | XX% | 100% | ✅/❌ |

## 回歸測試

| 之前失敗的案例 | 本次結果 | 說明 |
|--------------|----------|------|
| TC-XXX | ✅ PASS | 已修復並驗證 |
```

> ⚠️ **根本原因分析要求**：失敗原因必須具體到代碼行數，不能只寫「邏輯錯誤」。
> 差：「邏輯錯誤」vs 好：「TextProcessor.split() 第 47 行，regex 分割邏輯錯誤」

---

### Phase 4 WHAT — 兩次 A/B 審查流程

#### 第一次 A/B 審查：TEST_PLAN 審查（執行前）

```markdown
## Phase 4 TEST_PLAN A/B 審查紀錄（第一次）

### 需求追蹤完整性
- [ ] SRS FR 條數：XX 條；TEST_PLAN TC 條數：XX 條
- [ ] 每條 FR 至少有 1 個對應 TC：✅/❌
- [ ] P0 需求有三類測試（正向 + 邊界 + 負面）：✅/❌
- 說明：______

### 測試設計品質
- [ ] TC 從 SRS 推導（非從代碼推導）：✅/❌
- [ ] 負面測試包含關鍵約束（合併字符驗證、格式一致性）：✅/❌
- [ ] 錯誤路徑測試覆蓋 L1-L6：✅/❌
- 說明：______

### 可執行性
- [ ] 每個 TC 預期結果可量化：✅/❌
- [ ] 可自動化執行（無手動確認項）：✅/❌
- [ ] Mock 策略已定義：✅/❌
- 說明：______

### 審查結論
- [ ] ✅ APPROVE — 執行測試
- [ ] ❌ REJECT — 返回 Agent A 修改（原因：______）

Agent B 簽名：______  Session ID：______  日期：______
```

#### 第二次 A/B 審查：TEST_RESULTS 審查（執行後）

```markdown
## Phase 4 TEST_RESULTS A/B 審查紀錄（第二次）

### 結果真實性
- [ ] 所有 TC 有 pytest 實際輸出（非手動填寫）：✅/❌
- [ ] 覆蓋率由工具自動生成：✅/❌
- [ ] 通過率計算正確（通過數/總數）：✅/❌
- 說明：______

### 問題處理完整性
- [ ] 所有失敗案例有具體根本原因（到代碼行數）：✅/❌
- [ ] 所有失敗案例已修復或有明確處置說明：✅/❌
- [ ] 修復後的回歸測試已執行：✅/❌
- 說明：______

### 覆蓋完整性
- [ ] SRS FR 覆蓋率 = 100%：✅/❌
- [ ] 代碼覆蓋率 ≥ 80%：✅/❌（實際：XX%）
- [ ] P0 測試全部 PASS：✅/❌
- 說明：______

### 審查結論
- [ ] ✅ APPROVE — 進入 Quality Gate
- [ ] ❌ REJECT — 補充資料 / 重新執行（原因：______）

Agent B 簽名：______  Session ID：______  日期：______
```

> ⚠️ **關鍵節點**：Phase 4 有**兩次** A/B 審查——第一次在執行測試**前**（審查計劃），第二次在執行測試**後**（審查結果）。兩次都必須 APPROVE 才能繼續。

---

### Phase 4 WHAT — 失敗案例根本原因分析要求

| 層級 | 要求 | 範例 |
|------|------|------|
| ❌ 差 | 只說「邏輯錯誤」| 無法定位、無法預防 |
| ✅ 好 | 具體到代碼行數 | `TextProcessor.split() 第 47 行，regex 分割邏輯錯誤` |

**根本原因分析模板**：

```markdown
### TC-XXX：[失敗案例名稱]
- **根本原因**：[具體技術原因，不能只說「邏輯錯誤」]
  - 問題模組：______
  - 問題函數：______
  - 問題行數：______
  - 具體原因：______
- **影響範圍**：[影響哪些 SRS FR]
- **修復方式**：[具體代碼修改說明]
- **修復驗證**：[重新執行後的結果]
- **狀態**：已修復 ✅ / 待修復 / 已知問題
```

---

### Phase 4 進入條件（全部必須為 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| Phase 3 已完成 | phase_artifact_enforcer 通過 | Framework Enforcement |
| 代碼存在且可執行 | pytest 可啟動 | Agent A |
| TEST_PLAN A/B 審查通過 | APPROVE | AgentEvaluator（計劃版）|

---

### Phase 4 退出條件（全部必須為 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| TEST_PLAN A/B 審查通過 | APPROVE | AgentEvaluator（計劃版）|
| Constitution test_plan | 正確性 100%、可維護性 > 70% | constitution runner --type test_plan |
| pytest 全部測試通過 | 通過率 = 100% | pytest 實際輸出 |
| 代碼覆蓋率 | ≥ 80% | pytest-cov 實際輸出 |
| SRS FR 覆蓋率 | = 100%（每條 FR 有對應 TC）| Agent B 確認 |
| 失敗案例全數修復 | 0 個 open 失敗 | TEST_RESULTS.md |
| TEST_RESULTS A/B 審查通過 | APPROVE | AgentEvaluator（結果版）|
| TRACEABILITY_MATRIX 已更新 | FR → TC 欄位完整 | Agent B |
| ASPICE 合規率 | > 80% | doc_checker |

---

### 5-8 Quality Gate 持續檢查（強制）

   每個 Phase 完成後都必須通過 Quality Gate：
   
   | Phase | 檢查項目 | 門檻 |
   |-------|----------|------|
   | Phase 5 | Constitution | ≥ 80% |
   | Phase 6 | Constitution | ≥ 80% |
   | Phase 7 | Constitution | ≥ 80% |
   | Phase 8 | Constitution | ≥ 80% |

   **注意**：Phase 5-8 也需要執行 Logic Correctness 檢查，確保交付品質不低於開發品質。

#### 5-8 A/B Testing 持續監控（新增）

每次部署後執行快速回歸測試：

```markdown
## A/B Testing 持續監控（每次部署後）

### 閾值
- 邏輯正確性：≥ 90 分
- 效能：與基線偏差 < 10%
- 穩定性：熔斷器不觸發

### 監控項目
1. **邏輯正確性**：執行 spec_logic_checker.py，分數 ≥ 90
2. **效能**：回應時間不超過基線 + 10%
3. **穩定性**：熔斷器不觸發、錯誤率 < 1%

### 記錄
每次部署後的監控結果記錄到 MONITORING_PLAN.md
```
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

#### 集成測試模板（Phase 3-4）

```markdown
## tests/test_integration.py 模板

```python
import pytest
from src.module import MainClass

class TestIntegration:
    """端到端集成測試"""
    
    def test_full_pipeline_text_to_audio(self):
        """驗證：文字 → 音訊完整流程"""
        # 1. 輸入文字
        text = "大家好。我是導引員。"
        
        # 2. 執行完整流程
        result = main_class.process(text)
        
        # 3. 驗證輸出
        assert result.audio_file.exists()
        assert result.duration > 0
    
    def test_output_not_exceed_input(self):
        """驗證：輸出不應比輸入多字符（字串操作）"""
        text = "大家好。我是導引員。今天天氣好。"
        processor = TextProcessor()
        chunks = processor.split(text)
        
        # 關鍵：合併後的字符不應多於原文
        merged = ''.join(chunks)
        assert len(merged) <= len(text), "輸出多於原文！"
    
    def test_single_file_format_consistency(self):
        """驗證：單一檔案與多檔案格式一致"""
        merger = AudioMerger()
        
        single_output = merger.merge(["file1.mp3"], "single.mp3")
        multi_output = merger.merge(["file1.mp3", "file2.mp3"], "multi.mp3")
        
        # 格式應一致（bitrate, codec 等）
        assert get_format(single_output) == get_format(multi_output)
    
    def test_error_recovery(self):
        """驗證：錯誤復原流程"""
        # 模擬錯誤情況
        with pytest.raises(ExpectedError):
            main_class.process(invalid_input)
        
        # 驗證可以復原
        result = main_class.process(valid_input)
        assert result.success
```

**注意**：集成測試應覆蓋以下關鍵場景：
- [ ] 文字 → 音訊完整流程
- [ ] 輸出不超過輸入（字串操作）
- [ ] 單一檔案格式 = 多檔案格式
- [ ] 錯誤復原流程
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

### A/B 審查模板（v5.87 新增）

> 每次 Phase 轉換時，Agent B 必須填寫此模板作為審查記錄。

#### Agent B 審查對話模板

```markdown
## Phase X A/B 審查紀錄

### Agent B 審查項目
1. FR 完整性：[✅/❌] 說明：______
2. 邏輯驗證方法：[✅/❌] 說明：______
3. 邊界條件覆蓋：[✅/❌] 說明：______
4. 外部依賴 Lazy Check 標記：[✅/❌] 說明：______
5. SPEC_TRACKING 連結：[✅/❌] 說明：______

### 審查結論
- [ ] ✅ APPROVE — 進入 Quality Gate
- [ ] ❌ REJECT — 返回 Agent A 修改（原因：______）

### Agent B 簽名：______
### 日期：______
```

#### DEVELOPMENT_LOG 正確記錄格式（v5.87 新增）

```markdown
## Phase X Quality Gate 結果（YYYY-MM-DD HH:MM）

### ASPICE 文檔檢查
執行命令：python3 quality_gate/doc_checker.py
結果：
- Compliance Rate: XX%
- [文件]: ✅ 存在

### Constitution 檢查
執行命令：python3 quality_gate/constitution/runner.py --type [type]
結果：
- 正確性: XX%（目標 100%）
- 可維護性: XX%（目標 > 70%）

### A/B 審查結果
- Agent A：[角色]（session_id）
- Agent B：[角色]（session_id）
- 審查結論：APPROVE ✅ / REJECT ❌

### 結論
- [ ] ✅ 通過，進入 Phase Y
- [ ] ❌ 未通過（原因：______）
```

#### 禁止行為清單（v5.87 新增）

```markdown
## 禁止行為

### A/B 協作
- ❌ Agent A 自行審查自己的產出
- ❌ Agent B 代替 Agent A 修改內容
- ❌ 跳過 AgentEvaluator 直接進入下一 Phase

### 記錄
- ❌ DEVELOPMENT_LOG 只寫「已通過」無實際輸出
- ❌ 未記錄 session_id（無法追溯）
```

#### 空泛記錄範例（禁止）

```markdown
❌ 禁止：
### Phase X Quality Gate
✅ 已通過

❌ 禁止：
## Phase 1 結論
通過了，可以進入下一階段。
```

> **正確做法**：必須有實際命令輸出、實際分數、實際審查結果，不能只寫「已通過」。

---

*改善方案日期: 2026-03-27*
*模板新增日期: 2026-03-29 (v5.87)*

---

## 附錄 X：領域知識檢查清單

### X.1 TTS（文字轉語音）領域

| 檢查項 | 說明 | 驗證方法 |
|--------|------|----------|
| 標點保留 | 標點=停頓信號，刪除會破壞韻律 | 輸出長度 ≤ 輸入長度 |
| 合併不多於原文 | 合併時不插入額外字符 | 合併後字符數 ≤ 原始字符數 |
| 格式一致性 | 單一檔案與多檔案格式相同 | 檢查 bitrate/codec 一致 |
| Lazy Check | 外部依賴不在 __init__ 直接呼叫 | 初始化不崩潰 |

### X.2 通用領域

| 檢查項 | 說明 | 驗證方法 |
|--------|------|----------|
| 輸出≤輸入 | 字串操作不插入額外字符 | 自動化檢查或人工覆盤 |
| 分支一致 | if len(x)==1 與一般情况一致 | 邊界測試覆蓋 |
| Lazy Init | 外部依賴在實際需要時才檢查 | 模擬無依賴環境測試 |

### X.3 使用方式

1. **實作前**：查閱領域知識清單
2. **實作中**：自我檢查清單項目
3. **測試 Phase**：負面測試覆蓋清單項目
4. **Code Review**：確認清單項目已檢查

---

*附錄新增日期: 2026-03-28 - 基於 v574 專案學習*

---

## 附錄 Y：Quality Gate 三層檢查系統

### Y.1 系統概述

PhaseEnforcer 採用三層檢查系統，確保每個 Phase 的產出符合標準：

| 層級 | 名稱 | 權重 | 檢查內容 |
|------|------|------|----------|
| L1 | 結構檢查 | 25% | 資料夾結構、檔案是否存在 |
| L2 | 內容檢查 | 25% | 檔案內容結構、章節完整性 |
| L3 | 代碼品質檢查 | 50% | 代碼品質問題（使用 Agent Quality Guard） |

### Y.2 使用方式

```python
from quality_gate.phase_enforcer import PhaseEnforcer

# 預設：三層檢查（結構 25% + 內容 25% + 代碼 50%）
enforcer = PhaseEnforcer("/path/to/project", strict_mode=True)
result = enforce.enforce_phase(1)

# 略過代碼品質檢查（L3）
enforcer = PhaseEnforcer(
    "/path/to/project", 
    strict_mode=True,
    include_code_quality=False
)

# 自訂權重
enforcer = PhaseEnforcer(
    "/path/to/project",
    weights=(0.3, 0.3, 0.4)  # 結構 30%, 內容 30%, 代碼 40%
)
```

### Y.3 CLI 使用方式

```bash
# 預設：三層檢查
python -m quality_gate.cli quality check-phase 1

# 略過代碼品質檢查
python -m quality_gate.cli quality check-phase 1 --no-code-check

# 自訂權重
python -m quality_gate.cli quality check-phase 1 --weights 0.3,0.3,0.4
```

### Y.4 輸出格式

```json
{
  "phase": 1,
  "passed": true,
  "structure_check": {
    "score": 100,
    "missing": []
  },
  "content_check": {
    "score": 85,
    "missing_sections": []
  },
  "code_quality_check": {
    "score": 78,
    "files_scanned": 12,
    "issues": [
      { "file": "src/main.py", "line": 45, "issue": "long_function", "severity": "high" }
    ]
  },
  "gate_score": 85.25,
  "can_proceed": true,
  "blocker_issues": []
}
```

### Y.5 Agent Quality Guard

L3 代碼品質檢查使用 Agent Quality Guard（`/workspace/agent-quality-guard`）進行分析：

- **掃描目錄**：`03-development/`（Phase 1-3 代碼存放位置）
- **檢查維度**：正確性、安全性、可維護性、性能、測試覆蓋率
- **評分維度**：
  - correctness (30%)
  - security (25%)
  - maintainability (20%)
  - performance (15%)
  - coverage (10%)
- **通過標準**：高嚴重性問題少於 5 個

---

*附錄新增日期: 2026-03-29 - 整合 Agent Quality Guard*

---

## v6.02 新模組：Integrity Tracker

### 概述
Integrity Tracker 是誠信追蹤系統，用於記錄和追蹤 Agent 的誠信行為。每次「聲稱 vs 實際」不符都會被記錄並扣分。

### 扣分規則

| 違規類型 | 扣分 | 說明 |
|----------|------|------|
| subagent_claim | -20 | 聲稱使用 Sub-agent 但未使用 |
| code_lines_claim | -15 | 代碼行數聲稱與實際不符 > 5% |
| qg_not_executed | -10 | 聲稱執行 Quality Gate 但未執行 |
| qa_equals_developer | -25 | QA = Developer（角色衝突）|
| missing_dialogue | -15 | 缺少 Developer 回應 Reviewer 的記錄 |
| fake_qg_result | -20 | 虛假 Quality Gate 結果 |
| skip_phase | -30 | 跳過 Phase |
| revision_zero | -15 | 聲稱 Revision = 0 但有修改 |

### 信任等級

| 等級 | 分數範圍 | 說明 |
|------|----------|------|
| FULL_TRUST | ≥ 80 | 完整信任 |
| PARTIAL_TRUST | 50-79 | 部分信任 |
| LOW_TRUST | < 50 | 低信任，需要更多審查 |

### 使用方式

```python
from quality_gate.integrity_tracker import IntegrityTracker

# 初始化
tracker = IntegrityTracker("/path/to/project")

# 記錄違規
tracker.record_violation({
    "type": "qg_not_executed",
    "details": "聲稱執行 Quality Gate 但未實際執行"
})

# 取得信任等級
trust_level = tracker.get_trust_level()
print(f"Trust Level: {trust_level['level']}")
print(f"Score: {trust_level['score']}")

# 取得詳細報告
report = tracker.get_report()
print(f"Total Violations: {report['total_violations']}")
print(f"Score: {report['score']}")
```

### Constitution 整合

Integrity Tracker 也整合進 Constitution 檢查：

```python
from constitution.integrity_constitution_checker import IntegrityConstitutionChecker

# 執行 Constitution 檢查時自動檢查誠信維度
checker = IntegrityConstitutionChecker()
result = checker.check("/path/to/project")
print(f"Integrity Score: {result['integrity_score']}")
```

### Phase Enforcer 整合

Phase Enforcer 現在會自動觸發 Integrity Tracker：

```python
from quality_gate.phase_enforcer import PhaseEnforcer

enforcer = PhaseEnforcer("/path/to/project", strict_mode=True)
result = enforcer.enforce_phase(1)

# 如果有誠信問題，會記錄到 Integrity Tracker
print(f"Integrity Issues: {result.get('integrity_issues', [])}")
```

### 檔案位置

- `quality_gate/integrity_tracker.py` - 核心模組
- `constitution/integrity_constitution_checker.py` - Constitution 整合
- `quality_gate/phase_enforcer.py` - Phase Enforcer Hook

---

## 附錄

### 附錄 A：Phase 執行指南 (5W1H)

> Phase 1-8 的 5W1H 執行指南，確保每個 Phase 都有明確的 WHO/WHAT/WHEN/WHERE/WHY/HOW。

- Phase 1: [docs/Phase1_Plan_5W1H_AB.md](docs/Phase1_Plan_5W1H_AB.md) ✅
- Phase 2: [docs/Phase2_Plan_5W1H_AB.md](docs/Phase2_Plan_5W1H_AB.md) ✅
- Phase 3: [docs/Phase3_Plan_5W1H_AB.md](docs/Phase3_Plan_5W1H_AB.md) ✅ 新增
- Phase 4: [docs/Phase4_Plan_5W1H_AB.md](docs/Phase4_Plan_5W1H_AB.md) ✅ 新增
- Phase 5: [docs/Phase5_Plan_5W1H_AB.md](docs/Phase5_Plan_5W1H_AB.md) ✅ 新增
- Phase 6: [docs/Phase6_Plan_5W1H_AB.md](docs/Phase6_Plan_5W1H_AB.md) ✅
- Phase 7: [docs/Phase7_Plan_5W1H_AB.md](docs/Phase7_Plan_5W1H_AB.md) ✅ 新增
- Phase 8: [docs/Phase8_Plan_5W1H_AB.md](docs/Phase8_Plan_5W1H_AB.md) ✅ 新增

### 附錄 B：DEVELOPMENT_LOG 範例參考

> 正確的 DEVELOPMENT_LOG 記錄格式 vs 禁止的空泛記錄

#### ✅ 正確範例

```markdown
## Phase 1 Quality Gate 結果（2026-03-29 14:30）

### ASPICE 文檔檢查
執行命令：python3 quality_gate/doc_checker.py
結果：
- Compliance Rate: 87.5%
- SRS.md: ✅ 存在
- SPEC_TRACKING.md: ✅ 存在

### Constitution SRS 檢查
執行命令：python3 quality_gate/constitution/runner.py --type srs
結果：
- 正確性: 100%（目標 100%）
- 安全性: 100%（目標 100%）
- 可維護性: 75%（目標 > 70%）
- 測試覆蓋率: 85%（目標 > 80%）

### A/B 審查結果
- Agent A：Architect（session_abc123）
- Agent B：Reviewer（session_def456）
- 審查結論：APPROVE ✅
- Evaluator Score：92/100

### Phase 1 結論
- [ ] ✅ 通過，進入 Phase 2
- [ ] ❌ 未通過（原因：______）
```

#### ❌ 禁止範例

```markdown
### Phase 1 Quality Gate
✅ 已通過

## Phase 1 結論
通過了，可以進入下一階段。
```

> ⚠️ **警告**：空泛記錄無法追溯問題，Quality Gate 分數必須有實際命令輸出支撐。

---
