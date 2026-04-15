# Johnny 使用手冊 v6.102

> **版本**: v6.102
> **對象**: Johnny（Human-in-the-Loop）
> **用途**: 快速上手 methodology-v2

---

## 1. methodology-v2 今天長什麼樣？

### v6.70 ~ v6.102 版本歷史

| 版本 | 改善內容 |
|------|----------|
| v6.70 | 完整 FR Execution Loop |
| v6.71-v6.81 | 多次 Bug 修復 |
| v6.86 | Phase 3 preflight/postflight 分離 |
| v6.87 | NameError 'runner' 修復 |
| v6.88 | FR A/B Review Loop 實作 |
| v6.89-v6.97 | 多次 review_status bug 修復 |
| v6.100 | Developer 返回 JSON，CLI 寫入磁碟 |
| v6.101 | Markdown JSON 解析 |
| v6.102 | **PhaseHooks 框架重構**（核心架構變更）|

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
Agent: 使用 sessions_spawn 直接派遣 sub-agent（依照 plan）
    ↓
Agent: 每步呼叫 PhaseHooks 監控
    ↓
Agent: run-phase --phase {N} --resume（POST-FLIGHT）
    ↓
失敗 → plan-phase --repair --step {N}.X
    ↓
成功 → 下一 Phase
```

---

## 3. 執行架構說明（v6.102 重要變更）

### ⚠️ sessions_spawn 無法直接 import

`sessions_spawn` 是 **OpenClaw runtime tool**，不是 Python module。

```python
# ❌ 錯誤：無法這樣 import
from openclaw import sessions_spawn  # ImportError!

# ✅ 正確：sessions_spawn 是 runtime tool，由 Agent 直接呼叫
```

### 新架構：Agent 呼叫 sessions_spawn，CLI 提供 PhaseHooks

```
┌─────────────────────────────────────────────────────────────┐
│ Agent（照 plan 執行）                                       │
│                                                             │
│ Agent: sessions_spawn(...) ← 直接呼叫（可做到）              │
└─────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ cli.py（變成「檢查/監控框架」）                              │
│                                                             │
│ • PRE-FLIGHT checks（FSM、Constitution、Tool Registry）      │
│ • PhaseHooks（監控每個 FR 執行）                            │
│ • POST-FLIGHT checks（Constitution、state 更新）            │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. plan-phase 用法

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

---

## 5. run-phase 用法（v6.102）

```bash
# 執行 Phase 3（含 PRE-FLIGHT checks）
python cli.py run-phase --phase 3

# 執行後恢復（跳過 PRE-FLIGHT，直接執行 POST-FLIGHT）
python cli.py run-phase --phase 3 --resume

# 指定 Step 和 Task
python cli.py run-phase --phase 3 --step 3.1 --task "FR-01 實作"
```

### --resume 用途

```bash
# 第一次執行：PRE-FLIGHT → Agent 執行 FRs → POST-FLIGHT
python cli.py run-phase --phase 3

# 如果中途中斷：可以用 --resume 跳過 PRE-FLIGHT，直接 POST-FLIGHT
python cli.py run-phase --phase 3 --resume
```

---

## 6. PhaseHooks 用法（v6.102 新增）

### 什麼是 PhaseHooks？

PhaseHooks 是獨立的監控框架，Agent 在執行 FR 時呼叫。

### 基本用法

```python
from phase_hooks import PhaseHooks

hooks = PhaseHooks("/path/to/project", phase=3)

# PRE-FLIGHT（一次性）
hooks.preflight_all()

# MONITORING（每個 FR 呼叫）
hooks.monitoring_before_dev("FR-01")
# ... Agent 執行 Developer ...
hooks.monitoring_after_dev("FR-01", dev_result)

hooks.monitoring_before_rev("FR-01")
# ... Agent 執行 Reviewer ...
hooks.monitoring_after_rev("FR-01", rev_result)

# HR-12 檢查
if not hooks.monitoring_hr12_check("FR-01", iteration=2):
    # HR-12 觸發，專案暫停
    pass

# POST-FLIGHT（最後呼叫）
hooks.postflight_all()
```

### 可用 Hooks

