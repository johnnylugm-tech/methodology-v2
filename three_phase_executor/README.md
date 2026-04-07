# Three Phase Executor - 三階段並行執行器

將工作流程優化為「串 → 並 → 串」三階段執行，大幅提升效能。

## 效能

| 方法 | 時間 | 加速比 |
|------|------|--------|
| 純循序 | 971ms | 1.00x |
| **3-Phase** | 471ms | **2.06x** ⚡ |

## 概念

```
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Sequential (初始化)                               │
│   - 初始化系統                                             │
│   - 登入/驗證                                              │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Parallel (可擴展)                                  │
│   - 班次查詢 ✓                                             │
│   - 價格比對 ✓                                             │
│   - 庫存檢查 ✓                                             │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│ Phase 3: Sequential (確認)                                   │
│   - 訂票                                                   │
│   - 確認付款                                               │
└─────────────────────────────────────────────────────────────┘
```

## 安裝

```bash
pip install -r requirements.txt
```

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

## API

### ThreePhaseExecutor

| 方法 | 說明 |
|------|------|
| `execute(tasks)` | 執行所有任務 |
| `get_report()` | 取得執行報告 |

### Task

| 欄位 | 說明 |
|------|------|
| `id` | 任務 ID |
| `name` | 任務名稱 |
| `func` | 執行的函數 |
| `phase` | 所屬階段 |
| `max_retries` | 最大重試次數 |

### Phase

| 階段 | 類型 | 說明 |
|------|------|------|
| `INIT` | Sequential | 初始化 |
| `PREPARE` | Sequential | 準備（登入、驗證） |
| `QUERY` | Parallel | 查詢（可並行） |
| `BOOK` | Sequential | 訂票 |
| `CONFIRM` | Sequential | 確認 |

## 特性

- **智慧分流**: 將可並行的任務自動分配到 Phase 2
- **並發控制**: 透過 Semaphore 控制最大並發數
- **重試機制**: 支援指數退避重試
- **錯誤處理**: 個別任務失敗不影響整體流程

## 整合

可與 `parallel_executor.py` 整合使用：

```python
from parallel_executor import ParallelExecutor
from three_phase_executor import ThreePhaseExecutor

# 使用 ThreePhase 決定執行策略
# 使用 ParallelExecutor 實際執行
```
