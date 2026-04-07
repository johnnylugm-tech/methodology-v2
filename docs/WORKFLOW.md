# methodology-v2 完整工作流程

> 從專案啟動到發布的完整流程 · v5.42

---

## 🔄 專案生命週期

```
┌──────────────────────────────────────────────────────────────────┐
│                                                                  │
│   ┌─────────────┐      ┌──────────────────────┐      ┌────────┐ │
│   │    init    │ ───► │      develop         │ ───► │ finish │ │
│   └─────────────┘      └──────────────────────┘      └────────┘ │
│        │                        │                        │       │
│        ▼                        ▼                        ▼       │
│   quality_watch          quality_watch              quality_watch │
│      start                  daemon                    stop       │
│                         (continuous)                              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

### Lifecycle 階段說明

| 階段 | 命令 | Quality Gate 行為 | 產出 |
|------|------|-------------------|------|
| **init** | `python3 cli.py init [name]` | 初始化品質閘道設定 | 專案結構、`.methodology/` |
| **develop** | `python3 cli.py quality-gate check` | 手動執行 Quality Gate（每 Phase 結束） | `.methodology/quality_log.json` |
| **finish** | `python3 cli.py finish` | 執行最終 Quality Gate，寫入品質報告 | 專案關閉、清盤 |

## 🏛️ Constitution + Enforcement + Quality Gate 三者關係

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           三層品質保障體系                                   │
│                                                                             │
│   ┌───────────────────┐                                                     │
│   │    Constitution   │  「我們要達到什麼標準？」—— 品質原則與目標定義         │
│   │  (品質標準定義)    │  - 正確性 >= 80%                                    │
│   └────────┬──────────┘  - 安全性 >= 95%                                    │
│            │               - 可維護性 >= 70%                                 │
│            │               - 覆蓋率 >= 80%                                   │
│            ▼               - 必須有 [TASK-XXX] commit message                │
│   ┌───────────────────┐                                                     │
│   │    Enforcement    │  「你是否遵守了規則？」—— 強制執行層                   │
│   │  (強制執行層)      │  - git hook 提交阻擋                                │
│   └────────┬──────────┘  - Policy Engine 等級 BLOCK                         │
│            │               - Execution Registry 不可偽造記錄                  │
│            ▼               - Constitution as Code 業務規則                    │
│   ┌───────────────────┐                                                     │
│   │   Quality Gate    │  「你的產出符合標準嗎？」—— 閘門驗證層                 │
│   │  (閘門驗證層)      │  - doc_checker: ASPICE 文檔檢查                     │
│   └────────┬──────────┘  - phase_artifact_enforcer: Phase 產物引用鏈        │
│            │               - quality-gate check: 每次存檔自動觸發            │
│            ▼                                                             │
│   ┌───────────────────┐                                                     │
│   │  Quality Watch    │  「持續監控，無論何時」—— 持續監控 daemon             │
│   │  (持續監控層)      │  - watchdog: 檔案變更偵測                           │
│   └───────────────────┘  - 2秒 debounce 防抖動                             │
│                             - quality_log.json: 所有檢查結果                 │
│                             - CRITICAL 問題即時警告                          │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 三者如何協作

```
   Quality Watch daemon
         │
         │ 檔案變更
         ▼
   Quality Gate Runner ──► Constitution 標準查詢
         │                      │
         │                      │ 閾值
         ▼                      ▼
   Enforcement check ◄── Policy Engine
         │
         │ BLOCK?
         ▼
   Execution Registry 記錄
         │
         │ commit 成功 / 阻擋
         ▼
   ┌─────────────────────────────────┐
   │      專案產出 quality_log.json  │
   └─────────────────────────────────┘
