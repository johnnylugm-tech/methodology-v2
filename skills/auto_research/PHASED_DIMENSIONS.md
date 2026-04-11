# AutoResearch 維度階段化策略

> **Version**: v1.0.0
> **Date**: 2026-04-11
> **Author**: Musk Agent
> **Purpose**: 根據專案階段漸進式納入品質維度

---

## 核心理念

不是所有維度在專案一開始就「ready」。根據：
1. **依賴關係** — 某些維度需要其他產出（如測試）
2. **工具支援程度** — 工具能否獨立在早期階段運作
3. **資訊完整性** — 必要資訊是否足夠評估

---

## 維度階段化矩陣

| 維度 | Phase 3 | Phase 4 | Phase 5 | Phase 6 | Phase 7+ |
|------|---------|---------|---------|---------|----------|
| **D1 Linting** | ✅ MUST | ✅ | ✅ | ✅ | ✅ |
| **D5 Complexity** | ✅ MUST | ✅ | ✅ | ✅ | ✅ |
| **D6 Architecture** | ✅ CAN | ✅ | ✅ | ✅ | ✅ |
| **D7 Readability** | ✅ CAN | ✅ | ✅ | ✅ | ✅ |
| **D8 ErrorHandling** | ⚠️ PARTIAL | ✅ CAN | ✅ | ✅ | ✅ |
| **D9 Documentation** | ⚠️ PARTIAL | ✅ CAN | ✅ | ✅ | ✅ |
| **D2 TypeSafety** | ❌ 0% | ⚠️ PARTIAL | ✅ CAN | ✅ | ✅ |
| **D4 Security** | ❌ ~30% | ⚠️ PARTIAL | ✅ CAN | ✅ | ✅ |
| **D3 Coverage** | ❌ 0% | ❌ 0% | ⚠️ PARTIAL | ✅ CAN | ✅ |

### 圖示說明

| 圖示 | 意義 |
|------|------|
| ✅ MUST | 必須納入，工具完整支援 |
| ✅ CAN | 可納入，取決於團隊意願 |
| ⚠️ PARTIAL | 部分支援，但需要手動介入 |
| ❌ 0% | 依賴尚未存在的產出，不適合納入 |

---

## 階段詳細分析

### Phase 3 (Code Implementation) — 代碼實作

**可用維度**: D1, D5, D6, D7

| 維度 | Readiness | 原因 |
|------|----------|------|
| D1 Linting | ✅ MUST | ruff 直接分析源代碼，無需測試 |
| D5 Complexity | ✅ MUST | lizard 分析 CC，無需測試 |
| D6 Architecture | ✅ CAN | radon 分析結構，無需測試 |
| D7 Readability | ✅ CAN | Agent 可閱讀代碼做主觀評估 |
| D8 ErrorHandling | ⚠️ PARTIAL | 可檢測 try-except，但需要業務理解 |
| D9 Documentation | ⚠️ PARTIAL | 可檢測 docstring，但品質需要人工 |
| D2 TypeSafety | ❌ 0% | mypy 需要完整類型註解，Phase 3 通常沒有 |
| D3 Coverage | ❌ 0% | 沒有 tests/ 目錄，無法測量 |
| D4 Security | ⚠️ ~30% | bandit 可運行，但深度審計需要測試 |

**Phase 3 目標分數**: ~50-60%（4個 MUST + 2個 CAN）

### Phase 4 (Testing) — 測試生成

**可用維度**: D3 加入, D2/D4 提升

| 維度 | Readiness | 原因 |
|------|----------|------|
| D3 Coverage | ✅ CAN | tests/ 存在，可測量覆蓋率 |
| D2 TypeSafety | ⚠️ PARTIAL | 有測試後，類型問題更明顯 |
| D4 Security | ⚠️ PARTIAL | 可加入安全測試 |

**Phase 4 目標分數**: ~65-75%（6個維度）

### Phase 5 (Verification) — 驗證

**可用維度**: D2/D3/D4 提升至 MUST

| 維度 | Readiness | 原因 |
|------|----------|------|
| D2 TypeSafety | ✅ CAN | 類型註解已成為常見 |
| D3 Coverage | ✅ CAN | 測試成熟，覆盖率可達標 |
| D4 Security | ✅ CAN | 安全測試可自動化 |

**Phase 5 目標分數**: ~80%+(9個維度)

### Phase 6-7 (Maintenance) — 維護

**可用維度**: 全部維度 MUST

所有維度都ready，目標全面達標。

---

## 漸進式分數計算

### Phase 3 計算

