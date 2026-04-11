# AutoResearch 維度階段化策略 v3.0

> **Version**: v3.0
> **Date**: 2026-04-11
> **Author**: Musk Agent
> **Purpose**: 漸進式維度納入 + Phase-aware scoring

---

## 核心理念（v3.0）

### Phase-aware Scoring

每個 Phase 只計算該 Phase 的**活躍維度**，分數都是 100 分滿分。

```
Phase 3: (D1 + D5 + D6 + D7) / 4 × 100 = 85-100分
Phase 4: (D1 + D2 + D3 + D4 + D5 + D6 + D7) / 7 × 100 = 85分
Phase 5+: (D1 + D2 + D3 + D4 + D5 + D6 + D7 + D8 + D9) / 9 × 100 = 85分
```

### 問題優先原則

```
❌ 不再問：「修這個能加多少分？」
✅ 只問：「這個維度有問題嗎？有就修」
```

---

## 各 Phase 維度配置

### Phase 3: 代碼實作階段

| 維度 | 類別 | 計入方式 |
|------|------|----------|
| D1 Linting | MUST | ✅ 100% |
| D5 Complexity | MUST | ✅ 100% |
| D6 Architecture | CAN | ✅ 100% |
| D7 Readability | CAN | ✅ 100% |

**計算**: `(D1 + D5 + D6 + D7) / 4`
**及格**: 70分 | **目標**: 85分

### Phase 4: 測試生成階段

| 維度 | 類別 | 計入方式 |
|------|------|----------|
| D1 Linting | MUST | ✅ 100% |
| D5 Complexity | MUST | ✅ 100% |
| D6 Architecture | CAN | ✅ 100% |
| D7 Readability | CAN | ✅ 100% |
| D2 TypeSafety | PARTIAL | ⚠️ 50% |
| D3 Coverage | PARTIAL | ⚠️ 50% |
| D4 Security | PARTIAL | ⚠️ 50% |

**計算**: `(D1 + D5 + D6 + D7 + D2×0.5 + D3×0.5 + D4×0.5) / 7`
**及格**: 70分 | **目標**: 85分

### Phase 5+: 驗證/維護階段

| 維度 | 類別 | 計入方式 |
|------|------|----------|
| 全部 9 維度 | MUST | ✅ 100% |

**計算**: `(D1 + D2 + D3 + D4 + D5 + D6 + D7 + D8 + D9) / 9`
**及格**: 70分 | **目標**: 85分

---

## 分數對照表

| Phase | 維度數 | 滿分 | 及格 | 目標 |
|-------|--------|------|------|------|
| Phase 3 | 4 | 100 | 70 | 85 |
| Phase 4 | 7 | 100 | 70 | 85 |
| Phase 5+ | 9 | 100 | 70 | 85 |

---

## AutoResearch Loop 流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 根據 Phase 取得活躍維度                                 │
│    Phase 3 → [D1, D5, D6, D7]                             │
│    Phase 4 → [D1, D2, D3, D4, D5, D6, D7]                 │
│    Phase 5+ → [D1, D2, D3, D4, D5, D6, D7, D8, D9]        │
│ 2. 測量活躍維度的分數                                       │
│ 3. 識別有問題的維度（< 70 分）                              │
│ 4. 修復問題（不考慮加分多少）                              │
│ 5. 重複直到：                                              │
│    ├─ 所有維度都 ≥ 85 或                                  │
│    ├─ 已達最大迭代次數 或                                 │
│    └─ 連續無改善                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 實例：tts-kokoro-v613 Phase 3

### 修復前
| 維度 | 分數 | 有問題？ |
|------|------|----------|
| D1 Linting | 90% | 有 |
| D5 Complexity | 40% | 有 |
| D6 Architecture | 70% | 有 |
| D7 Readability | 100% | 無 |

```
分數 = (90 + 40 + 70 + 100) / 4 = 75 分 ❌ 未達標
```

### 修復後
| 維度 | 分數 |
|------|------|
| D1 Linting | 100% |
| D5 Complexity | 100% |
| D6 Architecture | 100% |
| D7 Readability | 100% |

```
分數 = (100 + 100 + 100 + 100) / 4 = 100 分 ✅
```

---

## CLI 整合

```bash
# Phase 3 AutoResearch
python3 cli.py auto-research --project /path --phase 3

# Phase 5 AutoResearch
python3 cli.py auto-research --project /path --phase 5

# 設定檔關閉
# project-config.yaml:
# auto_research:
#   enabled: false
```

---

## Quick Reference

| Phase | 活躍維度 | 公式 | 及格 | 目標 |
|-------|----------|------|------|------|
| Phase 3 | D1, D5, D6, D7 | /4 | 70 | 85 |
| Phase 4 | D1-D7 | /7 | 70 | 85 |
| Phase 5+ | D1-D9 | /9 | 70 | 85 |

---

*最後更新: 2026-04-11*
