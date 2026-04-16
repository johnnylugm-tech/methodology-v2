# methodology-v2 → v3.0 Feature Integration Workflow
## 每個 Feature 的開發與驗證流程

**版本**: 1.0
**日期**: 2026-04-17
**目的**: 定義 Feature-by-Feature 的嚴謹整合流程

---

## 核心流程

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEATURE INTEGRATION CYCLE                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐                                               │
│  │ WIP: Feature │ ←── 從待辦清單取出                             │
│  └──────┬───────┘                                               │
│         │                                                         │
│         ▼                                                         │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ STEP 1: methodology-v3 Branch                              │   │
│  │ • 在 methodology-v3 實作 Feature                            │   │
│  │ • TDD Red → Green → Refactor                               │   │
│  │ • 單元測試 + 整合測試 全部 PASS                            │   │
│  │ • Coverage ≥ 80%                                           │   │
│  └──────────────────────┬───────────────────────────────────────┘   │
│                         │                                            │
│                         ▼                                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ STEP 2: Merge to main                                       │   │
│  │ • Feature branch → main (via PR)                            │   │
│  │ • Code Review                                               │   │
│  │ • Pre-push checks PASS                                      │   │
│  └──────────────────────┬───────────────────────────────────────┘   │
│                         │                                            │
│                         ▼                                            │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │ STEP 3: main Branch — Real Project Validation               │   │
│  │ • 用真實專案執行 Phase 1-8                                  │   │
│  │ • 發現並修復 Bug                                            │   │
│  │ • 修復完成 → Feature 正式完成                               │   │
│  └──────────────────────┬───────────────────────────────────────┘   │
│                         │                                            │
│                         ▼                                            │
│                  ┌─────────────┐                                   │
│                  │ Next Feature │                                   │
│                  └─────────────┘                                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Feature 清單（按優先級）

| # | Feature | Branch | PR → main | 預估工時 |
|---|---------|--------|------------|----------|
| 1 | P0-1: MCP Protocol | `v3/mcp` | PR #1 | ~2 天 |
| 2 | P0-2: 分級治理 | `v3/tiered-governance` | PR #2 | ~1.5 天 |
| 3 | P1-1: Kill-Switch | `v3/kill-switch` | PR #3 | ~1 天 |
| 4 | P1-2: 5-Agent Debate | `v3/debate` | PR #4 | ~3 天 |
| 5 | P1-3: 幻覺偵測 | `v3/hallucination` | PR #5 | ~4 天 |
| 6 | P1-4: Gap Detection | `v3/gap-detector` | PR #6 | ~2 天 |
| 7 | P1-5: 風險評估 | `v3/risk-engine` | PR #7 | ~2 天 |
| 8 | P1-6: LangGraph | `v3/langgraph` | PR #8 | ~2.5 天 |
| 9 | P2-1: Langfuse | `v3/langfuse` | PR #9 | ~2 天 |
| 10 | P2-2: 合規 | `v3/compliance` | PR #10 | ~5 天 |

---

## STEP 1: methodology-v3 開發流程

### 1.1 建立 Feature Branch

```bash
# 從 methodology-v3 建立 feature branch
git checkout methodology-v3
git pull origin methodology-v3
git checkout -b v3/[feature-name]
```

### 1.2 TDD 執行循環

```
┌─────────────────────────────────────────┐
│ TDD Loop (每個 test 都要經過)           │
├─────────────────────────────────────────┤
│                                          │
│  1. Red: 寫測試（一定 FAIL）            │
│     pytest tests/v3/[feature]/           │
│     → FAIL: 功能不存在                   │
│                                          │
│  2. Green: 實作最小代碼                 │
│     → PASS: 功能存在但可能不完整         │
│                                          │
│  3. Refactor: 重構                     │
│     → PASS: 行為不變，品質提升           │
│                                          │
│  4. Repeat: 下一個 test                 │
│                                          │
└─────────────────────────────────────────┘
```

### 1.3 測試分類

```
tests/
└── v3/
    └── [feature-name]/
        ├── unit/
        │   ├── test_[component]_001.py
        │   └── test_[component]_002.py
        └── integration/
            └── test_[feature]_integration.py
```

### 1.4 驗收標準（每個 Feature）

| 標準 | 條件 |
|------|------|
| 單元測試 | 100% PASS |
| 整合測試 | 100% PASS |
| Coverage | ≥ 80% |
| Pre-push checks | PASS |
| Linting | PASS |

### 1.5 提交規範

```bash
# 每次 TDD cycle 完成後
git add .
git commit -m "TDD: [feature] - [what was implemented]"

# Feature 完成後
git push -u origin v3/[feature-name]
```

