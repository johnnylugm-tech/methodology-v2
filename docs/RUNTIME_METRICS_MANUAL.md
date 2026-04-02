# Runtime Metrics 操作手冊

> **版本**: v6.15.1  
> **日期**: 2026-04-02  
> **適用專案**: 所有使用 methodology-v2 的專案

---

## 1. 系統概覽

### 1.1 state.json 的角色

`.methodology/state.json` 是整個 methodology-v2 的**單一真相來源**（Single Source of Truth）。它記錄：

- `current_phase`: 目前正在執行的 Phase (1-8)
- `phase_state`: Phase 執行階段的運行時狀態
- `current_step` / `current_module` / `next_action`: 目前工作進度
- `history`: Phase 執行歷史（BLOCK、AB_ROUND、PHASE_START 等事件）

```json
{
  "current_phase": 3,
  "current_step": 3,
  "current_module": "代碼實作",
  "next_action": "Phase 3 APPROVE",
  "phase_state": {
    "status": "RUNNING",
    "started_at": "2026-04-02T10:00:00Z",
    "blocks": 0,
    "ab_rounds": 1,
    "integrity_score": 100,
    "warnings": 0
  },
  "phase_history": [
    {"phase": 1, "status": "COMPLETED", "duration_min": 45},
    {"phase": 2, "status": "COMPLETED", "duration_min": 60}
  ],
  "domain": "generic",
  "project_root": "/path/to/project",
  "started_at": "2026-04-01"
}
```

### 1.2 鉤子觸發時機

鉤子在 Phase SOP 執行過程中**自動觸發**，分為三類：

| 鉤子類型 | 觸發時機 | 影響 |
|---------|---------|------|
| `update-step` | 每個 Step 開始/完成時 | 更新 `current_step`、`current_module`、`next_action` |
| `end-phase` | Phase 完成，進入下一 Phase 前 | 呼叫 PHASE_END 重置 `phase_state`，遞增 `current_phase` |
| `update-project-status` | 需要更新 PROJECT_STATUS.md 時 | 更新「下一步動作」表格 |

### 1.3 工具鏟地圖

```
Phase 執行流程
│
├── Phase N 開始
│   └── update-step --step N --module "MODULE" --action "開始執行"
│
├── 每個交付物完成
│   └── update-step --step N --module "MODULE" --action "交付物名稱完成"
│
├── Quality Gate 通過
│   └── update-step --step N --module "MODULE" --action "Phase N APPROVE"
│
└── Phase N 結束
    └── end-phase --phase N
        │
        ├── PHASE_END hook 觸發
        ├── phase_state 重置
        └── current_phase → N+1
```

---

## 2. 專案初始化

每個新專案需要以下初始化步驟：

### 2.1 建立目錄結構

```bash
mkdir -p .methodology
mkdir -p .methodology/tasks
mkdir -p .methodology/sprints
```

### 2.2 初始化 state.json

state.json 的標準模板：

```json
{
  "current_phase": 1,
  "current_step": 1,
  "current_module": "SRS",
  "next_action": "開始撰寫 SRS.md",
  "phase_state": {
    "status": "RUNNING",
    "started_at": "2026-04-02T10:00:00Z",
    "blocks": 0,
    "ab_rounds": 0,
    "integrity_score": 100,
    "warnings": 0,
    "last_gate_score": null
  },
  "phase_history": [],
  "domain": "generic",
  "project_root": "/absolute/path/to/project",
  "started_at": "2026-04-02",
  "trend_alerts": []
}
```

### 2.3 快速初始化命令

```bash
# 在專案根目錄執行
python /path/to/methodology-v2/cli.py init "專案名稱"
```

---

## 3. Phase 執行時的鉤子呼叫

### 3.1 Phase 1-8 具體指令速查

