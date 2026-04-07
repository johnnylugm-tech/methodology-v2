# Phase 1 計劃：功能規格
## methodology-v2 | 5W1H 框架 × A/B 協作機制

> **版本基準**：SKILL.md v5.56 | 整理日期：2026-03-29

---

## 🗺️ 一覽表

| 5W1H | 核心答案 |
|------|----------|
| **WHO**   | Agent A（Architect）撰寫 × Agent B（Reviewer/PM）審查 |
| **WHAT**  | 產出 SRS.md + 初始化 SPEC/TRACE 追蹤文件 |
| **WHEN**  | 專案啟動後第一個 Phase；所有其他 Phase 的前置條件 |
| **WHERE** | `01-requirements/` 目錄；Quality Gate 工具在 `quality_gate/` |
| **WHY**   | 建立需求基線、ASPICE 合規、防止規格漂移 |
| **HOW**   | A 撰寫 → B 審查 → Quality Gate → 雙方 sign-off → 進入 Phase 2 |

---

## 1. WHO — 誰執行？（A/B 角色分工）

> ⚠️ **強制原則**：A/B 必須是不同 Agent，禁止自寫自審。

### Agent A（Architect）—— 主責撰寫

| 屬性 | 內容 |
|------|------|
| Persona | `architect` |
| Goal | 將需求轉化為符合 ASPICE 規範的 SRS.md |
| 職責 | 撰寫 SRS、建立 SPEC_TRACKING.md、初始化 TRACEABILITY_MATRIX.md |
| 禁止 | 自行通過 Quality Gate；不得審查自己的產出 |

```python
# 啟動 Agent A
from methodology import quick_start
from agent_spawner import spawn_with_persona

team = quick_start("dev")  # Developer + Reviewer 最小配置
agent_a = spawn_with_persona(role="architect", task="撰寫 Phase 1 SRS")
```

### Agent B（Reviewer / PM）—— 主責審查

| 屬性 | 內容 |
|------|------|
| Persona | `reviewer` 或 `pm` |
| Goal | 確保需求完整、邏輯無矛盾、符合方法論規範 |
| 職責 | 審查 SRS 品質、執行 A/B 評估、給出 approve 或 reject |
| 禁止 | 代替 Agent A 修改內容；不得跳過 AgentEvaluator |

```python
# 強制 A/B 評估
from agent_evaluator import AgentEvaluator
from hybrid_workflow import HybridWorkflow

evaluator = AgentEvaluator()
workflow = HybridWorkflow(mode="ON")  # 強制 A/B 審查模式
```

---

## 2. WHAT — 做什麼？（Phase 1 交付物）

### 必要交付物（Mandatory）

| 文件 | 負責方 | 驗證方 |
|------|--------|--------|
| `SRS.md` | Agent A | Agent B + Quality Gate |
| `SPEC_TRACKING.md` | Agent A | Quality Gate（BLOCK 項目）|
| `TRACEABILITY_MATRIX.md` | Agent A | Agent B |
| `DEVELOPMENT_LOG.md`（Phase 1 段落） | Agent A | Agent B |

### SRS.md 最低內容要求

```markdown
# SRS - [專案名稱]

## 1. 需求概述
## 2. 功能需求（FR-01 ~ FR-XX）
## 3. 非功能需求（NFR）
## 4. 限制條件
## 5. 術語表

# 每條 FR 必須附上「邏輯驗證方法」（Spec Logic Mapping）
| SRS ID | 需求描述 | 實作函數（預估） | 邏輯驗證方法 |
|--------|----------|----------------|-------------|
| FR-01  | ...      | ...            | 輸出 ≤ 輸入  |
```

### A/B 審查清單（Agent B 逐項確認）

- [ ] 所有 FR 編號唯一、無遺漏
- [ ] 每條 FR 有對應的邏輯驗證方法
- [ ] 無「輸出可能大於輸入」的隱患
- [ ] 分支邏輯（if/else）覆蓋完整
- [ ] 外部依賴已標記 Lazy Check 需求
- [ ] SPEC_TRACKING.md 已建立
- [ ] TRACEABILITY_MATRIX.md 已初始化

---

## 3. WHEN — 何時執行？（時序 & 門檻）

### Phase 1 時序圖

```
專案啟動
    │
    ▼
[Agent A] methodology init          ← 初始化追蹤文件（自動建立 3 個文件）
    │
    ▼
[Agent A] 撰寫 SRS.md               ← 包含 Spec Logic Mapping 表格
    │
    ▼
[Agent A → Agent B] A/B 審查請求    ← HybridWorkflow mode=ON 觸發
    │
    ├──── B: REJECT ──────────────→ Agent A 修改 → 重新提交
    │
    └──── B: APPROVE
              │
              ▼
         Quality Gate 執行           ← 必須有實際命令輸出
              │
              ├── 未通過 → Agent A 修正 → 重新 Gate
              │
              └── 通過（Compliance > 80%）
                        │
                        ▼
                  記錄到 DEVELOPMENT_LOG.md
                        │
                        ▼
                  ✅ Phase 1 完成 → 進入 Phase 2
```