```

### Quality Watch 在各階段的角色

| 階段 | Quality Watch 行為 | 觸發時機 |
|------|-------------------|----------|
| **init** | 啟動 daemon，寫入 watch.pid | `python3 cli.py init` |
| **develop** | 持續監控：偵測 → Quality Gate → Enforcement | 每次存檔自動觸發 |
| **finish** | 停止 daemon，寫入最終品質報告 | `python3 cli.py finish` |

### Enforcement 政策速查

| Policy ID | 說明 | 等級 |
|-----------|------|------|
| `commit-has-task-id` | Commit 必須有 `[TASK-XXX]` | BLOCK |
| `quality-gate-90` | Quality Gate >= 90 | BLOCK |
| `no-bypass-commands` | 禁止使用 `--no-verify` | BLOCK |
| `test-coverage-80` | 測試覆蓋率 >= 80% | BLOCK |
| `security-score-95` | 安全分數 >= 95 | BLOCK |
| `aspice-docs-required` | ASPICE 文檔必須存在 | BLOCK |
| `phase-artifact-reference` | Phase 必須引用上階段產物 | BLOCK |

---

## 🔴🟡🔵 Decision Gate - 決策分類閘道

### 為什麼需要？

**現有流程的問題：**
- 開發過程中「隨機」決定重大事項
- 導致後期重構成本高
- 沒有決策依據，出了問題無法追溯

**Decision Gate 的價值：**
- 讓每一個技術決策都有踪跡可循
- 風險分級，確保重要決策經過確認
- 建立團隊共識

### 風險分類

| 等級 | 決策類型 | 處理方式 |
|------|----------|----------|
| 🔴 HIGH | 架構、API、核心演算法 | 必須照 spec，需 user 確認 |
| 🟡 MEDIUM | 預設值、工具選型 | 列出選項 + 建議 |
| 🔵 LOW | 目錄結構、檔案命名 | 可自主決定 |

### 完整流程

```
收到需求/任務
     ↓
1. 識別技術決策（classifier）
     ↓
2. 分類風險等級
     ↓
   🔴 HIGH → 列出選項 → user 確認 → 記錄
   🟡 MEDIUM → 列出選項 + 建議 → 自動記錄
   🔵 LOW → 自動記錄
     ↓
3. 執行開發
```

### 與其他模組的關係

```
Decision Gate → 決定要做什麼
     ↓
Constitution → 確保符合標準
     ↓
Quality Gate → 檢查產出
     ↓
Quality Watch → 持續監控
```

### 決策流程（詳細）

```
遇到技術決策
     │
     ▼
┌───────────────────────────────────────┐
│  Decision Gate 分類                   │
│  - HIGH → 停等 user 確認              │
│  - MEDIUM → 列出選項 + 建議            │
│  - LOW → 自主決定                      │
└──────────────────┬────────────────────┘
                   │
         ┌─────────┴─────────┐
         │                   │
      HIGH              MEDIUM/LOW
         │                   │
         ▼                   ▼
  ┌─────────────┐    ┌─────────────────┐
  │ User 確認    │    │ 執行並記錄       │
  │ 選擇或建議   │    │ decision_log    │
  └─────────────┘    └─────────────────┘
```

### CLI 命令

```bash
# 分類一個決策
python3 cli.py decision classify <key> "<description>"

# 列出所有決策
python3 cli.py decision list

# 確認 HIGH 風險決策
python3 cli.py decision confirm <id> "<value>"

# 查看決策日誌
python3 cli.py decision log
```

### Decision Gate 整合 Quality Watch

Quality Watch 在檢查時也會驗證決策日誌：

```
quality_watch daemon
       │
       ▼
   Quality Gate
       │
       ▼
   Decision Gate 檢查
       │
       ├── MEDIUM/HIGH 決策已確認？
       │
       └── 未確認 → CRITICAL 警告
```

📖 詳見：[DECISION_GATE_GUIDE.md](DECISION_GATE_GUIDE.md)

---

## 🛡️ Quality Watch 流程圖

```
init (Quality Watch 啟動)
        │
        ▼
┌───────────────────────────────────────────────────────┐
│  檔案變更偵測 (watchdog)                               │
│  - .py, .md, .json, .yaml, .yml, .sh                  │
│  - 防抖動：2 秒 debounce                               │
└─────────────────────┬─────────────────────────────────┘
                      │
                      ▼
┌───────────────────────────────────────────────────────┐
│  Quality Gate Runner                                    │
│  → python3 cli.py quality-gate check                  │
│  → Timeout: 60 秒                                     │
└─────────────────────┬─────────────────────────────────┘
                      │
            ┌─────────┴─────────┐
            │                   │
         PASS                  FAIL
            │                   │
            │                   ▼
            │         ┌─────────────────────┐
            │         │ 寫入 quality_log.json │
            │         │ severity: CRITICAL   │
            │         └─────────────────────┘
            │                   │
            ▼                   ▼
     (silent)          [QualityWatch] ⚠️ Quality check FAILED
                             [QualityWatch] 🔴 CRITICAL: <error>
```

---

## 🛡️ 品質閘道（v5.45 - 手動執行模式）

> **v5.45 更新**：quality_watch.py daemon 功能已移除。所有檢查都需要手動執行！

### 角色定位

**品質閘道（Quality Gate）** 是一個手動執行的品質驗證系統，嵌入每個 Phase 結束時，確保 AI Agent 的產出符合 ASPICE 標準與 Constitution 憲章。

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

### Quality Gate 檢查命令

```bash
# 完整 Quality Gate（含 ASPICE + Phase 產物）
python3 cli.py quality-gate check
python3 cli.py quality-gate all        # 別名

