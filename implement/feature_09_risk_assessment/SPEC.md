# Feature #9 SPEC.md — 風險評估引擎 (Risk Assessment)

> **版本**: v1.0.0  
> **Layer**: 4 - Executive Assurance  
> **Framework**: methodology-v2  
> **Status**: Draft

---

## 1. Overview

### 1.1 Purpose

Feature #9 是 Layer 4 的風險評估引擎，職責：

1. **識別風險** — 在專案執行過程中主動識別技術/操作/外部風險
2. **評估風險** — 量化風險發生的概率與影響
3. **生成策略** — 產生風險應對策略
4. **追蹤狀態** — 持續追蹤風險狀態直到關閉

### 1.2 Scope

| 維度 | 說明 |
|------|------|
| Layer | 4 (Executive Assurance) |
| Phase 整合 | Phase 6 (風險管理) / Phase 7 (決策門) |
| 輸出 | `RISK_ASSESSMENT.md`, `RISK_REGISTER.md` |
| Constitution 整合 | `risk_management_constitution_checker.py` |

### 1.3 Relationship to Existing Components

```
risk_registry.py          # 現有風險登記 CRUD
risk_status_checker.py    # 現有狀態追蹤工具
risk_dashboard.py         # 現有風險儀表板
risk_management_constitution_checker.py  # Constitution 檢查器
```

Feature #9 強化這些現有元件，統一為一個 engine。

---

## 2. Functionality Specification

### 2.1 Core Features

#### [FR-01] 風險識別 (Risk Identification)

**輸入**：
- Phase 交付物（代碼、測試、架構文件）
- Phase 6/7 執行記錄
- 系統監控數據

**處理**：
- 掃描所有 Phase 交付物中的風險信號
- 比對已知的風險模式（anti-patterns）
- 識別新興風險（emerging risks）

**輸出**：
- 風險清單（Risk List）
- 風險維度分類（Technical / Operational / External）

#### [FR-02] 風險評估 (Risk Evaluation)

**評估模型**：

```python
Risk Score = Probability × Impact × Detectability_Factor

where:
  Probability: 0.0 - 1.0 (發生機率)
  Impact: 1 - 5 (影響程度)
  Detectability_Factor: 0.5 - 1.0 (可檢測性)
```

**維度評估**：

| 維度 | 評估因子 |
|------|----------|
| Technical | 系統複雜度、依賴關係、程式碼品質 |
| Operational | 人力資源、流程成熟度、知識傳遞 |
| External | 市場變化、法規遵循、協力廠商依賴 |

#### [FR-03] 風險應對策略生成 (Risk Response Strategy)

**策略類型**：

| 策略 | 觸發條件 | 行動 |
|------|----------|------|
| Avoid | Score > 0.6 | 消除風險源 |
| Mitigate | Score 0.3-0.6 | 降低概率或影響 |
| Transfer | Score 0.3-0.6 | 保險、外包 |
| Accept | Score < 0.3 | 列入監控清單 |

**策略生成 Prompt**：
```
Given risk: {risk_description}
Probability: {probability}
Impact: {impact}
Context: {project_context}

Generate a mitigation plan with:
1. Immediate actions (within 24h)
2. Short-term actions (within 1 week)
3. Long-term actions (within 1 month)
4. Fallback plan if primary fails
```

#### [FR-04] 風險狀態追蹤 (Risk Tracking)

**狀態機**：

```
OPEN → MITIGATED → ACCEPTED → CLOSED
         ↓
      ESCALATED → (resolved) → CLOSED
```

**追蹤內容**：
- 創建時間
- 最後更新時間
- 緩解措施執行情況
- 驗證結果

### 2.2 User Interactions

#### Phase 6 Entry Point

```
Developer/Agent → Phase 6 執行
                    ↓
              RiskAssessmentEngine.assess(project_root)
                    ↓
              生成/更新 RISK_ASSESSMENT.md
                    ↓
              寫入 .methodology/execution_registry.db
```

#### Phase 7 Decision Gate

```
Reviewer → Phase 7 Decision Gate
             ↓
        RiskAssessmentEngine.evaluate_gates(project_root)
             ↓
        產出 Decision Gate Report
             ↓
        可通過 / 有條件通過 / 阻擋
```

### 2.3 Data Handling

#### 風險資料結構

```python
@dataclass
class Risk:
    id: str                    # R-01, R-02, ...
    title: str                 # 風險標題
    description: str           # 風險描述
    dimension: RiskDimension   # TECHNICAL / OPERATIONAL / EXTERNAL
    level: RiskLevel          # LOW / MEDIUM / HIGH / CRITICAL
    status: RiskStatus        # OPEN / MITIGATED / ACCEPTED / CLOSED
    probability: float        # 0.0 - 1.0
    impact: int               # 1 - 5
    score: float              # 計算後的分數
    owner: str                # 負責人
    mitigation: str          # 緩解措施
    created_at: datetime
    updated_at: datetime
    closed_at: Optional[datetime]
    evidence: List[str]       # 風險識別的證據
    strategy: StrategyType   # AVOID / MITIGATE / TRANSFER / ACCEPT
```

