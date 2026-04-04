# plan-phase 完整規格 v1.0

> 基於 SKILL.md v6.26 100% 落實

---

## 1. 概述

### 1.1 目的

`plan-phase` 是一個**自動化 Phase Planner**，在 Agent 執行每個 Phase 前，先掃描所有相關資料，產生一份 100% 符合 SKILL.md 的詳細執行計畫。

### 1.2 與 run-phase 的關係

```
plan-phase（生成計畫） → Johnny 審核 → run-phase（執行計畫）
                                    ↓
                              失敗 → plan-phase --repair（修復迭代）
```

---

## 2. 輸入掃描清單

### 2.1 必須掃描（無條件執行）

| 掃描項目 | 檔案 | 目的 |
|---------|------|------|
| **SKILL.md** | `./SKILL.md` | 核心規則、HR、TH |
| **Phase SOP** | `docs/P{N}_SOP.md` | Phase 詳細步驟 |
| **State** | `.methodology/state.json` | current_phase, FSM 狀態 |
| **Iterations** | `.methodology/iterations/{phase}.json` | 歷史失敗修復記錄 |

### 2.2 按 Phase 掃描

| Phase | 需掃描的交付物 |
|-------|--------------|
| P1 | SRS.md, SPEC_TRACKING.md, TRACEABILITY_MATRIX.md |
| P2 | SRS.md, SAD.md, ADR.md |
| P3 | SRS.md, SAD.md, `app/processing/*.py` |
| P4 | SRS.md, SAD.md, TEST_PLAN.md |
| P5 | BASELINE.md, MONITORING_PLAN.md |
| P6 | QUALITY_REPORT.md |
| P7 | RISK_REGISTER.md |
| P8 | CONFIG_RECORDS.md, pip freeze |

### 2.3 按需掃描（Lazy Load）

| 文檔 | 何時需要 | 目的 |
|------|---------|------|
| `docs/ANNOTATION_GUIDE.md` | Phase 3-4 | @FR/@covers annotation 規範 |
| `docs/HYBRID_WORKFLOW_GUIDE.md` | 任何 Phase | A/B 協作詳細協議 |
| `docs/VERIFIER_GUIDE.md` | Phase 3+ | Verify_Agent 觸發條件 |
| `docs/RUNTIME_METRICS_MANUAL.md` | 任何 Phase | HR-12/13 時間追蹤 |
| `docs/CONSTITUTION_GUIDE.md` | 任何 Phase | Constitution 規範 |
| `docs/COWORK_PROTOCOL_v1.0.md` | 任何 Phase | DEVELOPMENT_LOG 格式 |
| `docs/RISK_REGISTRY.md` | Phase 7 | 風險識別框架 |

---

## 3. Pre-flight 檢查清單

### 3.1 FSM 狀態檢查

```python
def check_fsm_state(phase: int) -> CheckResult:
    """HR-03: Phase 順序執行，不可跳過"""
    state = read_state_json()
    current_phase = state.get("current_phase", 0)
    fsm_state = state.get("fsm_state", "INIT")

    if fsm_state == "FREEZE":
        return CheckResult(passed=False, reason="HR-14: Project FREEZE")
    if fsm_state == "PAUSED":
        return CheckResult(passed=False, reason="HR-12/13: Project PAUSED")
    if current_phase >= phase:
        return CheckResult(passed=False, reason="HR-03: Phase 已執行或跳過")
    return CheckResult(passed=True)
```

### 3.2 Phase 特定進入條件檢查

| Phase | 進入條件 |
|-------|---------|
| P1 | SRS.md 存在且完整度 ≥90%（TH-14）|
| P2 | SRS.md 存在；TH-01 ASPICE >80% |
| P3 | SAD.md 存在；Phase 2 APPROVE |
| P4 | 代碼存在；Phase 3 APPROVE |
| P5 | TEST_RESULTS.md 存在；Phase 4 APPROVE |
| P6 | BASELINE.md 存在；Phase 5 APPROVE |
| P7 | QUALITY_REPORT.md 存在；Phase 6 APPROVE |
| P8 | 所有前置 Phase APPROVE；pip freeze 存在 |

### 3.3 Constitution 檢查