| Phase | Step 開始 | Step 完成（每次交付物） | Phase 結束 |
|-------|-----------|----------------------|------------|
| 1 | `--step 1 --module SRS --action "開始撰寫"` | `--step 1 --module SRS --action "SRS.md 完成"` | `--step 1 --module SRS --action "Phase 1 APPROVE"` + `end-phase --phase 1` |
| 2 | `--step 2 --module SAD --action "開始設計"` | `--step 2 --module SAD --action "SAD.md 完成"` | `--step 2 --module SAD --action "Phase 2 APPROVE"` + `end-phase --phase 2` |
| 3 | `--step 3 --module 代碼實作 --action "開始實作"` | 每模組完成時呼叫 | `--step 3 --module 代碼實作 --action "Phase 3 APPROVE"` + `end-phase --phase 3` |
| 4 | `--step 4 --module 測試 --action "開始測試"` | 每測試項完成時呼叫 | `--step 4 --module 測試 --action "Phase 4 APPROVE"` + `end-phase --phase 4` |
| 5 | `--step 5 --module 驗證交付 --action "開始交付"` | 每交付物完成時呼叫 | `--step 5 --module 驗證交付 --action "Phase 5 APPROVE"` + `end-phase --phase 5` |
| 6 | `--step 6 --module 品質保證 --action "開始品質確認"` | 每檢查項完成時呼叫 | `--step 6 --module 品質保證 --action "Phase 6 APPROVE"` + `end-phase --phase 6` |
| 7 | `--step 7 --module 風險管理 --action "開始風險識別"` | 每風險關閉時呼叫 | `--step 7 --module 風險管理 --action "Phase 7 APPROVE"` + `end-phase --phase 7` |
| 8 | `--step 8 --module 配置管理 --action "開始配置管理"` | 每配置項完成時呼叫 | `--step 8 --module 配置管理 --action "Phase 8 APPROVE"` + `end-phase --phase 8` |

### 3.2 SKILL.md Phase SOP 中的鉤子位置

每個 Phase 的 SOP 末尾（STAGE_PASS 生成之後，EXIT 之前）都包含鉤子指令。例如 Phase 1：

```markdown
6. 生成 Phase1_STAGE_PASS.md

6. 更新狀態追蹤
```bash
python cli.py update-step --step 1 --module "SRS" --action "Phase 1 APPROVE"
python cli.py end-phase --phase 1
```
```

---

## 4. CLI 工具參考

### 4.1 model-recommend

根據 Phase 推薦最適合的 AI 模型。

**功能**：根據 Phase 推薦模型  
**用法**：
```bash
python cli.py model-recommend --phase N --repo /path/to/project
```

**輸出格式**：
```
╔══════════════════════════════════════════════════════════════╗
║  Phase N → Model 推薦                                     ║
╠══════════════════════════════════════════════════════════════╣
║  Model:        anthropic/claude-sonnet-4-20250514           ║
║  Provider:     anthropic                                    ║
║  Est. Cost:    $0.0035                                      ║
╠══════════════════════════════════════════════════════════════╣
║  Reasoning: 適合 Phase N 的複雜度與速度平衡                 ║
╚══════════════════════════════════════════════════════════════╝
```

**範例**：
```bash
python cli.py model-recommend --phase 3 --repo .
# 輸出 Phase 3 代碼實作推薦模型
```

---

### 4.2 update-step

更新 `current_step`、`current_module`、`next_action` 三個欄位。

**功能**：更新目前工作進度狀態  
**用法**：
```bash
python cli.py update-step --step X --module "MODULE_NAME" --action "ACTION_DESCRIPTION" --repo /path/to/project
```

**參數說明**：

| 參數 | 必填 | 說明 |
|------|------|------|
| `--step` | ✅ | Step 編號 (1-8，對應 Phase) |
| `--module` | ✅ | 模組名稱（英文或中文） |
| `--action` | ✅ | 當前動作描述 |
| `--repo` | ❌ | 專案路徑，預設 `.` |

**範例**：
```bash
# 開始 Phase 1
python cli.py update-step --step 1 --module "SRS" --action "開始撰寫 SRS.md"

# 完成 SRS.md 交付物
python cli.py update-step --step 1 --module "SRS" --action "SRS.md 完成"

# Phase 1 結束
python cli.py update-step --step 1 --module "SRS" --action "Phase 1 APPROVE"

# 開始 Phase 2
python cli.py update-step --step 2 --module "SAD" --action "開始 SAD.md 設計"
```

**對 state.json 的影響**：
```json
{
  "current_step": 1,
  "current_module": "SRS",
  "next_action": "Phase 1 APPROVE"
}
```

---

### 4.3 end-phase

觸發 PHASE_END hook，重置 `phase_state`，並遞增 `current_phase`。

