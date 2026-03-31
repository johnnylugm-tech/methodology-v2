# methodology-v2 v6.13

> Multi-Agent Collaboration Development Methodology — Agent Executable Specification
> 精簡版：Agent 執行時真正需要的內容

---

## 0. 執行協議

### 0.1 啟動流程

```
1. READ  → .methodology/state.json → 取得 current_phase
2. LOAD  → 本文件「Phase {N}」章節
3. CHECK → Phase {N} 進入條件 → IF any blocker fails THEN STOP
4. EXECUTE → Phase {N} SOP（按順序）
5. FOR EACH step:
   a. IF 需要模板 → LAZY LOAD SKILL_TEMPLATES.md §T{N}
   b. RECORD actual command output
   c. IF A/B review → SPAWN agent with designated persona
6. CHECK → Phase {N} 退出條件 → IF any blocker fails THEN FIX + RETRY
7. UPDATE → state.json → phase = N+1
8. GOTO step 1
```

### 0.2 Lazy Loading 規則

| 外部文件 | 載入時機 |
|---------|---------|
| SKILL_TEMPLATES.md | SOP 步驟需要模板時 |
| SKILL_DOMAIN.md | Phase 3 實作前 |

### 0.3 狀態文件

```json
{
  "current_phase": 1,
  "domain": "generic",
  "phase_history": [],
  "project_root": "/path/to/project",
  "started_at": "YYYY-MM-DD"
}
```

### 0.4 STAGE_PASS 產生時機

每個 Phase 退出時執行：
```bash
python cli.py stage-pass --phase N
```

---

## 1. 硬規則（違反即終止）

| ID | 規則 | 違反後果 |
|----|------|---------|
| HR-01 | A/B 必須不同 Agent，禁止自寫自審 | 終止，Integrity -25 |
| HR-02 | Quality Gate 必須有實際命令輸出 | 終止，Integrity -20 |
| HR-03 | Phase 必須順序執行，不可跳過 | 終止，Integrity -30 |
| HR-04 | HybridWorkflow mode=ON，強制 A/B 審查 | 終止 |
| HR-05 | 衝突時優先 methodology-v2 | 記錄 |
| HR-06 | 禁止引入規格書/methodology-v2 以外的框架 | 終止，Integrity -20 |
| HR-07 | DEVELOPMENT_LOG 必須記錄 session_id | Integrity -15 |
| HR-08 | 每個 Phase 結束必須執行 Quality Gate | 終止，Integrity -10 |
| HR-09 | Claims Verifier 驗證必須通過 | 終止，Integrity -20 |
| HR-10 | sessions_spawn.log 必須存在且有 A/B 記錄 | 終止，Integrity -15 |
| HR-11 | Phase Truth 分數 < 70% 禁止進入下一 Phase | 終止 |

---

## 2. 閾值配置

### 2.1 Quality Gate

| ID | 指標 | 門檻 | 適用 Phase | 驗證命令 |
|----|------|------|-----------|---------|
| TH-01 | ASPICE 合規率 | > 80% | 1-8 | `python3 quality_gate/doc_checker.py` |
| TH-02 | Constitution 總分 | ≥ 80% | 5-8 | `python3 quality_gate/constitution/runner.py` |
| TH-03 | Constitution 正確性 | = 100% | 1-4 | `python3 quality_gate/constitution/runner.py --type {type}` |
| TH-04 | Constitution 安全性 | = 100% | 1-4 | 同上 |
| TH-05 | Constitution 可維護性 | > 70% | 2-4 | 同上 |
| TH-06 | Constitution 測試覆蓋率 | > 80% | 3-4 | 同上 |
| TH-07 | 邏輯正確性分數 | ≥ 90 分 | 5-8 | `python3 quality_gate/spec_logic_checker.py` |
| TH-08 | AgentEvaluator（標準） | ≥ 80 分 | 1-2 | AgentEvaluator |
| TH-09 | AgentEvaluator（嚴格） | ≥ 90 分 | 3-8 | AgentEvaluator |
| TH-10 | 測試通過率 | = 100% | 3-8 | `pytest` |
| TH-11 | 單元測試覆蓋率 | ≥ 70% | 3 | `pytest --cov` |
| TH-12 | 單元測試覆蓋率 | ≥ 80% | 4-8 | `pytest --cov` |
| TH-13 | SRS FR 覆蓋率 | = 100% | 4-8 | Agent B 確認 |
| TH-14 | 規格完整性 | ≥ 90% | 1 | Agent B 確認 |

