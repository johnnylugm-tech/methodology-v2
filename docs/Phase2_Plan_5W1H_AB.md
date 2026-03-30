# Phase 2 計劃：架構設計
## methodology-v2 | 5W1H 框架 × A/B 協作機制

> **版本基準**：SKILL.md v5.56 | 整理日期：2026-03-29
> **前置條件**：Phase 1 全部 Sign-off ✅（phase_artifact_enforcer 通過）

---

## 🗺️ 一覽表

| 5W1H | 核心答案 |
|------|----------|
| **WHO**   | Agent A（Architect）設計 × Agent B（Senior Dev / Reviewer）審查架構 |
| **WHAT**  | 產出 SAD.md（系統架構文件）+ 更新 TRACEABILITY_MATRIX.md |
| **WHEN**  | Phase 1 完整通過後；Phase 3 開發的前置條件 |
| **WHERE** | `02-architecture/` 目錄；Quality Gate 工具在 `quality_gate/` |
| **WHY**   | 架構決策一旦進入 Phase 3 才修改，成本指數級上升；A/B 在此攔截最有效 |
| **HOW**   | A 設計 → B 架構審查 → Conflict Log → Quality Gate → 雙方 sign-off → Phase 3 |

---

## 1. WHO — 誰執行？（A/B 角色分工）

> ⚠️ **強制原則**：A/B 必須是不同 Agent，禁止自寫自審。架構設計比需求更需要對抗性審查。

### Agent A（Architect）—— 主責架構設計

| 屬性 | 內容 |
|------|------|
| Persona | `architect` |
| Goal | 將 SRS.md 中所有 FR/NFR 轉化為可實作的系統架構 |
| 職責 | 撰寫 SAD.md、定義模組邊界、決定技術選型、記錄架構決策（ADR） |
| 黃金準則 | 100% 對應 SRS FR 編號；架構分層符合 methodology-v2 命名規則 |
| 禁止 | 引入規格書與 methodology-v2 以外的第三方框架（防止幻覺）；私自妥協衝突 |

```python
# Phase 2 Agent A 啟動
from agent_spawner import spawn_with_persona

agent_a = spawn_with_persona(
    role="architect",
    task="依據 SRS.md 設計系統架構，產出 SAD.md",
)
```

### Agent B（Senior Dev / Reviewer）—— 主責架構審查

| 屬性 | 內容 |
|------|------|
| Persona | `reviewer` 或 `developer`（資深）|
| Goal | 以實作可行性角度挑戰架構設計，確保 Phase 3 不會踩坑 |
| 職責 | 審查模組解耦、介面定義、錯誤處理機制、技術選型合理性 |
| 核心問題 | 「這個架構在 Phase 3 能直接實作嗎？」|
| 禁止 | 代替 Agent A 重寫架構；不得跳過 AgentEvaluator |

```python
# Phase 2 Agent B 啟動
agent_b = spawn_with_persona(
    role="reviewer",
    task="審查 SAD.md 架構設計，從實作可行性角度提出問題",
)
```

### A/B 協作啟動

```python
from methodology import quick_start
from hybrid_workflow import HybridWorkflow
from agent_evaluator import AgentEvaluator

# 確保雙 Agent 運行（繼承 Phase 1 team 或重新建立）
team = quick_start("dev")         # Developer + Reviewer
workflow = HybridWorkflow(mode="ON")  # 強制 A/B 審查
evaluator = AgentEvaluator()

# 確認有 2+ Agent
team.list_agents()  # 必須 ≥ 2 個 Agent
```

---

## 2. WHAT — 做什麼？（Phase 2 交付物）

### 必要交付物（Mandatory）

| 文件 | 負責方 | 驗證方 | 位置 |
|------|--------|--------|------|
| `SAD.md` | Agent A | Agent B + Quality Gate | `02-architecture/` |
| `TRACEABILITY_MATRIX.md`（更新）| Agent A | Agent B | 專案根目錄 |
| `DEVELOPMENT_LOG.md`（Phase 2 段落）| Agent A | Agent B | 專案根目錄 |
| Conflict Log（若有衝突）| Agent A | Agent B | `DEVELOPMENT_LOG.md` 內 |

### SAD.md 最低內容要求

