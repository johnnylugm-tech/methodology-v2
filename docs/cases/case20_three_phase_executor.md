# 案例 20：Three-Phase Executor

## 概述

三階段並行執行器將工作流程優化為「串 → 並 → 串」模式，大幅提升效能。

## 核心概念

```
Phase 1: Sequential (初始化)
  - 初始化系統
  - 登入/驗證
              ↓
Phase 2: Parallel (可擴展)
  - 班次查詢 ✓
  - 價格比對 ✓
  - 庫存檢查 ✓
              ↓
Phase 3: Sequential (確認)
  - 訂票
  - 確認付款
```

## 效能提升

| 方法 | 時間 | 加速比 |
|------|------|--------|
| 純循序 | 971ms | 1.00x |
| **3-Phase** | 471ms | **2.06x** ⚡ |

## 使用方式

```python
from three_phase_executor import ThreePhaseExecutor, Task, Phase

# 定義任務
tasks = [
    Task("init", "初始化", init_func, Phase.INIT),
    Task("login", "登入", login_func, Phase.PREPARE),
    Task("query_1", "查詢班次1", query_func1, Phase.QUERY),
    Task("query_2", "查詢班次2", query_func2, Phase.QUERY),
    Task("book", "訂票", book_func, Phase.BOOK),
    Task("confirm", "確認", confirm_func, Phase.CONFIRM),
]

# 執行
executor = ThreePhaseExecutor()
result = await executor.execute(tasks)

print(f"總時間: {result.total_time_ms}ms")
print(f"加速比: {result.speedup_ratio:.2f}x")
```

## 與 ParallelExecutor 比較

| 功能 | ParallelExecutor | ThreePhaseExecutor |
|------|-----------------|-------------------|
| 依賴驅動 | ✅ | ✅ |
| Phase 分組 | ❌ | ✅ |
| 自動並行識別 | ❌ | ✅ |
| 效能分析 | ❌ | ✅ |

## 相關模組

- parallel_executor.py
- fault_tolerant.py (整合錯誤處理)