### 2.2 Phase Truth

| ID | 指標 | 門檻 | 驗證命令 |
|----|------|------|---------|
| TH-15 | Phase Truth 分數 | ≥ 70% | `python cli.py phase-verify --phase N` |

### 2.3 Integrity Tracker

| 違規類型 | 扣分 |
|----------|------|
| subagent_claim | -20 |
| fake_qg_result | -20 |
| skip_phase | -30 |
| qa_equals_developer | -25 |
| missing_dialogue | -15 |

信任等級：FULL_TRUST ≥ 80 / PARTIAL_TRUST 50-79 / LOW_TRUST < 50

---

## 3. Phase 路由表

| Phase | 名稱 | Agent A | Agent B | A/B 次數 | 關鍵交付物 |
|-------|------|---------|---------|---------|-----------|
| 1 | 需求規格 | architect | reviewer | 1 | SRS.md, SPEC_TRACKING.md, TRACEABILITY_MATRIX.md |
| 2 | 架構設計 | architect | reviewer | 1 | SAD.md, ADR |
| 3 | 代碼實現 | developer | reviewer | 每模組 1 | 代碼, 單元測試, 合規矩陣 |
| 4 | 測試 | qa | reviewer | 2 | TEST_PLAN.md, TEST_RESULTS.md |
| 5 | 驗證交付 | devops | architect | 2 | BASELINE.md, MONITORING_PLAN.md |
| 6 | 品質保證 | qa | architect/pm | 1 | QUALITY_REPORT.md |
| 7 | 風險管理 | qa/devops | pm/architect | 1 | RISK_REGISTER.md |
| 8 | 配置管理 | devops | pm/architect | 1+封版 | CONFIG_RECORDS.md, Git Tag |

---

## 4. Phase 定義

### Phase 1: 需求規格

**ROLE**:
- Agent A: `architect` — 撰寫 SRS.md, SPEC_TRACKING.md, TRACEABILITY_MATRIX.md
- Agent B: `reviewer` — 審查 FR 完整性、A/B 評估
- 禁止：自寫自審

**ENTRY**: 專案初始化完成

**SOP**:
```
1. Agent A 撰寫 SRS.md（含邏輯驗證方法）
2. Agent A 初始化 SPEC_TRACKING.md
3. Agent A 初始化 TRACEABILITY_MATRIX.md
4. Agent B A/B 審查（5W1H 清單逐項確認）
5. Quality Gate: doc_checker + constitution + spec-track
6. 生成 Phase1_STAGE_PASS.md
```

**EXIT**: TH-01 > 80%, TH-03 = 100%, TH-14 ≥ 90%, Agent B APPROVE

---

### Phase 2: 架構設計

**ROLE**:
- Agent A: `architect` — 撰寫 SAD.md, ADR
- Agent B: `reviewer` — 架構審查、Conflict Log
- 禁止：引入規格書外框架

**ENTRY**: Phase 1 APPROVE

**SOP**:
```
1. Agent A 撰寫 SAD.md（含模組邊界圖）
2. Agent A 建立 ADR（如有技術選型）
3. Agent B 架構審查（5 維度）
4. Quality Gate: doc_checker + constitution + spec-track
5. 生成 Phase2_STAGE_PASS.md
```

**EXIT**: TH-01 > 80%, TH-03 = 100%, TH-05 > 70%, Agent B APPROVE

---

### Phase 3: 代碼實現

**ROLE**:
- Agent A: `developer` — 代碼實作、單元測試
- Agent B: `reviewer` — 同行邏輯審查
- 禁止：自寫自審、引入第三方框架

**ENTRY**: Phase 2 APPROVE

