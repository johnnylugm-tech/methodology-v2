# methodology-v2 v6.22

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

### 0.5 Phase Reset 標準程序（重要）

當需要放棄當前 Phase 並重新開始時，**必須**嚴格執行以下步驟：

```bash
# Step 1: 確認目標狀態
git ls-tree <target_commit> --name-only

# Step 2: 清理工作目錄（非常重要！否則殘留檔案會混入新 commit）
git clean -fdx

# Step 3: Reset 到目標 commit
git reset --hard <target_commit>

# Step 4: 確認工作目錄狀態
ls -la && git status
```

**⚠️ 警告**：省略 `git clean -fdx` 會導致新 commit 混入舊檔案。

---

## 框架五大支柱

> methodology-v2 的核心價值，所有功能設計都圍繞這五點展開。

| 支柱 | 說明 | 關鍵機制 |
|------|------|--------|
| 🏛️ A/B 協作 | 雙角色分離，不可自寫自審 | HR-01, HR-04, HR-10 |
| 🎭 Agent 人格 | 每次 sessions_spawn 必須明確人格 | §A/B 協作機制 |
| 📜 Constitution | 產出品質憲法，正確性/安全性/可維護性 | TH-02~06, TH-08~09 |
| 🔍 ASPICE 合規 | 文件結構與內容標準化 | TH-01 |
| 🔗 可追溯性 | FR→SAD→代碼→測試 全鏈路追蹤 | TH-16, TH-17 |

**Quality Gate** 是所有支柱的匯聚點：每一次 Phase EXIT 都必須通過。

**詳見**：
- A/B 協作：`docs/HYBRID_WORKFLOW_GUIDE.md`
- Constitution：`docs/CONSTITUTION_GUIDE.md`
- ASPICE：`docs/ASPICE_MAPPING.md`
- 可追溯性：`docs/ANNOTATION_GUIDE.md`

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
| HR-12 | A/B 審查同一 Phase 超過 5 輪 | 強制 PAUSE，通知 Johnny，等待人工裁決 |
| HR-13 | Phase 執行時長超過預估時間的 3 倍 | 強制 checkpoint，輸出 BLOCKER 清單，PAUSE 等待裁決 |
| HR-14 | Integrity 分數降至 < 40 | FREEZE 專案，全面審計後才能繼續 |

---

## A/B 協作機制

**原則**：主代理啟動 sub-agent 必須用 `sessions_spawn` + 明確人格，HybridWorkflow(mode=ON) 強制審查。

**人格定義**：

| 角色 | 職責 | 禁用 |
|------|------|------|
| Developer | 產出代碼 | 自己審自己的產出 |
| Reviewer | 審查把關 | 不可兼任 Developer |

**A/B 流程**：
```
Developer Sub-agent 產出 → Reviewer Sub-agent 審查 → [Reject? 回修重審 / Approve? 下一 Phase]
```

**⚠️ 禁止行爲**：
- 自寫自審（HR-01）
- HybridWorkflow=OFF（HR-04）
- 同一 Agent 人格兼任雙角色
- sessions_spawn.log 缺失（HR-10）

**⚠️ 負面約束（新增）**：
- 回傳 `status: "unable_to_proceed"` 而不說明原因 → Integrity -15
- 嘗試編造無法完成的內容 → Integrity -20
- 程式碼中使用省略號 `...` → 視為任務失敗

**Subagent 隔離原則**：
- 每次 `sessions_spawn` 必須使用 **獨立的 fresh messages[]**
- 不得繼承父 Agent 的完整上下文（只能傳遞 task 描述）
- 結果合併：主代理在收到 Subagent 回傳後，僅提取 `result` 和 `summary`，其餘捨棄

**sessions_spawn 格式**：
```python
sessions_spawn(
    runtime="subagent",
    task="...",
    # 不得傳遞父 Agent 的 messages[] 或對話歷史
)
```

