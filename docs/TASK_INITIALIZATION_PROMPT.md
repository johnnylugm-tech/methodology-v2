# 任務初始化 Prompt Template

> **版本**: v6.11.0  
> **用途**: 啟動新專案時使用  
> **前提**: 已具備規格書 (SRS.md) 和 GitHub 倉庫

---

## 🛡️ SKILL.md 讀取強制機制

在開始任何任務前，Agent 必須通過以下三個機制確保已認真讀過 SKILL.md：

### 1. 預熱程序 (Preheating) - 每 Phase 開始前執行

```bash
python cli.py skill-check --mode preheat --phase N
```

**目的**: 強制 Agent 在執行任務前複習並回答 SKILL.md 相關問題。

**必須回答的問題**:
1. Phase N 的 WHO（角色分工）定義是什麼？
2. Phase N 的 WHAT（交付物）清單有哪些？
3. Phase N 的 WHEN（時序門檻）是什麼？
4. Phase N 的 BLOCK 級別包含哪些檢查？
5. Phase N 的 Constitution 類型是什麼？

**通過標準**: 至少 3 題回答完整（每題 >20 字）

### 2. 拷問法 (Interrogation) - 每 Phase 完成後執行

```bash
python cli.py skill-check --mode interrogate --phase N
```

**目的**: 隨機抽查 Agent 對 SKILL.md 的理解深度。

**抽查問題範例**:
- FrameworkEnforcer BLOCK 級別包含幾項檢查？
- Constitution runner.py 的 command 是什麼？
- sessions_spawn 的必要參數有哪些？
- phase-verify 的分數門檻是多少？

**通過標準**: 回答包含至少 1 個關鍵提示且長度 >10 字

### 3. 強制引用 (Forced Citation) - 所有 claims 必須附上行號

```bash
python cli.py skill-check --mode citation --phase N
```

**目的**: 要求 Agent 的每個聲稱必須附上 SKILL.md 的具體行號或章節。

**要求**:
- 每個事實聲稱必須引用 SKILL.md 的具體行號
- 格式：`[line 123]` 或 `第 123 行`
- 或引用章節：`### Phase N 流程`

### 完整執行（一次執行所有機制）

```bash
python cli.py skill-check --phase N
```

---

## 🚀 任務啟動 Prompt

```markdown
# 任務初始化：{專案名稱}

## 任務概述

你需要帶領團隊完成 {專案名稱} 的完整開發，使用 methodology-v2 框架，
確保 100% 落實 SKILL.md 規範。

## 當下專案資訊

- **規格書**: `/{path/to}/SRS.md`
- **GitHub 倉庫**: `https://github.com/{owner}/{repo}`
- **專案根目錄**: `/{path/to}/`

## 核心原則

1. **100% 落實 SKILL.md** - 每個 Phase 必須完全符合 framework 定義
2. **零容忍作假** - 所有聲稱必須有實際證據
3. **Human-in-the-Loop** - Johnny 介入每個 Phase 的審核
4. **A/B 協作** - 每個關鍵決策必須有兩個不同角色的 Agent

---

## 📋 8 Phase 執行流程

### 總體流程

```
Phase 1 ──► Phase 2 ──► Phase 3 ──► Phase 4 ──► Phase 5 ──► Phase 6 ──► Phase 7 ──► Phase 8
  │           │           │           │           │           │           │           │
  ▼           ▼           ▼           ▼           ▼           ▼           ▼           ▼
BLOCK       BLOCK       BLOCK       BLOCK       BLOCK       BLOCK       BLOCK       BLOCK
  │           │           │           │           │           │           │           │
  ▼           ▼           ▼           ▼           ▼           ▼           ▼           ▼
Johnny       Johnny       Johnny       Johnny       Johnny       Johnny       Johnny       Johnny
HITL         HITL         HITL         HITL         HITL         HITL         HITL         HITL
  │           │           │           │           │           │           │           │
  ▼           ▼           ▼           ▼           ▼           ▼           ▼           ▼
CONFIRM    CONFIRM     CONFIRM     CONFIRM     CONFIRM     CONFIRM     CONFIRM     CONFIRM
  │           │           │           │           │           │           │           │
  └───────────┴───────────┴───────────┴───────────┴───────────┴───────────┴───────────┘
                                    完成
```

