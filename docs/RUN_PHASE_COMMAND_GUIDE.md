# `python cli.py run-phase --phase 3` 完整說明

> **版本**: v6.49
> **命令**: `python cli.py run-phase --phase {N} [OPTIONS]`

---

## 指令格式

```bash
python cli.py run-phase --phase 3
python cli.py run-phase --phase 3 --step 3.1
python cli.py run-phase --phase 3 --task "Custom task description"
python cli.py run-phase --phase 3 --repo /path/to/project
python cli.py run-phase --phase 3 --step 3.1 --task "..." --repo "..."
```

---

## 完整流程圖

```
┌─────────────────────────────────────────────────────────┐
│  PRE-FLIGHT CHECKS (6 步)                              │
│  ┌─────────────────────────────────────────────────┐   │
│  1. FSM State Check     → FREEZE/PAUSED → STOP     │   │
│  2. Phase Sequence      → 已完成 → STOP             │   │
│  3. Constitution Check  → <80% → STOP               │   │
│  4. Tool Registry       → Warning (可繼續)          │   │
│  5. Session Save        → Pre-flight 快照            │   │
│  6. SubagentIsolator   → HR-10/12/13/14 驗證       │   │
│  └─────────────────────────────────────────────────┘   │
│                          ↓ 全部通過                    │
│  ┌─────────────────────────────────────────────────┐   │
│  EXECUTE Phase {N}                                    │   │
│  - 讀取 P{N}_SOP.md                                  │   │
│  - 執行步驟（--step 控制）                           │   │
│  - Sub-agent 派遣（若需要）                          │   │
│  └─────────────────────────────────────────────────┘   │
│                          ↓                            │
│  ┌─────────────────────────────────────────────────┐   │
│  POST-FLIGHT (2 步)                                  │   │
│  1. Final Constitution Check                         │   │
│  2. Update state.json                               │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## 參數說明

### `--phase` (必填)

| 參數 | 說明 |
|------|------|
| `--phase 1` | 需求規格 |
| `--phase 2` | 架構設計 |
| `--phase 3` | 代碼實現 |
| `--phase 4` | 測試規劃 |
| `--phase 5` | 驗證交付 |
| `--phase 6` | 品質保證 |
| `--phase 7` | 風險管理 |
| `--phase 8` | 配置管理 |

---

## 選項說明

### `--step` (可選)

**用途**: 指定從哪個 Step 開始執行

| 執行方式 | 行為 |
|---------|------|
| **沒有 `--step`** | 從 Step 1 開始執行整個 Phase |
| **`--step 3.1`** | 從 Phase 3, Step 1 開始執行 |
| **`--step 3.5`** | 從 Phase 3, Step 5 開始執行 |

**具體差別**:

```bash
# 沒有 --step：執行全部步驟
python cli.py run-phase --phase 3
# 輸出：
# 📍 Executing step: 1
# 📍 Executing step: 2
# 📍 Executing step: 3
# ... (所有步驟)

# 有 --step：只執行指定步驟
python cli.py run-phase --phase 3 --step 3.2
# 輸出：
# 📍 Executing step: 3.2
# (只執行 step 3.2)
```

---

### `--task` (可選)

**用途**: 覆蓋預設的任務描述

| 執行方式 | 行為 |
|---------|------|
| **沒有 `--task`** | 任務描述為 "Phase {N} execution" |
| **`--task "..."`** | 使用自定義描述 |

**具體差別**:

```bash
# 沒有 --task：使用預設描述
python cli.py run-phase --phase 3
# 📌 Task: Phase 3 execution

# 有 --task：使用自定義描述
python cli.py run-phase --phase 3 --task "Implement FR-01 to FR-08"
# 📌 Task: Implement FR-01 to FR-08
```

**用途場景**:
- 當你只想執行特定任務時
- 恢復中斷的執行時說明目的
- 與 `--step` 配合使用

---

### `--repo` (可選)

**用途**: 指定專案路徑（預設為當前目錄）

| 執行方式 | 行為 |
|---------|------|
| **沒有 `--repo`** | 使用當前目錄 `.` |
| **`--repo /path`** | 使用指定路徑 |

**具體差別**:

```bash
# 沒有 --repo：使用當前目錄
python cli.py run-phase --phase 3
# 🚀 run-phase --phase 3
# Repo: /Users/johnny/.openclaw/workspace-musk/skills/tts-kokoro-v613

# 有 --repo：使用指定路徑
python cli.py run-phase --phase 3 --repo /path/to/other/project
# 🚀 run-phase --phase 3
# Repo: /path/to/other/project
```

---

## Pre-Flight Check 詳細說明

### 1. FSM State Check

| 當前狀態 | 行為 |
|---------|------|
| **RUNNING** | ✅ 繼續執行 |
| **PAUSED** | ⚠️ 停止，提示使用 `fsm-resume` |
| **FREEZE** | ❌ 停止，提示使用 `fsm-unfreeze` |

**沒有這個檢查**:
- Agent 可能在不安全的狀態執行
- 可能覆蓋已完成的 Phase

### 2. Phase Sequence Check

| 情況 | 行為 |
|------|------|
| **current_phase < target** | ✅ 繼續執行 |
| **current_phase >= target** | ⚠️ 警告，可使用 `--step` 繼續 |

**沒有這個檢查**:
- 可能重新執行已完成的 Phase
- 覆蓋現有產出

### 3. Constitution Check

| 分數 | 行為 |
|------|------|
| **≥ 80%** | ✅ 繼續執行 |
| **< 80%** | ❌ 停止，列出 violations |

**輸出範例**:
```
❌ Constitution score 65% < 80% (required)
   Violations: ['FR-01 描述模糊', '缺少介面規格']
   Recommendations: ['補充 FR-01 驗收標準', '新增 API 規格']
