# 新團隊三步驟上手：Multi-Agent 協同

## 概述

本指南幫助新團隊理解並實作 Multi-Agent 協同作業，核心特點：

> **自動化並行** — 能並行的儘量並行，需要順序時自動切換，錯誤時自動處理

---

## 核心概念：智慧路由

```
┌─────────────────────────────────────────────────────┐
│                  任務輸入                              │
└──────────────────────┬──────────────────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  智慧路由器     │ ← 自動判斷
              │  TaskRouter   │
              └────────┬───────┘
                       │
         ┌─────────────┴─────────────┐
         │                           │
         ▼                           ▼
   ┌───────────┐             ┌───────────┐
   │  可並行？  │             │ 需順序？   │
   │   YES     │             │   YES     │
   └─────┬─────┘             └─────┬─────┘
         │                           │
         ▼                           ▼
   ┌───────────┐             ┌───────────┐
   │ Parallel  │             │ Sequential│
   │ Executor  │             │  Executor │
   └─────┬─────┘             └─────┬─────┘
         │                           │
         └─────────────┬─────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  錯誤處理器     │
              │ ErrorHandler   │
              └────────────────┘
```

---

## Step 1：理解三種協同模式

### 模式 A：完全並行（Parallel）

**情境**：多個獨立的任務，同時執行

```python
from parallel_executor import ParallelExecutor

executor = ParallelExecutor(max_workers=4)

# 這些任務沒有依賴關係，可以同時執行
tasks = [
    "任務A：分析數據",
    "任務B：寫報告",
    "任務C：翻譯文檔",
    "任務D：整理資料"
]

results = executor.run_all(tasks)
# 輸出：4 個任務同時完成，節省 75% 時間
```

**何時使用**：
- 任務之間沒有依賴
- 結果不會互相影響
- 可以同時執行

---

### 模式 B：完全順序（Sequential）

**情境**：任務有依賴關係，必須等上一個完成

```python
from sequential_executor import SequentialExecutor

executor = SequentialExecutor()

# 這些任務有順序依賴
tasks = [
    ("任務A", "分析需求"),
    ("任務B", "根據需求設計架構"),  # 依賴 A
    ("任務C", "根據架構寫代碼"),     # 依賴 B
    ("任務D", "測試代碼")            # 依賴 C
]

results = executor.run_all(tasks)
# 輸出：按順序一個個完成
```

**何時使用**：
- 任務有前後依賴
- 結果是下一個任務的輸入
- 需要確保資料一致性

---

### 模式 C：智慧混合（Smart Hybrid）⭐

**情境**：自動判斷每個任務該並行還是順序執行

```python
from smart_workflow_executor import SmartWorkflowExecutor

executor = SmartWorkflowExecutor()

# 定義任務，依賴關係用 graph 表示
workflow = {
    "tasks": [
        {"id": "A", "name": "資料收集", "deps": []},
        {"id": "B", "name": "數據分析", "deps": ["A"]},
        {"id": "C", "name": "寫報告", "deps": ["A"]},
        {"id": "D", "name": "翻譯報告", "deps": ["C"]},
        {"id": "E", "name": "最終審查", "deps": ["B", "D"]},
    ]
}

# 自動分析並行可能性
results = executor.execute(workflow)

# 執行計劃：
# Phase 1: A (順序)
# Phase 2: B, C (並行)
# Phase 3: D (順序, 因為依賴 C)
# Phase 4: E (順序, 因為依賴 B,D)
```

**輸出範例**：
```
Phase 1: A [資料收集]     ████████████ 100%
Phase 2: B [分析] ████████  │  C [報告] ████████
         └──────────────────────┘
Phase 3: D [翻譯]         ████████████
Phase 4: E [審查]         ████████████
總時間: 4 phases (原本需 7 phases 如果完全順序)
```

---

## Step 2：設定與配置

### 基础配置

```yaml
# config.yaml
multi_agent:
  # 最大並行數
  max_parallel: 4
  
  # 並行策略
  parallel_strategy: "auto"  # auto | force_parallel | force_sequential
  
  # 錯誤處理
  error_handling:
    retry_count: 3
    retry_delay: 1.0  # 秒
    fallback_mode: "sequential"  # 出錯時自動降級
```

### 錯誤處理配置