### 進入 Phase 2 的前置條件（全部必須為 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| ASPICE 文檔合規率 | > 80% | Quality Gate |
| Constitution SRS 分數 | 正確性 100%、可維護性 > 70% | Constitution Runner |
| SPEC_TRACKING.md 存在 | 必須存在 | Framework Enforcement（BLOCK）|
| Agent B 已 approve | 必須完成 | AgentEvaluator |
| DEVELOPMENT_LOG.md 有實際輸出記錄 | 不能只寫「已通過」| Agent B 人工確認 |

---

## 4. WHERE — 在哪裡執行？（路徑 & 工具位置）

### 文件結構

```
project-root/
├── 01-requirements/
│   ├── SRS.md                        ← Agent A 主要產出
│   ├── SPEC_TRACKING.md              ← 規格追蹤（BLOCK 必要）
│   └── TRACEABILITY_MATRIX.md        ← 需求追蹤矩陣
│
├── quality_gate/
│   ├── doc_checker.py                ← ASPICE 文檔檢查
│   ├── constitution/
│   │   └── runner.py                 ← Constitution 品質檢查
│   └── phase_artifact_enforcer.py   ← Phase 依賴順序檢查
│
├── .methodology/
│   └── decisions/
│       └── check_decisions.py        ← 風險決策確認
│
└── DEVELOPMENT_LOG.md                ← Phase 1 段落（必須記錄實際輸出）
```

### 工具執行位置

```bash
# 所有命令在 project-root/ 執行

# 初始化（Agent A）
methodology init

# Quality Gate（Phase 1 結束時執行）
python3 quality_gate/doc_checker.py
python3 quality_gate/constitution/runner.py --type srs

# 規格追蹤
python3 cli.py spec-track init    # 初始化
python3 cli.py spec-track check   # 完整性檢查
```

---

## 5. WHY — 為什麼這樣做？（設計理由）

### 需求基線的價值

| 如果跳過 Phase 1 | 後果 |
|-----------------|------|
| 無 SRS.md | Phase 3 開發無依據，出現「規格漂移」 |
| 無 SPEC_TRACKING.md | Framework Enforcement **BLOCK**，無法執行 `methodology quality` |
| 無 Spec Logic Mapping | Phase 3 可能出現「輸出 > 輸入」等邏輯錯誤（參考 PolyTrade 案例）|
| 跳過 A/B 審查 | 需求缺陷到 Phase 4 才發現，修復成本 × 10 |

### A/B 協作的核心理由（來自 PolyTrade 案例）

> **PolyTrade 完整度僅 44% 的根本原因之一**：沒有使用雙 Agent，沒人審查需求，
> 錯誤直到測試階段才暴露。A/B 機制的目的是把缺陷攔截在 Phase 1。

```
Phase 1 A/B 審查攔截缺陷成本 ≈ 1×
Phase 3 開發後才發現 ≈ 10×
Phase 4 測試後才發現 ≈ 50×
```

### ASPICE 合規理由

methodology-v2 對標 ASPICE 標準，Phase 1 對應：
- **SWE.1**：軟體需求分析
- **MAN.3**：專案管理（TRACEABILITY 追蹤）
- **SUP.8**：配置管理（版本控制基礎）

---

## 6. HOW — 如何執行？（完整 SOP）

### Step 0：初始化（Agent A）

```bash
# 1. 建立專案結構
methodology init

# 自動建立：
# ✅ TRACEABILITY_MATRIX.md
# ✅ SPEC_TRACKING.md
# ✅ Phase 目錄結構（01-requirements/ 等）
```

### Step 1：Agent A 撰寫 SRS（Agent A）

```markdown
1. 使用 architect persona
2. 撰寫 SRS.md，包含：
   - 功能需求（FR-01 起編號）
   - 非功能需求（NFR）
   - Spec Logic Mapping 表格（每條 FR 必填）
3. 更新 SPEC_TRACKING.md
4. 初始化 TRACEABILITY_MATRIX.md
```

### Step 2：A/B 審查（Agent A → Agent B）

```python
from hybrid_workflow import HybridWorkflow
from agent_evaluator import AgentEvaluator

# 觸發 A/B 審查
workflow = HybridWorkflow(mode="ON")
evaluator = AgentEvaluator()

# Agent B 執行評估
result = evaluator.evaluate(
    spec_a=srs_draft,       # Agent A 的產出
    spec_b=review_checklist # Agent B 的審查標準
)

if not result.approved:
    # 返回 Agent A 修改
    raise Exception(f"SRS 未通過 A/B 審查：{result.rejection_reason}")

# 通過後繼續
print("✅ A/B 審查通過")
```

