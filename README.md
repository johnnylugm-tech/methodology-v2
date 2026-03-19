# 🎯 AI Agent 開發工具箱 - methodology-v2

> 統一的方法論 + 工具集 + 框架整合

---

## 安裝

```bash
pip install methodology-v2
```

或開發模式：

```bash
git clone https://github.com/johnnylugm-tech/methodology-v2
cd methodology-v2
pip install -e .
```

---

## 快速開始

### 1. Dashboard

```python
from methodology import Dashboard

# 完整版 (v3)
dashboard = Dashboard()

# 輕量版 (v2)
dashboard = Dashboard(mode="light")

dashboard.run()
```

### 2. Smart Router

```python
from methodology import SmartRouter

router = SmartRouter(budget="medium")
result = router.route("幫我寫一個 Python 函數")
print(f"Model: {result.model}")
```

### 3. Auto Quality Gate

```python
from methodology import AutoQualityGate

gate = AutoQualityGate(auto_fix=True)
report = gate.scan("your_code.py")
```

### 4. Storage

```python
from methodology import Storage

storage = Storage()
conv_id = storage.create_conversation("我的對話")
storage.add_message(conv_id, "user", "你好")
```

### 5. OpenClaw Adapter

```python
from methodology import create_musk_agent

agent = create_musk_agent()
result = agent.execute("幫我完成這個任務")
```

### 6. Task Splitter

```python
from methodology import TaskSplitter

splitter = TaskSplitter()
tasks = splitter.split_from_goal("開發一個 AI 系統")
for task in splitter.get_execution_order():
    print(f"{task.id}: {task.name}")
```

### 7. Doc Generator

```python
from methodology import DocGenerator

generator = DocGenerator()
items = generator.parse_file("module.py")
print(generator.generate_markdown(items))
```

### 8. Test Generator

```python
from methodology import TestGenerator

generator = TestGenerator()
test_code = generator.generate_from_file("module.py")
```

### 9. Predictive Monitor

```python
from methodology import PredictiveMonitor

monitor = PredictiveMonitor()
monitor.record("latency", 1.5)
monitor.set_threshold("latency", warning=2, critical=5)

prediction = monitor.predict("latency")
print(f"Predicted: {prediction.predicted_value}")
```

---

## 核心模組

| 模組 | 功能 |
|------|------|
| `methodology` | 錯誤分類 (L1-L4)、生命週期、Agent 協作 |
| `dashboard` | Dashboard (v2/v3) |
| `smart_router` | 智慧模型路由 |
| `auto_quality_gate` | 自動品質把關 |
| `storage` | SQLite 對話存儲 |
| `openclaw_adapter` | OpenClaw 整合 |
| `task_splitter` | 任務自動分解 |
| `doc_generator` | 文檔自動生成 |
| `test_generator` | 測試自動生成 |
| `predictive_monitor` | 預測性監控 |

---

## Docker 一鍵部署

```bash
# 啟動所有服務
docker-compose up -d

# 訪問
# - Model Router: http://localhost:8080
# - Agent Monitor: http://localhost:3000
# - Unified Dashboard: http://localhost:8081
```

---

## 配置開關

| 功能 | 預設 | 關閉 |
|------|------|------|
| Auto Quality Gate | `auto_fix=True` | `auto_fix=False` |
| Smart Router | `auto_route=True` | `auto_route=False` |
| Dashboard | `version="full"` (v3) | `version="light"` (v2) |

---

## 版本

v2.6.0

---

## GitHub

https://github.com/johnnylugm-tech/methodology-v2
