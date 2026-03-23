# Case 51: TDAD Hidden Tests - 可見/隱藏測試分割

## 概述

TDAD（Test-Driven AI Development）方法論的核心創新之一是 **Visible/Hidden Test Splits**。這個設計解決了傳統 TDD 的一個根本問題：**開發者如果知道測試內容，可能會針對測試而非真實需求編寫程式碼**（specification gaming）。

本案例介紹如何在 Quality Gate 中實作 TDAD 風格的隱藏測試機制。

---

## 核心概念

### Visible Tests（可見測試）

開發者可以看到的測試，用於：
- **引導開發方向**：告訴開發者需要滿足的規格
- **提供即時反饋**：讓開發者知道距離目標還有多遠
- **記錄預期行為**：作為團隊共識的規格文件

### Hidden Tests（隱藏測試）

開發者**看不到**的測試，用於：
- **最終驗證**：在提交前確保真正滿足需求
- **防止 gaming**：開發者無法針對未知的測試優化
- **公平評估**：所有提交的程式碼都面對相同的隱藏測試

### 為什麼需要分割？

```
傳統 TDD 問題：
┌──────────────┐    ┌──────────────┐
│   開發者      │ →  │  看到測試     │ →  針對測試編寫代碼
│              │    │  (藍圖)       │    只通過測試但不符合真實需求
└──────────────┘    └──────────────┘

TDAD 解決方案：
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│   開發者      │ →  │  Visible     │ →  │  Hidden      │
│              │    │  Tests       │    │  Tests       │
│              │    │  (引導方向)    │    │  (最終驗證)   │
└──────────────┘    └──────────────┘    └──────────────┘
```

---

## 核心指標：Hidden Pass Rate

Hidden Pass Rate 是 TDAD 的核心品質指標：

```
Hidden Pass Rate = 通過的隱藏測試數 / 隱藏測試總數 × 100%
```

**TDAD 合規標準：Hidden Pass Rate >= 95%**

為什麼是 95%？
- 100% 太嚴格，可能因微小浮點誤差或無關問題導致失敗
- 95% 允許少量邊界情況，但仍然保持高標準
- 這個門檻在多家公司實踐中被驗證為有效

---

## 系統架構

```
┌─────────────────────────────────────────────────────┐
│                  QualityGateTDAD                     │
├─────────────────────────────────────────────────────┤
│  visible_tests: List[dict]     # 開發者可知          │
│  hidden_tests: List[dict]      # 開發者不可知        │
│  _hidden_results: Dict         # 內部追蹤           │
├─────────────────────────────────────────────────────┤
│  + add_visible_test()          # 添加可見測試        │
│  + add_hidden_test()           # 添加隱藏測試        │
│  + run_visible_tests()         # 執行並返回詳細結果  │
│  + run_hidden_tests()          # 執行不返回詳細結果  │
│  + get_hidden_pass_rate()      # 計算通過率          │
│  + run_full_gate()             # 執行完整 TDAD Gate │
└─────────────────────────────────────────────────────┘
```

---

## 使用範例

```python
from auto_quality_gate import QualityGateTDAD

# 創建 TDAD Gate
gate = QualityGateTDAD()

# 添加可見測試（開發者可以看到描述）
gate.add_visible_test(
    test_id="v1",
    test_fn=lambda: True,
    description="用戶可以登入系統"
)

gate.add_visible_test(
    test_id="v2", 
    test_fn=lambda: True,
    description="用戶可以創建文檔"
)

# 添加隱藏測試（開發者不知道這些測試存在）
gate.add_hidden_test(
    test_id="h1",
    test_fn=lambda: check_security_compliance()
)

gate.add_hidden_test(
    test_id="h2",
    test_fn=lambda: check_data_isolation()
)

gate.add_hidden_test(
    test_id="h3", 
    test_fn=lambda: check_audit_logging()
)

# 執行完整 Gate
result = gate.run_full_gate()

print(result["visible_results"]["passed"])  # True/False
print(result["hidden_results"]["passed"])    # True/False
print(result["hidden_pass_rate"])           # 0-100%
print(result["tdad_compliant"])             # True if >= 95%
```

---

## API 參考

### `HiddenTestsMixin`