**Agent B 審查對話模板**：

```markdown
## Phase 1 A/B 審查紀錄

### Agent B 審查項目
1. FR 完整性：[✅/❌] 說明：______
2. 邏輯驗證方法：[✅/❌] 說明：______
3. 邊界條件覆蓋：[✅/❌] 說明：______
4. 外部依賴 Lazy Check 標記：[✅/❌] 說明：______
5. SPEC_TRACKING 連結：[✅/❌] 說明：______

### 審查結論
- [ ] ✅ APPROVE — 進入 Quality Gate
- [ ] ❌ REJECT — 返回 Agent A 修改（原因：______）

### Agent B 簽名：______
### 日期：______
```

### Step 3：Quality Gate（雙方皆可執行，結果記錄到 LOG）

```bash
# 必須執行，不能跳過
python3 quality_gate/doc_checker.py
python3 quality_gate/constitution/runner.py --type srs

# 規格追蹤完整性
python3 cli.py spec-track check
```

**DEVELOPMENT_LOG.md 正確記錄格式**：

```markdown
## Phase 1 Quality Gate 結果（YYYY-MM-DD HH:MM）

### ASPICE 文檔檢查
執行命令：python3 quality_gate/doc_checker.py
結果：
- Compliance Rate: XX%
- SRS.md: ✅ 存在
- SPEC_TRACKING.md: ✅ 存在

### Constitution SRS 檢查
執行命令：python3 quality_gate/constitution/runner.py --type srs
結果：
- 正確性: XX%（目標 100%）
- 安全性: XX%（目標 100%）
- 可維護性: XX%（目標 > 70%）
- 測試覆蓋率: XX%（目標 > 80%）

### A/B 審查結果
- Agent A：Architect（[session_id]）
- Agent B：Reviewer（[session_id]）
- 審查結論：APPROVE ✅ / REJECT ❌
- Evaluator Score：XX/100

### Phase 1 結論
- [ ] ✅ 通過，進入 Phase 2
- [ ] ❌ 未通過（原因：______）
```

> ❌ **禁止這樣記錄**：
> ```markdown
> ### Phase 1 Quality Gate
> ✅ 已通過
> ```

### Step 4：Framework Enforcement 確認（系統自動）

```bash
# 執行 methodology quality 時自動觸發
methodology quality

# 預期輸出：
# ✅ SPEC_TRACKING.md 存在
# ✅ 規格完整性 > 90%
# ✅ Constitution Score > 60%
# ✅ Framework Enforcement 通過
```

---

## 7. Phase 1 完整清單（最終 Sign-off）

### Agent A 確認

- [ ] `SRS.md` 撰寫完成，包含所有 FR 及 Spec Logic Mapping
- [ ] `SPEC_TRACKING.md` 已建立（非空）
- [ ] `TRACEABILITY_MATRIX.md` 已初始化
- [ ] 已提交 A/B 審查請求

### Agent B 確認

- [ ] 逐條審查 FR 完整性
- [ ] 確認所有 FR 有邏輯驗證方法
- [ ] AgentEvaluator 評估完成
- [ ] 給出明確 APPROVE 或 REJECT

### Quality Gate 確認

- [ ] `doc_checker.py` 執行，Compliance Rate > 80%
- [ ] `constitution/runner.py --type srs` 執行，正確性 = 100%
- [ ] `spec-track check` 通過
- [ ] `methodology quality` 無 BLOCK 項目

### 記錄確認

- [ ] `DEVELOPMENT_LOG.md` 有實際命令輸出（非「已通過」空泛文字）
- [ ] A/B 審查記錄已存入 LOG
- [ ] 雙方 session_id 已記錄（可追溯）

---

## 附錄：快速指令備查

```bash
# ── 初始化 ──────────────────────────────
methodology init

# ── Agent 啟動 ──────────────────────────
# Agent A
python -c "from agent_spawner import spawn_with_persona; spawn_with_persona(role='architect', task='SRS')"

# Agent B  
python -c "from agent_spawner import spawn_with_persona; spawn_with_persona(role='reviewer', task='SRS Review')"

# ── 品質檢查 ────────────────────────────
python3 quality_gate/doc_checker.py
python3 quality_gate/constitution/runner.py --type srs
python3 cli.py spec-track check
methodology quality

# ── A/B 評估 ────────────────────────────
python -m agent_evaluator --check

# ── Phase Enforcer ──────────────────────
python3 quality_gate/phase_artifact_enforcer.py
```

---

*整理依據：SKILL.md v5.56 | methodology-v2 Multi-Agent Collaboration Development Methodology*
*格式：5W1H × A/B 協作機制 | 整理日期：2026-03-29*
