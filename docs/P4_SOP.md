# Phase 4 SOP — 測試

> 本檔案為 On-demand Lazy Load 檔案，僅在執行 Phase 4 時載入。
> 基於：SKILL.md v6.26 + PLAN_PHASE_SPEC.md

---

## 單一入口：plan-phase + run-phase

> ⚠️ **所有 Phase 執行必須經過此入口**，不可繞過。

### 用法

```bash
# Step 1: 生成執行計畫
python cli.py plan-phase --phase 4 --goal "TEST_PLAN.md, TEST_RESULTS.md"

# Step 2: Johnny 審核計畫

# Step 3: 執行計畫
python cli.py run-phase --phase 4
```

---

## Pre-flight 檢查（自動化）

| 檢查項 | 標準 | 不通過時 |
|--------|------|---------|
| FSM State | 非 FREEZE/PAUSED | ❌ 停在 Pre-flight |
| Phase Sequence | Phase 3 APPROVE → Phase 4 | ❌ HR-03 阻擋 |
| Constitution | TH-06>80% | ❌ HR-08 阻擋 |
| 前置交付物 | 代碼存在於 `app/` | ❌ 停在 Pre-flight |
| Tool Registry | 6 核心工具就緒 | ⚠️ 警告 |

---

## A/B 角色（HR-01, HR-04）

| 角色 | Agent | 職責 |
|------|-------|------|
| **Agent A** | `qa` | 撰寫 TEST_PLAN.md, TEST_RESULTS.md |
| **Agent B** | `reviewer` | 兩次審查 |

### 禁止事項（HR-01, HR-04, HR-06）
- ❌ 自寫自審（HR-01）
- ❌ HybridWorkflow=OFF（HR-04）
- ❌ 引入規格書外框架（HR-06）
- ❌ sessions_spawn.log 缺失（HR-10）
- ❌ Tester = Developer

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
  "citations": ["FR-01", "SRS.md#section"],
  "summary": "50字內摘要"
}
```

---

## Step-by-Step 執行

### Step 4.1: 撰寫 TEST_PLAN.md

| 項目 | 內容 |
|------|------|
| **工具** | SubagentIsolator（Agent A: qa）|
| **Prompt** | 使用 `templates/TEST_PLAN.md` 模板 |
| **驗證** | FR↔測試映射 TH-17 ≥90% |

### Step 4.2: 執行測試

| 項目 | 內容 |
|------|------|
| **工具** | exec + PermissionGuard |
| **命令** | `pytest --cov=app --cov-report=term` |
| **驗證** | TH-10=100%, TH-12 ≥80% |

### Step 4.3: A/B 審查（兩次，HR-01）

| 項目 | 內容 |
|------|------|
| **工具** | SubagentIsolator（Agent B: reviewer）|
| **驗證** | Constitution TH-06>80%, TH-03=100%, TH-04=100% |
| **產出** | APPROVE 或 REJECT |

---

## 閾值對照（TH-01, TH-03, TH-04, TH-06, TH-10, TH-12, TH-13, TH-17）

| 閾值 | 門檻 | 驗證方式 |
|------|------|---------|
| TH-01 | ASPICE >80% | ASPICE check |
| TH-03 | Constitution 正確性 =100% | constitution runner |
| TH-04 | Constitution 安全性 =100% | constitution runner |
| TH-06 | Constitution 測試覆蓋率 >80% | constitution runner |
| TH-10 | 測試通過率 =100% | pytest |
| TH-12 | 單元測試覆蓋率 ≥80% | pytest --cov |
| TH-13 | SRS FR 覆蓋率 =100% | trace-check |
| TH-17 | FR↔測試映射率 ≥90% | trace-check |

---

## HR-12/13 時間追蹤

| Step | 預估 | HR-13 臨界值 |
|------|------|--------------|
| 4.1 | 60m | 180m |
| 4.2 | 90m | 270m |
| 4.3 | 60m | 180m |
| **總計** | **210m** | **630m** |

---

## 交付物

| 交付物 | 模板 | 驗證 |
|--------|------|------|
| TEST_PLAN.md | `templates/TEST_PLAN.md` | TH-06>80%, TH-17 ≥90% |
| TEST_RESULTS.md | `templates/TEST_RESULTS.md` | TH-10=100%, TH-12 ≥80% |

---

## Exit 條件

- ✅ Constitution TH-06>80%, TH-03=100%, TH-04=100%
- ✅ TH-10=100%, TH-12 ≥80%
- ✅ TH-13=100%, TH-17 ≥90%
- ✅ Agent B 兩次 APPROVE
- ✅ sessions_spawn.log 有記錄（HR-10）