**功能**：Phase 結束，進入下一 Phase  
**用法**：
```bash
python cli.py end-phase --phase N --repo /path/to/project
```

**參數說明**：

| 參數 | 必填 | 說明 |
|------|------|------|
| `--phase` | ✅ | Phase 編號 (1-8) |
| `--repo` | ❌ | 專案路徑，預設 `.` |

**PHASE_END Hook 執行的操作**：
1. 記錄 Phase 完成時間到 `phase_history`
2. 重置 `phase_state`（blocks、ab_rounds、warnings 歸零）
3. 遞增 `current_phase` 至 N+1
4. 重置 `phase_state.status` 為 `RUNNING`
5. 更新 `started_at` 為當前時間

**範例**：
```bash
# Phase 1 完成，進入 Phase 2
python cli.py end-phase --phase 1 --repo .

# Phase 3 完成，進入 Phase 4
python cli.py end-phase --phase 3 --repo .
```

**執行後 state.json 變化**：
```json
{
  "current_phase": 2,
  "phase_state": {
    "status": "RUNNING",
    "started_at": "2026-04-02T11:00:00Z",
    "blocks": 0,
    "ab_rounds": 0,
    "integrity_score": 100,
    "warnings": 0
  },
  "phase_history": [
    {"phase": 1, "status": "COMPLETED", "duration_min": 45}
  ]
}
```

---

### 4.4 update-project-status

更新 `PROJECT_STATUS.md` 中的「下一步動作」區塊。

**功能**：更新 PROJECT_STATUS.md 的「下一步動作」  
**用法**：
```bash
python cli.py update-project-status --step X --module Y --action "ACTION" --repo /path
```

**參數說明**：

| 參數 | 必填 | 說明 |
|------|------|------|
| `--step` | ✅ | Step 名稱（如 `4.1`） |
| `--module` | ✅ | 模組名稱 |
| `--action` | ✅ | 動作描述 |
| `--status` | ❌ | 狀態（`pending`/`in-progress`/`completed`），預設 `in-progress` |
| `--repo` | ❌ | 專案路徑，預設 `.` |

**範例**：
```bash
# 更新下一步動作
python cli.py update-project-status --step 4.1 --module "SynthEngine" --action "完成 TC 追蹤"

# 標記為已完成
python cli.py update-project-status --step 3.2 --module "代碼實作" --action "Module A 完成" --status completed
```

---

## 5. 快速參考

### 5.1 初始化新專案

```bash
# 建立目錄結構
mkdir -p .methodology

# 初始化專案
python /path/to/methodology-v2/cli.py init "my-project"

# 確認 state.json 已建立
cat .methodology/state.json
```

### 5.2 查看目前狀態

```bash
# 查看 Phase 執行狀態
python cli.py phase-status --phase 1

# 模型推薦
python cli.py model-recommend --repo .

# 查看 A/B 歷史
python cli.py ab-history --phase 1
```

### 5.3 Phase 執行鉤子序列（完整範例）

```bash
# ===== Phase 1 執行序列 =====

# 1. 開始 Phase 1
python cli.py update-step --step 1 --module "SRS" --action "開始撰寫 SRS.md"

# 2. 完成 SRS.md
python cli.py update-step --step 1 --module "SRS" --action "SRS.md 完成"

# 3. 完成 SPEC_TRACKING.md
python cli.py update-step --step 1 --module "SRS" --action "SPEC_TRACKING.md 完成"

# 4. 完成 TRACEABILITY_MATRIX.md
python cli.py update-step --step 1 --module "SRS" --action "TRACEABILITY_MATRIX.md 完成"

# 5. Agent B 審查完成
python cli.py update-step --step 1 --module "SRS" --action "Agent B 審查 APPROVE"

# 6. Phase 1 結束 → Phase 2 開始
python cli.py update-step --step 1 --module "SRS" --action "Phase 1 APPROVE"
python cli.py end-phase --phase 1

# ===== Phase 2 執行序列 =====

python cli.py update-step --step 2 --module "SAD" --action "開始 SAD.md 設計"
# ... 中間步驟 ...
python cli.py update-step --step 2 --module "SAD" --action "Phase 2 APPROVE"
python cli.py end-phase --phase 2

# ===== Phase 3 執行序列 =====

python cli.py update-step --step 3 --module "代碼實作" --action "開始代碼實作"
# ... 每模組完成時 ...
python cli.py update-step --step 3 --module "代碼實作" --action "Phase 3 APPROVE"
python cli.py end-phase --phase 3
```

