# Feature Development Workflow — A/B Collaboration Pattern
**版本**: v1.0
**日期**: 2026-04-17
**適用範圍**: methodology-v3 Feature Integration

---

## 1. 概述

本workflow定義了一套適配AI Agent特性的Feature開發流程，核心是「A/B協作模式」——主代理（Agent A）負責協調把關，子代理（Agent B）負責實際執行。

### 1.1 關鍵原則

| 原則 | 說明 |
|------|------|
| **A/B分責** | 主代理不做實際coding，只協調 + 把關 |
| **八階段串聯** | 每個Feature走8個Phase，串聯執行（不並行） |
| **TDD驗證** | Phase 5必須通過pytest + coverage門檻 |
| **Sub-agent人格** | sessions_spawn時賦予對應人格，確保產出風格一致 |
| **Timeout紀律** | 所有子代理timeout設定30分鐘，超時、果斷放棄、優化重來 |

---

## 2. A/B 協作模式

### 2.1 角色定義

| 角色 | 代號 | 職責 |
|------|------|------|
| **主代理** | Agent A | 協調、完整性把關、正確性審查、階段銜接 |
| **子代理** | Agent B | 實際執行工作（寫碼、寫文檔、測試） |

### 2.2 協作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    FEATURE N DEVELOPMENT                    │
└─────────────────────────────────────────────────────────────┘
         │                                                      │
         ▼                                                      │
┌─────────────────────┐                                         │
│  Phase N Sub-task   │ ←── 我啟動 sessions_spawn               │
│  (Agent B 執行)     │                                         │
└─────────┬───────────┘                                         │
          │                                                      │
          ▼                                                      │
┌─────────────────────────────────────────────────────────────┐ │
│              PHASE REVIEW (Agent A)                          │ │
│  • 完整性檢查                                                    │ │
│  • 正確性驗證                                                    │ │
│  • 一致性確認                                                    │ │
└─────────┬───────────────────────────────────────────────────┘ │
          │                                                      │
    ┌─────┴─────┐                                                │
    ▼           ▼                                                │
  APPROVE    REJECT                                              │
    │           │                                                │
    ▼           ▼                                                │
  Next      Back to Sub-agent                                    │
  Phase     (with feedback)                                      │
```

### 2.3 Sub-agent 人格調用

每個Phase的sub-task都必須包含明確的**人格指令**，確保產出風格一致：

```markdown
## 你的角色
- 你是一個資深的Python框架開發者
- 專精：系統架構、測試驅動開發、程式碼品質
- 風格：清晰、完整、實用導向
- 不說廢話，直接給結果
```

### 2.4 Timeout 設定

| 場景 | Timeout | 處理方式 |
|------|---------|----------|
| Phase 1-2 (文檔) | 30 min | 超時→我補完遺漏章節 |
| Phase 3 (implement) | 30 min | 超時→評估進度，決定是否重派 |
| Phase 4 (test) | 30 min | 超時→評估進度，決定是否重派 |
| Phase 6-8 (報告) | 30 min | 超時→我補完 |

---

## 3. 八階段流程

### 3.1 階段總覽

| Phase | 名稱 | 交付物 | Agent B產出 | Agent A審查 |
|-------|------|--------|------------|-------------|
| **Phase 1** | SPEC.md | 需求規格 | 351 lines, 16 user stories, 8 FRs | 完整性 + 正確性 |
| **Phase 2** | ARCHITECTURE.md | 架構設計 | 1,285 lines, 5 components | 架構合理性 |
| **Phase 3** | implement/ | 實作模組 | 9 modules, ~2,410 lines | 程式碼品質 |
| **Phase 4** | test/ | 單元測試 | 8 files, 84 tests | 測試覆蓋率 |
| **Phase 5** | pytest | TDD驗證 | 84 passed, 92% coverage | 門檻判斷 |
| **Phase 6** | DELIVERY_REPORT.md | 交付報告 | 6,557 bytes | 格式正確性 |
| **Phase 7** | RISK_REGISTER.md | 風險登記 | 22 risks | 風險評估 |
| **Phase 8** | DEPLOYMENT.md | 部署指南 | 566 lines | 操作可行性 |

### 3.2 Phase 詳細說明

#### Phase 1: SPEC.md
```
目標：定義完整的需求規格
輸入：Feature Overview + Tiered Governance Example
產出：SPEC.md
sub-agent指令重點：
  - 必須包含所有FRs（FR-TG-1 至 FR-TG-8）
  - 必須包含User Stories（每Tier至少3個）
  - Decision Matrix（24種場景分類）
  - Success Metrics（具體可測量）
