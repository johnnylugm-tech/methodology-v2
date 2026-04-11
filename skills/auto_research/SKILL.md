# AutoResearch Skill

> **Version**: v2.0.0
> **Date**: 2026-04-11
> **Author**: Musk Agent
> **Purpose**: 自動品質改進系統 - 迭代式優化軟體品質
> **Inspired by**: [karpathy/autoresearch](https://github.com/karpathy/autoresearch)

---

## 1. Concept & Vision

**AutoResearch** 是基於 Karpathy AutoResearch 概念的自動品質改進系統。

### 1.1 核心靈感（來自 Karpathy）

Karpathy 的 AutoResearch 核心設計：
- **Agent 只修改一個檔案** (`train.py`) — 這讓範圍可控、diff 可審查
- **固定時間預算** (5 分鐘) — 使得實驗可直接比較
- **`program.md` 是核心** — AI agent 閱讀這個檔案並遵循指示
- **自我包含** — 不需要外部依賴

### 1.2 對應到軟體品質

| Karpathy AutoResearch | 軟體品質版 |
|----------------------|------------|
| `train.py` | 源代碼 (`.py` 檔案) |
| `program.md` | `SOFTWARE_QUALITY_TEMPLATE.md` |
| val_bpb (越低越好) | 9維度分數 (越高越好) |
| 5分鐘固定訓練預算 | 每維度修復限時 |
| 實驗次數/小時 | 迭代次數 |

### 1.3 核心理念

- **不依賴主觀假設，用數據說話**
- **迭代式改進，每次小前進**
- **保護機制：無改善則回滾**
- **Phase-aware scoring** — 每個 Phase 只計算活躍維度

---

## 2. 9 維度品質模型

### 2.1 Phase-aware Scoring（重要！）

| Phase | 活躍維度 | 數量 | 及格 | 目標 |
|-------|----------|------|------|------|
| **Phase 3** | D1, D5, D6, D7 | 4 | 70 | 85 |
| **Phase 4** | D1, D2, D3, D4, D5, D6, D7 | 7 | 70 | 85 |
| **Phase 5+** | D1-D9 全部 | 9 | 70 | 85 |

### 2.2 維度權重（靜態參考）

| 維度 | 權重 | Tool-Driven | 目標 |
|------|------|-------------|------|
| D1 Linting | 10% | ✅ ruff | ≥85% |
| D2 Type Safety | 15% | ✅ mypy | ≥90% |
| D3 Test Coverage | 20% | ✅ pytest-cov | ≥70% |
| D4 Security | 15% | ✅ bandit/semgrep | ≥90% |
| D5 Complexity | 10% | ✅ lizard | ≥80% |
| D6 Architecture | 10% | ⚠️ radon | ≥70% |
| D7 Readability | 10% | ⚠️ agent | ≥70% |
| D8 Error Handling | 5% | ⚠️ agent | ≥60% |
| D9 Documentation | 5% | ⚠️ agent | ≥70% |

---

## 3. 檔案結構

```
skills/auto_research/
├── SKILL.md                      # 本檔案
├── PHASED_DIMENSIONS.md          # 維度階段化策略 v3.0
├── SOFTWARE_QUALITY_TEMPLATE.md  # Prompt 模板
├── INTEGRATION.md               # methodology-v2 整合方案
└── README.md

quality_dashboard/
├── dashboard.py                  # 9維度評估引擎
├── agent_auto_research.py        # Agent驅動版（含 phase-aware）
└── ...
```

---

## 4. 快速開始

### 4.1 CLI 命令

```bash
# 獨立執行 AutoResearch
python3 cli.py auto-research --project /path/to/project --phase 3

# 執行 Phase（AutoResearch 自動啟動）
python3 cli.py run-phase --phase 3 --repo /path/to/project

# 停用 AutoResearch
python3 cli.py run-phase --phase 3 --repo /path/to/project --no-autoresearch
```

### 4.2 設定檔

```yaml
# project-config.yaml
auto_research:
  enabled: true  # 預設 true
```

### 4.3 程式碼呼叫

```python
from quality_dashboard.agent_auto_research import AgentDrivenAutoResearch

# Phase 3（只計算 D1, D5, D6, D7）
agent = AgentDrivenAutoResearch('/path/to/project', phase=3)
result = agent.run(max_iterations=3)
```

---

## 5. Phase-aware Scoring 邏輯

### 5.1 分數計算

```python
# Phase 3：只計算 4 個維度的平均
active_scores = {D1: 90, D5: 100, D6: 100, D7: 100}
total_score = sum(active_scores.values()) / 4  # = 97.5

# Phase 5+：計算全部 9 個維度的平均
active_scores = {D1: 90, D2: 0, D3: 0, D4: 30, D5: 100, ...}
total_score = sum(active_scores.values()) / 9
```

### 5.2 維度分類

| 類別 | Phase 3 | Phase 4 | Phase 5+ |
|------|---------|---------|----------|
| **MUST** | D1, D5 | D1, D5 | 全部 |
| **CAN** | D6, D7 | D6, D7 | - |
| **PARTIAL** | D8, D9 | D2, D3, D4 | - |
| **INACTIVE** | D2, D3, D4 | D8, D9 | - |

---

## 6. AutoResearch Loop 流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 測量活躍維度（根據 Phase）                              │
│    └─→ Phase 3: D1, D5, D6, D7                            │
│ 2. 識別低分維度（< 及格線 70）                              │
│ 3. 修復問題（不考慮加分多少）                              │
│ 4. 重新測量                                               │
│ 5. 重複直到：                                              │
│    ├─ 所有維度都 ≥ 85，或                                │
│    ├─ 已達最大迭代次數，或                                │
│    └─ 連續無改善                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 7. 實作狀態

| 元件 | 狀態 | 版本 |
|------|------|------|
| `dashboard.py` | ✅ 完成 | 9維度評估 |
| `agent_auto_research.py` | ✅ 完成 | v2.0 (phase-aware) |
| `SOFTWARE_QUALITY_TEMPLATE.md` | ✅ 完成 | v1.1 |
| `PHASED_DIMENSIONS.md` | ✅ 完成 | v3.0 |
| `INTEGRATION.md` | ✅ 完成 | v1.0 |
| **CLI 整合** | ✅ 完成 | v7.35+ |
| **Phase-aware scoring** | ✅ 完成 | v7.36 |

---

## 8. Quick Reference

| 命令 | 說明 |
|------|------|
| `python3 cli.py auto-research -p /path --phase 3` | 執行 AutoResearch |
| `python3 cli.py run-phase --phase 3 --repo /path` | Phase 3 + AutoResearch |
| `python3 cli.py run-phase --phase 3 --no-autoresearch` | 停用 AutoResearch |

---

*最後更新: 2026-04-11*