```python
def check_constitution(phase: int) -> CheckResult:
    """HR-08, HR-09"""
    phase_type_map = {
        1: "srs",
        2: "sad",
        3: "implementation",
        4: "test_plan",
        5: "verification",
        6: "quality_report",
        7: "risk_management",
        8: "configuration"
    }
    runner = ConstitutionRunner(project_path=".")
    result = runner.run_phase_check(phase_type_map[phase])

    # Phase-specific Constitution 門檻
    threshold_map = {
        1: 100,  # TH-03, TH-04 = 100%
        2: 100,  # TH-03, TH-04 = 100%
        3: 80,   # TH-06 >80%
        4: 80,
        5: 80,   # TH-02 ≥80%
        6: 80,
        7: 80,
        8: 80
    }

    if result.score < threshold_map[phase]:
        return CheckResult(passed=False, reason=f"HR-08: Constitution {result.score}% < {threshold_map[phase]}%")
    return CheckResult(passed=True, score=result.score)
```

### 3.4 Tool Registry 檢查

```python
def check_tool_registry() -> CheckResult:
    """確認關鍵工具已註冊"""
    from tool_registry import ToolRegistry
    tools = ToolRegistry.list_tools()

    required_tools = [
        "knowledge_curator",
        "context_manager",
        "subagent_isolator",
        "permission_guard",
        "tool_registry",
        "session_manager"
    ]

    missing = [t for t in required_tools if t not in tools]
    if missing:
        return CheckResult(passed=False, reason=f"缺少工具: {missing}")
    return CheckResult(passed=True, tools_count=len(tools))
```

### 3.5 Integrity 分數檢查（HR-14）

```python
def check_integrity() -> CheckResult:
    """HR-14: Integrity < 40 → FREEZE"""
    from agent_evaluator import AgentEvaluator
    evaluator = AgentEvaluator()
    score = evaluator.calculate_integrity()

    if score < 40:
        return CheckResult(passed=False, reason=f"HR-14: Integrity {score}% < 40% → FREEZE")
    return CheckResult(passed=True, score=score)
```

---

## 4. Step-by-Step 執行計畫輸出格式

### 4.1 完整格式