```

#### Phase 2: ARCHITECTURE.md
```
目標：設計系統架構
輸入：SPEC.md
產出：ARCHITECTURE.md
sub-agent指令重點：
  - 5個核心元件詳細規格
  - Data Models（TierDecision, GovernanceContext等）
  - Tier-Specific Workflows（3個workflow）
  - API Design（6個public methods）
  - Edge Cases & Error Handling
```

#### Phase 3: implement/
```
目標：實作所有模組
輸入：SPEC.md + ARCHITECTURE.md
產出：implement/governance/（9個.py檔案）
sub-agent指令重點：
  - Type hints on ALL functions
  - Docstrings on all public methods
  - Raise custom exceptions
  - No external dependencies beyond Python stdlib
  - 嚴格遵守ARCHITECTURE.md的元件規格
```

#### Phase 4: test/
```
目標：撰寫完整單元測試
輸入：implement/（所有實作模組）
產出：test/governance/（8個測試檔案）
sub-agent指令重點：
  - 使用pytest framework
  - 每個模組至少5個test cases
  - test_<method>_<scenario>()命名
  - Fixtures for common setup
  - Assert with descriptive messages
```

#### Phase 5: pytest + coverage
```
目標：TDD驗證
輸入：test/governance/
產出：測試報告 + coverage報告
審查標準：
  - All tests pass: 100%
  - Coverage ≥ 80%（各模組）
  - Coverage ≥ 85%（整體）
  - FR coverage: 100%
```

#### Phase 6: DELIVERY_REPORT.md
```
目標：交付文件
輸入：所有Phase交付物
產出：DELIVERY_REPORT.md
內容：
  - Phase Completion Status
  - Implementation Summary
  - Functional Coverage
  - Test Results
  - Known Limitations
```

#### Phase 7: RISK_REGISTER.md
```
目標：風險識別
輸入：Implementation
產出：RISK_REGISTER.md
內容：
  - 至少8個風險（8個類別）
  - Risk Score = Likelihood × Impact
  - Mitigation strategies
```

#### Phase 8: DEPLOYMENT.md
```
目標：部署指南
輸入：Implementation
產出：DEPLOYMENT.md
內容：
  - Prerequisites
  - Installation Steps
  - Configuration Parameters
  - Usage Examples
  - Troubleshooting
