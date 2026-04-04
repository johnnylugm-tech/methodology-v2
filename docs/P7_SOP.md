# Phase 7 SOP — 風險管理

> 本檔案為 On-demand Lazy Load 檔案，僅在執行 Phase 7 時載入。
> 基於：SKILL.md v6.26 + PLAN_PHASE_SPEC.md

---

## 單一入口：plan-phase + run-phase

> ⚠️ **所有 Phase 執行必須經過此入口**，不可繞過。

### 用法

```bash
python cli.py plan-phase --phase 7 --goal "RISK_REGISTER.md"
python cli.py run-phase --phase 7
```

---

## Pre-flight 檢查（自動化）

| 檢查項 | 標準 | 不通過時 |
|--------|------|---------|
| FSM State | 非 FREEZE/PAUSED | ❌ 停在 Pre-flight |
| Phase Sequence | Phase 6 APPROVE → Phase 7 | ❌ HR-03 阻擋 |
| Constitution | TH-07 ≥90 | ❌ HR-08 阻擋 |
| 前置交付物 | QUALITY_REPORT.md 存在 | ❌ 停在 Pre-flight |
| Tool Registry | 6 核心工具就緒 | ⚠️ 警告 |

---

## A/B 角色（HR-01, HR-04）

| 角色 | Agent | 職責 |
|------|-------|------|
| **Agent A** | `qa` 或 `devops` | 撰寫 RISK_REGISTER.md |
| **Agent B** | `pm` 或 `architect` | 風險確認、演練 |

### 禁止事項（HR-01）
- ❌ 自寫自審（HR-01）
- ❌ Decision Gate 未確認
- ❌ sessions_spawn.log 缺失（HR-10）

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
  "citations": ["RISK_REGISTER.md#section"],
  "summary": "50字內摘要"
}
```

---

## Step-by-Step 執行

### Step 7.1: 風險識別

| 項目 | 內容 |
|------|------|
| **工具** | SubagentIsolator（Agent A: qa/devops）|
| **Prompt** | 使用 `templates/RISK_REGISTER.md` 模板 |
| **驗證** | TH-07 ≥90 |

### Step 7.2: 風險緩解計畫

| 項目 | 內容 |
|------|------|
| **工具** | SubagentIsolator |
| **驗證** | Decision Gate = 100%（每個風險都有對應緩解）|

### Step 7.3: A/B 審查

| 項目 | 內容 |
|------|------|
| **工具** | SubagentIsolator（Agent B: pm/architect）|
| **驗證** | Decision Gate = 100% |
| **產出** | APPROVE 或 REJECT |

---

## 閾值對照（TH-07）

| 閾值 | 門檻 | 驗證方式 |
|------|------|---------|
| TH-07 | 邏輯正確性 ≥90 | verification |

---

## HR-12/13 時間追蹤

| Step | 預估 | HR-13 臨界值 |
|------|------|--------------|
| 7.1 | 60m | 180m |
| 7.2 | 45m | 135m |
| 7.3 | 30m | 90m |
| **總計** | **135m** | **405m** |

---

## 交付物

| 交付物 | 模板 | 驗證 |
|--------|------|------|
| RISK_REGISTER.md | `templates/RISK_REGISTER.md` | Decision Gate = 100% |

---

## Exit 條件

- ✅ TH-07 ≥90
- ✅ Decision Gate = 100%
- ✅ Agent B APPROVE
- ✅ sessions_spawn.log 有記錄（HR-10）