# 只檢查文檔
python3 cli.py quality-gate doc
python3 cli.py quality-gate docs       # 別名

# 只檢查 Phase 產物
python3 cli.py quality-gate phase

# 直接執行 ASPICE 文檔檢查
python3 quality_gate/doc_checker.py

# 直接執行 Constitution 檢查
python3 quality_gate/constitution/runner.py --type <srs|sad|test_plan>
```

---

## 🛡️ Enforcement Framework（整合 Quality Watch）

Enforcement 是**閘道層**，Quality Watch 是**持續監控層**。兩者整合：

```
Enforcement Gateway（Policy Engine + Constitution as Code）
        │
        ├── 提交時阻擋（git hook）
        │
        └── 持續監控（Quality Watch daemon）
                   │
                   ▼
           quality_log.json（審計日誌）
                   │
                   ▼
           Enforcement Registry（不可偽造）
```

### 三層保護

| 層次 | 元件 | 職責 |
|------|------|------|
| **Layer 1** | Policy Engine | 流程政策、BLOCK 等級 |
| **Layer 2** | Execution Registry | 執行記錄、不可偽造 |
| **Layer 3** | Constitution as Code | 業務規則、違反阻擋 |

### CLI 命令

```bash
# 執行所有檢查
python3 cli.py enforcement run

# 查看狀態
python3 cli.py enforcement status

# 安裝 Hook
python3 cli.py enforcement install

# Agent-Proof Hook
python3 cli.py agent-proof-hook install
```

### 閾值

| 維度 | 閾值 |
|------|------|
| Quality Gate | >= 90 |
| Security | >= 95 |
| Coverage | >= 80 |
| Commit Message | 必須包含 `[TASK-XXX]` |

---

## 🛡️ Anti-Shortcut Framework

本流程已整合 **Anti-Shortcut Framework**，確保 AI Agent 無法走捷徑：

| 模組 | 功能 |
|------|------|
| **Blacklist (B)** | 阻止危險操作 |
| **Gatekeeper (A)** | 確保流程完整 |
| **Enforcer (F)** | 防範捷徑 |
| **Audit Logger (C)** | 記錄審計 |
| **Double Confirm (D)** | 雙重確認 |
| **Phase Hooks (E)** | 自動化驗證 |

📖 詳見：[ANTI_SHORTCUT_FRAMEWORK.md](ANTI_SHORTCUT_FRAMEWORK.md)

---

## 📊 Code Metrics - 代碼品質指標

### 功能
- Cyclomatic Complexity 追蹤
- Coupling 分析
- Instability 指標

### 命令
```bash
python3 cli.py metrics report
python3 cli.py metrics history
```

---

## 🔧 Technical Debt - 技術債務

### 功能
- 債務添加/追蹤/解決
- 嚴重性分級
- 報告生成

### 命令
```bash
python3 cli.py debt add <description> [--severity high|medium|low]
python3 cli.py debt list
python3 cli.py debt resolve <id>
python3 cli.py debt report
```

---

## 📋 ADR - Architecture Decision Records

### 功能
- 正式架構決策記錄
- Markdown 導出
- 狀態追蹤

### 命令
```bash
python3 cli.py adr create <title>
python3 cli.py adr list
python3 cli.py adr get <id>
python3 cli.py adr export
```

---

## 🧪 TDAD Testing Methodology

本流程已整合 **TDAD (Test-Driven AI Agent Development)**，用測試驅動 Agent 開發：

| 概念 | 實作 | 功能 |
|------|------|------|
| **Compiled Prompts** | `CompiledConstitution` | 將 Constitution 視為編譯後 artifact |
| **Visible/Hidden Tests** | `QualityGateTDAD` | 防止 specification gaming |
| **Mutation Testing** | `MutationTester` | 偵測測試有效性 |
| **Impact Analysis** | `ImpactAnalyzer` | 圖形化變更影響分析 |

📖 詳見：[TDAD_METHODOLOGY.md](TDAD_METHODOLOGY.md)

---

## 完整工作流程圖（傳統視圖）

```
┌─────────────────────────────────────────────────────────────┐
│                     專案啟動（init）                          │
│              → quality_watch daemon 啟動                    │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. Constitution 階段                                        │
│    - 建立團隊憲章                                           │
│    - 定義品質標準                                           │
│    - 設定錯誤分類                                           │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Specify 階段                                            │
│    - 撰寫需求規格                                           │
│    - 建立 User Stories                                      │
│    - 定義驗收標準                                           │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Plan 階段                                              │
│    - 設計架構                                               │
│    - 規劃 Roadmap                                           │
│    - 分配任務                                               │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Tasks 階段（develop → Quality Watch 持續監控）            │
│    - 實作功能                                               │
│    - 單元測試                                               │
│    - Code Review                                            │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Verification 階段                                       │
│    - Gate 1: 語法檢查                                       │
│    - Gate 2: 單元測試                                       │
│    - Gate 3: Quality Gate                                   │
│    - Gate 4: 安全掃描                                       │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. 發布（finish → quality_watch daemon 停止）               │
│    - 整合測試                                               │
│    - 部署                                                   │
│    - 監控                                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 各階段產出