**SOP**:
```
FOR EACH 模組:
  1. Agent A 實作模組（含規範標注）
  2. Agent A 撰寫單元測試（正向/邊界/負面三類）
  3. Agent A 填寫邏輯審查對話 Developer 部分
  4. Agent B 同行邏輯審查（填寫 Architect 確認部分）
  5. Agent B 確認測試完整性
  6. Quality Gate: pytest + coverage + constitution
7. 生成合規矩陣
8. 生成 Phase3_STAGE_PASS.md
```

**EXIT**: TH-06 > 80%, TH-08 ≥ 80/90, TH-10 = 100%, TH-11 ≥ 70%, Agent B APPROVE

**代碼規範**:
```python
class ModuleName:
    """
    對應 methodology-v2 規範：
    - SKILL.md - Core Modules
    - SKILL.md - Error Handling (L1-L6)
    - SAD.md FR-XX

    邏輯約束：
    - [具體邏輯約束]
    """
    def __init__(self):
        self._engine = None  # Lazy Init

    def _get_engine(self):
        if self._engine is None:
            self._engine = ExternalSDK()
        return self._engine
```

---

### Phase 4: 測試

**ROLE**:
- Agent A: `qa` — 撰寫 TEST_PLAN.md, TEST_RESULTS.md
- Agent B: `reviewer` — 兩次審查
- 禁止：Tester = Developer

**ENTRY**: Phase 3 APPROVE

**SOP**:
```
1. Agent A 撰寫 TEST_PLAN.md
2. Agent B 第一次審查（測試策略）
3. Agent A 執行測試、記錄 TEST_RESULTS.md
4. Agent B 第二次審查（pytest 輸出真實性）
5. Quality Gate: pytest + constitution + spec_logic
6. 生成 Phase4_STAGE_PASS.md
```

**EXIT**: TH-01 > 80%, TH-03 = 100%, TH-06 > 80%, TH-10 = 100%, TH-12 ≥ 80%

---

### Phase 5: 驗證交付

**ROLE**:
- Agent A: `devops` — 建立 BASELINE.md, MONITORING_PLAN.md
- Agent B: `architect` — 兩次審查
- 禁止：BASELINE 功能對照不完整

**ENTRY**: Phase 4 APPROVE, 測試通過率 = 100%

**SOP**:
```
1. Agent A 建立 BASELINE.md（功能/品質/效能基線）
2. Agent B 基線審查
3. Agent A 建立 MONITORING_PLAN.md（四個監控維度）
4. Agent B 驗收報告審查
5. Quality Gate: logic checker ≥ 90 + constitution ≥ 80
6. 生成 Phase5_STAGE_PASS.md
```

**EXIT**: TH-02 ≥ 80%, TH-07 ≥ 90, Agent B APPROVE

---

### Phase 6: 品質保證

**ROLE**:
- Agent A: `qa` — 撰寫 QUALITY_REPORT.md
- Agent B: `architect` 或 `pm` — 品質確認
- 禁止：session_id 缺失

**ENTRY**: Phase 5 APPROVE

**SOP**:
```
1. Agent A 收集 Phase 6 監控數據
2. Agent A 撰寫 QUALITY_REPORT.md（完整版）
3. Agent B 品質確認
4. Quality Gate: constitution ≥ 80 + 邏輯正確性
5. 生成 Phase6_STAGE_PASS.md
```

**EXIT**: TH-02 ≥ 80%, TH-07 ≥ 90, Agent B APPROVE

---

### Phase 7: 風險管理

**ROLE**:
- Agent A: `qa` 或 `devops` — 撰寫 RISK_REGISTER.md
- Agent B: `pm` 或 `architect` — 風險確認、演練
- 禁止：Decision Gate 未確認

**ENTRY**: Phase 6 APPROVE

**SOP**:
```
1. Agent A 五維度風險識別
2. Agent A 建立 RISK_REGISTER.md
3. Agent B Decision Gate 確認（MEDIUM/HIGH）
4. Agent B 風險演練（如有 HIGH 風險）
5. Quality Gate: 邏輯正確性 ≥ 90
6. 生成 Phase7_STAGE_PASS.md
```

