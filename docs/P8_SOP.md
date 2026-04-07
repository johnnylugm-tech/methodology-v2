# Phase 8 SOP — 配置管理

> 本檔案為 On-demand Lazy Load 檔案，僅在執行 Phase 8 時載入。
> 基於：SKILL.md v6.26 + PLAN_PHASE_SPEC.md

---

## 單一入口：plan-phase + run-phase

> ⚠️ **所有 Phase 執行必須經過此入口**，不可繞過。

### 用法

```bash
python cli.py plan-phase --phase 8 --goal "CONFIG_RECORDS.md, Git Tag, pip freeze"
python cli.py run-phase --phase 8
```

---

## Pre-flight 檢查（自動化）

| 檢查項 | 標準 | 不通過時 |
|--------|------|---------|
| FSM State | 非 FREEZE/PAUSED | ❌ 停在 Pre-flight |
| Phase Sequence | Phase 7 APPROVE → Phase 8 | ❌ HR-03 阻擋 |
| Constitution | TH-02 ≥80% | ❌ HR-08 阻擋 |
| 前置交付物 | 所有 Phase 1-7 APPROVE | ❌ 停在 Pre-flight |
| pip freeze | 存在於 repo root | ❌ 停在 Pre-flight |

---

## A/B 角色（HR-01, HR-04）

| 角色 | Agent | 職責 |
|------|-------|------|
| **Agent A** | `devops` | 撰寫 CONFIG_RECORDS.md, Git Tag |
| **Agent B** | `pm` 或 `architect` | 配置確認、封版審查 |

### 禁止事項（HR-01）
- ❌ 自寫自審（HR-01）
- ❌ 配置不完整
- ❌ pip freeze 缺失
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
  "citations": ["CONFIG_RECORDS.md#section"],
  "summary": "50字內摘要"
}
```

---

## Step-by-Step 執行

### Step 8.1: 建立 CONFIG_RECORDS.md

| 項目 | 內容 |
|------|------|
| **工具** | SubagentIsolator（Agent A: devops）|
| **Prompt** | 使用 `templates/CONFIG_RECORDS.md` 模板 |
| **驗證** | 配置記錄完整 |

### Step 8.2: 產生 pip freeze

| 項目 | 內容 |
|------|------|
| **工具** | exec + PermissionGuard |
| **命令** | `pip freeze > requirements.lock` |
| **驗證** | pip freeze 存在於 repo root |

### Step 8.3: Git Tag

| 項目 | 內容 |
|------|------|
| **工具** | exec |
| **命令** | `git tag -a v1.0.0 -m "Phase 8 complete"` |
| **驗證** | tag 存在 |

### Step 8.4: A/B 審查（封版）

| 項目 | 內容 |
|------|------|
| **工具** | SubagentIsolator（Agent B: pm/architect）|
| **驗證** | CONFIG_RECORDS.md 完整、pip freeze 存在 |
| **產出** | APPROVE → 封版 |

---

## HR-12/13 時間追蹤

| Step | 預估 | HR-13 臨界值 |
|------|------|--------------|
| 8.1 | 30m | 90m |
| 8.2 | 10m | 30m |
| 8.3 | 10m | 30m |
| 8.4 | 30m | 90m |
| **總計** | **80m** | **240m** |

---

## 交付物

| 交付物 | 模板 | 驗證 |
|--------|------|------|
| CONFIG_RECORDS.md | `templates/CONFIG_RECORDS.md` | 配置完整 |
| requirements.lock | `pip freeze` | 存在於 root |
| Git Tag | `v{version}` | tag 存在 |

---

## Exit 條件

- ✅ CONFIG_RECORDS.md 完整
- ✅ pip freeze 存在
- ✅ Git Tag 已建立
- ✅ Agent B APPROVE（封版）
- ✅ sessions_spawn.log 有記錄（HR-10）
- ✅ **專案完成**