---

## 🔧 每 Phase 標準作業程序

### Phase N 開始時，執行以下步驟：

```
1. 【讀取 Prompt Template】
   - 讀取 docs/PHASE_PROMPTS.md 中的 Phase N 模板
   - 確認 WHO/WHAT/WHEN/WHERE/WHY/HOW

2. 【啟動 A/B 協作】
   - 使用 sessions_spawn 啟動 Agent A
   - 使用 sessions_spawn 啟動 Agent B
   - 確認使用不同 persona

3. 【執行工作】
   - Agent A 根據 Prompt Template 執行
   - 記錄 sessions_spawn.log

4. 【自動化檢查】
   - 執行 FrameworkEnforcer BLOCK
   - 執行 Constitution runner
   - 執行 pytest（如適用）

5. 【處理失敗】
   - 如果 BLOCK 未通過 → 修復問題
   - 如果 Constitution 未通過 → 修復問題
   - 回到步驟 4 直到通過

6. 【生成 STAGE_PASS】
   - 執行 stage-pass --phase N
   - 推送到 GitHub

7. 【HITL 審核】
   - 通知 Johnny 執行 phase-verify --phase N
   - 等待 Johnny CONFIRM/REJECT

8. 【處理 REJECT】
   - 如果 Johnny REJECT → 回到步驟 1
   - 根據 Johnny 意見修復
```

---

## ⚠️ 失敗處理機制

### 自動化檢查失敗

| 檢查 | 失敗時的動作 |
|------|-------------|
| FrameworkEnforcer BLOCK | 停在當前 Step，修复问题后重新執行檢查 |
| Constitution < 60% | 停在當前 Step，修复问题后重新執行檢查 |
| pytest 失敗 | 停在 Phase 3，修复测试后重新執行 |
| 覆蓋率 < 70% | 停在 Phase 3，增加測試後重新執行 |
| SPEC_TRACKING < 90% | 停在 Phase 1，更新追蹤後重新執行 |

### Johnny REJECT

```
當 Johnny REJECT 時：
1. 暫停當前工作
2. 讀取 Johnny 的 REJECT 理由
3. 根據理由制定修復計畫
4. 執行修復
5. 通知 Johnny 重新審核
6. 直到 Johnny CONFIRM 才能繼續
```

---

## 📊 每 Phase 交付物清單

### Phase 1: 需求規格
- `01-requirements/SRS.md`
- `01-requirements/SPEC_TRACKING.md`
- `01-requirements/TRACEABILITY_MATRIX.md`
- `DEVELOPMENT_LOG.md`
- `Phase1_STAGE_PASS.md`

### Phase 2: 架構設計
- `02-architecture/SAD.md`
- `02-architecture/CONFLICT_LOG.md`（如有衝突）
- `TRACEABILITY_MATRIX.md`（已更新 FR→模組）
- `DEVELOPMENT_LOG.md`
- `Phase2_STAGE_PASS.md`

### Phase 3: 代碼實現
- `03-implementation/src/`（所有模組）
- `03-implementation/tests/`（三類測試）
- `03-implementation/COMPLIANCE_MATRIX.md`
- `DEVELOPMENT_LOG.md`
- `Phase3_STAGE_PASS.md`

### Phase 4: 測試
- `04-testing/TEST_PLAN.md`
- `04-testing/TEST_RESULTS.md`
- pytest 實際輸出
- `DEVELOPMENT_LOG.md`
- `Phase4_STAGE_PASS.md`

### Phase 5: 驗收與交付
- `05-verify/BASELINE.md`
- `05-verify/VERIFICATION_REPORT.md`
- `05-verify/QUALITY_REPORT.md`（初版）
- `MONITORING_PLAN.md`
- `DEVELOPMENT_LOG.md`
- `Phase5_STAGE_PASS.md`