```markdown
# Phase {N} 執行計畫 v{version}

> 生成時間: {timestamp}
> 基於: SKILL.md v6.26
> FSM 狀態: {fsm_state}
> Phase Truth: {phase_truth_score}%

---

## 1. Pre-flight 檢查結果

| 檢查項 | 結果 | 備註 |
|--------|------|------|
| FSM State | ✅ PASS | HR-03 合規 |
| Phase Sequence | ✅ PASS | Phase {N-1} → Phase {N} |
| Constitution | ✅ {score}% | HR-08 合規 |
| Tool Registry | ✅ {count} tools | 全部就緒 |
| Integrity | ✅ {score}% | HR-14 合規 |
| Phase Entry | ✅ PASS | {entry_condition} |

---

## 2. A/B 協作宣告（HR-01, HR-04）

### Agent A: {role_A}
- **角色**: {architect|developer|qa|devops}
- **職責**: {根據 Phase}

### Agent B: {role_B}
- **角色**: {reviewer|architect}
- **職責**: {根據 Phase}

### 禁止事項（HR-01, HR-04）
- ❌ 自寫自審（HR-01）
- ❌ HybridWorkflow=OFF（HR-04）
- ❌ sessions_spawn.log 缺失（HR-10）
- ❌ 程式碼省略號`...`（任務失敗）
- ❌ `unable_to_proceed` 不說明原因（HR-05）
- ❌ 編造內容（HR-06）
- ❌ Subagent 繼承父 context（HR-05）

---

## 3. Step-by-Step 執行計畫

### Step {N}.1: {名稱}

| 項目 | 內容 |
|------|------|
| **目的** | {清晰描述} |
| **工具** | {工具名} |
| **命令** | `python cli.py {command}` |
| **Subagent** | {是/否}，角色: {role} |
| **驗證標準** | {TH-XX} = {value} |

**Prompt（若有 Subagent）：**
```
{完整的 Subagent Prompt，見 Section 5}
```

**風險評估**：
- 等級: {低/中/高}
- HR-13 時間風險: {有/無}
- HR-06 框架風險: {有/無}

**前置條件**：
- {前置 Step 完成}

**產出**：
- {交付物路徑}

---

### Step {N}.2: {名稱}
...（重複格式）

---

## 4. 閾值對照表（TH-01~TH-17）

| 閾值 | 門檻 | 本 Phase 目標 | 驗證方式 |
|------|------|-------------|---------|
| TH-01 | >80% | {target}% | ASPICE check |
| TH-03 | =100% | {target}% | Constitution |
| TH-04 | =100% | {target}% | Constitution |
| ... | ... | ... | ... |

---

## 5. HR-12/13 時間追蹤

### 預估時間

| Step | 預估 | Agent | 依據 |
|------|------|-------|------|
| {N}.1 | {X}m | Agent A | {依據} |
| {N}.2 | {Y}m | Agent A | {依據} |
| **總計** | {Z}m | — | — |

### HR-13 臨界值
- Phase 最大時間: {Z × 3}m
- 若超過: HR-13 觸發 → PAUSE

---

## 6. 迭代歷史（HR-12）

| Iteration | Step | 問題 | 修復方式 | 結果 |
|-----------|------|------|---------|------|
| #1 | {N}.2 | coverage 62% | 增加邊界測試 | ✅ |
| #2 | {N}.3 | timeout | 增加 retry | ❌ |

---

## 7. DEVELOPMENT_LOG 格式（HR-07）

每次 Step 完成後，必須寫入 `.methodology/development_log.md`：

```json
{
  "timestamp": "{ISO8601}",
  "session_id": "{uuid}",
  "phase": {N},
  "step": "{N}.{X}",
  "agent": "{role}",
  "action": "{描述}",
  "output": "{實際產出}",
  "verification": {
    "th_10": "{pytest 100%}",
    "th_11": "{coverage ≥70%}",
    "hr_10": "{sessions_spawn.log 有記錄}"
  }
}
```

---

## 8. sessions_spawn.log 格式（HR-10）

每次 Subagent spawn 後，寫入 `.methodology/sessions_spawn.log`：

```json
{"timestamp":"{ISO8601}","role":"{developer|reviewer}","task":"{FR-0X Name}","session_id":"{uuid}","confidence":{1-10}}
```

---

## 9. 產出格式標準（HR-05）

所有 Subagent 產出必須包含：

```json
{
  "status": "success | error | unable_to_proceed",
  "result": "實際產出",
  "confidence": {1-10},
  "citations": ["FR-01", "SRS.md#section"],
  "summary": "50字內摘要"
}
```

**confidence 評估標準**：

| 分數 | 意義 | 動作 |
|------|------|------|
| 9-10 | 高度確定，有引用 | 繼續 |
| 7-8 | 確定，無引用 | 標記，繼續 |
| 5-6 | 不確定 | 重新派遣（最多 3 次）|
| 1-4 | 嚴重懷疑 | 上報 Johnny |

---

## 10. Verify_Agent 觸發條件（Phase 3+）

觸發時機（滿足任一）：
- Agent B score < 80
- 自評分數與實際分數差異 > 20

觸發時：
1. 停止當前執行
2. 執行 Verify_Agent
3. 根據 Verify_Agent 結果決定：
   - APPROVE → 繼續
   - REJECT → 修復後重新派遣

Verify_Agent 詳細流程 → `docs/VERIFIER_GUIDE.md`

---

## 11. 失敗修復流程（HR-12）

```
Step 執行失敗
    ↓
讀取 .methodology/iterations/{phase}.json
    ↓
iteration++
    ↓
分析失敗原因
    ↓
生成修復 plan（考慮歷史問題）
    ↓
執行修復
    ↓
成功 → 下一 Step
失敗 → iteration++ → 回到「分析失敗原因」
    ↓
iteration > 5 → HR-12 觸發 → PAUSE → Johnny 干預
```

---

## 12. CLI 用法

```bash
# 生成執行計畫（第一版）
python cli.py plan-phase --phase 3 --goal "FR-01~FR-03 實作"

# 生成修復計畫（某 Step 失敗後）
python cli.py plan-phase --phase 3 --goal "FR-01~FR-03" --repair --step 3.2

# 查看迭代歷史
python cli.py plan-phase --phase 3 --history

# 查看某 Step 的迭代
python cli.py plan-phase --phase 3 --step 3.2 --history