#### 持久化

- 風險資料寫入 `.methodology/risk_assessment.db`（SQLite）
- RISK_ASSESSMENT.md 同步更新（人類可讀格式）
- RISK_REGISTER.md 同步更新（階段性快照）

### 2.4 Edge Cases

| 場景 | 處理方式 |
|------|----------|
| 無法識別風險 | 回報「No significant risks identified」，但仍生成空白註冊表 |
| 風險 ID 衝突 | 使用 UUID 尾碼 (R-01_abc123) |
| Phase 跳過執行 | 警告但允許，記錄在執行日誌 |
| 資料庫損壞 | 從 RISK_ASSESSMENT.md 重建 |
| 分数异常 (NaN/Inf) | 預設為 MEDIUM，並發出警告 |

---

## 3. Technical Architecture

### 3.1 Module Structure

```
implement/feature-09-risk-assessment/
├── SPEC.md                           # 本文件
├── __init__.py
├── engine/
│   ├── __init__.py
│   ├── assessor.py                   # [FR-01, FR-02] 風險識別與評估
│   ├── strategist.py                 # [FR-03] 策略生成
│   └── tracker.py                    # [FR-04] 狀態追蹤
├── models/
│   ├── __init__.py
│   ├── risk.py                       # Risk dataclass
│   └── enums.py                      # RiskDimension, RiskLevel, etc.
├── constitution/
│   ├── __init__.py
│   └── risk_assessment_checker.py   # Constitution 合規檢查
├── reports/
│   ├── __init__.py
│   ├── assessor_report.py            # 評估報告生成
│   └── decision_gate_report.py       # Phase 7 決策門報告
└── tests/
    ├── __init__.py
    ├── test_assessor.py              # [FR-01, FR-02] 測試
    ├── test_strategist.py            # [FR-03] 測試
    └── test_tracker.py               # [FR-04] 測試
```

### 3.2 Class Design

#### RiskAssessmentEngine

```python
class RiskAssessmentEngine:
    """主要的風險評估引擎"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.registry = RiskRegistry(str(project_root))
    
    def assess(self) -> RiskAssessmentResult:
        """執行完整風險評估 [FR-01, FR-02]"""
        
    def generate_strategies(self, risk_id: str) -> List[Strategy]:
        """為單一風險生成應對策略 [FR-03]"""
        
    def update_status(self, risk_id: str, new_status: RiskStatus) -> bool:
        """更新風險狀態 [FR-04]"""
        
    def evaluate_gates(self) -> DecisionGateResult:
        """Phase 7 決策門評估"""
```

#### RiskScorer

```python
class RiskScorer:
    """風險評分器"""
    
    def calculate(self, risk: Risk) -> float:
        """計算風險分數"""
        
    def assess_probability(self, risk: Risk) -> float:
        """評估發生概率"""
        
    def assess_impact(self, risk: Risk) -> int:
        """評估影響程度"""
```

### 3.3 Integration Points

#### 與 risk_registry.py 的整合

```python
from risk_registry import RiskRegistry, RiskLevel, RiskStatus

class RiskAssessmentEngine:
    def __init__(self, project_root: str):
        self.registry = RiskRegistry(str(project_root))
```

#### 與 Constitution 的整合

```python
# 呼叫 risk_management_constitution_checker
from quality_gate.constitution.risk_management_constitution_checker import (
    check_risk_management_constitution
)

def check_constitution_compliance(project_root: str) -> ConstitutionCheckResult:
    return check_risk_management_constitution(project_root)
```

#### 與 quality_gate 的整合

```python
# RiskAssessmentEngine 可被 quality_gate/stage_pass_generator.py 呼叫
# 在 Phase 6/7 的 BLOCK 檢查中使用
```

---

## 4. Output Specifications

### 4.1 RISK_ASSESSMENT.md

```markdown
# Risk Assessment Report

**Project**: {project_name}
**Generated**: {timestamp}
**Phase**: Phase {n}

---

## Executive Summary

- Total Risks: {count}
- Critical: {count} | High: {count} | Medium: {count} | Low: {count}
- Average Score: {avg_score}

## Risk Register

| ID | Title | Dimension | Level | Score | Status | Owner |
|----|-------|-----------|-------|-------|--------|-------|
| R-01 | ... | TECHNICAL | HIGH | 0.72 | OPEN | Agent-A |

## Detailed Assessments

### R-01: {title}

- **Dimension**: TECHNICAL
- **Probability**: 0.7
- **Impact**: 4
- **Score**: 0.72
- **Description**: {description}
- **Evidence**: {evidence_list}
- **Strategy**: MITIGATE
- **Mitigation Plan**:
  - Immediate: {actions}
  - Short-term: {actions}
  - Long-term: {actions}
- **Created**: {date}
- **Updated**: {date}
```