### 5.4 單行命令速查

```bash
# 開始新 Step
python cli.py update-step --step 1 --module "SRS" --action "開始撰寫"

# Step 完成
python cli.py update-step --step 1 --module "SRS" --action "完成草稿"

# Phase 完成
python cli.py end-phase --phase 1

# 查看狀態
python cli.py phase-status --phase 1

# 模型推薦
python cli.py model-recommend --repo .
```

---

## 6. 故障排除

### 6.1 state.json 找不到

**症狀**：
```
❌ state.json not found. Phase N may not have started yet.
```

**原因**：`.methodology/state.json` 不存在或路徑錯誤

**解決方式**：
```bash
# 檢查目錄是否存在
ls -la .methodology/

# 如果不存在，建立並初始化
mkdir -p .methodology
python cli.py init "專案名"

# 或手動建立 state.json
echo '{"current_phase": 1, ...}' > .methodology/state.json
```

### 6.2 鉤子沒反應

**症狀**：`update-step` 或 `end-phase` 執行後 state.json 沒有更新

**原因**：可能在錯誤的目錄執行

**解決方式**：
```bash
# 確認當前目錄是專案根目錄
pwd
cd /path/to/your/project

# 使用絕對路徑
python /path/to/methodology-v2/cli.py update-step --step 1 --module "SRS" --action "test" --repo /path/to/your/project

# 確認 state.json 權限
ls -la .methodology/state.json
chmod 644 .methodology/state.json
```

### 6.3 Phase 狀態異常（RUNNING/PAUSE/FREEZE）

**症狀**：`phase_state.status` 不是 `RUNNING`

**解決方式**：

```bash
# 查看當前狀態
python cli.py phase-status --phase 3

# 如果是 PAUSE（暫停），恢復執行
python cli.py phase-resume --phase 3

# 如果是 FREEZE（凍結，需要審計後才能恢復）
# 先確認 HR-14 條件已修復
python cli.py phase-unfreeze --phase 3  # 需要管理員權限
```

### 6.4 PHASE_END hook 未觸發

**症狀**：`current_phase` 沒有遞增

**原因**：`end-phase` 命令執行失敗或被阻擋

**解決方式**：
```bash
# 直接編輯 state.json（最後手段）
# 確保 current_phase 正確
# 確保 phase_history 包含當前 Phase 記錄

# 然後手動重置 phase_state
```

### 6.5 Invalid phase number

**症狀**：`error: argument --phase: invalid int value`

**原因**：Phase 編號必須是 1-8 的整數

**解決方式**：
```bash
# 確認 phase 參數是數字
python cli.py end-phase --phase 1 --repo .

# 不要用變數拼接（容易出錯）
PHASE_NUM=1
python cli.py end-phase --phase $PHASE_NUM --repo .  # 可能失敗

# 正確做法
python cli.py end-phase --phase 1 --repo .
```

---

## 7. 附錄：state.json 欄位說明

| 欄位 | 類型 | 說明 |
|------|------|------|
| `current_phase` | int | 目前 Phase (1-8) |
| `current_step` | int | 目前 Step 編號 |
| `current_module` | string | 目前模組名稱 |
| `next_action` | string | 下一步動作描述 |
| `phase_state.status` | string | RUNNING / PAUSE / FREEZE / COMPLETED |
| `phase_state.started_at` | ISO8601 | Phase 開始時間 |
| `phase_state.blocks` | int | BLOCK 次數 |
| `phase_state.ab_rounds` | int | A/B 來回次數 |
| `phase_state.integrity_score` | int | 誠信分數 (0-100) |
| `phase_state.warnings` | int | 警告次數 |
| `phase_state.last_gate_score` | float | 最後 Quality Gate 分數 |
| `phase_history` | array | Phase 完成歷史 |
| `domain` | string | 專案領域 |
| `project_root` | string | 專案根目錄 |
| `started_at` | ISO8601 | 專案開始時間 |
| `trend_alerts` | array | 趨勢警報 |

---

*最後更新：2026-04-02 | methodology-v2 v6.15.1*