# 完整 plan + 預估時間
python cli.py plan-phase --phase 3 --goal "..." --with-timeline
```

---

## 13. Iteration JSON 格式

`.methodology/iterations/{phase}.json`:

```json
{
  "phase": 3,
  "current_iteration": 3,
  "max_iterations": 5,
  "created_at": "{ISO8601}",
  "steps": {
    "3.1": {
      "status": "done",
      "iterations": 1,
      "started_at": "{ISO8601}",
      "completed_at": "{ISO8601}",
      "duration_minutes": 10
    },
    "3.2": {
      "status": "in_progress",
      "iterations": 2,
      "started_at": "{ISO8601}",
      "last_issue": "coverage 62% < 70%",
      "history": [
        {"iteration": 1, "issue": "coverage 62%", "fix": "增加邊界測試", "result": "fail"},
        {"iteration": 2, "issue": "timeout", "fix": "增加 retry", "result": "in_progress"}
      ]
    }
  },
  "summary": {
    "total_steps": 5,
    "completed_steps": 1,
    "total_duration_minutes": 45,
    "blockers": []
  }
}
```

---

## 14. 與 run-phase 的整合

### plan-phase + run-phase 完整流程

```
Johnny: 「執行 Phase 3」
    ↓
Agent: python cli.py plan-phase --phase 3 --goal "FR-01~FR-03"
    ↓
Plan 輸出 → Johnny 審核
    ↓
Johnny: 「確認執行」
    ↓
Agent: python cli.py run-phase --phase 3
    ↓
Pre-flight (plan-phase 已做，run-phase 複驗)
    ↓
For each Step in Plan:
    ↓
    Execute Step
    ↓
    Verify: TH-10 = 100%, TH-11 ≥ 70%
    ↓
    Write: DEVELOPMENT_LOG + sessions_spawn.log
    ↓
    If fail:
        Agent: python cli.py plan-phase --phase 3 --repair --step {N}.{X}
        ↓
        Johnny 審核修復 plan
        ↓
        執行修復
        ↓
        iteration > 5 → PAUSE
    ↓
    If success → 下一 Step
    ↓
Post-flight: Constitution Final Check
    ↓
Update: state.json + iterations.json
    ↓
Johnny: 看結果
```

---

## 15. HR-14 Integrity 計算

Integrity 分數由以下組成：

```python
def calculate_integrity():
    """
    Integrity = 扣分後的分數
    初始 = 100
    """
    penalties = {
        "HR-01": -25,  # 自寫自審
        "HR-02": -20,  # 無實際命令輸出
        "HR-03": -30,  # 跳過 Phase
        "HR-06": -20,  # 引入外框架
        "HR-07": -15,  # 無 session_id
        "HR-08": -10,  # 未執行 Quality Gate
        "HR-09": -20,  # Claims Verifier 失敗
        "HR-10": -15,  # sessions_spawn.log 缺失
    }

    score = 100
    for hr, penalty in penalties.items():
        if violations[hr]:
            score += penalty  # penalty 是負數

    return max(0, score)
```

---

## 16. 錯誤處理

| 錯誤類型 | 例外類別 | 處理方式 |
|---------|---------|---------|
| Phase 順序錯誤 | `PhaseTransitionError` | 停在 Pre-flight |
| Constitution 失敗 | `ConstitutionViolationError` | 停在 Pre-flight |
| Integrity < 40 | `IntegrityError` | FREEZE |
| Subagent 派遣失敗 | `AgentSpawnError` | 重試 3 次 |
| HR-12 超限 | — | PAUSE + Johnny 干預 |

---

## 17. 產出 Commit 規範

每次 Step 完成後，Commit 格式：

```
{Step}.{N}: {簡短描述}

- FR: {FR-0X}
- TH: {TH-YY}={value}
- HR: {HR-ZZ} 合規
- Session: {uuid}
- Confidence: {1-10}
```

---

## 18. 禁止事項彙整（進 Subagent Prompt）

```
❌ 禁止自寫自審（HR-01）→ 不同 Agent 執行 A/B
❌ 禁止省略內容（HR-01）→ `...` = 任務失敗
❌ 禁止 HybridWorkflow=OFF（HR-04）→ A/B 強制開啟
❌ 禁止 sessions_spawn.log 缺失（HR-10）→ 每次 spawn 必須記錄
❌ 禁止 unable_to_proceed 不說明原因（HR-05）
❌ 禁止編造內容（HR-06）
❌ 禁止引入 methodology-v2 外框架（HR-06）
❌ 禁止 Subagent 繼承父 context（HR-05）→ 必須用 SubagentIsolator
❌ 禁止 Phase 跳過（HR-03）→ 順序執行
❌ 禁止 Phase Truth < 70%（HR-11）
```

---

*本規格基於 methodology-v2 SKILL.md v6.26，100% 落實所有 HR/TH/Phase 規定*