| 階段 | 產出 | 檔案位置 |
|------|------|----------|
| Constitution | CONSTITUTION.md | /constitution/ |
| Specify | requirements.md | /02-specify/ |
| Plan | architecture.md | /03-plan/ |
| Tasks | sprint_*.md | /04-tasks/ |
| Verification | gates.md | /05-verification/ |
| Outputs | src/, tests/ | /06-outputs/ |

---

## 錯誤處理流程

```
執行任務
    ↓
成功？ → 是 → 下一個任務
    ↓ 否
錯誤分類（L1-L6）
    ↓
L1-L2 → 自動重試 + Fallback
    ↓
L3-L4 → 記錄 + 降級
    ↓
L5-L6 → Human Intervention
```

---

## Quality Gate 閾值

| 維度 | 閾值 | 權重 |
|------|------|------|
| 正確性 | >= 80% | 30% |
| 安全性 | >= 100% | 25% |
| 可維護性 | >= 70% | 20% |
| 效能 | >= 80% | 15% |
| 覆蓋率 | >= 80% | 10% |

---

## 階段強制鉤子 (Phase Hooks)

每個階段結束時自動觸發驗證，確保品質標準不被繞過。

### 鉤子類型

| 階段 | 鉤子 | 說明 | 必填 |
|------|------|------|------|
| Development | `dev-lint` | 語法檢查 | ✓ |
| Development | `dev-test` | 單元測試 | ✓ |
| Development | `dev-constitution` | Constitution 合規 | ✓ |
| Verification | `verify-quality` | Quality Gate | ✓ |
| Verification | `verify-security` | 安全掃描 | ✓ |
| Verification | `verify-coverage` | 覆蓋率檢查 | ✗ |
| Release | `release-approval` | 審批確認 | ✓ |
| Release | `release-version` | 版本確認 | ✓ |
| Release | `release-changelog` | 更新日誌 | ✓ |

### 使用方式

```python
from anti_shortcut import PhaseHooks, Phase

hooks = PhaseHooks()

# 執行 development 階段的鉤子
result = hooks.execute_phase(Phase.DEVELOPMENT)

# 檢查是否可以進入下一階段
can_proceed, reason = hooks.can_proceed(
    from_phase=Phase.DEVELOPMENT,
    to_phase=Phase.VERIFICATION
)

if not can_proceed:
    print(f"Blocked: {reason}")
```

### 跳過鉤子

```python
# 有正當理由時可跳過（需要記錄）
hooks.skip_hook(
    hook_id="verify-coverage",
    reason="緊急修復，coverage 稍後補上"
)
```

---

## 命令速查表

### 專案 Lifecycle

```bash
# 初始化專案
python3 cli.py init "專案名"

# 結束專案
python3 cli.py finish
```

### Quality Gate（v5.45 手動執行）

> **v5.45 更新**：quality_watch.py daemon 已移除，所有檢查改為手動執行。

```bash
# 完整檢查（ASPICE + Phase 產物）
python3 cli.py quality-gate check
python3 cli.py quality-gate all          # 別名

# 只檢查文檔
python3 cli.py quality-gate doc
python3 cli.py quality-gate docs         # 別名

# 只檢查 Phase 產物
python3 cli.py quality-gate phase

# ASPICE 合規檢查
python3 cli.py quality-gate aspice
```

### Enforcement

```bash
# 執行所有 enforcement 檢查
python3 cli.py enforcement run

# 查看狀態
python3 cli.py enforcement status

# 安裝 git hook
python3 cli.py enforcement install

# Agent-Proof Hook
python3 cli.py agent-proof-hook install

# Policy Engine
python3 cli.py policy
```

### 任務管理

```bash
python3 cli.py task add "任務名" --points 5 --priority 3
python3 cli.py task list
python3 cli.py task complete <task-id>
```

### Sprint

```bash
python3 cli.py sprint create "Sprint 1" --start 2026-03-24 --end 2026-04-07
python3 cli.py sprint list
python3 cli.py sprint start <sprint-id>
```

---

*最後更新：2026-03-25 (v5.45.0)*
