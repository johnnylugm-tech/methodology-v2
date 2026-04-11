# AutoResearch Skill

> **Version**: v1.2.0
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
- **Agent 只做一件事：提升品質分數**

---

## 2. 9 維度品質模型

### 2.1 維度權重

| 維度 | 權重 | Tool-Driven | 目標分數 |
|------|------|-------------|----------|
| D1 Linting | 10% | ✅ ruff | ≥85% |
| D2 Type Safety | 15% | ✅ mypy | ≥90% |
| D3 Test Coverage | 20% | ✅ pytest-cov | ≥70% |
| D4 Security | 15% | ✅ bandit/semgrep | ≥90% |
| D5 Complexity | 10% | ✅ lizard | ≥80% |
| D6 Architecture | 10% | ⚠️ radon + agent | ≥70% |
| D7 Readability | 10% | ⚠️ agent | ≥70% |
| D8 Error Handling | 5% | ⚠️ agent | ≥60% |
| D9 Documentation | 5% | ⚠️ agent | ≥70% |

### 2.2 評估標準

| 維度 | 評估標準 |
|------|----------|
| D1 Linting | ruff/flake8 錯誤數量，代碼風格一致性 |
| D2 TypeSafety | mypy 錯誤數量，類型註解完整度 |
| D3 Coverage | pytest-cov 覆蓋率，關鍵函數是否被測試 |
| D4 Security | bandit 安全問題數量，是否有已知漏洞 |
| D5 Complexity | lizard CCN 複雜度，函數是否過於複雜 |
| D6 Architecture | radon 架構評分，模組耦合度 |
| D7 Readability | 代碼可讀性，是否符合 PEP8 |
| D8 ErrorHandling | 錯誤處理覆蓋率，是否有 try-except |
| D9 Documentation | docstring 完整度，是否有使用範例 |

---

## 3. 檔案結構

```
quality_dashboard/
├── SKILL.md                    # 本檔案
├── dashboard.py               # 9維度評估引擎
├── auto_research_loop.py      # 標準 AutoResearch
├── agent_auto_research.py     # Agent驅動版（推薦）
└── programs/                  # 維度program模板
    ├── D3_Coverage.md
    ├── D8_ErrorHandling.md
    └── ...

skills/auto_research/
├── SKILL.md                   # 本檔案
├── SOFTWARE_QUALITY_TEMPLATE.md  # program.md 等價物
└── README.md
```

---

## 4. 快速開始

### 4.1 基本評估

```bash
# 基本評估
python3 quality_dashboard/dashboard.py --project /path/to/project

# 生成 HTML 報告
python3 quality_dashboard/dashboard.py --project /path/to/project --html
```

### 4.2 AutoResearch 改進

```bash
# 使用 AI Agent 進行 3 輪自動改進
python3 quality_dashboard/agent_auto_research.py --project /path/to/project --iterations 3

# 指定維度和目標
python3 quality_dashboard/agent_auto_research.py \
    --project /path/to/project \
    --iterations 5 \
    --dimensions D2,D3,D4 \
    --target 85
```

---

## 5. AutoResearch Loop 流程

### 5.1 標準流程

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 評估                                                  │
│    python3 dashboard.py --project /path                  │
│    ↓                                                     │
│ 2. 識別最低分維度（< 70%）                              │
│    ↓                                                     │
│ 3. 根據 SOFTWARE_QUALITY_TEMPLATE.md 執行修復           │
│    ↓                                                     │
│ 4. 重新評估                                              │
│    ↓                                                     │
│ 5. 如果改善 → 保留                                       │
│    如果未改善 → 回滾 + 繼續下一個維度                     │
│    ↓                                                     │
│ 6. 重複直到達標或達到最大迭代                            │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 保護機制

| 機制 | 觸發條件 | 行為 |
|------|----------|------|
| 迭代上限 | 達到 max_iterations | 停止並報告 |
| 回滾機制 | 無改善 | 回復原始代碼 |
| 無改善停止 | 連續 2 次無改善 | 停止該維度 |
| 分數上限 | 達到 100% | 跳過該維度 |

### 5.3 迭代參數

| 參數 | 預設值 | 說明 |
|------|--------|------|
| max_iterations | 5 | 最大迭代次數 |
| target_score | 85.0% | 目標總分 |
| min_dim_score | 70% | 最低維度分數門檻 |

---

## 6. program.md 等價物

`SOFTWARE_QUALITY_TEMPLATE.md` 是 AutoResearch 的核心指導文件。

### 6.1 模板結構

```markdown
#### 第一階段：定義品質基線與瓶頸分析
> **指令**：分析 9 個維度的分數，識別瓶頸

#### 第二階段：設定品質評分量表
> **指令**：評估改進幅度、品質、副作用風險

#### 第三階段：啟動「上帝模式」品質改進迭代
> **指令**：執行 5 輪迭代修復

#### 第四階段：研究成果落地儀表板
> **指令**：生成 Quality Dashboard 報告
```

---

## 7. 與 methodology-v2 整合

### 7.1 Phase Trigger

在特定 Phase 完成後自動觸發：

```yaml
# project-config.yaml
auto_research:
  enabled: true
  trigger_after_phase: [3, 5]
  target_dimensions: [D2, D3, D4]
  min_score_threshold: 60
```

### 7.2 觸發流程

```
Phase 3 完成 → 檢查品質分數 → < 60% → 自動執行 AutoResearch → 產出報告
```

---

## 8. 已知限制

### 8.1 維度限制

| 維度 | 問題 | 解決方案 |
|------|------|----------|
| D2 TypeSafety | 需要理解業務邏輯 | Phase 4 後手動添加 |
| D3 Coverage | 需要建立測試架構 | Phase 4 實作測試 |
| D4 Security | 需要深度安全審計 | 建議人工複審 |

### 8.2 AutoResearch 能力

- ✅ **能發現**：Linting、Complexity 問題
- ⚠️ **部分能修復**：Error Handling、Documentation
- ❌ **無法自動修復**：Type Safety、Coverage（需要 Agent 深度理解代碼）

---

## 9. 維度階段化策略

根據 Phase 漸進納入維度，避免 0% 分數拉低整體：

| 維度 | Phase 3 | Phase 4 | Phase 5+ |
|------|---------|---------|----------|
| D1 Linting | ✅ MUST | ✅ | ✅ |
| D5 Complexity | ✅ MUST | ✅ | ✅ |
| D6 Architecture | ✅ CAN | ✅ | ✅ |
| D7 Readability | ✅ CAN | ✅ | ✅ |
| D8 ErrorHandling | ⚠️ PARTIAL | ✅ | ✅ |
| D9 Documentation | ⚠️ PARTIAL | ✅ | ✅ |
| D2 TypeSafety | ❌ 0% | ⚠️ PARTIAL | ✅ |
| D3 Coverage | ❌ 0% | ❌ 0% | ✅ |
| D4 Security | ❌ ~30% | ⚠️ PARTIAL | ✅ |

詳見 `PHASED_DIMENSIONS.md`。

---

## 10. Quick Reference

```bash
# 1. 基本評估
python3 quality_dashboard/dashboard.py --project /path/to/project

# 2. 生成 HTML 報告
python3 quality_dashboard/dashboard.py --project /path --html

# 3. AutoResearch 3輪改進
python3 quality_dashboard/agent_auto_research.py --project /path --iterations 3

# 4. 指定維度
python3 quality_dashboard/agent_auto_research.py --project /path --dimensions D2,D3,D4
```

---

*最後更新: 2026-04-11*
