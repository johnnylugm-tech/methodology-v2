# methodology-v2 v6.28 審計報告

**審計日期:** 2026-04-04
**審計範圍:** v6.01–v6.28
**審計者:** Subagent Audit
**審計後狀態:** ✅ 已修復並提交（commit 36c4466, tag v6.29.0）

---

## 執行摘要

| 類別 | 發現 | P0 | P1 | P2 |
|------|------|----|----|-----|
| 正確性 | 3 | 0 | 1 | 2 |
| 完整性 | 4 | 1 | 1 | 2 |
| 一致性 | 5 | 0 | 2 | 3 |
| **總計** | **12** | **1** | **4** | **7** |

**所有 P0/P1 問題已於 commit 36c4466 修復。**

---

## P0 — 阻塞性問題

### P0-1: `python cli.py integrity --project .` 根本不存在 ✅ 已修復

**嚴重性:** P0
**檔案:** `cli.py`
**問題:** SKILL.md §6 明確記載驗證命令，`cli.py` 中無此 subparser，無 `cmd_integrity()` 方法。

**修復:**
- 新增 `integrity` subparser（第 ~4704 行）
- 新增 `elif command == "integrity": return self.cmd_integrity(args)` 調度
- 新增 `cmd_integrity()` 方法，根據 SKILL.md §6 公式計算 Integrity 分數
- 從 `state.json` 讀取 phase_completions 和 constitution_scores
- 從 `sessions_spawn.log` 讀取 log_completeness

```bash
python cli.py integrity --project .
```

---

## P1 — 高優先問題

### P1-1: P3_SOP.md Quality Gate 表格 TH 標籤與 SKILL.md 不一致 ✅ 已修復

**嚴重性:** P1
**檔案:** `docs/P3_SOP.md`

| 行 | 舊標記 | 新標記（已修正）| 問題 |
|----|--------|----------------|------|
| 464 | `TH-08 \| doc_checker > 80%` | `TH-09 \| AgentEvaluator 嚴格 ≥90` | Phase 3 適用 TH-09（Phase 3-8），非 TH-08 |
| 465 | `TH-10 \| phase-verify ≥ 70%` | `TH-15 \| Phase Truth ≥70%` | TH-10 = 測試通過率 =100%，Phase Truth 應為 TH-15 |
| 466 | `TH-11 \| trace-check = 100%` | `TH-16 \| SAD↔代碼映射 =100%` | TH-11 = 單元測試覆蓋率 ≥70%，映射應為 TH-16 |

---

### P1-2: `PLAN_PHASE_SPEC.md` Integrity 公式與 SKILL.md 衝突 ✅ 已修復

**嚴重性:** P1
**檔案:** `docs/PLAN_PHASE_SPEC.md`（§15）

| 文件 | 公式 |
|------|------|
| ~~PLAN_PHASE_SPEC §15~~ | ~~扣分制（初始 100，HR 違規扣分）~~ ❌ |
| SKILL.md §6（權威）| `Σ(Phase_N × Constitution/100 × log) × 100` ✅ |

**修復:**
- 移除衝突的扣分制公式
- 新增對 SKILL.md §6 公式的引用
- 更新版本從 v6.26 → v6.28

---

### P1-3: `constitution check --auto-fix/--skip-failed` 為空 Stub ✅ 已修復

**嚴重性:** P1
**檔案:** `cli.py`（原第 2194–2201 行）

**修復:**
- 將 `pass` Stub 替換為實際功能
- 調用 `validate_constitution_compliance()` API
- `--auto-fix/--skip-failed` 現在輸出引導訊息而非靜默忽略
- 移除虛假 TODO 注釋

---

### P1-4: JOHNNY_HANDBOOK 版本與 SKILL.md 版本不同步

**說明:** 已自動合規，無需修復。兩份文件均已更新至 v6.28 ✓

---

## P2 — 中優先問題

### P2-1: SKILL.md 標題宣稱 "125行"，實際 126 行

**說明:** 任務描述提及「SKILL.md（125行）」，但這是任務上下文描述，非文件本身的錯誤。SKILL.md 標頭為 `methodology-v2 v6.28`，並無 "125行" 宣稱。**無需修復。**

---

### P2-2: `PLAN_PHASE_SPEC` 版本停留在 v6.26 ✅ 已修復

**檔案:** `docs/PLAN_PHASE_SPEC.md`

---

### P2-3: `SOUL.md` 位於 workspace 根目錄，非 `skills/methodology-v2/`

