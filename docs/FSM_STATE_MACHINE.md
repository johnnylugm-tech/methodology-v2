# FSM 狀態機手冊

## 概述

FSM (Finite State Machine) 狀態機將 HR-12/13/14 煞車系統從簡單的 PAUSE 升級為完整的狀態管理系統。

## 狀態定義

| 狀態 | 說明 |
|------|------|
| INIT | 專案/Phase 初始化 |
| RUNNING | 正常執行中 |
| VERIFYING | A/B 審查中 |
| WRITING | 回修產出中 |
| PAUSED | 煞車暫停（HR-12/13 觸發）|
| FREEZE | 凍住（HR-14 或嚴重問題）|
| COMPLETED | Phase 完成 |

## 狀態切換圖

```
INIT ──→ RUNNING
   ↑        │
   │        ├──→ VERIFYING ──→ WRITING
   │        │         ↑
   │        │         │
   │        └──←──────┘
   │        │
   │        ├──→ PAUSED ──→ RUNNING（解除）
   │        │         ↑
   │        │         │
   │        └──←──────┘
   │        │
   │        └──→ FREEZE ──→ INIT（重置）
   │        │
   └──────────── COMPLETED
```

## 允許的狀態切換

| 來源狀態 | 允許的目標狀態 |
|----------|----------------|
| INIT | RUNNING |
| RUNNING | VERIFYING, PAUSED, COMPLETED |
| VERIFYING | WRITING, RUNNING |
| WRITING | VERIFYING, PAUSED |
| PAUSED | RUNNING, FREEZE |
| FREEZE | INIT |
| COMPLETED | INIT |

## HR-12/13/14 觸發行為

| 規則 | 觸發條件 | 狀態切換 |
|------|---------|---------|
| HR-12 | A/B 審查 > 5 輪 | RUNNING → PAUSED |
| HR-13 | Phase 時間 > 3× 預估 | RUNNING → PAUSED |
| HR-14 | Integrity < 40 | RUNNING → FREEZE |

## CLI 命令

### 查看當前狀態

```bash
python cli.py fsm-status --repo .
```

輸出範例：
```
╔══════════════════════════════════════════════════════════════╗
║  FSM State Machine Status                                     ║
╠══════════════════════════════════════════════════════════════╣
║  Current State: RUNNING                                      ║
╠══════════════════════════════════════════════════════════════╣
║  State History (last 5):                                     ║
║    INIT → RUNNING (2026-04-03T12:00:00)                        ║
║      Reason: Phase started                                     ║
╚══════════════════════════════════════════════════════════════╝
```

### 手動觸發狀態切換

```bash
# 手動暫停
python cli.py fsm-transition --to PAUSED --reason "手動暫停" --repo .

# 開始審查
python cli.py fsm-transition --to VERIFYING --reason "開始 A/B 審查" --repo .

# 審查不通過，回修
python cli.py fsm-transition --to WRITING --reason "審查不通過" --repo .
```

### 解除煞車

```bash
python cli.py fsm-resume --repo .
```

### 解除凍住（需審計後）

```bash
python cli.py fsm-unfreeze --repo .
```

## API 使用方式

### Python API

```python
from quality_gate.unified_gate import FSMStateMachine, ProjectState
from pathlib import Path

# 初始化
repo_path = Path("/path/to/project")
fsm = FSMStateMachine(project_path=repo_path)

# 查詢狀態
current = fsm.get_state()
print(f"Current state: {current.value}")

# 開始 Phase
fsm.start_phase()  # INIT → RUNNING

# 開始審查
fsm.start_verification()  # RUNNING → VERIFYING

# 審查不通過
fsm.verification_fail()  # VERIFYING → WRITING

# 完成回修
fsm.verification_pass()  # VERIFYING → RUNNING

# 觸發煞車（HR-12/13）
fsm.trigger_brake("HR-12", "A/B 審查超過 5 輪")

# 觸發凍住（HR-14）
fsm.trigger_brake("HR-14", "Integrity < 40")

# 解除煞車
fsm.resume()  # PAUSED → RUNNING

# 解除凍住
fsm.unfreeze()  # FREEZE → INIT

# 手動狀態切換
fsm.transition(ProjectState.RUNNING, ProjectState.PAUSED, "Manual pause")

# 重置 Phase
fsm.reset_phase()  # 任意 → INIT
```

## state.json 結構

FSM 會在 `state.json` 中記錄以下欄位：

```json
{
  "status": "RUNNING",
  "state_history": [
    {
      "from": "INIT",
      "to": "RUNNING",
      "reason": "Phase started",
      "timestamp": "2026-04-03T12:00:00+00:00"
    }
  ]
}
```

## 與 PhaseEnforcer 整合

FSM 狀態機會在以下時機被觸發：

1. **HR-12 觸發**：當 A/B 審查來回超過 5 輪時
2. **HR-13 觸發**：當 Phase 時間超過 3× 預估時
3. **HR-14 觸發**：當 Integrity Score < 40 時
4. **Phase 開始**：INIT → RUNNING
5. **審查開始**：RUNNING → VERIFYING
6. **審查通過**：VERIFYING → RUNNING
7. **審查不通過**：VERIFYING → WRITING
8. **Phase 完成**：RUNNING → COMPLETED
9. **Phase 重置**：任意 → INIT
