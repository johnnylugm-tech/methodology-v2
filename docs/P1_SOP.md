# Phase 1 SOP — 需求規格

> 本檔案為 On-demand Lazy Load 檔案，僅在執行 Phase 1 時載入。
> 基於：SKILL.md v6.26 + PLAN_PHASE_SPEC.md

---

## 單一入口：plan-phase + run-phase

> ⚠️ **所有 Phase 執行必須經過此入口**，不可繞過。

### 用法

```bash
# Step 1: 生成執行計畫
python cli.py plan-phase --phase 1 --goal "SRS.md, SPEC_TRACKING.md, TRACEABILITY_MATRIX.md"

# Step 2: Johnny 審核計畫

# Step 3: 執行計畫
python cli.py run-phase --phase 1
```

### 完整流程

```
plan-phase（生成計畫） → Johnny 審核 → run-phase（執行）
                                        ↓
                              失敗 → plan-phase --repair
```

---

## Pre-flight 檢查（自動化）

| 檢查項 | 標準 | 不通過時 |
|--------|------|---------|
| FSM State | 非 FREEZE/PAUSED | ❌ 停在 Pre-flight |
| Phase Sequence | Phase 0 → Phase 1 | ❌ HR-03 阻擋 |
| Constitution | TH-03=100%, TH-04=100% | ❌ HR-08 阻擋 |
| Tool Registry | 6 核心工具就緒 | ⚠️ 警告 |
| Integrity | ≥ 40 | ❌ HR-14 FREEZE |

---

## A/B 角色（HR-01, HR-04）

| 角色 | Agent | 職責 |
|------|-------|------|
| **Agent A** | `architect` | 撰寫 SRS.md, SPEC_TRACKING.md, TRACEABILITY_MATRIX.md |
| **Agent B** | `reviewer` | 審查 FR 完整性、A/B 評估 |

### 禁止事項（HR-01, HR-04, HR-06）
- ❌ 自寫自審（HR-01）
- ❌ HybridWorkflow=OFF（HR-04）
- ❌ 引入規格書外框架（HR-06）
- ❌ sessions_spawn.log 缺失（HR-10）
- ❌ 程式碼省略號`...`（任務失敗）
- ❌ 編造內容（HR-06）

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

### confidence 評估

| 分數 | 意義 | 動作 |
|------|------|------|
| 9-10 | 高度確定，有引用 | 繼續 |
| 7-8 | 確定，無引用 | 標記，繼續 |
| 5-6 | 不確定 | 重新派遣 |
| 1-4 | 嚴重懷疑 | 上報 Johnny |

---

## Step-by-Step 執行

### Step 1.1: 需求收集

| 項目 | 內容 |
|------|------|
| **工具** | KnowledgeCurator |
| **命令** | `python cli.py knowledge-curator --verify FR` |
| **驗證** | FR 覆蓋率 = 100% |

### Step 1.2: 撰寫 SRS.md

| 項目 | 內容 |
|------|------|
| **工具** | SubagentIsolator（Agent A: architect）|
| **Prompt** | 使用 `templates/SRS.md` 模板 |
| **驗證** | TH-14 ≥90% |

### Step 1.3: A/B 審查（HR-01）

| 項目 | 內容 |
|------|------|
| **工具** | SubagentIsolator（Agent B: reviewer）|
| **驗證** | Constitution TH-03=100%, TH-04=100% |
| **產出** | APPROVE 或 REJECT |

---

## 閾值對照（TH-01, TH-03, TH-04, TH-08, TH-14, TH-15）

| 閾值 | 門檻 | 驗證方式 |
|------|------|---------|
| TH-01 | ASPICE >80% | ASPICE check |
| TH-03 | Constitution 正確性 =100% | constitution runner |
| TH-04 | Constitution 安全性 =100% | constitution runner |
| TH-08 | AgentEvaluator ≥80 | agent_evaluator |
| TH-14 | 規格完整性 ≥90% | doc_checker |
| TH-15 | Phase Truth ≥70% | phase-verify |

---

## HR-12/13 時間追蹤

| Step | 預估 | HR-13 臨界值 |
|------|------|--------------|
| 1.1 | 15m | 45m |
| 1.2 | 60m | 180m |
| 1.3 | 30m | 90m |
| **總計** | **105m** | **315m** |

---

## 交付物

| 交付物 | 模板 | 驗證 |
|--------|------|------|
| SRS.md | `templates/SRS.md` | TH-14 ≥90% |
| SPEC_TRACKING.md | `templates/SPEC_TRACKING.md` | TH-01 >80% |
| TRACEABILITY_MATRIX.md | `templates/TRACEABILITY_MATRIX.md` | TH-15 ≥70% |

---

## DEVELOPMENT_LOG 格式（HR-07）

```json
{
  "timestamp": "{ISO8601}",
  "session_id": "{uuid}",
  "phase": 1,
  "step": "1.{X}",
  "agent": "{role}",
  "action": "{描述}",
  "verification": {
    "th_14": "{SRS 完整度}",
    "th_01": "{ASPICE 合規}"
  }
}
```

---

## Exit 條件

- ✅ Constitution TH-03=100%, TH-04=100%
- ✅ TH-14 ≥90%
- ✅ Agent B APPROVE
- ✅ sessions_spawn.log 有記錄（HR-10）
- ✅ DEVELOPMENT_LOG 有 session_id（HR-07）