```yaml
error_handling:
  # L1: 輸入錯誤 → 立即失敗
  L1:
    action: "fail_fast"
    
  # L2: 工具錯誤 → 重試
  L2:
    action: "retry"
    max_attempts: 3
    backoff: "exponential"
    
  # L3: 執行錯誤 → 降級
  L3:
    action: "degrade"
    degrade_to: "sequential"
    
  # L4: 系統錯誤 → 熔斷
  L4:
    action: "circuit_break"
    alert: true
```

---

## Step 3：實作與監控

### 實作範例

```python
from smart_workflow_executor import SmartWorkflowExecutor
from error_handler import ErrorHandler

# 1. 初始化
executor = SmartWorkflowExecutor()
handler = ErrorHandler()

# 2. 定義任務
workflow = {
    "tasks": [
        {"id": "research", "name": "研究", "deps": []},
        {"id": "code", "name": "開發", "deps": ["research"]},
        {"id": "test", "name": "測試", "deps": ["code"]},
        {"id": "review", "name": "審查", "deps": ["test"]},
    ]
}

# 3. 執行（帶錯誤處理）
try:
    results = executor.execute(workflow)
    
except Exception as e:
    error_level = handler.classify(e)
    
    if error_level == "L2":
        # 重試
        results = executor.retry(workflow, max_attempts=3)
        
    elif error_level == "L3":
        # 降級到順序執行
        executor.set_mode("sequential")
        results = executor.execute(workflow)
        
    elif error_level == "L4":
        # 熔斷
        executor.circuit_break()
        handler.alert("critical_error", str(e))
```

### 監控儀表板

```bash
# 查看執行狀態
python cli.py workflow status

# 查看並行分析
python cli.py workflow analyze --task research

# 查看錯誤日誌
python cli.py workflow errors --last 10
```

**輸出範例**：
```
┌────────────────────────────────────────────┐
│ Workflow Status                             │
├────────────────────────────────────────────┤
│ Status: ● Running                          │
│ Mode: Smart Hybrid                         │
│ Parallel Tasks: 3 / 4                      │
├────────────────────────────────────────────┤
│ Task      │ Status   │ Mode      │ Time   │
│ research  │ ● Done   │ sequential │ 2.1s  │
│ code      │ ● Done   │ parallel  │ 5.3s  │
│ test      │ ● Running│ parallel  │ 1.2s  │
│ review    │ ○ Pending│ sequential │ -      │
└────────────────────────────────────────────┘
```

---

## 常見問題

### Q1: 如何判斷任務是否可以並行？

```python
# 自動分析
can_parallel = TaskAnalyzer.analyze_dependencies(tasks)

# 規則：
# 1. 沒有共同依賴 → 可以並行
# 2. 寫入相同資源 → 不能並行
# 3. 有順序標記 → 不能並行
```

### Q2: 錯誤發生時會怎樣？

```python
# 預設行為：
# L1: 立即失敗，快速返回
# L2: 重試 3 次，指數退避
# L3: 自動降級到順序執行
# L4: 熔斷，發送警報
```

### Q3: 如何恢復執行？

```bash
# 從上次失敗處恢復
python cli.py workflow resume --workflow-id abc123

# 跳過失敗的任務繼續
python cli.py workflow skip --task-id task-456
```

---

## 快速參考卡

```
┌─────────────────────────────────────────────────┐
│ Multi-Agent 協同決策樹                            │
├─────────────────────────────────────────────────┤
│                                                 │
│  任務沒有依賴？                                  │
│      │                                          │
│   YES ├→ Parallel Executor → 完成              │
│      │                                          │
│   NO  │                                          │
│      ▼                                          │
│  智慧分析依賴圖                                  │
│      │                                          │
│   可拆解？                                       │
│      │                                          │
│   YES ├→ Smart Hybrid → Phase 1 並行           │
│      │              → Phase 2 順序             │
│      │                                          │
│   NO  │                                          │
│      ▼                                          │
│  Sequential Executor → 順序執行                  │
│                                                 │
└─────────────────────────────────────────────────┘
```

---

## 下一步

1. 閱讀 `case03_multi_agent.md` 深入範例
2. 嘗試 `python cli.py workflow demo`
3. 設定團隊的第一個 Multi-Agent 工作流
