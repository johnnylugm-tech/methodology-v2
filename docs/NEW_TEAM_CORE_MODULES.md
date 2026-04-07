# 新團隊上手指南：核心模組篇

## 目標

幫助新團隊在 3 天內掌握 methodology-v2 的核心模組。

---

## 第 1 天：理解三大核心模組

### 上午：Three-Phase Executor（並行執行）

**為什麼要懂這個？**

```
傳統方式：所有任務串行執行
三階段：能並行的並行，不能並行的串行

結果：效能提升 2x+
```

**核心概念**：

```
Phase 1 (串): 初始化、登入
Phase 2 (並): 查詢、搜尋 ← 最大效能提升點
Phase 3 (串): 訂票、確認
```

**使用時機**：
- 多個獨立任務同時執行
- 效能優化
- 高鐵訂票、機票比價等場景

---

### 下午：Fault Tolerant（容錯處理）

**為什麼要懂這個？**

```
AI Agent 不穩定 → 需要錯誤處理
LLM 會 hallucinate → 需要輸出驗證

結果：系統可靠性大幅提升
```

**核心概念**：

| 機制 | 說明 |
|------|------|
| **Retry** | 失敗重試（指數退避） |
| **Circuit Breaker** | 連續失敗 → 熔斷 → 恢復 |
| **Fallback** | 主方案失敗 → 備援方案 |
| **Output Validator** | 檢測 LLM hallucination |

**使用時機**：
- API 呼叫可能失敗
- LLM 輸出需要驗證
- 需要備援機制

---

### 晚上：Smart Orchestrator（任務協調）

**為什麼要懂這個？**

```
多個 Agent 協作 → 需要協調
避免某個 Agent 過載 → 需要負載均衡

結果：多 Agent 系統穩定運行
```

**核心概念**：

```
任務 → 協調器 → 選擇最低負載的 Agent → 執行
              ↑
         自動負載追蹤
```

**使用時機**：
- 多個 Agent 協作
- 需要任務分配
- 避免 Agent 過載

---

## 第 2 天：實作演練

### 演練 1：三階段執行

```python
from three_phase_executor import ThreePhaseExecutor, Task, Phase

tasks = [
    Task("login", "登入系統", login_func, Phase.PREPARE),
    Task("query_1", "查詢班次1", query_func1, Phase.QUERY),
    Task("query_2", "查詢班次2", query_func2, Phase.QUERY),
    Task("book", "訂票", book_func, Phase.BOOK),
]

executor = ThreePhaseExecutor()
result = await executor.execute(tasks)

print(f"加速比: {result.speedup_ratio:.2f}x")
```

### 演練 2：容錯處理

```python
from fault_tolerant import FaultTolerantExecutor, RetryConfig

executor = FaultTolerantExecutor(
    name="api_call",
    retry_config=RetryConfig(max_attempts=3),
    fallback=lambda: "backup_result"
)

result = await executor.execute(risky_api_call)
```

### 演練 3：智能協調

```python
from smart_orchestrator import SmartOrchestrator

orchestrator = SmartOrchestrator(max_concurrent=3)

orchestrator.register_agent("dev", "開發 Agent", "coding")
orchestrator.register_agent("qa", "測試 Agent", "testing")

task1 = orchestrator.create_task("開發", "寫代碼", "coding")
task2 = orchestrator.create_task("測試", "測試代碼", "testing", dependencies=[task1])

result = await orchestrator.execute()
```

---

## 第 3 天：整合應用

### 三者整合範例

```python
from smart_orchestrator import SmartOrchestrator
from three_phase_executor import ThreePhaseExecutor, Phase
from fault_tolerant import FaultTolerantExecutor

# 1. 協調器管理多個 Agent
orchestrator = SmartOrchestrator()

# 2. 每個任務用三階段執行
# 3. 失敗時用容錯處理

async def execute_task_chain():
    # Phase 1: 準備
    await init_system()
    
    # Phase 2: 並行查詢（協調器分配）
    results = await parallel_query()
    
    # Phase 3: 確認（容錯處理）
    for result in results:
        executor = FaultTolerantExecutor(fallback=lambda: None)
        await executor.execute(process_result)
```

---

## 快速參考卡

```
┌─────────────────────────────────────────────────────┐
│           新團隊必懂三大模組                           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Three-Phase Executor                               │
│  → 效能提升 2x+                                    │
│  → 串 → 並 → 串                                    │
│                                                     │
│  Fault Tolerant                                     │
│  → 錯誤處理（重試、熔斷）                            │
│  → LLM hallucination 檢測                          │
│                                                     │
│  Smart Orchestrator                                 │
│  → 多 Agent 協調                                   │
│  → 負載均衡                                        │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 常見問題

### Q1：三階段和普通並行有什麼不同？

```
普通並行：所有任務無腦並行
三階段：根據任務類型自動選擇串/並
```

### Q2：什麼時候需要容錯？

```
以下情況需要：
- API 可能超時
- LLM 輸出不穩定
- 需要備援方案
```

### Q3：三個模組都要用嗎？

```
不一定，根據需求：
- 效能優化 → Three-Phase
- 穩定性需求 → Fault Tolerant
- 多 Agent 系統 → Smart Orchestrator
- 全部都要 → 三者整合
```

---

## 下一步

1. 閱讀案例 20-22 深入了解
2. 嘗試 `python cli.py` 查看 CLI 命令
3. 根據團隊需求選擇性使用
