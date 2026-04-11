# Phase 6 SOP — 品質保證

> 本檔案為 On-demand Lazy Load 檔案，僅在執行 Phase 6 時載入。
> 基於：SKILL.md v6.26 + PLAN_PHASE_SPEC.md

---

## 單一入口：plan-phase + run-phase

> ⚠️ **所有 Phase 執行必須經過此入口**，不可繞過。

### 用法

```bash
python cli.py plan-phase --phase 6 --goal "QUALITY_REPORT.md"
python cli.py run-phase --phase 6
```

---

## Pre-flight 檢查（自動化）

| 檢查項 | 標準 | 不通過時 |
|--------|------|---------|
| FSM State | 非 FREEZE/PAUSED | ❌ 停在 Pre-flight |
| Phase Sequence | Phase 5 APPROVE → Phase 6 | ❌ HR-03 阻擋 |
| Constitution | TH-02 ≥80% | ❌ HR-08 阻擋 |
| 前置交付物 | BASELINE.md, MONITORING_PLAN.md 存在 | ❌ 停在 Pre-flight |
| Tool Registry | 6 核心工具就緒 | ⚠️ 警告 |

---

## A/B 角色（HR-01, HR-04）

| 角色 | Agent | 職責 |
|------|-------|------|
| **Agent A** | `qa` | 撰寫 QUALITY_REPORT.md |
| **Agent B** | `architect` 或 `pm` | 品質確認 |

### 禁止事項（HR-01, HR-07）
- ❌ 自寫自審（HR-01）
- ❌ session_id 缺失（HR-07）
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
  "citations": ["QUALITY_REPORT.md#section"],
  "summary": "50字內摘要"
}
```

---

## Step-by-Step 執行

### Step 6.1: 撰寫 QUALITY_REPORT.md

| 項目 | 內容 |
|------|------|
| **工具** | SubagentIsolator（Agent A: qa）|
| **Prompt** | 使用 `templates/QUALITY_REPORT.md` 模板 |
| **驗證** | TH-02 ≥80% |

### Step 6.2: A/B 審查

| 項目 | 內容 |
|------|------|
| **工具** | SubagentIsolator（Agent B: architect/pm）|
| **驗證** | Constitution TH-02 ≥80%, TH-07 ≥90 |
| **產出** | APPROVE 或 REJECT |

---

## 閾值對照（TH-02, TH-07）

| 閾值 | 門檻 | 驗證方式 |
|------|------|---------|
| TH-02 | Constitution 總分 ≥80% | constitution runner |
| TH-07 | 邏輯正確性 ≥90 | verification |

---

## HR-12/13 時間追蹤

| Step | 預估 | HR-13 臨界值 |
|------|------|--------------|
| 6.1 | 60m | 180m |
| 6.2 | 30m | 90m |
| **總計** | **90m** | **270m** |

---

## 交付物

| 交付物 | 模板 | 驗證 |
|--------|------|------|
| QUALITY_REPORT.md | `templates/QUALITY_REPORT.md` | TH-02 ≥80%, TH-07 ≥90 |

---

## Exit 條件

- ✅ Constitution TH-02 ≥80%
- ✅ TH-07 ≥90
- ✅ Agent B APPROVE
- ✅ sessions_spawn.log 有記錄（HR-10）
- ✅ DEVELOPMENT_LOG 有 session_id（HR-07）

---

## Traceability 驗證（Quality→Audit 連結）

> ⚠️ **Phase 6 必須建立 Quality Score→Audit Finding 連結，完成完整追溯鏈**

### 驗證時機

| Step | 內容 | Traceability 動作 |
|------|------|------------------|
| 6.1 | 執行審計 | 建立 Quality→Audit 連結 |
| 6.2 | 產出報告 | 驗證完整追溯鏈 |

### 使用方式

```python
from requirement_traceability import RequirementTraceability

rt = RequirementTraceability(project_id="my-project")

# 建立 Quality→Audit Finding 連結
rt.add_link(
    source_type="quality",
    source_id="BASELINE: Test Coverage 85%",
    target_type="audit",
    target_id="AUDIT: FR-01 Verified",
    link_type=LinkType.QUALITY_TO_AUDIT
)

# 驗證完整追溯鏈（FR→SRS→Code→Test→Quality→Audit）
result = rt.verify_completeness()
print(f"Complete traceability chain: {result['overall_completeness']}")
```

### 完整追溯鏈驗證

```
FR-01 → SRS.md §2.1 → src/processing/lexicon_mapper.py
    → tests/test_fr01_lexicon_mapper.py
    → Quality Score: 85%
    → AUDIT: VERIFIED ✓
```

### 驗證命令

```bash
# 驗證完整追溯鏈
python requirement_traceability.py \
    --project-id my-project \
    --verify \
    --format aspice \
    --export phase6_traceability.json
```

### ASPICE 合規最終驗證

| ASPICE 能力 | Phase 1 | Phase 2 | Phase 3 | Phase 4 | Phase 5 | Phase 6 |
|-------------|---------|---------|---------|---------|---------|---------|
| SWE.3.B.SP1 | ✅ FR→SRS | ✅ SAD | ✅ Code | ✅ Test | ✅ | ✅ Audit |
| SWE.3.B.SP2 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| SWE.3.B.SP3 | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
