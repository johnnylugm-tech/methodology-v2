# Johnny 使用手冊 v6.69

> **版本**: v6.69
> **對象**: Johnny（Human-in-the-Loop）
> **用途**: 快速上手 methodology-v2

---

## 1. methodology-v2 今天長什麼樣？

### v6.32 ~ v6.69 版本歷史

| 版本 | 改善內容 |
|------|----------|
| v6.32 | Template-based plan generation |
| v6.34 | SAD parser (FR→module mapping) + deliverable structure tree |
| v6.36 | TH thresholds table + External docs section |
| v6.37 | `--detailed` flag for FR detailed tasks |
| v6.38 | Phase 1-8 TH thresholds + External docs complete |
| v6.39 | `generate_full_plan.py` supports all phases |
| v6.41 | `--detailed` merges FR tasks into single plan |
| v6.42 | Agent A/B roles per phase + Reviewer Prompt |
| v6.43 | On Demand restrictions + Tool Usage Timing section |
| v6.44 | Pre-flight deliverable check fix |
| v6.45 | OUTPUT path from SAD parsing + Forbidden clarification |
| v6.61 | CQG+SAB — 代碼品質閘道 + 軟體架構基線 |
| v6.62 | BVS — Behaviour Validation System |
| v6.63 | HR-09 Claims Verifier |
| v6.64 | AI Test Suite + HR-17 |
| v6.65 | Steering Loop + AB Workflow 方向控制 |
| v6.66 | Feedback Loop — 標準化品質信號收集（P2-2）|
| v6.67 | Self-Correction Engine — 自動化錯誤修正（P2-3）|
| v6.68 | P0 Integration Fix — 觸發鍊全部自動化 |
| v6.69 | Audit fixes — core package、orchestration paths、CHANGELOG |

### 三層文件架構