```

**沒有這個檢查**:
- 可能執行不符合品質標準的 Phase
- 違反 Constitution 規範

### 4. Tool Registry Check

| 情況 | 行為 |
|------|------|
| **有 tools** | ✅ 顯示已註冊工具數量 |
| **沒有 tools** | ⚠️ Warning（可繼續） |

**沒有這個檢查**:
- Agent 可能使用未註冊的工具
- 違反 Tool Registry 規範

### 5. Session Save

| 功能 | 說明 |
|------|------|
| **快照內容** | phase, timestamp, constitution_score, tools_count, fsm_state |
| **保存位置** | `.methodology/sessions/{session_id}.json` |
| **用途** | 中斷後可恢復 |

**沒有這個檢查**:
- 中斷後無法精確恢復
- 失去執行歷史

### 6. SubagentIsolator Hooks

| HR 規則 | 驗證內容 |
|---------|---------|
| **HR-10** | sessions_spawn.log 格式正確 |
| **HR-12** | A/B 審查 > 5 輪 → PAUSE 通知 |
| **HR-13** | Phase 執行 > 預估 ×3 → PAUSE checkpoint |
| **HR-14** | Integrity < 40% → FREEZE |

**沒有這個檢查**:
- HR-12/13/14 不會自動觸發
- Sub-agent 可能不被正確隔離

---

## 組合使用範例

### 範例 1: 基本執行

```bash
python cli.py run-phase --phase 3
```

**行為**:
- ✅ FSM State = RUNNING
- ✅ Pre-flight 全部檢查
- ✅ 執行 Phase 3 全部步驟 (Step 1 → N)
- ✅ 任務描述 = "Phase 3 execution"
- ✅ 使用當前目錄

---

### 範例 2: 指定 Step + 自定義 Task

```bash
python cli.py run-phase --phase 3 --step 3.2 --task "Implement LexiconMapper"
```

**行為**:
- ✅ FSM State = RUNNING
- ✅ Pre-flight 全部檢查
- ✅ 只執行 Step 3.2
- ✅ 任務描述 = "Implement LexiconMapper"
- ✅ 使用當前目錄

**使用場景**:
- Step 3.1 完成後中斷
- 恢復時只想執行 3.2
- 明確說明下一步要做什麼

---

### 範例 3: 指定 Repo + 完整選項

```bash
python cli.py run-phase --phase 3 --step 3.5 --task "Final testing" --repo /path/to/project
```

**行為**:
- ✅ FSM State = RUNNING
- ✅ Pre-flight 全部檢查
- ✅ 只執行 Step 3.5
- ✅ 任務描述 = "Final testing"
- ✅ Repo = /path/to/project

---

## 輸出日誌

執行時會寫入 `.methodology/run-phase.log`:

```json
{"timestamp": "2026-04-05T13:42:00", "phase": 3, "event": "EXECUTE_START", "message": "Phase 3 started - Implement FR-01 to FR-08", "duration_ms": null, "subagent_session": null}
{"timestamp": "2026-04-05T13:45:00", "phase": 3, "event": "STEP_COMPLETE", "message": "Step 3.1 completed", "duration_ms": 180000, "subagent_session": "sess_abc123"}
{"timestamp": "2026-04-05T13:50:00", "phase": 3, "event": "EXECUTE_END", "message": "Phase 3 completed", "duration_ms": 480000, "subagent_session": null}
```

---

## 錯誤處理

### FSM 狀態錯誤

```
❌ Project is FREEZE. Run 'fsm-unfreeze' first.
```

**解決**: `python cli.py fsm-unfreeze`

---

### Constitution 分數過低

```
❌ Constitution score 65% < 80% (required)
   Violations: ['FR-01 描述模糊', '缺少介面規格']
```

**解決**: 
1. 修正問題
2. `python cli.py constitution check --type implementation`
3. 重新執行 `run-phase`

---

### Phase 已完成

```
⚠️  Phase 3 has already been completed or is in progress.
    Current phase: 3, target: 3
    Use --step to continue from a specific step.
```

**解決**: 使用 `--step` 繼續執行

---

## 總結：選項組合對照表

| 命令 | Step | Task | Repo | 行為 |
|------|:----:|------|:----:|------|
| `--phase 3` | 全部 | "Phase 3 execution" | `.` | 完整執行 |
| `--phase 3 --step 3.1` | 3.1 | "Phase 3 execution" | `.` | 從頭開始 |
| `--phase 3 --step 3.5` | 3.5 | "Phase 3 execution" | `.` | 從 3.5 開始 |
| `--phase 3 --task "..."` | 全部 | 自定義 | `.` | 自定義描述 |
| `--phase 3 --repo /path` | 全部 | "Phase 3 execution" | /path | 指定專案 |
| `--phase 3 --step 3.2 --task "..." --repo /path` | 3.2 | 自定義 | /path | 全部自定義 |

---

*最後更新: 2026-04-05*