**詳見**：`docs/HYBRID_WORKFLOW_GUIDE.md`

### 產出格式規範（重要）

所有 Agent 回傳必須包含：
- `status`: success | error | unable_to_proceed
- `result`: 實際產出
- `confidence`: 1-10
- `citations`: 引用來源陣列
- `summary`: 50字內摘要（長任務必填）

**負面約束**：
- `status: "error"` → 附帶錯誤訊息
- `status: "unable_to_proceed"` → 說明原因，**嚴禁編造**
- 程式碼產出：嚴禁使用省略號 `...`

**驗證**：格式不符 → 任務失敗，Integrity -10

詳見 `docs/ANNOTATION_GUIDE.md`

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
| TH-16 | 代碼 ↔ SAD 映射率 | = 100% | 3 | `python cli.py trace-check --from phase2 --to phase3` |
| TH-17 | FR ↔ 測試 映射率 | ≥ 90% | 4 | `python cli.py trace-check --from phase1 --to phase3-tests` |

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
7. 更新狀態追蹤：python cli.py update-step / end-phase
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

6. 更新狀態追蹤：python cli.py update-step / end-phase
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
  7. Verify_Agent（如滿足觸發條件）
  8. 生成合規矩陣 + Phase3_STAGE_PASS.md
  9. 更新狀態追蹤：python cli.py update-step / end-phase
```

**EXIT**: TH-06 > 80%, TH-08 ≥ 80/90, TH-10 = 100%, TH-11 ≥ 70%, TH-16 = 100%, Agent B APPROVE

**代碼規範**：詳見 `docs/ANNOTATION_GUIDE.md`

### 代碼 Annotation 格式

`@FR`、`@SAD`、`@NFR` annotation 規範。詳見 `docs/ANNOTATION_GUIDE.md`

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
6. Verify_Agent（如滿足觸發條件）
7. 生成 Phase4_STAGE_PASS.md
8. 更新狀態追蹤：python cli.py update-step / end-phase
```

**EXIT**: TH-01 > 80%, TH-03 = 100%, TH-06 > 80%, TH-10 = 100%, TH-12 ≥ 80%, TH-17 ≥ 90%

### 測試 Annotation 格式

`@covers`、`@type` annotation 規範。詳見 `docs/ANNOTATION_GUIDE.md`

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
7. 更新狀態追蹤：python cli.py update-step / end-phase
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
6. 更新狀態追蹤：python cli.py update-step / end-phase
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
7. 更新狀態追蹤：python cli.py update-step / end-phase
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
8. 更新狀態追蹤：python cli.py update-step / end-phase
```

**EXIT**: CONFIG_RECORDS.md 完整, pip freeze 存在, Git Tag 建立, Agent B APPROVE

---

## 5. 工具速查

**詳見** `docs/CLI_REFERENCE.md`（完整命令列表）

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

---

## Verify_Agent 流程

在 A/B 審查之後、主代理接受結果前，執行獨立的驗證 Agent。

**觸發條件**：Phase 3+ 代碼交付、Agent B 分數 < 80、Agent A 自評分差異 > 20

**Prompt + 詳細流程**：詳見 `docs/VERIFIER_GUIDE.md`

### 6.2 Agent A 自評（誠實）

每位 Agent 完成後回傳時，**必須**包含：
- `result`: 完整產出
- `summary`: 50字內摘要

| 檢查項目 | 說明 |
|----------|------|
| 5W1H 合規性 | 是否 100% 遵從 Phase N 的 5W1H？ |
| 問題修復 | 是否發現並修復了問題？ |
| 交付完整性 | 所有交付物是否提供？ |
| **摘要** | **50字內簡述本 Phase 完成內容** |
| confidence | 1-10 自評分 |
| citations | 事實性聲稱的引用（如有） |

**誠實原則**：Agent A 必須如實報告問題，不隱瞞。

### STAGE_PASS 產出格式

每個 Phase 交付時，Agent A 必須填寫：
- 5W1H 合規性、問題修復、交付完整性
- 摘要（50字內）、confidence（1-10）、citations（如有）

詳見 `docs/HYBRID_WORKFLOW_GUIDE.md`

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

### 6.5 Johnny 介入條件（擴充版）

| 觸發條件 | 自動行為 | Johnny 動作 |
|---------|---------|------------|
| Agent B 有重大疑問無法解決 | 暫停執行 | 人工裁決 |
| 分數 < 50 | 禁止進入下一 Phase | 審查 Agent A 工作 |
| 作假跡象（L6 錯誤） | 終止 + 記錄 | 調查 session log |
| A/B 輪次 > 5（HR-12） | 自動 PAUSE | 判斷是否重新分工或 RESET |
| Phase 時間 > 3× 預估（HR-13） | 自動 PAUSE | 評估是否簡化範圍 |
| Integrity < 40（HR-14） | FREEZE 專案 | 全面稽核 |
| BLOCK 數 > 5 且同一維度 | 觸發 Phase Reset | 評估 SRS/SAD 品質 |

### 6.6 CLI 命令

```bash
# 生成 STAGE_PASS
python cli.py stage-pass --phase N

