# 任務初始化 Prompt Template v6.13

> **版本**: v6.13  
> **用途**: 啟動新專案時使用  
> **對象**: Agent（由 Johnny 引導執行）

---

## 🚀 初始化流程

### Step 1: Agent 讀取 SKILL.md

```bash
# Agent 必須執行
python cli.py skill-check --mode preheat --phase 1
```

**Agent 必須報告**:
1. Phase 1 的 WHO（角色分工）
2. Phase 1 的 WHAT（交付物）
3. Phase 1 的 WHEN（時序門檻）
4. Phase 1 的 BLOCK 級別
5. Phase 1 的 Constitution 類型

### Step 2: Johnny 確認 Agent 理解

Johnny 問 2-3 題拷問法：
- 「Phase 1 的進入/退出條件是什麼？」
- 「HR-01 的內容是什麼？」
- 「TH-14 的門檻是多少？」

### Step 3: Johnny 發布任務

```markdown
請開始 Phase 1: 需求規格

任務目標：
- {具體目標}

交付物：
- SRS.md
- SPEC_TRACKING.md
- TRACEABILITY_MATRIX.md

要求：
- 嚴格遵守 SKILL.md v6.13
- 所有 claims 必須附上 [SKILL.md line XXX]
- 每個 Quality Gate 必須有實際命令輸出
```

### Step 4: Agent 執行

Agent 按照以下流程執行：

```
Phase 1 SOP:
1. Agent A（architect）撰寫 SRS.md
2. Agent A 初始化 SPEC_TRACKING.md
3. Agent A 初始化 TRACEABILITY_MATRIX.md
4. Agent B（reviewer）A/B 審查
5. Quality Gate: doc_checker + constitution
6. 生成 Phase1_STAGE_PASS.md
7. 通知 Johnny 審核
```

### Step 5: Johnny HITL 審核

```bash
# Johnny 執行
python cli.py phase-verify --phase 1
```

根據結果：
- 分數 ≥70% → ✅ CONFIRM
- 分數 <70% → ❌ REJECT（說明原因）

---

## 📋 Phase 1-8 Johnny 發布模板

### Phase 1 任務發布

```markdown
請開始 Phase 1: 需求規格

交付物：
- 01-requirements/SRS.md
- 01-requirements/SPEC_TRACKING.md
- 01-requirements/TRACEABILITY_MATRIX.md
- DEVELOPMENT_LOG.md

Quality Gate：
- doc_checker.py
- constitution/runner.py --type srs
```

### Phase 2 任務發布

```markdown
請開始 Phase 2: 架構設計

前提：Phase 1 CONFIRM

交付物：
- 02-architecture/SAD.md
- 02-architecture/ADR.md（如有）
- TRACEABILITY_MATRIX.md（更新）

Quality Gate：
- 同 Phase 1 + phase_artifact_enforcer.py
```

### Phase 3 任務發布

```markdown
請開始 Phase 3: 代碼實現

前提：Phase 2 CONFIRM

交付物：
- 03-implementation/src/（代碼）
- 03-implementation/tests/（測試）
- 03-implementation/COMPLIANCE_MATRIX.md

Quality Gate：
- pytest（100% 通過）
- pytest --cov（覆蓋率 ≥70%）
```

### Phase 4-8...（以此類推）

---

## ⚠️ 失敗處理

### Quality Gate 失敗

| 失敗 | Agent 動作 |
|------|-----------|
| FrameworkEnforcer BLOCK | 停在當前，修復後重試 |
| Constitution < 門檻 | 停在當前，修復後重試 |
| pytest 失敗 | 停在 Phase 3，修復後重試 |

### Johnny REJECT

```
1. Agent: 讀取 Johnny 的 REJECT 理由
2. Agent: 根據理由修復
3. Agent: 重新提交審核
4. Johnny: 直到 CONFIRM 才能繼續
```

---

## 🛡️ 防作假機制

### 預熱程序
Agent 每 Phase 開始前必須通過

### 強制引用
所有 claims 必須格式：`[SKILL.md line XXX]`

### 拷問法
Johnny 隨機抽查 Agent 理解

---

## 📝 Agent 執行後的輸出格式

```markdown
## Phase {N} 完成報告

### 交付物
| 檔案 | 狀態 | 路徑 |
|------|------|------|
| SRS.md | ✅ | 01-requirements/SRS.md |

### Quality Gate 結果
```
$ python quality_gate/doc_checker.py
Compliance Rate: 85%
Passed: 17/20
```

### Agent A 自評
分數：92/100
問題：無

### Agent B 審查
結論：✅ APPROVE

### 請求
Johnny 審核，執行 `python cli.py phase-verify --phase {N}`
```

---

## 📊 8 Phase 交付物總覽

| Phase | 主要交付物 |
|-------|-----------|
| 1 | SRS.md, SPEC_TRACKING.md, TRACEABILITY_MATRIX.md |
| 2 | SAD.md, ADR.md（如有）, TRACEABILITY_MATRIX.md（更新） |
| 3 | src/, tests/, COMPLIANCE_MATRIX.md |
| 4 | TEST_PLAN.md, TEST_RESULTS.md |
| 5 | BASELINE.md, VERIFICATION_REPORT.md |
| 6 | QUALITY_REPORT.md（完整版） |
| 7 | RISK_REGISTER.md, RISK_ASSESSMENT.md |
| 8 | CONFIG_RECORDS.md, requirements.txt |

---

## 🔑 關鍵 CLI 速查

```bash
# Phase 真相驗證
python cli.py phase-verify --phase N

# 預熱程序
python cli.py skill-check --mode preheat --phase N

# 拷問法
python cli.py skill-check --mode interrogate --phase N

# 生成 STAGE_PASS
python cli.py stage-pass --phase N

# Framework BLOCK 檢查
python cli.py enforce --level BLOCK
```

---

*此 Prompt 基於 methodology-v2 v6.13*
*最後更新: 2026-03-31*