```markdown
# SAD - [專案名稱]

## 1. 架構概覽
- 系統邊界圖
- 核心模組清單

## 2. 模組設計
| 模組名稱 | 職責 | 對應 SRS FR | 依賴模組 |
|----------|------|-------------|----------|
| ModuleA  | ...  | FR-01, FR-02 | ModuleB |

## 3. 介面定義
- 模組間 API 合約
- 資料流向圖

## 4. 錯誤處理機制
- L1-L6 分類對應（參照 methodology-v2）
- Retry / Fallback / Circuit Breaker 設計

## 5. 技術選型決策（ADR）
| 決策 | 選擇 | 理由 | 替代方案 | 捨棄原因 |
|------|------|------|----------|----------|

## 6. 架構合規矩陣
| 模組 | 對應 methodology-v2 規範 | 執行狀態 | 備註 |
|------|--------------------------|----------|------|
```

### Spec Logic Mapping 延伸（Phase 2 版）

Phase 1 的 Spec Logic Mapping 在 Phase 2 必須延伸至架構層級：

| SRS ID | 需求描述 | 實作模組 | 架構驗證方法 |
|--------|----------|----------|-------------|
| FR-01  | 按標點分段 | TextProcessor.split() | 模組輸出長度 ≤ 輸入長度 |
| FR-05  | 多段合併 | AudioMerger.merge() | 單一與多檔案格式一致性測試 |
| NFR-01 | 99% 可用性 | CircuitBreaker + Retry | Fault Tolerance 四層架構 |

### A/B 架構審查清單（Agent B 逐項確認）

- [ ] SAD 模組列表完整對應所有 SRS FR 編號（無遺漏）
- [ ] 模組間耦合度合理（低耦合、高內聚）
- [ ] 每個外部依賴都有 Lazy Init 設計
- [ ] 錯誤處理明確對應 L1-L6 分類
- [ ] Retry / Fallback / Circuit Breaker 已設計
- [ ] 技術選型決策（ADR）已記錄，無「幻覺框架」
- [ ] 架構可直接指導 Phase 3 實作（無模糊地帶）
- [ ] TRACEABILITY_MATRIX.md 已從 FR → 模組 更新

---

## 3. WHEN — 何時執行？（時序 & 門檻）

### Phase 2 完整時序圖

```
Phase 1 sign-off ✅
        │
        ▼
[確認前置條件]
python3 quality_gate/phase_artifact_enforcer.py
        │
        ├── ❌ Phase 1 未完成 → 停止，回 Phase 1
        │
        └── ✅ 前置條件通過
                │
                ▼
        [Agent A] 讀取 SRS.md
        確認所有 FR / NFR 已理解
                │
                ▼
        [Agent A] 撰寫 SAD.md
        + Spec Logic Mapping 延伸
        + 技術選型 ADR
                │
                ▼
        [Agent A → Agent B]
        A/B 架構審查請求
        HybridWorkflow mode=ON 觸發
                │
                ├── ❌ REJECT
                │       │
                │       ▼
                │   記錄 Conflict Log
                │   Agent A 修改
                │   重新提交審查
                │
                └── ✅ APPROVE
                        │
                        ▼
                   Quality Gate 執行
                   （必須有實際命令輸出）
                        │
                        ├── 未通過 → Agent A 修正 → 重新 Gate
                        │
                        └── 通過（Compliance > 80%）
                                │
                                ▼
                        更新 TRACEABILITY_MATRIX.md
                        （FR → 模組 對應）
                                │
                                ▼
                        記錄到 DEVELOPMENT_LOG.md
                                │
                                ▼
                        ✅ Phase 2 完成 → 進入 Phase 3
```

### 進入 Phase 3 的前置條件（全部必須為 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| ASPICE 文檔合規率 | > 80% | Quality Gate doc_checker |
| Constitution SAD 分數：正確性 | = 100% | Constitution Runner |
| Constitution SAD 分數：可維護性 | > 70% | Constitution Runner |
| SPEC_TRACKING.md 存在 | 必須存在 | Framework Enforcement（BLOCK）|
| 所有 FR 在 SAD 中有對應模組 | 無遺漏 | Agent B 人工確認 |
| Agent B 已 APPROVE | AgentEvaluator 輸出 | AgentEvaluator |
| TRACEABILITY_MATRIX 已更新 | FR → 模組欄位完整 | Agent B |
| DEVELOPMENT_LOG 有實際輸出 | 非空泛文字 | Agent B 人工確認 |