---

## STEP 2: Merge to main

### 2.1 建立 PR

```bash
# 在 GitHub 上建立 PR
# From: v3/[feature-name]
# To: main
```

### 2.2 PR Review 檢查清單

- [ ] TDD 測試全部 PASS
- [ ] Coverage ≥ 80%
- [ ] Pre-push checks PASS
- [ ] Code Review 通過
- [ ] 文件更新（SKILL.md, CHANGELOG.md）

### 2.3 Merge

```
PR approved
       │
       ▼
┌──────────────┐
│ Squash & Merge│
│ to main      │
└──────┬───────┘
       │
       ▼
  main branch
  (含新 Feature)
```

---

## STEP 3: main Branch — Real Project Validation

### 3.1 為什麼要在 main 驗證？

```
┌─────────────────────────────────────────────────────┐
│ 為什麼需要 Real Project Validation？                   │
├─────────────────────────────────────────────────────┤
│                                                      │
│ TDD 測試 ──► 理想條件下的驗證                       │
│           ──► 不等於 真實專案                        │
│                                                      │
│ 真實專案會遇到：                                     │
│ • 複雜的 edge cases                                 │
│ • 與其他 Feature 的交互                             │
│ • 實際的 project structure                          │
│ • 團隊的實際使用方式                                │
│                                                      │
│ 所以要在 main branch 用真實專案驗證                   │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 3.2 驗證流程

```
┌─────────────────────────────────────────────────────┐
│ main branch — Real Project Validation                │
├─────────────────────────────────────────────────────┤
│                                                      │
│  1. Checkout main (已含新 Feature)                  │
│                                                      │
│  2. 建立測試專案 或 使用現有專案                     │
│     • 新專案：快速驗證基本功能                       │
│     • 現有專案：驗證與其他 Feature 整合              │
│                                                      │
│  3. 執行 Phase 1-8                                  │
│     • Phase 1: 初始化                                │
│     • Phase 2: Constitution Check                    │
│     • Phase 3: BVS / CQG                            │
│     • Phase 4: Test Execution                        │
│     • Phase 5: Baseline Verification                  │
│     • Phase 6: Quality Assurance                     │
│     • Phase 7: Risk Management                        │
│     • Phase 8: Configuration                          │
│                                                      │
│  4. 發現 Bug                                        │
│     • 記錄 bug 在 issues                             │
│     • 修復後 commit                                  │
│                                                      │
│  5. 所有 Phase PASS → Feature 正式完成               │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### 3.3 Bug 追蹤

```markdown
## Feature Bug Report

| Bug ID | 描述 | 嚴重性 | 狀態 | 修復 commit |
|--------|------|--------|------|------------|
| MCP-001 | stdio transport 異常 | High | Fixed | abc123 |
| MCP-002 | service discovery timeout | Medium | Fixed | def456 |
```

### 3.4 Feature 完成標準

```
┌─────────────────────────────────────────────────────┐
│ Feature 完成標準                                      │
├─────────────────────────────────────────────────────┤
│                                                      │
│ [ ] 在 methodology-v3 完成 TDD 驗證                   │
│ [ ] Merge 到 main                                    │
│ [ ] 在 main 用真實專案執行 Phase 1-8                 │
│ [ ] 所有 Bug 已修復                                  │
│ [ ] Phase 1-8 全部 PASS                             │
│ [ ] Feature 正式完成                                │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## 完整循環示意圖

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                  │
│  Feature #1: MCP Protocol                                        │
│  ─────────────────────────────                                    │
│  v3/mcp → PR → main → Real Project Validation → DONE            │
│                           │                                        │
│                           ▼                                        │
│  Feature #2: 分級治理                                              │
│  ─────────────────────────────                                    │
│  v3/tiered-governance → PR → main → Real Project Validation → DONE│
│                           │                                        │
│                           ▼                                        │
│  Feature #3: Kill-Switch                                          │
│  ─────────────────────────────                                    │
│  v3/kill-switch → PR → main → Real Project Validation → DONE    │
│                           │                                        │
│                           ▼                                        │
│  ...                                                               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 注意事項

### 失敗處理

```
若 Real Project Validation 發現 Bug：
1. 在 main branch 修復 bug
2. commit 修復
3. 繼續 validation
4. 修復後仍無法通過 → 回溯到 methodology-v3
   重新檢視 Feature 實作
```

### Feature 暫停

```
若 Feature 開發遇到 blocking issue：
1. 記錄 issue
2. 暫停此 Feature
3. 進行下一個 Feature
4. 稍後回頭處理
```

---

*文件版本：1.0*
*更新日期：2026-04-17*