### Phase 6: 品質保證
- `06-quality/QUALITY_REPORT.md`（完整版）
- `MONITORING_PLAN.md`（Phase 6 數據）
- `DEVELOPMENT_LOG.md`
- `Phase6_STAGE_PASS.md`

### Phase 7: 風險評估
- `07-risk/RISK_ASSESSMENT.md`
- `07-risk/RISK_REGISTER.md`
- `.methodology/decisions/`（Decision Gate 記錄）
- `MONITORING_PLAN.md`（Phase 7 更新）
- `DEVELOPMENT_LOG.md`
- `Phase7_STAGE_PASS.md`

### Phase 8: 配置管理
- `08-config/CONFIG_RECORDS.md`
- `requirements.txt`（pip freeze）
- `Git Tag v[version]`
- `DEVELOPMENT_LOG.md`（Phase 8 + 方法論閉環）
- `Phase8_STAGE_PASS.md`

---

## 🔍 Johnny 審核責任

### 每個 Phase 完成後

```bash
# Johnny 必須執行
python cli.py phase-verify --phase N

# 根據輸出決定
# 分數 ≥70% + 手動確認通過 → CONFIRM
# 分數 <70% 或 有疑問 → REJECT
```

### Johnny 必檢項目（每 Phase）

| Phase | 必檢內容 |
|-------|----------|
| 1 | SRS.md 隨機抽 3 條 FR，確認有邏輯驗證方法 |
| 2 | SAD.md 模組邊界圖是否合理 |
| 3 | 隨機抽 1 個測試，確認邊界條件 |
| 4 | TEST_RESULTS.md pytest 輸出真實性 |
| 5 | BASELINE.md 功能對照表 |
| 6 | QUALITY_REPORT.md 問題根源分析 |
| 7 | RISK_REGISTER.md 演練記錄 |
| 8 | CONFIG_RECORDS.md pip freeze 輸出 |

---

## 🛠️ 自動化工具速查

### Agent 必須使用的工具

| 工具 | 用途 | 命令 |
|------|------|------|
| FrameworkEnforcer | BLOCK 檢查 | `python cli.py enforce --level BLOCK` |
| Constitution Runner | 品質檢查 | `python quality_gate/constitution/runner.py --type {type}` |
| Claims Verifier | 驗證 A/B 事實 | `from quality_gate.claims_verifier import ClaimsVerifier` |
| AB Enforcer | A/B 分離驗證 | `from quality_gate.ab_enforcer import ABEnforcer` |
| Phase Truth Verifier | 真實性驗證 | `python cli.py phase-verify --phase N` |

---

## 📝 sessions_spawn 標準用法

### 啟動 Agent A

```python
sessions_spawn(
    task="""你是 architect persona。
    
    根據 Phase N Prompt Template 执行工作。
    
    你的職責：
    - [根據 Prompt Template 填寫]
    
    執行後：
    - 記錄 session_id 到 sessions_spawn.log
    - 等待 Agent B 審查
    """,
    runtime="subagent",
    mode="run"
)
```

### 啟動 Agent B

```python
sessions_spawn(
    task="""你是 reviewer persona。
    
    你的職責：
    - [根據 Prompt Template 填寫]
    
    執行後：
    - 記錄 session_id 到 sessions_spawn.log
    - 給出 APPROVE 或 REJECT
    """,
    runtime="subagent",
    mode="run"
)
```

---

## ✅ 開始執行

當你收到這個 Prompt 時：

1. **立即執行** Phase 1（需求規格）
2. **使用** Phase 1 Prompt Template
3. **啟動** A/B 協作
4. **執行** 自動化檢查
5. **生成** STAGE_PASS.md
6. **通知** Johnny 審核

---

## ⚡ 緊急規則

```
如果遇到以下情況，立即停止並報告：
1. FrameworkEnforcer BLOCK 連續失敗 3 次
2. Constitution 分數 < 40%
3. Johnny REJECT 超過 2 次同一個問題
4. 發現任何作假跡象

立即通知 Johnny，等待指示。
```

---

*此 Prompt 基於 methodology-v2 v6.11.0*
*最後更新: 2026-03-31*