---

## 4. WHERE — 在哪裡執行？（路徑 & 工具位置）

### 文件結構（Phase 2 新增 / 更新）

```
project-root/
├── 01-requirements/              ← Phase 1 產出（只讀，不修改）
│   ├── SRS.md
│   ├── SPEC_TRACKING.md
│   └── TRACEABILITY_MATRIX.md   ← Phase 2 更新（FR → 模組欄位）
│
├── 02-architecture/              ← Phase 2 主要工作區
│   └── SAD.md                   ← Agent A 主要產出
│
├── quality_gate/
│   ├── doc_checker.py           ← ASPICE 文檔檢查
│   ├── constitution/
│   │   └── runner.py            ← --type sad 執行
│   └── phase_artifact_enforcer.py  ← 確認 Phase 1 已完成
│
├── .methodology/
│   └── decisions/
│       └── check_decisions.py   ← 技術選型風險決策確認
│
└── DEVELOPMENT_LOG.md           ← Phase 2 段落（含 Conflict Log）
```

### 工具執行位置

```bash
# ── 前置確認 ────────────────────────────
python3 quality_gate/phase_artifact_enforcer.py

# ── Phase 2 Quality Gate ────────────────
python3 quality_gate/doc_checker.py
python3 quality_gate/constitution/runner.py --type sad

# ── 風險決策確認 ────────────────────────
python3 .methodology/decisions/check_decisions.py

# ── 規格追蹤更新 ────────────────────────
python3 cli.py spec-track check

# ── Framework Enforcement ───────────────
methodology quality
```

---

## 5. WHY — 為什麼這樣做？（設計理由）

### 架構決策的不可逆性

```
Phase 2 修改架構成本 ≈ 1×
Phase 3 開發中修改  ≈ 15×
Phase 4 測試後修改  ≈ 60×
Phase 5+ 交付後修改 ≈ 200×
```

A/B 在 Phase 2 攔截架構缺陷，是整個方法論中 ROI 最高的品質投入。

### 為什麼 Agent B 必須是「資深開發者」視角？

Architect（Agent A）擅長抽象設計，但可能產出「無法實作的優美架構」。Agent B 從**實作可行性**出發，提問：

- 「這個模組邊界在 Phase 3 怎麼測試？」
- 「這個 Lazy Init 設計是否會造成競態條件？」
- 「Circuit Breaker 的觸發條件有沒有具體數字？」

### 衝突處理原則（來自 methodology-v2 黃金準則）

當架構設計與 methodology-v2 規範衝突時：

1. **禁止私自妥協** — 不能悄悄選其中一個
2. **優先選擇符合 methodology-v2 的方式**
3. **在 Conflict Log 詳細記錄** — 格式如下：

```markdown
| 衝突點 | 規格書建議 | methodology-v2 選擇 | 理由 |
|--------|------------|---------------------|------|
| 快取機制 | Redis Cluster | 單機 Redis（符合架構分層規範）| 規格書未說明分散式需求 |
```

### 為什麼需要 ADR（架構決策記錄）？

SAD.md 寫「用 PostgreSQL」不夠——需要記錄**為什麼不用 MySQL**。ADR 的目的：
- Phase 3 開發者不重複發問
- Phase 7 風險評估有依據
- 未來版本迭代有決策軌跡

---

## 6. HOW — 如何執行？（完整 SOP）

### Step 0：前置確認（Agent A）

```bash
# 確認 Phase 1 已完成
python3 quality_gate/phase_artifact_enforcer.py

# 確認 SRS.md 可讀
cat 01-requirements/SRS.md | head -50

# 確認 SPEC_TRACKING.md 存在
python3 cli.py spec-track check
```

### Step 1：Agent A 設計架構

```markdown
設計順序（建議）：
1. 從 SRS.md 的 FR 清單出發，列出所有「動詞」（功能動作）
2. 將相關動詞聚合為模組（高內聚）
3. 定義模組間介面（低耦合）
4. 為每個外部依賴設計 Lazy Init
5. 對應 L1-L6 錯誤分類，設計 Fault Tolerance
6. 記錄每個重大技術選型為 ADR
7. 填寫架構合規矩陣（對照 methodology-v2 規範）
```