| 層級 | 檔案 | 用途 |
|------|------|------|
| Layer 1 | SKILL.md | 核心規則（HR/TH/Phase路由 + Integrity計算）|
| Layer 2 | docs/P{N}_SOP.md（8檔）| Phase 詳細步驟（按需載入）|
| Layer 3 | templates/*.md（16檔）| 交付物模板（按需載入）|

---

## 2. 執行流程：plan-phase → Johnny 審核 → run-phase

> ⚠️ **所有 Phase 執行必須經過此流程**，不可繞過。

### 完整流程

```
Johnny: 「執行 Phase {N}」
    ↓
Agent: plan-phase --phase {N} --goal "..."
    ↓
Johnny: 看執行計畫（透明）
    ↓
Johnny: 「確認執行」
    ↓
Agent: run-phase --phase {N}
    ↓
失敗 → plan-phase --repair --step {N}.X
    ↓
成功 → 下一 Phase
```

### plan-phase 用法

```bash
# 生成執行計畫（基礎版）
python cli.py plan-phase --phase 3 --goal "FR-01~FR-08 實作"

# 生成執行計畫（含 FR 詳細任務）
python cli.py plan-phase --phase 3 --detailed --goal "FR-01~FR-08 實作"

# 修復迭代
python cli.py plan-phase --phase 3 --repair --step 3.2

# 查看歷史
python cli.py plan-phase --phase 3 --history

# 指定專案
python cli.py plan-phase --phase 3 --repo /path/to/project
```

### generate_full_plan.py 用法（可單獨使用）

```bash
# 生成完整 FR 詳細任務（所有 Phase 支援）
python3 scripts/generate_full_plan.py --phase 3 --repo /path/to/project

# 指定輸出檔案
python3 scripts/generate_full_plan.py --phase 3 --repo /path --output phase3_FULL.md
```

### run-phase 用法

```bash
python cli.py run-phase --phase 3
python cli.py run-phase --phase 3 --step 3.1 --task "FR-01 實作"
```

---

## 3. plan-phase 自動做什麼

```
┌─────────────────────────────────────────────────────────────┐
│  SCAN（讀取所有相關資料）                                      │
│                                                             │
│  1. SKILL.md → 核心規則                                      │
│  2. docs/P{N}_SOP.md → Phase 步驟                            │
│  3. .methodology/state.json → FSM 狀態                       │
│  4. .methodology/iterations/{phase}.json → 歷史迭代         │
│  5. 上階段交付物 → SRS/SAD/代碼等（SAD parser 自動解析）      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  PRE-FLIGHT（任一失敗就停止）                                 │
│                                                             │
│  1. FSM State Check → FREEZE/PAUSED 阻擋                  │
│  2. Phase Sequence → 不可跳過 Phase                          │
│  3. Constitution Check → <80% 阻擋                           │
│  4. Tool Registry Check → 工具狀態                           │
│  5. Session Save → Pre-flight 存檔                          │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    ✅ 全部通過
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  GENERATE PLAN（Template-based）                            │
│                                                             │
│  6. 讀取 plan_phase_template.md                              │
│  7. 解析 SAD.md → FR→module mapping                        │
│  8. 替換所有 placeholder ({PHASE}, {FR_COUNT}, etc.)       │
│  9. 若 --detailed → 呼叫 generate_full_plan.py            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  EXECUTE                                                     │
│ 10. Load docs/P3_SOP.md                                   │
│ 11. Execute via SubagentIsolator                           │
│ 12. PermissionGuard.check() before exec/rm                │
│ 13. Log to .methodology/run-phase.log                      │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  POST-FLIGHT                                                 │
│ 14. Final Constitution Check                                │
│ 15. Update state.json                                       │
│ 16. Report Summary                                          │
└─────────────────────────────────────────────────────────────┘
```

### Johnny 看到什麼

- Pre-flight 結果（✅/❌）
- Constitution 分數
- Session ID
- Log 檔位置
- 執行計畫（18 章節）

---

## 4. 執行計畫的 18 個章節

`plan-phase` 生成的執行計畫包含以下 19 個章節：

| # | 章節 | 說明 |
|---|------|------|
| 0 | 執行協議 | CLI 命令、Step 流程 |
| 1 | 硬規則 | HR-01~HR-15 含具體行動 |
| 2 | A/B 協作 | HR/TH 約束、Agent A/B 角色 |
| 3 | FR-by-FR 任務表格 | 從 SAD 解析，含模組/檔案/驗證命令 |
| 4 | 產出結構樹 | 從 SAD 解析的目錄結構 |
| 5 | FR 詳細任務 | 若 --detailed，含 SRS 完整內容 |
| 6 | 外部文檔 | Phase 適用的文檔列表 |
| 7 | Developer/Reviewer Prompt | On Demand 格式，含 Anti-Dump |
| 8 | Iteration 修復流程 | HR-12 5輪限制 |
| 9 | **工具調用時機** | **6 大工具觸發條件** |
| 10 | Quality Gate | 7步驗證命令 |
| 11 | sessions_spawn.log 格式 | HR-10 規範 |
| 12 | Commit 格式 | 標準 commit 格式 |
| 13 | 估計時間 | 各階段時間 + HR-13 臨界值 |
| 14 | Phase Truth 組成 | 權重計算 |
| 15 | 工具速查 | 6 大工具 Python 範例 |
| 16 | Pre-Execution Checklist | 12 項檢查清單 |
| 17 | 下一步 | --repair 指令 |

---

## 5. FR 詳細任務解析

### Phase → 解析的上一階段產物

| Phase | 解析的產物 | 內容 |
|-------|-----------|------|
| 1 | 無 | FR + NFR 需求 |
| 2 | SRS.md | 架構對應 |
| 3 | SRS.md + SAD.md | 代碼實作 + 測試案例 |
| 4 | SRS.md + SAD.md + Code | 測試項目 |
| 5 | TEST_RESULTS + BASELINE | 驗證交付 |
| 6 | QUALITY_REPORT | 品質保證 |
| 7 | RISK_REGISTER | 風險管理 |
| 8 | CONFIG_RECORDS | 配置管理 |

### SRS Parser 解析內容

- **FR sections**: FR-01~FR-08 標題、描述
- **Requirements**: 內容列表
- **Test cases**: 測試案例（輸入→輸出）
- **NFR sections**: 非功能需求

### SAD Parser 解析內容

- **FR→Module mapping**: FR-01 → `lexicon_mapper`
- **File paths**: `app/processing/lexicon_mapper.py`
- **Deliverable structure**: 目錄樹

---

## 6. 快速開始

### 新專案初始化（第一次）

```
對 Agent 說：
「請根據 TASK_INITIALIZATION_PROMPT.md 初始化專案」

Agent 會：
- 讀取 SRS.md
- 建立 GitHub 倉庫
- 初始化 state.json
```

### Step 1: 發布任務

```
對 Agent 說：
「請執行 Phase {N}
- 任務目標：{具體目標}
- 交付物：{清單}
」
```

### Step 2: Agent 生成計畫

Agent 必須使用 `plan-phase`：

```
Agent: python cli.py plan-phase --phase {N} --detailed --goal "{任務目標}"
```

Johnny 看執行計畫（18 章節透明）。

### Step 3: Johnny 審核計畫

```
如果計畫合理 → 「確認執行」
如果計畫有問題 → 「修改：{具體要求}」
```

### Step 4: Agent 執行

```
Agent: python cli.py run-phase --phase {N}
```

Johnny 等到執行完成，看結果。

### Step 5: Johnny 最終審核

```
1. Johnny: 看 run-phase 輸出
2. Johnny: 問 2-3 題拷問法
3. 如果正確 → ✅ CONFIRM
4. 如果錯誤 → ❌ REJECT
```

---

## 7. 每 Phase 審核流程

### Agent 完成 Phase N 後

```
1. Johnny: 看 run-phase 輸出結果
2. Johnny: 問 2-3 題拷問法

   Constitution 分數 ≥80% + 拷問正確:
   → ✅ CONFIRM 或 ⚠️ QUERY

   Constitution 分數 <80%:
   → ❌ REJECT
   → 要求 Agent 修復後重新提交
```

### Johnny 決策表

| 分數 | 等級 | Johnny 動作 |
|------|------|-------------|
| ≥95 | 🟢 完全合規 | 快速確認 |
| 80-94 | 🟢 高度合規 | 抽查後確認 |
| 70-79 | 🟡 基本合規 | 仔細檢查 |
| <70 | 🔴 可疑 | REJECT + 原因 |

---

## 8. On Demand 執行原則

### 核心原則

| 原則 | 定義 |
|------|------|
| **Need to Know** | 只給必要資訊，L1/NFR 被問時才提供 |
| **On Demand** | Sub-agent 自己讀 artifact paths，不 dump |
| **Anti-Dump** | 禁止要求主代理給完整 artifact 內容 |

### Prompt 限制

Developer/Reviewer Prompt 明確規定：
```
【On Demand 讀取範圍】（只讀這些章節，❌ 禁止 dump 全文）

FORBIDDEN:
- ❌ dump SRS.md/SAD.md 全文
- ❌ 無 citations 或 citations 無行號 → HR-15 違規
```

### 工具調用時機

| 工具 | 觸發時機 |
|------|---------|
| SubagentIsolator | 派遣 Sub-agent 前（HR-01）|
| PermissionGuard | exec/rm 操作前 |
| ContextManager | context > 50 條訊息 |
| SessionManager | 任務 > 30 分鐘 |
| KnowledgeCurator | Phase 開始前 verify |
| ToolRegistry | 新工具引入時 |

---

## 8.5 Sub-Agent Management

### 核心原則

每個 Phase 的 Sub-agent 管理都有明確的 5 大要素：

| 要素 | 說明 |
|------|------|
| **Need-to-Know** | 只給必要資訊（L1/NFR 被問時才提供）|
| **On-Demand** | Sub-agent 自己讀 artifact paths，不 dump |
| **Tool Timing** | 何時用什麼工具（spawn/KC/CM/QG/checkpoint）|
| **Isolation** | SubagentIsolator + fresh_messages |
| **HR-12** | 5 輪限制自動追蹤 |

### 8 個 Phase 的管理重點

| Phase | Agent A | Need-to-Know | 工具時機 |
|-------|---------|--------------|----------|
| 1 | architect | TASK_INITIALIZATION_PROMPT.md | spawn → KC |
| 2 | architect | SRS.md（只讀 FR） | spawn → KC → QG |
| 3 | developer | SRS §FR + SAD §Module | parallel → KC → CM → QG |
| 4 | qa | SRS + SAD + src/ | spawn → test_runner → coverage |
| 5 | devops | TEST_RESULTS + SRS | spawn → monitoring |
| 6 | qa | TEST_RESULTS + BASELINE | spawn → QG |
| 7 | qa | QUALITY_REPORT + SRS | spawn → risk_matrix |
| 8 | devops | RISK_REGISTER + BASELINE | spawn → lock_deps |

### Phase 3 範例

```
## Phase 3: 代碼實現

### Agent 角色
- **Agent A（developer）**: 實作 FR-XX
- **Agent B（reviewer）**: 審查 FR-XX 代碼

### Need-to-Know（只給必要資訊）

| 檔案 | 章節 | 原因 |
|------|------|------|
| SRS.md | §FR-XX 需求描述 | 只實作這個 FR 的功能 |
| SAD.md | §Module 邊界對照表 | 知道 Module 介面和邊界 |

**Skip**: `完整 SRS.md, 完整 SAD.md, 其他 FR 的實作`
**Context**: single_fr

### On-Demand（需要時才請求）
- **觸發條件**: 當需要知道其他 FR 的實作細節時
- **請求對象**: N/A（不該發生，每個 FR 獨立）
- **格式**: 返回錯誤：違反 Need-to-Know

### 工具調用時機
| 事件 | 工具 | 參數 |
|------|------|------|
| spawn | 派遣 Sub-agent | {'role': 'developer'} |
| knowledge_curator | KnowledgeCurator | verify_coverage |
| context_manager | ContextManager | 訊息 >30 時 L1 壓縮 |
| checkpoint | SessionManager | 每 FR 完成後 save |
```

---

## 9. 拷問法範例

在 Agent 完成 Phase 後，隨機問這些問題：

### Phase 1 相關
- 「Phase 1 的 Constitution 類型是什麼？」
- 「TH-14 的門檻是多少？」

### Phase 2 相關
- 「HR-05 的內容是什麼？」
- 「Phase 2 的 Agent B 是什麼角色？」

### Phase 3 相關
- 「SubagentIsolator 和直接 sessions_spawn 的差別？」
- 「Pre-flight 有哪 5 個檢查？」
- 「HR-15 的 citations 格式規定是什麼？」
- 「代碼和測試的分離是什麼？」
- 「FR-by-FR 表格從哪裡解析？」
- 「On Demand 原則是什麼？禁止什麼？」

### Phase 4-8 相關
- 「TH-02 的門檻是多少？」
- 「Phase 8 必須有哪些交付物？」
- 「各 Phase 解析哪些上一階段的產物？」

---

## 10. 新工具速查

### 六大工具

| 工具 | 解決的問題 | Agent 什麼時候用 |
|------|-----------|----------------|
| `KnowledgeCurator` | 知識一致性 | 派遣前 verify_coverage() |
| `ContextManager` | 上下文膨脹 | context > 50 時 compress() |
| `SubagentIsolator` | 結果污染 | 派遣時 spawn() |
| `PermissionGuard` | 危險操作 | exec/rm 前 check() |
| `SessionManager` | 任務中斷 | 任務 > 30 分鐘 |
| `ToolRegistry` | 新工具追蹤 | 發現新工具時 |

### v6.32+ 新增功能

| 功能 | 說明 |
|------|------|
| Template-based plan | `templates/plan_phase_template.md` 為基礎 |
| SAD parser | 自動解析 FR→module→file 路徑 |
| TH thresholds table | Phase 適用的 TH 閾值 |
| External docs | Phase 適用的文檔列表 |
| `--detailed` flag | 生成 FR 詳細任務（含 SRS 內容）|
| generate_full_plan.py | 支援所有 Phase（1-8）|

---

## 11. CLI 速查

```bash
# === 單一入口（必用）===
python cli.py run-phase --phase N
python cli.py run-phase --phase N --step N.X --task "..."

# === plan-phase（必用，執行前）===
python cli.py plan-phase --phase N --goal "..."
python cli.py plan-phase --phase N --detailed --goal "..."
python cli.py plan-phase --phase N --repair --step N.X
python cli.py plan-phase --phase N --history

# === generate_full_plan.py ===
python3 scripts/generate_full_plan.py --phase N --repo /path

# === Integrity 計算 ===
python cli.py integrity --project .

# === auto-fix / skip-failed ===
python cli.py stage-pass --phase N --auto-fix
python cli.py stage-pass --phase N --skip-failed
python cli.py enforce --level BLOCK --auto-fix

# === Phase 真相驗證 ===
python cli.py phase-verify --phase N

# === FSM 狀態 ===
python cli.py fsm-status
python cli.py fsm-transition --to PAUSED
python cli.py fsm-unfreeze

# === Constitution Check ===
python cli.py constitution check --type <srs|sad|test_plan|...>

# === Feedback Loop Dashboard（v6.66+）===
python cli.py feedback --list
python cli.py feedback --dashboard
python cli.py feedback --export json --output feedback.json
python cli.py feedback --sla

# === Tool Registry ===
python cli.py tool-registry --list

# === Session 管理 ===
python cli.py session-save --id <name>
python cli.py session-list
python cli.py session-load --id <name>
python cli.py session-delete --id <name>

# === 狀態查詢 ===
python cli.py status
python cli.py phase-status
```

---

## 12. Johnny 的三個狀態

```
🤚 等待中 - Agent 在執行 run-phase
👀 審核中 - Agent 完成，等 Johnny
✅/❌ 決策後 - CONFIRM 或 REJECT
```

---

## 13. 緊急情況

### 發現作假跡象
1. 看 run-phase 輸出
2. Constitution 分數 < 50%
3. 問 Agent：「這個分數怎麼來的？」
4. 回答模糊 → REJECT
5. 記錄到 MEMORY.md

### Agent 跳過 Phase
1. 分數極低但 Agent 說完成了
2. Johnny: REJECT
3. Agent: 回到上一 Phase

### Project FREEZE
1. run-phase 報錯「Project is FREEZE」
2. Johnny: 執行全面審計
3. Johnny: `python cli.py fsm-unfreeze`

---

## 14. 關鍵閾值速查

| 閾值 | 數值 | Phase |
|------|------|-------|
| TH-01 | ASPICE > 80% | 1-8 |
| TH-02 | Constitution ≥ 80% | 5-8 |
| TH-03 | Constitution 正確性 = 100% | 1-4 |
| TH-04 | Constitution 安全性 = 100% | 1-4 |
| TH-05 | Constitution 可維護性 > 70% | 2-4 |
| TH-06 | Constitution 測試覆蓋率 > 80% | 3-4 |
| TH-07 | 邏輯正確性 ≥ 90 | 5-8 |
| TH-08 | AgentEvaluator 標準 ≥ 80 | 1-2 |
| TH-09 | AgentEvaluator 嚴格 ≥ 90 | 3-8 |
| TH-10 | pytest = 100% | 3-8 |
| TH-11 | 覆蓋率 ≥ 70% | 3 |
| TH-12 | 覆蓋率 ≥ 80% | 4-8 |
| TH-14 | 規格完整性 ≥ 90% | 1 |
| TH-15 | Phase Truth ≥ 70% | 1-8 |
| TH-16 | 代碼↔SAD = 100% | 3 |
| TH-17 | FR↔測試 ≥ 90% | 4 |

---

## 15. 硬規則速查

| 規則 | 內容 | 後果 |
|------|------|------|
| HR-01 | A/B 必須不同 Agent，禁止自寫自審 | 終止 -25 |
| HR-02 | Quality Gate 必須有實際命令輸出 | 終止 -20 |
| HR-03 | Phase 必須順序執行，不可跳過 | 終止 -30 |
| HR-04 | HybridWorkflow mode=ON，強制 A/B | 終止 |
| HR-05 | 衝突時優先 methodology-v2 | 記錄 |
| HR-06 | 禁引入規格書外框架 | 終止 -20 |
| HR-07 | DEVELOPMENT_LOG 需記錄 session_id | -15 |
| HR-08 | Phase 結束必須執行 Quality Gate | 終止 -10 |
| HR-09 | Claims Verifier 驗證需通過 | 終止 -20 |
| HR-10 | sessions_spawn.log 需有 A/B 記錄 | 終止 -15 |
| HR-11 | Phase Truth < 70% 禁止進入下一 Phase | 終止 |
| HR-12 | A/B 審查 > 5 輪 → PAUSE | — |
| HR-13 | Phase 時間 > 3× 預估 → PAUSE | — |
| HR-14 | Integrity < 40 → FREEZE | — |
| HR-15 | citations 必須含行號 + artifact_verification | -15 |

---

## 16. Feedback Loop — 品質信號追蹤（v6.66+）

### 什麼是 Feedback Loop？

Feedback Loop 是**統一框架**，用於收集、分類、優先排序和追蹤所有來源的品質信號。

### 9 種 Feedback Sources

| Source | 說明 | 觸發時機 |
|--------|------|----------|
| `constitution` | Constitution HR-01~HR-15 違規 | Phase 轉換 |
| `quality_gate` | Linter/Complexity/Coverage 違規 | Phase 完成 |
| `linter` | 代碼風格錯誤 | On commit |
| `test_failure` | 測試失敗 | CI pipeline |
| `complexity_alert` | Cyclomatic Complexity 超標 | On commit |
| `drift_detector` | 架構 drift | Periodic |
| `bvs` | Behaviour Validation 違規 | Phase 完成 |
| `code_review` | Human review comments | PR review |
| `user_report` | End user reports | Manual |

### 5×5 Severity Matrix

```
              URGENCY
IMPACT    |  Low      |  Medium   |  High     |  Critical
----------|-----------|-----------|-----------|----------
  Low     |  Low      |  Low      |  Medium   |  High
  Medium  |  Low      |  Medium   |  Medium   |  High
  High    |  Medium   |  Medium   |  High     |  Critical
  Critical|  High     |  High     |  Critical |  Critical
```

### SLA 配置

| Severity | Response | Resolution | Escalation |
|----------|----------|------------|------------|
| Critical | 15 min | 4 hours | Immediate |
| High | 1 hour | 24 hours | 1 hour |
| Medium | 4 hours | 3 days | Daily |
| Low | 1 day | Next sprint | Weekly |

### Self-Correction 三層策略（v6.67+）

| Tier | 說明 | Confidence |
|------|------|------------|
| **Auto-Fix** | 8 種規則可直接 patch | 85%+ |
| **AI-Assisted** | 需要 AI 介入 + human review | 60-75% |
| **Manual-Required** | 必須人工處理 | — |

### Auto-Fix 規則（8 種）

| Strategy | Applies To | Confidence |
|----------|------------|------------|
| `patch_syntax` | Linter syntax errors | 95% |
| `isort_autofix` | Unused imports | 90% |
| `remove_unused` | Unused variables | 90% |
| `ruff_format` | PEP8 violations | 95% |
| `extract_function` | High cyclomatic complexity | 80% |
| `add_test_stub` | Coverage gaps | 70% |
| `regenerate_import` | Import errors in tests | 75% |
| `ai_fix_logic` | Complex logic errors | 70% |

### Integration Trigger Chain（v6.68+）

```
Constitution check 完成 → violations 自動進 FeedbackStore
QualityGate check 完成 → violations 自動進 FeedbackStore
BVS invariant 失敗 → 自動進 FeedbackStore
Verification 失敗 → Self-Correction Engine 自動觸發
```

### 使用方式

```python
# 一行建立完整 Feedback Loop 系統
from orchestration import create_full_pipeline

pipeline = create_full_pipeline()
store = pipeline["store"]      # FeedbackStore
gate = pipeline["gate"]        # Integrated AutoQualityGate
bvs = pipeline["bvs"]          # Integrated BVSRunner
closure = pipeline["closure"]  # ClosureWithSelfCorrection

# Dashboard
from core.feedback.dashboard import print_dashboard
print_dashboard(store)
```

---

## 17. 版本一致性

| Component | Version | Status |
|-----------|---------|--------|
| cli.py | v6.69.0 | ✅ |
| generate_full_plan.py | v6.39.0 | ✅ |
| SKILL.md | v6.32.0 | ⚠️ |
| JOHNNY_HANDBOOK.md | v6.69 | ✅ |
| Feedback Loop | v6.66 | ✅ |
| Self-Correction | v6.67 | ✅ |
| Integration Fix | v6.68 | ✅ |
| 執行計畫輸出 | v6.69.0 | ✅ |

> ⚠️ SKILL.md 版本落後（v6.32.0），建議在下次 release 時同步更新。

---

*此手冊基於 methodology-v2 v6.69*
*最後更新: 2026-04-07*
