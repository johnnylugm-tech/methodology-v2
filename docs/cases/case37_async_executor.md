# Case 37: Async Executor - 非同步執行器

## 概述

`AsyncExecutor` 對標 AutoGen 的 async/await 支援，提供 asyncio 原生的並發任務執行能力。

## 核心功能

| 功能 | 說明 |
|------|------|
| 並發執行 | 控制最大並發數，避免資源耗盡 |
| 超時控制 | 支援任務級別的超時設定 |
| 錯誤處理 | 單一任務失敗不影響其他任務 |
| 結果收集 | 統一收集所有任務結果 |

## 使用範例

### 基本用法

```python
import asyncio
from async_executor import AsyncExecutor, run_async, run_parallel

# 使用 executor
executor = AsyncExecutor(max_concurrency=5)

async def my_task(name):
    await asyncio.sleep(1)
    return f"{name} done"

# 創建任務
executor.create_task("task1", my_task("A"))
executor.create_task("task2", my_task("B"))

# 執行並取得結果
results = await executor.execute_all()
print(results)
```

### 便捷函數

```python
# 單任務執行（帶超時）
result = await run_async(agent.execute("task"), timeout=30.0)

# 並行執行多個任務
results = await run_parallel(task1(), task2(), task3(), max_concurrency=10)
```

## 任務狀態

```
PENDING → RUNNING → COMPLETED
                    ↓
                FAILED / TIMEOUT / CANCELLED
```

## 與 AutoGen 的對標

| AutoGen | 本實作 |
|---------|--------|
| `async_agent` | `AsyncExecutor` |
| `await agent.run()` | `execute_all()` |
| `asyncio.gather` | 內建併發控制 |

## 適用場景

- 多 Agent 並發協作
- 批量任務處理
- 需要超時控制的長任務
- 資源受限的並發場景