**EXIT**: TH-07 ≥ 90, Decision Gate 100% 確認, Agent B APPROVE

---

### Phase 8: 配置管理

**ROLE**:
- Agent A: `devops` — 撰寫 CONFIG_RECORDS.md, Git Tag
- Agent B: `pm` 或 `architect` — 配置確認、封版審查
- 禁止：配置不完整、pip freeze 缺失

**ENTRY**: Phase 7 APPROVE

**SOP**:
```
1. Agent A 撰寫 CONFIG_RECORDS.md（8 章節）
2. Agent A 執行 pip freeze / npm lock
3. Agent A 建立 Git Tag
4. Agent B 配置確認（七區塊逐項確認）
5. Agent B 封版審查
6. Quality Gate: 配置合規性確認
7. 生成 Phase8_STAGE_PASS.md
```

**EXIT**: CONFIG_RECORDS.md 完整, pip freeze 存在, Git Tag 建立, Agent B APPROVE

---

## 5. 工具速查

### 5.1 核心工具

| 功能 | 命令 |
|------|------|
| ASPICE 檢查 | `python3 quality_gate/doc_checker.py` |
| Constitution | `python3 quality_gate/constitution/runner.py --type {type}` |
| Phase Truth | `python cli.py phase-verify --phase N` |
| Stage Pass | `python cli.py stage-pass --phase N` |
| Spec Tracking | `python3 cli.py spec-track {init/check/report}` |

### 5.2 Anti-Cheat 工具

| 功能 | 命令 |
|------|------|
| Claims Verifier | `python3 quality_gate/claims_verifier.py` |
| A/B Enforcer | `python3 quality_gate/ab_enforcer.py` |
| Integrity Tracker | `python3 quality_gate/integrity_tracker.py` |

### 5.3 Skill Check

| 模式 | 命令 |
|------|------|
| 預熱 | `python cli.py skill-check --mode preheat --phase N` |
| 拷問 | `python cli.py skill-check --mode interrogate --phase N` |
| 引用 | `python cli.py skill-check --mode citation --phase N` |

### 5.4 Phase Artifact Enforcer

```bash
python3 quality_gate/phase_artifact_enforcer.py --phase N
python3 quality_gate/phase_artifact_enforcer.py --all
```

---

## 6. STAGE_PASS 查核日誌

每個 Phase 完成後，必須經過 Agent A/B 審查流程。

### 6.1 審查流程

```
Agent A 自評 → STAGE_PASS.md
    ↓
Agent B 審查 → 提出疑問或 APPROVE
    ↓
❌ Agent B 有疑問 → 回到 Agent A 修復
    ↓
✅ Agent B APPROVE → 進入下一 Phase
```

### 6.2 Agent A 自評（誠實）

| 檢查項目 | 說明 |
|----------|------|
| 5W1H 合規性 | 是否 100% 遵從 Phase N 的 5W1H？ |
| 問題修復 | 是否發現並修復了問題？ |
| 交付完整性 | 所有交付物是否提供？ |

**誠實原則**：Agent A 必須如實報告問題，不隱瞞。

### 6.3 Agent B 審查（批判）

Agent B 必須對以下提出疑問：
- 發現 Agent A 可能忽略的問題
- 挑戰 Agent A 的假設
- 驗證聲稱的實際證據

**批判原則**：Agent B 扮演「挑刺」的角色。

### 6.4 分數角色

| 分數範圍 | Agent B 行動 |
|----------|--------------|
| 95-100 | 快速確認 |
| 80-94 | 仔細審查 |
| 70-79 | 特別注意 |
| <70 | 🔴 Flag，禁止進入下一 Phase |

### 6.5 Johnny 介入條件

Johnny 只在以下情況介入：
- Agent B 提出重大疑問無法解決
- 分數 < 50
- 發現作假跡象

### 6.6 CLI 命令

```bash
# 生成 STAGE_PASS
python cli.py stage-pass --phase N

# Agent B 審查
python cli.py stage-review --phase N
```

---

## 7. 開發日誌格式

