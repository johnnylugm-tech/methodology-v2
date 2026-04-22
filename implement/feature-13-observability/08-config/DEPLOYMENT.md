# Feature #13 — Deployment Configuration

## 環境需求

- Python 3.10+
- PyYAML（決策日誌 YAML 序列化）
- opentelemetry-api + opentelemetry-sdk（如使用真實 OTel tracer）

## 依賴套件

```bash
pip install pyyaml opentelemetry-api opentelemetry-sdk
```

## 環境變數

| 變數 | 預設值 | 說明 |
|------|--------|------|
| `DATA_DIR` | `workspace-root/data/` | decision_logs 和 effort_metrics.db 的父目錄 |
| `DECISION_LOG_DIR` | `DATA_DIR/decision_logs/` | 決策日誌根目錄 |
| `EFFORT_METRICS_DB` | `DATA_DIR/effort_metrics.db` | SQLite 資料庫路徑 |

## 目錄結構

```
data/
└── decision_logs/
    ├── context_001.jsonl   # decision logs
    ├── context_002.jsonl
    └── ...
effort_metrics.db           # SQLite DB
```

## 初始化

```python
from observability import setup_observability

# 若使用真實 OpenTelemetry tracer
from opentelemetry import trace

tracer = trace.get_tracer(__name__)
uqlm, decision_log, effort = setup_observability(tracer)

# 若不需要 OTel（使用無-op 無op mock span）
uqlm, decision_log, effort = setup_observability(None)
```

## 使用範例

```python
from observability import UqlmMetricsSpan, DecisionLogWriter, EffortTracker

# UQLM metrics span
with UqlmMetricsSpan("my_operation", uqlm) as span:
    span.set_success()
    # ... do work

# Decision log
writer = DecisionLogWriter(base_dir="data/decision_logs")
writer.write(
    context="user_123",
    decision="allocate_budget",
    goal_snapshot={"target": 1000, "constraint": "max_10pct"},
    reasoning="due to Q4 target alignment",
    selected_action={"action": "scale", "params": {"factor": 1.1}},
    feedback={"outcome": "success"},
)

# Effort tracker
tracker = EffortTracker(db_path="data/effort_metrics.db")
tracker.record("planner", "planning", start, end, success=True, tokens_used=1500)
tracker.flush()  # 定期 flush 或 shutdown 時呼叫
```

## Graceful Shutdown

```python
import atexit

tracker = EffortTracker(db_path="data/effort_metrics.db")
atexit.register(lambda: (tracker.flush(), tracker._timer.cancel()))
```

## 驗證安裝

```bash
python3 -c "from observability import setup_observability; print('✅ OK')"
```

## 健康檢查

```bash
# 確認 decision_logs 目錄存在
ls -la data/decision_logs/

# 確認 effort_metrics.db 可讀
sqlite3 data/effort_metrics.db "SELECT name FROM sqlite_master WHERE type='table';"

# 驗證模組 import
python3 -c "
from observability import (
    UqlmMetricsSpan,
    DecisionLogWriter, DecisionLogReader,
    EffortTracker,
    setup_observability,
)
print('All components imported successfully')
"
```

## 限制

- **單一 process SQLite**：不支援跨程序共享同一個 `effort_metrics.db`
  - 多 process 場景需自行實現鎖或使用獨立的 DB 檔案
- **不負責 Langfuse server 安裝**：Feature #11 的職責
- **決策日誌非 async I/O**：寫入為 fire-and-forget，不保證 fsync

## 更新日誌

| 日期 | 版本 | 變更 |
|------|------|------|
| 2026-04-22 | 1.0 | 初始版本 |