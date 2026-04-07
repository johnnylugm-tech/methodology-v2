# Drift Monitor Cron Setup

自動監控架構 drift，每小時執行一次檢查。

## 快速開始

### 1. 手動測試腳本

```bash
cd /Users/johnny/.openclaw/workspace-musk/projects/methodology-v2
./.venv/bin/python scripts/cron_drift_monitor.py
```

### 2. 安裝 Crontab

```bash
# 查看現有 crontab
crontab -l

# 加入 drift monitor（每小時第 0 分鐘執行）
crontab -e
# 貼上以下內容：
# 0 * * * * /Users/johnny/.openclaw/workspace-musk/projects/methodology-v2/.venv/bin/python /Users/johnny/.openclaw/workspace-musk/projects/methodology-v2/scripts/cron_drift_monitor.py >> /Users/johnny/.openclaw/workspace-musk/logs/drift_monitor.log 2>&1
```

或直接使用提供的範例：

```bash
crontab /Users/johnny/.openclaw/workspace-musk/projects/methodology-v2/scripts/drift_crontab.example
```

### 3. 查看日誌

```bash
tail -f /Users/johnny/.openclaw/workspace-musk/logs/drift_monitor.log
```

## 通知設定

### 基本日誌通知（預設）

腳本預設使用 `LogChannel`，將 alerts 寫入 `logs/drift_alerts.log`。

### Email 通知

```python
from quality_gate.drift_notifier import DriftNotifier, EmailChannel

notifier = DriftNotifier(channels=[
    EmailChannel(
        smtp_host="smtp.gmail.com",
        smtp_port=587,
        from_addr="alerts@yourdomain.com",
        to_addrs=["admin@yourdomain.com"],
    ),
])

# 在 cron script 中使用
monitor = DriftMonitor(project_path=project_path, feedback_store=store, notifier=notifier)
```

### Slack 通知

```python
from quality_gate.drift_notifier import DriftNotifier, SlackChannel

notifier = DriftNotifier(channels=[
    SlackChannel(webhook_url="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"),
])
```

## 檔案結構

```
scripts/
├── cron_drift_monitor.py      # Cron 執行腳本
├── drift_crontab.example      # Crontab 範例
└── DRIFT_CRON_SETUP.md        # 本文件

quality_gate/
├── drift_monitor.py           # 已更新：支援 notifier 參數
└── drift_notifier.py          # Notification 系統（log, email, slack）
```

## 驗收標準

- [x] `cron_drift_monitor.py` 可獨立執行
- [x] `drift_crontab.example` 包含完整的 crontab 設定
- [x] `DriftNotifier` 支援多個 channel（log, email, slack）
- [x] `DriftMonitor` 可整合 `notifier`
- [x] 本 README 說明如何設定 cron