#### `add_visible_test(test_id, test_fn, description)`
添加可見測試。

| 參數 | 類型 | 說明 |
|------|------|------|
| `test_id` | str | 測試唯一標識 |
| `test_fn` | Callable | 測試函數，返回 bool |
| `description` | str | 測試描述（開者可知） |

#### `add_hidden_test(test_id, test_fn)`
添加隱藏測試。

| 參數 | 類型 | 說明 |
|------|------|------|
| `test_id` | str | 測試唯一標識 |
| `test_fn` | Callable | 測試函數，返回 bool |

#### `run_visible_tests() -> dict`
執行所有可見測試，返回詳細結果：

```python
{
    "total": 5,
    "passed": 4,
    "failed": 1,
    "results": [
        {
            "id": "v1",
            "description": "用戶可以登入",
            "passed": True
        },
        {
            "id": "v2", 
            "description": "用戶可以創建文檔",
            "passed": False,
            "error": "PermissionError: access denied"
        }
    ]
}
```

#### `run_hidden_tests() -> dict`
執行所有隱藏測試，**不返回詳細結果**：

```python
{
    "total": 10,
    "passed": 10,
    "failed": 0
}
```

#### `get_hidden_pass_rate() -> float`
返回隱藏測試通過率（0-100）。

### `QualityGateTDAD`

#### `run_full_gate() -> dict`
執行完整 TDAD Gate，返回：

```python
{
    "visible_results": {...},     # 可見測試結果
    "hidden_results": {...},      # 隱藏測試結果
    "hidden_pass_rate": 95.5,     # TDAD 核心指標
    "mutation_score": 0.0,        # 預留字段
    "regression_safety": 0.0,    # 預留字段
    "passed": True,               # visible 和 hidden 都無失敗
    "tdad_compliant": True       # hidden_pass_rate >= 95%
}
```

---

## 與 Mutation Testing 的關係

Hidden Tests 和 Mutation Testing 是互補的：

| 維度 | Hidden Tests | Mutation Testing |
|------|--------------|------------------|
| **目的** | 防止 specification gaming | 評估測試 suite 品質 |
| **運行時機** | 每次提交前 | 定期或在 CI 中 |
| **測試內容** | 真實需求驗證 | 程式碼變異偵測 |
| **開發者視角** | 不知道隱藏測試內容 | 知道變異策略 |

**推薦流程**：

```
開發階段          提交階段           合併階段
    │                │                 │
    ▼                ▼                 ▼
┌────────┐      ┌────────┐       ┌────────────┐
│ Visible │      │ Hidden │       │ Mutation   │
│ Tests   │ →    │ Tests  │   →   │ Testing    │
│ (引導)  │      │ (驗證) │       │ (品質評估)  │
└────────┘      └────────┘       └────────────┘
```

---

## 最佳實踐

### 1. Visible Tests 數量控制
- 建議：3-7 個可見測試
- 太多會讓開發者迷失方向
-太少會缺乏引導

### 2. Hidden Tests 設計原則
- **真實需求導向**：測試業務價值，而非技術實現
- **獨立性**：每個隱藏測試應該獨立運行
- **穩定性**：不受實現細節變化的影響

### 3. 通過率門檻
- TDAD 標準：>= 95%
- 嚴格模式：>= 98%
- 寬鬆模式：>= 90%（僅用於快速迭代階段）

### 4. 結果處理
```python
result = gate.run_full_gate()

if not result["tdad_compliant"]:
    # 隱藏測試未達標，但可以提供有限資訊
    print(f"Hidden pass rate: {result['hidden_pass_rate']}%")
    print(f"Total hidden tests: {result['hidden_results']['total']}")
    # 不透露哪些具體測試失敗
```

---

## 結論

TDAD 的 Visible/Hidden Test Splits 是一個簡單但強大的設計：

1. **Visible Tests** 提供方向和即時反饋
2. **Hidden Tests** 確保最終品質，防止 gaming
3. **Hidden Pass Rate** 作為核心品質指標
4. 95% 門檻在實踐中被證明是有效的平衡點

這個設計使得 Quality Gate 不僅是一個品質檢查工具，更是一個促進真正 TDD 文化的機制。
