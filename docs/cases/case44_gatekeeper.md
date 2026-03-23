# Case 44: Gatekeeper - 工作流程守門員

## 問題背景

在 AI Agent 執行複雜工作流程時，常見的問題是：
- 階段可以被跳過，導致品質不一致
- 沒有强制性的檢查點，問題在後期才暴露
- 無法追蹤每個階段的完成狀態
- 缺乏對 Gate 的統一管理機制

沒有 Gatekeeper 的情況下：
1. Agent 可能跳過 Constitution 直接進入開發
2. Specification 可能不完整就開始實作
3. 沒有充分測試就準備 Release
4. 問題在部署後才被發現

## 傳統方案

```python
# 傳統方式：簡單的標記
class OldWorkflow:
    def __init__(self):
        self.stages = ["constitution", "spec", "plan", "tasks", "verify", "release"]
        self.current = 0
    
    def next(self):
        # 沒有任何檢查，直接前進
        if self.current < len(self.stages):
            self.current += 1
    
    def can_skip(self):
        # 總是允許跳過
        return True
```

**痛點：**
- 沒有強制性的 Gate 檢查
- 可以隨意跳過任何階段
- 沒有狀態追蹤
- 沒有統一的審批流程

## AI-Native 方案

```python
from anti_shortcut.gatekeeper import Gatekeeper, Phase, GateStatus

# 初始化 Gatekeeper
gk = Gatekeeper()

# ========== 1. 查看狀態 ==========
gk.print_status()
# 輸出：
# ============================================================
# Gatekeeper 狀態報告
# ============================================================
# 當前階段: None
# 
# ⭕ CONSTITUTION: not_started
#    ⭕ con-1: Constitution 存在
#    ⭕ con-2: Constitution CLI 可執行
# ...

# ========== 2. 執行 Constitution 階段 ==========
gk.start_phase(Phase.CONSTITUTION)
# 檢查每個 Gate
for gate in gk.phase_records[Phase.CONSTITUTION].gates:
    status = gk.check_gate(gate.gate_id)
    print(f"{gate.name}: {status}")

# ========== 3. 嘗試跳過階段（會被阻擋） ==========
# 嘗試直接進入 Plan 階段
can_start = gk.start_phase(Phase.PLAN)
print(f"可以開始 Plan 階段: {can_start}")  # False - Constitution 未完成

# ========== 4. 完整的階段流程 ==========
def run_full_workflow():
    phases = [
        Phase.CONSTITUTION,
        Phase.SPECIFY,
        Phase.PLAN,
        Phase.TASKS,
        Phase.VERIFICATION,
        Phase.RELEASE
    ]
    
    for phase in phases:
        # 嘗試開始階段
        if not gk.start_phase(phase):
            blocked = gk.get_blocked_reason(phase)
            print(f"🚫 無法開始 {phase.value}: {blocked}")
            return False
        
        # 執行該階段的所有 Gates
        for gate in gk.phase_records[phase].gates:
            gk.check_gate(gate.gate_id)
        
        # 檢查是否可以進入下一階段
        if not gk.can_proceed_to_next_phase():
            print(f"❌ {phase.value} 階段未完成")
            return False
        
        print(f"✅ {phase.value} 階段完成")
    
    print("\n🎉 完整工作流程執行成功！")
    return True

# ========== 5. 狀態報告 ==========
report = gk.get_status_report()
print(f"當前階段: {report['current_phase']}")
for p in report['phases']:
    print(f"{p['phase']}: {p['status']}")
    for g in p['gates']:
        print(f"  - {g['id']}: {g['name']} ({g['status']})")
```

## 核心設計

### 階段定義

| 階段 | Gates |
|------|-------|
| Constitution | con-1: Constitution 存在, con-2: Constitution CLI 可執行 |
| Specify | spec-1: 需求規格存在, spec-2: 驗收標準定義 |
| Plan | plan-1: 架構設計完成, plan-2: 任務拆分完成 |
| Tasks | task-1: 每個任務有 ID, task-2: 任務有對應測試 |
| Verification | verify-1: Quality Gate 通過, verify-2: 安全掃描通過, verify-3: 覆蓋率達標 |
| Release | release-1: Approval 獲得, release-2: 版本號確認, release-3: 更新日誌完整 |

### Gate 狀態

- `NOT_STARTED`: 尚未開始
- `IN_PROGRESS`: 執行中
- `PASSED`: 已通過
- `FAILED`: 未通過
- `BLOCKED`: 被阻擋

### CLI 命令

```bash
# 查看狀態
methodology gatekeeper status

# 檢查所有 Gates
methodology gatekeeper check

# 强制執行 Constitution
methodology gatekeeper enforce
```

## 優勢

1. **强制檢查點**: 每個階段都必須完成才能進入下一階段
2. **不可跳過**: 沒有捷徑，確保流程完整性
3. **狀態透明**: 所有階段和 Gate 的狀態都可追蹤
4. **可扩展**: 可以自定義每個 Gate 的檢查函數
5. **審批整合**: Release 階段需要明確的 Approval

## 適用場景

- 複雜的多階段 AI Agent 工作流程
- 需要強制品質控制的專案
- 合規性要求嚴格的环境
- 需要明確交付標準的敏捷團隊