### Step 2：A/B 架構審查（Agent A → Agent B）

```python
from hybrid_workflow import HybridWorkflow
from agent_evaluator import AgentEvaluator

workflow = HybridWorkflow(mode="ON")
evaluator = AgentEvaluator()

# Agent B 執行架構評估
result = evaluator.evaluate(
    spec_a=sad_draft,            # Agent A 的 SAD.md
    spec_b=architecture_checklist  # Agent B 的審查標準
)

if not result.approved:
    # 記錄 Conflict Log，返回 Agent A 修改
    log_conflict(
        point=result.rejection_reason,
        spec_suggestion="...",
        methodology_choice="...",
        rationale="..."
    )
    raise Exception(f"SAD 未通過架構審查：{result.rejection_reason}")

print(f"✅ 架構審查通過，Evaluator Score：{result.score}/100")
```

**Agent B 架構審查對話模板**：

```markdown
## Phase 2 A/B 架構審查紀錄

### 審查維度 1：需求覆蓋完整性
- [ ] 所有 FR 在 SAD 中有對應模組
- [ ] 所有 NFR 有架構級別的保障機制
- 說明：______

### 審查維度 2：模組設計品質
- [ ] 模組邊界清晰，無職責重疊
- [ ] 依賴方向單向（無循環依賴）
- [ ] 每個模組可獨立測試
- 說明：______

### 審查維度 3：錯誤處理完整性
- [ ] L1-L6 分類已明確對應到模組
- [ ] Retry / Fallback 策略有具體參數（次數、間隔）
- [ ] Circuit Breaker 觸發條件已定義
- 說明：______

### 審查維度 4：技術選型合理性
- [ ] 所有技術選型都有 ADR 記錄
- [ ] 無引入規格書外的第三方框架
- [ ] 外部依賴均有 Lazy Init 設計
- 說明：______

### 審查維度 5：實作可行性
- [ ] Phase 3 開發者能直接從 SAD 開始實作
- [ ] 無「設計上優美但無法測試」的模組
- 說明：______

### 審查結論
- [ ] ✅ APPROVE — 進入 Quality Gate
- [ ] ❌ REJECT — 返回 Agent A（原因：______）

### Conflict Log（若有）
| 衝突點 | 規格書建議 | methodology-v2 選擇 | 理由 |
|--------|------------|---------------------|------|
|        |            |                     |      |

### Agent B 簽名：______  Session ID：______
### 日期：______
```

### Step 3：Quality Gate（必須有實際輸出）

```bash
# ASPICE 文檔檢查
python3 quality_gate/doc_checker.py

# Constitution SAD 檢查
python3 quality_gate/constitution/runner.py --type sad

# 風險決策確認
python3 .methodology/decisions/check_decisions.py

# 規格追蹤完整性
python3 cli.py spec-track check

# Framework Enforcement
methodology quality
```

### Step 4：更新 TRACEABILITY_MATRIX.md（Agent A）

```markdown
## TRACEABILITY_MATRIX.md 更新內容（Phase 2 新增欄位）

| FR ID  | 需求描述 | 實作模組（Phase 2 新增）| 測試案例（Phase 4 填入）|
|--------|----------|------------------------|------------------------|
| FR-01  | 按標點分段 | TextProcessor.split() | TC-001（待填）|
| FR-05  | 多段合併   | AudioMerger.merge()   | TC-005（待填）|
```

### Step 5：DEVELOPMENT_LOG.md 記錄（正確格式）