```

---

## 4. TDD 驗證標準

### 4.1 質量門檻

| Gate | Threshold | 不達標處理 |
|------|-----------|-----------|
| Tests pass | 100% | FAIL → 修復測試 |
| Coverage ≥ 80% | per module | WARN → 補測試 |
| Coverage ≥ 85% | overall | FAIL → 補測試 |
| FR coverage | 100% | FAIL → 補實作 |
| User Story | 100% | FAIL → 補需求 |

### 4.2 測試命名規範

```
test_<component>_<method>_<scenario>
```

範例：
- `test_tier_classifier_classify_routine_operation_returns_hotlin`
- `test_audit_logger_hash_chain_integrity`
- `test_escalation_engine_max_depth_enforcement`

### 4.3 覆蓋率目標

| 元件 | 目標覆蓋率 |
|------|-----------|
| audit_logger.py | ≥ 90% |
| models.py | ≥ 90% |
| enums.py | 100% |
| exceptions.py | 100% |
| tier_classifier.py | ≥ 85% |
| governance_trigger.py | ≥ 80% |
| escalation_engine.py | ≥ 80% |
| override_manager.py | ≥ 85% |

---

## 5. sessions_spawn 呼叫範本

### 5.1 基本格式

```python
sessions_spawn(
    mode="run",           # 一次性執行
    runtime="subagent",    # subagent runtime
    timeoutSeconds=1800,  # 30分鐘 = 1800秒
    task="""
        ## 你的角色
        - 你是一個資深的Python框架開發者
        - 專精：系統架構、測試驅動開發、程式碼品質
        - 風格：清晰、完整、實用導向
        - 不說廢話，直接給結果
        
        ## 你的任務
        [具體任務描述]
        
        ## 重要提醒
        - Read SPEC.md and ARCHITECTURE.md before writing code
        - Write ALL files to disk immediately
        - Do NOT output only to console
    """
)
```

### 5.2 Phase 任務範本

#### Phase 3 (implement) 範本

```python
task="""
你正在實作 Feature #3 Tiered Governance。

## 你的任務
在 implement/governance/ 建立以下9個模組：

1. enums.py — Tier, GovernanceDecision, ApprovalStatus, RiskLevel, AuthorizedRole
2. models.py — TierDecision, GovernanceContext, ApprovalRequest, EscalationEvent, AuditEntry
3. exceptions.py — GovernanceError, TierClassificationError, ApprovalClosedError...
4. tier_classifier.py — TierClassifier with classify_operation()
5. governance_trigger.py — GovernanceTrigger with evaluate_triggers() + fire_workflow()
6. escalation_engine.py — EscalationEngine with escalate() + get_escalation_depth()
7. audit_logger.py — AuditLogger with log() + query() + export()
8. override_manager.py — OverrideManager with override_tier() + is_authorized()
9. __init__.py — Package exports

## 代碼標準
- Type hints on ALL functions
- Docstrings on all public methods
- Raise custom exceptions (from exceptions.py)
- No external dependencies beyond Python stdlib
- In-memory state (simple dict) for framework isolation

## 寫入磁盤
建立於: /Users/johnny/.openclaw/workspace-musk/skills/methodology-v2/implement/governance/

## 重要
- 讀取 ./SPEC.md 和 ./ARCHITECTURE.md 後再寫程式碼
- 每個檔案建立後立即寫入磁盤
- 不要只輸出到console，要寫入檔案
"""
```

---

## 6. Feature Branch 命名規範

```
v3/<feature-name-slug>
```

範例：
| Feature | Branch |
|---------|--------|
| MCP + SAIF 2.0 | v3/mcp-saif |
| Prompt Shields | v3/prompt-shields |
| Tiered Governance | v3/tiered-governance |
| Kill-Switch | v3/kill-switch |
| LLM Cascade | v3/llm-cascade |

---

## 7. 開發模式示意圖

```
                    ┌──────────────────┐
                    │   NEW SESSION     │
                    │  (new feature)   │
                    └────────┬─────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │  FEATURE WORKFLOW │
                    │   (8 phases)      │
                    └────────┬─────────┘
                             │
            ┌────────────────┼────────────────┐
            ▼                ▼                ▼
    ┌───────────┐    ┌───────────┐    ┌───────────┐
    │  Phase 1  │    │  Phase 2  │    │  Phase 3  │
    │  SPEC.md  │    │  ARCH.md  │    │ implement │
    └─────┬─────┘    └─────┬─────┘    └─────┬─────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                    sessions_spawn
                    (sub-agent)
                           │
                           ▼
                    ┌──────────────────┐
                    │   PHASE REVIEW    │
                    │   (Agent A)      │
                    └────────┬─────────┘
                             │
                    ┌───────┴───────┐
                    ▼              ▼
               APPROVE         REJECT
                │                │
                ▼                ▼
            Next Phase    Back to Sub-agent
                           (with feedback)
```

---

## 8. 已知問題與觀察

### 8.1 Sub-agent 穩定性
- **問題**: 約30%機率sub-agent不寫檔案，只輸出到console
- **解決**: 增強prompt：「Write to disk immediately after creating」

### 8.2 輸出與預期不符
- **問題**: sub-agent可能不讀取現有檔案
- **解決**: 明確要求「Read ./SPEC.md and ./ARCHITECTURE.md FIRST before writing」

### 8.3 Phase 2 Timeout 處理
- **問題**: Phase 2有時超時，但主體已完成
- **解決**: 我直接補完遺漏章節（第6-8節），不重派

### 8.4 Coverage 追蹤
- **追蹤**: tier_classifier.py 77% (目標85%)
- **補救**: 需要補15個測試

---

## 9. 下一步：merge to methodology-v3

```
1. Feature #3 完成 → commit to v3/tiered-governance
2. Feature #1-3 合并 → PR to methodology-v3
3. methodology-v3 → main (Real Project Validation)
4. Feature #4 (Kill-Switch) → start
```

---

*Document version: 1.0*
*Last updated: 2026-04-17 19:08 GMT+8*
