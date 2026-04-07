# Agent 執行指南（給 Sub-agent）

> **版本**: v6.54
> **適用**: 所有 Sub-agent（Developer, Reviewer, QA, DevOps 等）
> **用途**: 執行 Phase 時的標準流程

---

## 快速參考

### 執行 plan-phase
```bash
python cli.py plan-phase --phase {N} --detailed --repo /path/to/repo
```

### 執行 run-phase
```bash
python cli.py run-phase --phase {N} --repo /path/to/repo
```

---

## Phase 執行標準流程

### Phase 1: 需求規格

```
[Step 0] 讀取 TASK_INITIALIZATION_PROMPT.md
[Step 1] 制定 SRS.md
[Step 2] 制定 SPEC_TRACKING.md
[Step 3] 制定 TRACEABILITY_MATRIX.md
[Step 4] A/B 審查
[Step 5] Constitution Check（≥80%）
[Step 6] Commit + Push
```

### Phase 2: 架構設計

```
[Step 0] 讀取 SRS.md
[Step 1] 制定 SAD.md
[Step 2] 制定 ADR.md
[Step 3] A/B 審查（SAD↔SRS =100%）
[Step 4] Constitution Check（≥80%）
[Step 5] Commit + Push
```

### Phase 3: 代碼實現

```
[Step 0] 讀取 SRS.md §FR-XX + SAD.md §Module
[Step 1] Developer 實作代碼
[Step 2] 本地 pytest 驗證
[Step 3] Reviewer 審查
[Step 4] HR-15 citations（含行號）
[Step 5] Constitution Check（≥80%）
[Step 6] Commit + Push
```

### Phase 4-8: 測試/驗證/品質/風險/配置

類似流程，根據 Phase 調整交付物。

---

## HR-01~HR-15 速查

| HR | 規則 | 行動 |
|----|------|------|
| HR-01 | A/B 不同 Agent | Developer → Reviewer（嚴格順序）|
| HR-02 | QG 需實際輸出 | 保存 stdout |
| HR-03 | Phase 順序執行 | state.json phase=N |
| HR-04 | HybridWorkflow mode=ON | prompt 含 mode=ON |
| HR-05 | methodology-v2 優先 | 爭議時以 framework 為準 |
| HR-06 | 禁外框架 | forbidden list |
| HR-07 | session_id 記錄 | DEVELOPMENT_LOG |
| HR-08 | Phase 結束 QG | stage-pass |
| HR-09 | Claims Verifier | citations 含行號 |
| HR-10 | sessions_spawn.log | 每 step 2 筆記錄 |
| HR-11 | Phase Truth <70% | 禁進入下一 Phase |
| **HR-12** | **>5 輪 → PAUSE** | **通知 Johnny** |
| **HR-13** | **>3x 預估 → PAUSE** | **Checkpoint** |
| HR-14 | Integrity <40 → FREEZE | 通知 Johnny |
| HR-15 | citations 含行號 | 無 = 任務失敗 |

---

## 四維度評核標準（目標 10/10）

### 維度 1: 規範符合度

| Phase | 標準 |
|-------|------|
| P1 | HR-15 citations（含行號）|
| P2 | SAD↔SRS =100% |
| P3 | docstring [FR-XX] + citations |
| P4 | FR↔測試 映射率 ≥90% |
| P5 | Baseline 符合 SRS 約束 |
| P6 | Constitution ≥80% |
| P7 | 所有風險有緩解計畫 |
| P8 | requirements.lock 一致性 |

### 維度 2: A/B 協作

- Developer spawn → Reviewer spawn（嚴格順序）
- sessions_spawn.log 完整記錄

### 維度 3: 子代理管理

- SubagentIsolator.spawn()
- fresh_messages 隔離
- Need-to-Know：只讀必要資訊
- On-Demand：需要才請求

### 維度 4: 測試覆蓋率

| Phase | 標準 |
|-------|------|
| P1 | Traceability 100% |
| P2 | 每 Module 有對應 FR |
| P3 | pytest PASS + coverage ≥80% |
| P4 | 關鍵路徑覆蓋 100% |
| P5 | 監控指標覆蓋 100% |
| P6 | 邏輯正確性 ≥90% |
| P7 | 風險評估合理性 |
| P8 | 部署檢查清單 100% |

---

## 迭代修復流程

```
[FR-XX]
 ↓
[Developer spawn] → confidence < 6？（yes → 重新派遣，最多 3 次）
 ↓
[本地驗證] pytest + coverage → FAIL？（yes → 修復 → re-verify）
 ↓
[Reviewer spawn] → APPROVE？（no → 修復 → re-spawn）
 ↓
[HR-12 檢查] > 5 輪？（yes → PAUSE，通知 Johnny）
 ↓
[commit] → [sessions_spawn.log 補記]
 ↓
[next FR]
```

---

## sessions_spawn.log 格式

```json
{"timestamp":"ISO8601","role":"developer","task":"FR-XX","session_id":"uuid","confidence":8,"commit":"HASH"}
{"timestamp":"ISO8601","role":"reviewer","task":"FR-XX Review","session_id":"uuid","confidence":9,"verdict":"APPROVE"}
```

---

## Constitution Check 命令

```bash
# Phase 1
python -c "from quality_gate.constitution import run_constitution_check; run_constitution_check('srs', current_phase=1)"

# Phase 2
python -c "from quality_gate.constitution import run_constitution_check; run_constitution_check('sad', current_phase=2)"

# Phase 3
python -c "from quality_gate.constitution import run_constitution_check; run_constitution_check('implementation', current_phase=3)"
```

---

## HR-12/13 自動追蹤

```python
# IntegrationManager 自動追蹤
from integration_manager import IntegrationManager

mgr = IntegrationManager(phase=3, task_id="fr-01")
stats = mgr.get_stats()

if stats['remaining'] == 0:
    print("⚠️ HR-12: 已達 5 輪限制，請通知 Johnny")
```

---

## 工具觸發時機

| 工具 | 時機 |
|------|------|
| SubagentIsolator | 每次派遣前 |
| PermissionGuard | exec/rm 前 |
| ContextManager | 訊息 >50/100/200 |
| SessionManager | 任務開始 + 30 分鐘後 |
| KnowledgeCurator | Phase 開始前 |
| ToolRegistry | 發現新工具時 |

---

## 常見錯誤處理

| 錯誤 | 等級 | 處理 |
|------|------|------|
| SyntaxError | L1 | 立即返回，不重試 |
| API Timeout | L2 | 重試 3 次，指數退避 |
| 業務邏輯錯誤 | L3 | 降級 + 上報 |
| 系統錯誤 | L4 | 熔斷 + 警報 |

---

## 輸出格式（JSON）

```json
{
 "status": "success|error|unable_to_proceed",
 "result": "實際產出（路徑）",
 "confidence": 1-10,
 "citations": ["FR-XX", "SRS.md#L23-L45", "SAD.md#L50-L60"],
 "summary": "50字內"
}
```

---

*最後更新: 2026-04-05*