```
維度權重（Phase 3）:
- D1 Linting: 10%
- D5 Complexity: 10%
- D6 Architecture: 10%
- D7 Readability: 10%
- D8 ErrorHandling: 5%
- D9 Documentation: 5%
- D2 TypeSafety: 0% (不納入)
- D3 Coverage: 0% (不納入)
- D4 Security: 0% (不納入)

總權重: 50%
目標分數: 50% × 85% = 42.5% (約 43%)
```

### Phase 4 計算

```
新增維度:
- D3 Coverage: 20%
- D2 TypeSafety: 15% (PARTIAL)
- D4 Security: 15% (PARTIAL)

總權重: 50% + 35% = 85%
目標分數: 85% × 80% = 68%
```

### Phase 5+ 計算

```
全部維度:
- 總權重: 100%
- 目標分數: 85%+
```

---

## 實作策略

### 1. 維度配置檔案

```yaml
# auto_research_config.yaml
phases:
  phase_3:
    enabled_dimensions:
      - D1_Linting
      - D5_Complexity
      - D6_Architecture
      - D7_Readability
    optional_dimensions:
      - D8_ErrorHandling
      - D9_Documentation
    target_score: 43  # 50% × 85%
  
  phase_4:
    enabled_dimensions:
      - D1_Linting
      - D2_TypeSafety
      - D3_TestCoverage
      - D4_Security
      - D5_Complexity
      - D6_Architecture
    optional_dimensions:
      - D7_Readability
      - D8_ErrorHandling
      - D9_Documentation
    target_score: 68  # 85% × 80%
  
  phase_5:
    enabled_dimensions: all
    target_score: 85
```

### 2. 動態維度檢測

```python
def get_active_dimensions(phase: int) -> List[str]:
    """根據階段返回活躍維度"""
    dimension_map = {
        3: ['D1', 'D5', 'D6', 'D7', 'D8', 'D9'],
        4: ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9'],
        5: ['D1', 'D2', 'D3', 'D4', 'D5', 'D6', 'D7', 'D8', 'D9'],
    }
    return dimension_map.get(phase, dimension_map[5])
```

### 3. 分數標準化

```python
def calculate_normalized_score(scores: Dict, active_dims: List[str]) -> float:
    """只計算活躍維度的加權分數"""
    weight_map = {
        'D1': 10, 'D2': 15, 'D3': 20, 'D4': 15,
        'D5': 10, 'D6': 10, 'D7': 10, 'D8': 5, 'D9': 5
    }
    
    total_weight = sum(weight_map[d] for d in active_dims)
    weighted_score = sum(scores[d] * weight_map[d] for d in active_dims)
    
    return weighted_score / total_weight
```

---

## 範例：tts-kokoro-v613

### Phase 3 結束時的評估

```python
scores = {
    'D1_Linting': 85,      # ✅ MUST
    'D5_Complexity': 80,   # ✅ MUST  
    'D6_Architecture': 70, # ✅ CAN
    'D7_Readability': 70,   # ✅ CAN
    'D8_ErrorHandling': 54,  # ⚠️ PARTIAL
    'D9_Documentation': 70, # ⚠️ PARTIAL
    'D2_TypeSafety': 0,     # ❌ 不納入
    'D3_Coverage': 0,       # ❌ 不納入
    'D4_Security': 30,      # ⚠️ PARTIAL
}

active_dims = ['D1', 'D5', 'D6', 'D7', 'D8', 'D9']
normalized_score = calculate_normalized_score(scores, active_dims)
# = (85×10 + 80×10 + 70×10 + 70×10 + 54×5 + 70×5) / 50
# = 4290 / 50 = 85.8%
```

### 如果 Phase 3 分數是 0% 的維度？

```python
if scores.get('D3_Coverage', 0) == 0:
    print("❌ D3 不適合納入 Phase 3（沒有測試）")
    # 不計入分母，不影響normalized_score
```

---

## 決策樹

```
專案處於哪個 Phase？
    │
    ├─→ Phase 3
    │    └─→ 活躍維度: D1, D5, D6, D7 (+ D8, D9 可選)
    │        └─→ D3/D2/D4 分數為 0？→ 不納入計算
    │
    ├─→ Phase 4
    │    └─→ 活躍維度: D1, D2, D3, D4, D5, D6 (+ D7, D8, D9 可選)
    │
    ├─→ Phase 5+
    │    └─→ 活躍維度: 全部 9 維度
    │
    └─→ 其他
         └─→ 預設: 全部維度
```

---

## Quick Reference

| Phase | 活躍維度 | 目標分數 |
|-------|----------|----------|
| Phase 3 | D1, D5, D6, D7 (+ D8, D9 可選) | ~43% |
| Phase 4 | D1, D2, D3, D4, D5, D6 (+ D7, D8, D9 可選) | ~68% |
| Phase 5+ | 全部 9 維度 | 85%+ |

*最後更新: 2026-04-11*
