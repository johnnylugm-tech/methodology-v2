# Case 49: Mutation Testing - 變異測試系統

## 概述

Mutation Testing（變異測試）是一種軟體測試技術，用於評估現有測試 suite 的品質。其核心思想是：**故意在程式碼中注入錯誤（mutations），然後檢查測試是否能發現這些錯誤**。

對標 TDAD 的 Semantic Mutation Testing 系統，本案例實作了一套完整的變異測試框架。

---

## 核心概念

### Mutation Score

```
Mutation Score = 偵測到的變異體數量 / 總變異體數量 × 100%
```

- **100%**: 測試 suite 非常強，能發現所有錯誤
- **< 50%**: 測試 suite 有盲點，很多錯誤測不出來

### 變異類型 (MutationType)

| 類型 | 說明 | 範例 |
|------|------|------|
| `VARIABLE_REPLACE` | 變數替換 | `x` → `y` |
| `CONDITION_FLIP` | 條件反轉 | `if x == 5` → `if not (x == 5)` |
| `LOGIC_DELETE` | 刪除邏輯 | `return a and b` → `return a` |
| `CONSTANT_CHANGE` | 常數改變 | `limit = 100` → `limit = 101` |
| `OPERATOR_SWAP` | 操作符交換 | `a + b` → `a - b` |
| `DEAD_CODE` | 無用程式碼 | 插入無效程式碼 |

---

## 系統架構

```
┌─────────────────┐
│ MutationGenerator│ ← 讀取原始程式碼，套用變異操作
└────────┬────────┘
         │ List[Mutation]
         ▼
┌─────────────────┐
│  MutationTester │ ← 執行變異體，判斷是否被偵測
└────────┬────────┘
         │ MutationResult
         ▼
┌─────────────────┐
│   Summary       │ ← 計算 mutation score
└─────────────────┘
```

---

## 使用範例

### 基本用法

```python
from anti_shortcut.mutation_tester import run_mutation_testing, MutationGenerator, MutationTester

# 原始程式碼
code = """
def calculate_discount(price, age):
    if age >= 65:
        return price * 0.5
    elif age >= 18:
        return price * 1.0
    else:
        return price * 0.8
"""

# 自定義測試執行器
def my_test_runner(mutated_code: str) -> bool:
    """測試執行器：返回 True = 測試通過, False = 發現錯誤"""
    # 這裡可以執行實際的測試邏輯
    # 例如：compile + run + check output
    return True  # 預設：所有變異都通過（即未被偵測）

# 執行變異測試
result = run_mutation_testing(code, test_runner=my_test_runner)

print(f"Mutation Score: {result['mutation_score']}%")
print(f"Detected: {result['detected']}/{result['total']}")
```

### 進階用法

```python
from anti_shortcut.mutation_tester import MutationGenerator, MutationTester, MutationType

# 自定義變異生成器
generator = MutationGenerator()
mutations = generator.generate(code, num_mutations=50)

# 自定義測試器
def strict_test_runner(code: str) -> bool:
    # 假設這裡有嚴格的測試邏輯
    return run_your_test_suite(code)

tester = MutationTester(test_runner=strict_test_runner)
summary = tester.run_all(mutations)

# 輸出報告
print(f"""
=== Mutation Testing Report ===
Total Mutations: {summary['total']}
Detected:        {summary['detected']}
Not Detected:    {summary['not_detected']}
Mutation Score:  {summary['mutation_score']}%

By Type:
""")
for mt, stats in summary['by_type'].items():
    score = stats['detected'] / stats['total'] * 100
    print(f"  {mt}: {stats['detected']}/{stats['total']} ({score:.1f}%)")
```

---

## 實作細節

### MutationGenerator

負責生成變異體：

1. 逐行掃描原始程式碼
2. 對每行嘗試套用變異操作
3. 檢測變異類型並生成描述
4. 返回 `List[Mutation]`

變異策略：
- **條件反轉**: `if (x)` → `if not (x)`
- **常數增量**: `5` → `6`
- **布爾反轉**: `==` → `!=`, `True` → `False`

### MutationTester

負責執行變異測試：

1. 接收變異體列表
2. 對每個變異體執行 `test_runner`
3. 統計偵測結果
4. 計算分項和總體分數

### 偵測邏輯

```
detected = not test_runner(mutated_code)
```

- 變異後程式碼導致測試失敗 → `detected = True`（成功發現錯誤）
- 變異後程式碼仍通過測試 → `detected = False`（錯誤未被發現）

---

## 與 TDAD 的關係

本系統對標 TDAD 的 **Semantic Mutation Testing**：

| TDAD Feature | 本系統實作 |
|--------------|-----------|
| 變異操作多樣化 | 6 種變異類型 |
| 語意感知變異 | 條件/邏輯/常量分開處理 |
| Mutation Score | 0-100% 量化指標 |
| 分類統計 | `by_type` 維度分析 |

---

## 應用場景

### 1. 測試品質評估
- 評估現有測試 suite 的健壯性
- 發現測試覆蓋盲點

### 2. 回歸測試增強
- 對關鍵函數進行變異測試
- 確保測試能捕捉常見錯誤模式

### 3. AI Agent 評估
- 測試 AI 生成的程式碼品質
- 評估 AI 是否能發現/避免特定錯誤模式

---

## 限制與注意事項

1. **執行時間**: 變異測試通常比一般測試慢（需要執行 N 個變異體）
2. **等價變異**: 有些變異不改變程式行為（equivalent mutants），會影響分數
3. **測試設計**: 需要根據實際場景設計有意義的 `test_runner`
4. **覆蓋範圍**: 變異測試不能替代其他測試方法

---

## 延伸參考

- 相關案例: [Case 45 - Anti-Shortcut Framework](./case45_anti_shortcut.md)
- 相關案例: [Case 46 - Audit Logger](./case46_audit_logger.md)
- TDAD: Test-Driven Agent Debugging