| Hook | 說明 |
|------|------|
| `preflight_all()` | 執行所有 PRE-FLIGHT 檢查 |
| `preflight_fsm_check()` | FSM 狀態檢查 |
| `preflight_constitution()` | Constitution 檢查 |
| `preflight_tool_registry()` | 工具註冊檢查 |
| `monitoring_before_dev(fr_id)` | Developer 執行前 |
| `monitoring_after_dev(fr_id, result)` | Developer 執行後 |
| `monitoring_before_rev(fr_id)` | Reviewer 執行前 |
| `monitoring_after_rev(fr_id, result)` | Reviewer 執行後 |
| `monitoring_hr12_check(fr_id, iteration)` | HR-12 審查次數檢查 |
| `postflight_all()` | 執行所有 POST-FLIGHT 檢查 |
| `postflight_constitution()` | Constitution 最終檢查 |
| `postflight_update_state(success)` | 更新 FSM 狀態 |
| `postflight_summary()` | 產出執行摘要 |

### CLI 直接呼叫 Hooks

```bash
python phase_hooks.py --project /path --phase 3 --hook preflight-all
python phase_hooks.py --project /path --phase 3 --hook postflight-all
```

---

## 7. plan-phase 自動做什麼

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
│  EXECUTE（由 Agent 直接執行）                                │
│                                                             │
│ 10. Agent: sessions_spawn 派遣 Developer/Reviewer         │
│ 11. Agent: 每步呼叫 PhaseHooks 監控                        │
│ 12. Agent: 解析 JSON 並寫入檔案（Developer 返回 files）     │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  POST-FLIGHT                                                 │
│ 13. Final Constitution Check                                │
│ 14. Update state.json                                       │
│ 15. Report Summary                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 8. FR 執行流程（v6.102）

### Agent 內部執行的 Workflow

```
1. Agent: PRE-FLIGHT checks（呼叫 PhaseHooks）

2. Agent: 派遣 Developer
   sessions_spawn(
       role="developer",
       task="實作 FR-01...",
       ...
   )
   
3. Developer: 讀取 SRS/SAD → 實作代碼
   返回: {"status": "success", "files": [{"path": "...", "content": "..."}]}

4. Agent: 解析 Developer 返回的 JSON
   寫入檔案到 repo_path/

5. Agent: 派遣 Reviewer
   sessions_spawn(
       role="reviewer", 
       task="審查 FR-01...",
       ...
   )

6. Reviewer: 審查代碼
   返回: {"status": "success", "review_status": "APPROVE"}

7. Agent: 呼叫 PhaseHooks 記錄結果
   hooks.monitoring_after_dev("FR-01", dev_result)
   hooks.monitoring_after_rev("FR-01", rev_result)

8. 重複 2-7 執行下一個 FR

9. Agent: POST-FLIGHT checks（呼叫 PhaseHooks）
```

### JSON 返回格式

**Developer 返回：**
```json
{
  "status": "success",
  "files": [
    {"path": "03-development/module_FR-01/main.py", "content": "# 完整代碼..."},
    {"path": "03-development/module_FR-01/utils.py", "content": "# 完整代碼..."}
  ],
  "confidence": 8,
  "citations": ["FR-01", "SRS.md#L23"],
  "summary": "FR-01 實作完成"
}
```

**Reviewer 返回：**
```json
{
  "status": "success",
  "review_status": "APPROVE",
  "reason": "代碼符合規格",
  "confidence": 9,
  "citations": ["FR-01", "SAD.md#L45"],
  "summary": "審查通過"
}
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
- 「sessions_spawn 為什麼無法從 cli.py import？」
- 「Pre-flight 有哪 5 個檢查？」
- 「HR-15 的 citations 格式規定是什麼？」
- 「Developer 返回的 JSON 格式包含哪些欄位？」
- 「PhaseHooks 的 monitoring_after_rev 用途？」

---

## 10. CLI 速查

```bash
# === run-phase（必用）===
python cli.py run-phase --phase N
python cli.py run-phase --phase N --resume    # 跳過 PRE-FLIGHT
python cli.py run-phase --phase N --step N.X --task "..."

# === plan-phase（必用，執行前）===
python cli.py plan-phase --phase N --goal "..."
python cli.py plan-phase --phase N --detailed --goal "..."
python cli.py plan-phase --phase N --repair --step N.X
python cli.py plan-phase --phase N --history

# === PhaseHooks CLI ===
python phase_hooks.py --project /path --phase N --hook preflight-all
python phase_hooks.py --project /path --phase N --hook postflight-all

# === Constitution Check ===
python cli.py constitution check --type <srs|sad|test_plan|all>
python cli.py constitution check --type all --check-mode preflight
python cli.py constitution check --type all --check-mode postflight