```markdown
## Phase 2 Quality Gate 結果（YYYY-MM-DD HH:MM）

### 前置條件確認
執行命令：python3 quality_gate/phase_artifact_enforcer.py
結果：Phase 1 完成 ✅

### ASPICE 文檔檢查
執行命令：python3 quality_gate/doc_checker.py
結果：
- Compliance Rate: XX%
- SAD.md: ✅ 存在
- TRACEABILITY_MATRIX.md: ✅ 已更新

### Constitution SAD 檢查
執行命令：python3 quality_gate/constitution/runner.py --type sad
結果：
- 正確性: XX%（目標 100%）
- 安全性: XX%（目標 100%）
- 可維護性: XX%（目標 > 70%）
- 測試覆蓋率: XX%（目標 > 80%）

### A/B 架構審查結果
- Agent A：Architect（session_id：______）
- Agent B：Reviewer（session_id：______）
- AgentEvaluator Score：XX/100
- 審查結論：APPROVE ✅ / REJECT ❌
- Conflict Log 條數：X 條（詳見下方）

### Conflict Log（若有）
| 衝突點 | 規格書建議 | methodology-v2 選擇 | 理由 |
|--------|------------|---------------------|------|

### Phase 2 結論
- [ ] ✅ 通過，進入 Phase 3
- [ ] ❌ 未通過（原因：______）
```

> ❌ **禁止這樣記錄**：
> ```markdown
> ### Phase 2 Quality Gate
> ✅ 已通過
> ```

---

## 7. Phase 2 完整清單（最終 Sign-off）

### Agent A 確認

- [ ] `SAD.md` 撰寫完成，所有 FR/NFR 有對應模組
- [ ] Spec Logic Mapping 已延伸至架構層級
- [ ] 每個技術選型都有 ADR 記錄
- [ ] 外部依賴均有 Lazy Init 設計
- [ ] 錯誤處理對應 L1-L6 分類
- [ ] `TRACEABILITY_MATRIX.md` 已更新（FR → 模組欄位）
- [ ] 已提交 A/B 架構審查請求

### Agent B 確認

- [ ] 五個審查維度逐項完成（需求覆蓋、模組設計、錯誤處理、技術選型、實作可行性）
- [ ] Conflict Log 已記錄（若有衝突）
- [ ] `AgentEvaluator` 評估完成
- [ ] 給出明確 APPROVE 或 REJECT（含理由）
- [ ] Session ID 已記錄

### Quality Gate 確認

- [ ] `doc_checker.py` 執行，Compliance Rate > 80%
- [ ] `constitution/runner.py --type sad` 執行，正確性 = 100%
- [ ] `check_decisions.py` 執行，無未確認的 HIGH 風險決策
- [ ] `methodology quality` 無 BLOCK 項目

### 記錄確認

- [ ] `DEVELOPMENT_LOG.md` 有實際命令輸出（非「已通過」空泛文字）
- [ ] A/B 審查紀錄完整（雙方 session_id、評分、結論）
- [ ] Conflict Log 存在（即使 0 條也要標明）

---

## 附錄：Phase 1 → Phase 2 知識傳遞

Phase 2 必須明確承接 Phase 1 的以下內容：

| Phase 1 產出 | Phase 2 使用方式 |
|--------------|-----------------|
| SRS.md FR 清單 | SAD 模組設計的直接依據 |
| Spec Logic Mapping 表 | 延伸為架構層級驗證方法 |
| SPEC_TRACKING.md | 確認外部規格已覆蓋到架構 |
| 初始 TRACEABILITY_MATRIX | Phase 2 新增「實作模組」欄位 |

---

## 附錄：快速指令備查

```bash
# ── 前置確認 ────────────────────────────
python3 quality_gate/phase_artifact_enforcer.py

# ── Agent 啟動 ──────────────────────────
# Agent A（架構師）
python -c "from agent_spawner import spawn_with_persona; spawn_with_persona(role='architect', task='SAD 架構設計')"

# Agent B（審查者）
python -c "from agent_spawner import spawn_with_persona; spawn_with_persona(role='reviewer', task='SAD 架構審查')"

# ── A/B 強制模式 ────────────────────────
python -c "from hybrid_workflow import HybridWorkflow; HybridWorkflow(mode='ON')"
python -m agent_evaluator --check

# ── Quality Gate ────────────────────────
python3 quality_gate/doc_checker.py
python3 quality_gate/constitution/runner.py --type sad
python3 .methodology/decisions/check_decisions.py
python3 cli.py spec-track check
methodology quality
```

---

*整理依據：SKILL.md v5.56 | methodology-v2 Multi-Agent Collaboration Development Methodology*
*格式：5W1H × A/B 協作機制 | 整理日期：2026-03-29*
