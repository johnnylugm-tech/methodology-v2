# Phase 2 SOP — 架構設計

> 本檔案為 On-demand Lazy Load 檔案，僅在執行 Phase 2 時載入。
> 基於：SKILL.md v6.26 + PLAN_PHASE_SPEC.md

---

## 單一入口：plan-phase + run-phase

> ⚠️ **所有 Phase 執行必須經過此入口**，不可繞過。

### 用法

```bash
# Step 1: 生成執行計畫
python cli.py plan-phase --phase 2 --goal "SAD.md, ADR.md"

# Step 2: Johnny 審核計畫

# Step 3: 執行計畫
python cli.py run-phase --phase 2
```

---

## Pre-flight 檢查（自動化）

| 檢查項 | 標準 | 不通過時 |
|--------|------|---------|
| FSM State | 非 FREEZE/PAUSED | ❌ 停在 Pre-flight |
| Phase Sequence | Phase 1 APPROVE → Phase 2 | ❌ HR-03 阻擋 |
| Constitution | TH-03=100%, TH-04=100%, TH-05>70% | ❌ HR-08 阻擋 |
| 前置交付物 | SRS.md 存在且完整 | ❌ 停在 Pre-flight |
| Tool Registry | 6 核心工具就緒 | ⚠️ 警告 |

---

## A/B 角色（HR-01, HR-04）

| 角色 | Agent | 職責 |
|------|-------|------|
| **Agent A** | `architect` | 撰寫 SAD.md, ADR |
| **Agent B** | `reviewer` | 架構審查、Conflict Log |

### 禁止事項（HR-01, HR-04, HR-06）
- ❌ 自寫自審（HR-01）
- ❌ HybridWorkflow=OFF（HR-04）
- ❌ 引入規格書外框架（HR-06）
- ❌ sessions_spawn.log 缺失（HR-10）
- ❌ 程式碼省略號`...`（任務失敗）

---

## 四大工具定位

| 工具 | 解決的問題 | 觸發時機 |
|------|-----------|---------|
| `KnowledgeCurator` | 知識一致性 | **派遣前**（verify_coverage）|
| `ContextManager` | 上下文膨脹 | **派遣後**（context > 50）|
| `SubagentIsolator` | 結果污染 | **派遣時**（spawn）|
| `PermissionGuard` | 危險操作 | **任何 exec/rm 前** |

---

## 產出格式標準

```json
{
  "status": "success | error | unable_to_proceed",
  "result": "實際產出",
  "confidence": 1-10,
  "citations": ["FR-01", "SAD.md#section"],
  "summary": "50字內摘要"
}
```

---

## Step-by-Step 執行

### Step 2.1: 架構設計

| 項目 | 內容 |
|------|------|
| **工具** | SubagentIsolator（Agent A: architect）|
| **Prompt** | 使用 `templates/SAD.md` 模板 |
| **驗證** | TH-05 >70% |

### Step 2.2: ADR 決策記錄

| 項目 | 內容 |
|------|------|
| **工具** | SubagentIsolator（Agent A: architect）|
| **Prompt** | 使用 `templates/ADR.md` 模板 |
| **驗證** | 架構決策有據可查 |

### Step 2.3: A/B 審查（HR-01）

| 項目 | 內容 |
|------|------|
| **工具** | SubagentIsolator（Agent B: reviewer）|
| **驗證** | Constitution TH-03=100%, TH-04=100%, TH-05>70% |
| **產出** | APPROVE 或 REJECT |

---

## 閾值對照（TH-01, TH-03, TH-04, TH-05, TH-08, TH-15）

| 閾值 | 門檻 | 驗證方式 |
|------|------|---------|
| TH-01 | ASPICE >80% | ASPICE check |
| TH-03 | Constitution 正確性 =100% | constitution runner |
| TH-04 | Constitution 安全性 =100% | constitution runner |
| TH-05 | Constitution 可維護性 >70% | constitution runner |
| TH-08 | AgentEvaluator ≥80 | agent_evaluator |
| TH-15 | Phase Truth ≥70% | phase-verify |

---

## HR-12/13 時間追蹤

| Step | 預估 | HR-13 臨界值 |
|------|------|--------------|
| 2.1 | 90m | 270m |
| 2.2 | 30m | 90m |
| 2.3 | 45m | 135m |
| **總計** | **165m** | **495m** |

---

## 交付物

| 交付物 | 模板 | 驗證 |
|--------|------|------|
| SAD.md | `templates/SAD.md` | TH-03=100%, TH-04=100%, TH-05>70% |
| ADR.md | `templates/ADR.md` | 架構決策記錄完整 |

---

## Exit 條件

- ✅ Constitution TH-03=100%, TH-04=100%, TH-05>70%
- ✅ TH-01 >80%
- ✅ Agent B APPROVE
- ✅ sessions_spawn.log 有記錄（HR-10）