# === FSM 狀態 ===
python cli.py fsm-status
python cli.py fsm-transition --to PAUSED
python cli.py fsm-unfreeze

# === Feedback Loop Dashboard ===
python cli.py feedback --list
python cli.py feedback --dashboard

# === Integrity 計算 ===
python cli.py integrity --project .
```

---

## 11. Johnny 的三個狀態

```
🤚 等待中 - Agent 在執行 run-phase
👀 審核中 - Agent 完成，等 Johnny
✅/❌ 決策後 - CONFIRM 或 REJECT
```

---

## 12. 緊急情況

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

## 13. 關鍵閾值速查

| 閾值 | 數值 | Phase |
|------|------|-------|
| TH-01 | ASPICE 合規率 >80% | 1-8 |
| TH-02 | Constitution 總分 ≥80% | 5-8 |
| TH-03 | Constitution 正確性 =100% | 1-4 |
| TH-04 | Constitution 安全性 =100% | 1-4 |
| TH-05 | Constitution 可維護性 >90% | 2-4 |
| TH-06 | Constitution 測試覆蓋率 >90% | 3-4 |
| TH-07 | 邏輯正確性分數 ≥90 | 5-8 |
| TH-08 | AgentEvaluator 標準 ≥80 | 1-2 |
| TH-09 | AgentEvaluator 嚴格 ≥90 | 3-8 |
| TH-10 | 測試通過率 =100% | 3-8 |
| TH-11 | 單元測試覆蓋率 ≥70% | 3 |
| TH-12 | 單元測試覆蓋率 ≥80% | 4-8 |
| TH-13 | SRS FR 覆蓋率 =100% | 4-8 |
| TH-14 | 規格完整性 =100% | 1 |
| TH-15 | Phase Truth ≥70% | 1-8 |
| TH-16 | 代碼↔SAD 映射率 =100% | 3 |
| TH-17 | FR↔測試映射率 ≥90% | 4 |

---

## 14. 硬規則速查

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

## 15. 版本一致性

| Component | Version | Status |
|-----------|---------|--------|
| cli.py | v6.102.0 | ✅ |
| phase_hooks.py | v6.102 | ✅ |
| SKILL.md | v6.102 | ✅ |
| JOHNNY_HANDBOOK.md | v6.102 | ✅ |
| CHANGELOG.md | v6.102 | ✅ |

---

*此手冊基於 methodology-v2 v6.102*
*最後更新: 2026-04-09*

---

## v7.x 更新（2026-04-11）

### 新增自動化功能（v6.61+）

| 功能 | 版本 | 觸發方式 | Phase |
|------|------|----------|-------|
| **BVS** | v6.62 | 自動（Constitution）| 3+ |
| **HR-09** | v6.63 | 自動（Constitution）| 3+ |
| **CQG** | v6.61 | 自動（Constitution）| 3+ |
| **SAB Drift** | P0-3 | 自動（Constitution）| 3+ |
| **FR↔Test** | - | 自動（Constitution）| 4 |

### Phase 門檻更新

| Phase | 項目 | 門檻 |
|-------|------|-------|
| 3 | 代碼↔SAD 映射率 | =100% (SAB Drift) |
| 3 | Linter | 0 errors (CQG) |
| 3 | Complexity | ≤15 (CQG) |
| 4 | FR↔測試映射率 | ≥90% |

### STAGE_PASS.md 章節更新（v7.14）

H2 主章節（7個）：
1. 階段目標達成
2. Agent A 自評
3. Agent B 審查
4. Phase Challenges & Resolutions
5. Johnny 介入（如有）
6. artifact_verification（HR-15）
7. SIGN-OFF

H3 子章節（10個）：
- Phase Completion Summary
- 5W1H 合規性檢查
- 發現的問題
- 交付物清單
- Agent A Confidence Summary
- 疑問清單
- 審查結論
- Agent B Confidence Summary
- Phase Summary (50字內)
- 附：實際工具結果

### 版本歷史

| 版本 | 日期 | 內容 |
|------|------|------|
| v7.18 | 2026-04-11 | CQG + Phase 4 FR mapping |
| v7.17 | 2026-04-11 | SAB Drift Detection |
| v7.16 | 2026-04-11 | plan_phase SAB 說明 |
| v7.15 | 2026-04-11 | v6.61+ 自動化功能 |
| v7.14 | 2026-04-11 | STAGE_PASS 章節完整化 |
| v7.13 | 2026-04-11 | artifact_verification HR-15 |

*最後更新: 2026-04-11*
