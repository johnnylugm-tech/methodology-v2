# SKILL.md - Three-Phase Executor

## Metadata

```yaml
name: three-phase-executor
description: 三階段並行執行器。當需要優化工作流程效能時使用，特別是「能並行的任務儘量並行，不能並行的回到順序」。
```

## When to Use

- 多個獨立任務需要同時執行
- 工作流程有明顯的「準備→執行→確認」階段
- 效能優化需求
- 高併發場景

## Quick Start

```python
from three_phase_executor import ThreePhaseExecutor, Task, Phase

executor = ThreePhaseExecutor()
tasks = [
    Task("init", "初始化", init_func, Phase.PREPARE),
    Task("query_1", "查詢1", query_func1, Phase.QUERY),
    Task("query_2", "查詢2", query_func2, Phase.QUERY),
    Task("book", "訂票", book_func, Phase.BOOK),
]

result = await executor.execute(tasks)
print(f"加速比: {result.speedup_ratio:.2f}x")
```

## Key Concepts

| Phase | Type | Description |
|-------|------|-------------|
| INIT/PREPARE | Sequential | 初始化、登入 |
| QUERY | **Parallel** | 查詢（可並行）|
| BOOK/CONFIRM | Sequential | 訂票、確認 |

## CLI

```bash
# 查看幫助
python three_phase_executor/three_phase_executor.py --help
```

## Integration

```python
# 與 fault_tolerant 整合
from fault_tolerant import FaultTolerantExecutor

executor = FaultTolerantExecutor()
# 包裝三階段執行
```

## Related

- parallel_executor.py
- fault_tolerant.py
- smart_orchestrator.py