```markdown
# DEVELOPMENT_LOG.md

## Phase {N} - {日期}

### session_id
{session_id}

### Agent A 工作紀錄
[工作內容]

### Agent B 審查紀錄
[審查內容]

### Quality Gate 結果

執行命令：
```
{paste actual command}
```

結果：
```
{paste actual output}
```

### 問題與修復
| 問題 | 解決方式 |
|------|---------|
| [問題] | [解決] |

### sign-off
- Agent A: {name} ({session_id})
- Agent B: {name} ({session_id})
```

---

## 8. 錯誤處理

### L1-L6 分類

| 等級 | 類型 | 處理方式 |
|------|------|---------|
| L1 | 輸入錯誤 | 立即返回錯誤 |
| L2 | 工具錯誤 | 重試 3 次 |
| L3 | 執行錯誤 | 降級處理 |
| L4 | 系統錯誤 | 熔斷 + 警報 |
| L5 | 驗證失敗 | 停在當前 Step，修復後重試 |
| L6 | 作假行為 | 終止，Integrity 扣分 |

### 常見失敗處理

| 失敗場景 | 處理方式 |
|---------|---------|
| FrameworkEnforcer BLOCK 未通過 | 停在當前 Step，修复问题后重新執行檢查 |
| Constitution < 門檻 | 停在當前 Step，修复问题后重新執行檢查 |
| pytest 失敗 | 停在 Phase 3，修复测试后重新執行 |
| 覆蓋率 < 閾值 | 停在 Phase 3，增加測試後重新執行 |
| SPEC_TRACKING < 90% | 停在 Phase 1，更新追蹤後重新執行 |
| Johnny REJECT | 根據理由修復，重新提交審核 |

---

## 9. 外部文檔參考

| 文檔 | 用途 |
|------|------|
| docs/HUMAN_AGENT_INTERACTION_FLOW.md | Human-Agent 互動流程 |
| docs/PHASE_PROMPTS.md | Phase Prompt Templates |
| docs/CLI_REFERENCE.md | CLI 命令速查 |
| docs/TASK_INITIALIZATION_PROMPT.md | 任務初始化 Prompt |
| SKILL_TEMPLATES.md | 模板庫 |
| SKILL_DOMAIN.md | 領域知識 |

---

## 10. 附錄：Phase 詳細定義

### Phase 1 進入/退出條件速查

**進入條件**: 專案初始化完成
**退出條件**: TH-01 > 80%, TH-03 = 100%, TH-14 ≥ 90%, Agent B APPROVE

### Phase 2 進入/退出條件速查

**進入條件**: Phase 1 APPROVE
**退出條件**: TH-01 > 80%, TH-03 = 100%, TH-05 > 70%, Agent B APPROVE

### Phase 3 進入/退出條件速查

**進入條件**: Phase 2 APPROVE, SAD.md APPROVE
**退出條件**: TH-06 > 80%, TH-08 ≥ 90, TH-10 = 100%, TH-11 ≥ 70%, Agent B APPROVE

### Phase 4 進入/退出條件速查

**進入條件**: Phase 3 APPROVE
**退出條件**: TH-01 > 80%, TH-03 = 100%, TH-06 > 80%, TH-10 = 100%, TH-12 ≥ 80%

### Phase 5 進入/退出條件速查

**進入條件**: Phase 4 APPROVE, 測試通過率 = 100%
**退出條件**: TH-02 ≥ 80%, TH-07 ≥ 90, Agent B APPROVE

### Phase 6 進入/退出條件速查

**進入條件**: Phase 5 APPROVE
**退出條件**: TH-02 ≥ 80%, TH-07 ≥ 90, Agent B APPROVE

### Phase 7 進入/退出條件速查

**進入條件**: Phase 6 APPROVE, 測試通過率 = 100%
**退出條件**: TH-07 ≥ 90, Decision Gate 100% 確認, Agent B APPROVE

### Phase 8 進入/退出條件速查

**進入條件**: Phase 7 APPROVE
**退出條件**: CONFIG_RECORDS.md 完整, pip freeze 存在, Git Tag 建立, Agent B APPROVE

---

*methodology-v2 v6.13 | Agent Executable Specification*
*Last Updated: 2026-03-31*