# Agent B 審查
python cli.py stage-review --phase N
```

---

## 7. 開發日誌格式

每個 Phase 必須記錄：session_id、Agent A/B 工作紀錄、Quality Gate 命令輸出、問題與修復、sign-off。

詳見 `docs/COWORK_PROTOCOL_v1.0.md`

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

## 資源限制

| 資源 | 限制 | 超出行為 |
|------|------|---------|
| 工具呼叫 Timeout | 60s | 終止，狀態設為 TIMEOUT |
| Step 最大執行時間 | 30min | 觸發 HR-13 煞車 |
| Phase 最大執行時間 | 預估 × 3 | 觸發 HR-13 煞車 |
| A/B 審查輪次 | 5 輪 | 觸發 HR-12 PAUSE |

**Timeout 處理**：終止 → 記錄 state.json → L1-L4 對應處理 → 指數退避重試

**重試機制**：動態 Prompt 收緊（100字→50字→5行→OK/ERROR），退避 10s/20s/40s/80s

詳見 `docs/RUNTIME_METRICS_MANUAL.md`

---

## 9. 外部文檔參考

| 文檔 | 用途 |
|------|------|
| docs/HUMAN_AGENT_INTERACTION_FLOW.md | Human-Agent 互動流程 |
| docs/PHASE_PROMPTS.md | Phase Prompt Templates |
| docs/CLI_REFERENCE.md | CLI 命令速查 |
| docs/TASK_INITIALIZATION_PROMPT.md | 任務初始化 Prompt |
| docs/MAIN_AGENT_PLAYBOOK.md | 主代理最佳實踐（Sub-agent 管理）|
| docs/FSM_STATE_MACHINE.md | FSM 狀態機定義 |
| docs/VERIFIER_GUIDE.md | Verify_Agent 流程指南 |
| docs/ANNOTATION_GUIDE.md | 註解規範（@FR / @covers）|
| docs/PROVIDER_CONFIG_GUIDE.md | Provider 配置與 Phase→Model 映射 |
| docs/RUNTIME_METRICS_MANUAL.md | 資源限制與效能指標 |
| docs/CONSTITUTION_GUIDE.md | Constitution 品質憲法 |
| docs/GIT_VERSIONING_CONVENTION.md | Git 版本管理規範 |
| SKILL_TEMPLATES.md | CoT / Few-shot / 模板庫 |
| SKILL_DOMAIN.md | 領域知識 |

**Phase 進入/退出條件**：詳見 §4 Phase 定義各章節 EXIT 條件

---

*methodology-v2 v6.22 | Agent Executable Specification*
*Last Updated: 2026-04-03*