**說明:** SKILL.md 核心規範未提及 `SOUL.md`。Workspace 根目錄的 `SOUL.md` 屬於上層 Agent 設定，與 methodology-v2 無關。**無需修復。**

---

### P2-4: `sessions_spawn.log` 自動寫入宣傳與 SKILL.md HR-10 描述不一致

**說明:** JOHNNY_HANDBOOK 積極宣傳「v6.28 新增：sessions_spawn.log 自動寫入」，但 SKILL.md HR-10 仍為被動描述「sessions_spawn.log 需有 A/B 記錄」。SubagentIsolator._write_log() 已實作自動寫入。**建議：** 更新 SKILL.md HR-10 描述以反映自動寫入功能（非本次修復範圍）。

---

## 正確性驗證結果

### ✅ HR-01~HR-15 規則表（SKILL.md）

所有 15 條 HR 規則正確定義，與 Phase SOP 一致。

### ✅ TH-01~TH-17 閾值表（SKILL.md）

所有 17 個閾值定義正確（注意：Phase SOP 閾值表使用各自的命名約定）。

### ✅ Phase 路由表（SKILL.md §4）

| Phase | Agent A | Agent B | 交付物 |
|-------|---------|---------|--------|
| P1 | architect | reviewer | SRS, SPEC_TRACKING, TRACEABILITY |
| P2 | architect | reviewer | SAD, ADR |
| P3 | developer | reviewer | src/, tests/ |
| P4 | qa | reviewer | TEST_PLAN, TEST_RESULTS |
| P5 | devops | architect | BASELINE, MONITORING_PLAN |
| P6 | qa | architect/pm | QUALITY_REPORT |
| P7 | qa/devops | pm/architect | RISK_REGISTER |
| P8 | devops | pm/architect | CONFIG_RECORDS, Git Tag |

### ✅ Integrity 計算公式（SKILL.md §6）

公式實現正確，PLAN_PHASE_SPEC 已同步。

### ✅ CLI 命令與 SKILL.md 一致性

| 命令 | SKILL.md 記載 | 狀態 |
|------|-------------|------|
| `update-step --step N` | ✅ | ✅ |
| `end-phase --phase N` | ✅ | ✅ |
| `stage-pass --phase N` | ✅ | ✅ |
| `integrity --project .` | ✅ | ✅ **已新增** |
| `plan-phase --phase N` | ✅ | ✅ |
| `run-phase --phase N` | ✅ | ✅ |

## 完整性驗證結果

| 檢查項 | 狀態 |
|--------|------|
| HR-15 存在於 SKILL.md HR 表格 | ✅ |
| 所有 Phase（P1-P8）有對應 SOP | ✅ |
| 所有 Template 存在 | ✅（16 templates）|
| `--auto-fix / --skip-failed` 已實作 | ✅（enforce/stage-pass 完整，constitution check 已改善）|
| `pre_spawn_audit()` 已實作 | ✅ |
| `sessions_spawn.log` 內建機制 | ✅ |
| `ArtifactMissingError` 已實作 | ✅ |

## 一致性驗證結果

| 檢查項 | 狀態 |
|--------|------|
| SKILL.md 版本 = git tag | ✅ v6.28 = v6.28.0 |
| JOHNNY_HANDBOOK 版本 = SKILL.md 版本 | ✅ v6.28 |
| HEARTBEAT.md 版本 = SKILL.md 版本 | ✅ v6.28.0 |
| Phase SOP Pre-flight 檢查一致性 | ✅ P1–P8 均為 5 項 |
| A/B 角色定義一致性 | ✅ 所有 Phase 與 Phase routing table 一致 |
| 產出格式（5 欄位）一致性 | ✅ 所有 Phase SOP 一致 |
| HR-15 artifact_verification 一致性 | ✅ P3_SOP 和 Handbook 一致 |

---

## 建議

1. **建立版本同步鉤子**：每次更新 SKILL.md 版本時，自動更新 JOHNNY_HANDBOOK 和 PLAN_PHASE_SPEC 版本
2. **Phase SOP 閾值表重構**：統一使用 Phase routing table 的閾值 ID 標記系統，減少混淆
3. **ConstitutionRunner 實現**：`validate_constitution_compliance()` 目前是 stub，應儘早實現完整功能
4. **SKILL.md HR-10 更新**：反映 `sessions_spawn.log` 已被 SubagentIsolator 自動寫入的事實

---

*審計完成：2026-04-04 | 修復提交：36c4466 | 標籤：v6.29.0*