### 4.2 RISK_REGISTER.md

```markdown
# Risk Register

| ID | 風險描述 | 維度 | 等級 | 概率 | 影響 | 緩解措施 | 狀態 |
|----|----------|------|------|------|------|---------|------|
| R-01 | {描述} | {維度} | {等級} | {prob}% | {impact} | {措施} | {狀態} |

## Decision Gate 確認

| 風險 ID | 決策 | 確認人 | session_id | 日期 |
|---------|------|--------|------------|------|
| R-01 | {決策} | {name} | {session_id} | {date} |
```

---

## 5. Acceptance Criteria

### [AC-01] 風險識別完整性

- ✅ 系統能識別至少 3 種維度的風險（Technical, Operational, External）
- ✅ 每個識別的風險都有對應的 evidence
- ✅ 新專案執行時自動創建空白風險清單

### [AC-02] 風險評估準確性

- ✅ Score 計算公式正確：Probability × Impact × Detectability_Factor
- ✅ 評估結果與人工判斷一致度 > 80%（樣本測試）
- ✅ 異常分數（NaN/Inf）正確處理

### [AC-03] 策略生成品質

- ✅ 每個 HIGH/CRITICAL 風險都有 Mitigation Plan
- ✅ 策略包含 Immediate / Short-term / Long-term 行動
- ✅ Fallback Plan 存在於每個策略中

### [AC-04] 狀態追蹤正確性

- ✅ 狀態機轉換正確（OPEN → MITIGATED → ACCEPTED → CLOSED）
- ✅ 所有變更都有 timestamp
- ✅ 閉合時記錄 closed_at

### [AC-05] Constitution 合規

- ✅ 輸出符合 `risk_management_constitution_checker.py` 要求
- ✅ RISK_ASSESSMENT.md 和 RISK_REGISTER.md 都存在
- ✅ Mitigation Plans 欄位有內容

### [AC-06] Phase 6/7 整合

- ✅ `RiskAssessmentEngine.assess()` 可被 Phase 6 流程呼叫
- ✅ `RiskAssessmentEngine.evaluate_gates()` 產出 Phase 7 Decision Gate Report
- ✅ 與現有 `risk_status_checker.py` 完全相容

### [AC-07] 測試覆蓋率

- ✅ TDD 覆蓋率 100%（所有 FR）
- ✅ Edge cases 有對應測試
- ✅ Error handling 有測試

---

## 6. Implementation Notes

### 6.1 Chunked Write Protocol

所有 >500 lines 的檔案必須分 chunk 生成：

| 檔案 | 預估行數 | Chunk 數量 |
|------|----------|------------|
| assessor.py | ~400 | 1 |
| strategist.py | ~350 | 1 |
| tracker.py | ~300 | 1 |
| risk.py | ~150 | 1 |
| risk_assessment_checker.py | ~200 | 1 |

預計無需 chunking，但若超過則嚴格遵守。

### 6.2 FR Tagging Convention

每個函數/類別必須標記 FR：

```python
# [FR-01] Risk identification entry point
def identify_risks(self, project_root: Path) -> List[Risk]:
    ...

# [FR-02] Risk evaluation entry point
def evaluate_risk(self, risk: Risk) -> float:
    ...
```

### 6.3 Database Schema

```sql
CREATE TABLE risks (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    dimension TEXT,
    level TEXT,
    status TEXT DEFAULT 'OPEN',
    probability REAL DEFAULT 0.5,
    impact INTEGER DEFAULT 3,
    score REAL,
    owner TEXT,
    mitigation TEXT,
    created_at TEXT,
    updated_at TEXT,
    closed_at TEXT,
    evidence TEXT,  -- JSON array
    strategy TEXT
);

CREATE TABLE risk_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    risk_id TEXT,
    changed_at TEXT,
    old_status TEXT,
    new_status TEXT,
    changed_by TEXT,
    note TEXT
);
```

---

## 7. Dependencies

| 模組 | 版本 | 用途 |
|------|------|------|
| risk_registry.py | existing | 風險 CRUD 基礎 |
| risk_status_checker.py | existing | 狀態追蹤整合 |
| risk_management_constitution_checker.py | existing | Constitution 檢查 |
| quality_gate.phase_config | existing | Phase 設定 |

---

## 8. Revision History

| 版本 | 日期 | 作者 | 變更 |
|------|------|------|------|
| 1.0.0 | 2026-04-20 | Agent | 初始版本 |