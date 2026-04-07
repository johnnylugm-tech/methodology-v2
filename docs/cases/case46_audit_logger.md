# Case 46: AI Agent Audit Logger - AI 操作審計日誌

## 問題背景

AI Agent 在執行任務時，會進行各種操作：
- 執行 CLI 命令
- 修改/創建/刪除檔案
- 調用 API
- 請求審批

沒有統一的審計機制時：
- 無法追蹤 AI 的完整操作歷史
- 異常行為（如快速連續操作、嘗試繞過安全檢查）無法被偵測
- 安全審計和合規報告無法生成
- 問題發生時難以回溯根本原因

## 傳統方案

```python
# 傳統方式：簡單的日誌記錄
import logging

logger = logging.getLogger("ai_agent")

def execute_command(cmd):
    logger.info(f"Executing: {cmd}")
    # ... execute
    logger.info(f"Result: {result}")
```

**痛點：**
- 沒有結構化的審計條目
- 沒有異常行為偵測
- 沒有統一的查詢介面
- 沒有報告生成功能
- 難以滿足合規要求

## AI-Native 方案

```python
from anti_shortcut.audit_logger import AIAuditLogger, ActionType

# 初始化審計日誌
audit = AIAuditLogger(storage_path="./data/audit")

# 記錄各種操作
audit.log_cli("agent_001", "rm -rf /dangerous")
audit.log_file_change("agent_001", ActionType.FILE_DELETE, "/workspace/old_file.txt")
audit.log_approval("agent_001", "admin", "deploy_production", "approved")

# 查詢審計報告
report = audit.get_audit_report(agent_id="agent_001")
print(report)

# 導出報告
json_report = audit.export_report(format="json")
```

---

## 案例 46.1：基本審計記錄

### 背景
記錄 AI Agent 的所有關鍵操作，建立完整的操作軌跡。

### 使用方式

```python
from anti_shortcut.audit_logger import AIAuditLogger, ActionType

# 初始化審計日誌
audit = AIAuditLogger(storage_path="./data/audit")

# 記錄 CLI 命令
audit.log_cli(
    agent_id="dev_agent_001",
    command="git push origin main",
    result="success"
)

# 記錄檔案創建
audit.log_file_change(
    agent_id="dev_agent_001",
    action=ActionType.FILE_CREATE,
    file_path="/workspace/project/new_module.py"
)

# 記錄檔案修改
audit.log_file_change(
    agent_id="dev_agent_001",
    action=ActionType.FILE_MODIFY,
    file_path="/workspace/project/config.yaml"
)

# 記錄檔案刪除
audit.log_file_change(
    agent_id="dev_agent_001",
    action=ActionType.FILE_DELETE,
    file_path="/workspace/project/temp.txt"
)
```

### 輸出
```
# 查看審計狀態
audit status

# 輸出：
{
  "total_operations": 4,
  "by_type": {
    "cli_command": 1,
    "file_create": 1,
    "file_modify": 1,
    "file_delete": 1
  }
}
```

---

## 案例 46.2：異常行為偵測

### 背景
自動偵測異常的 AI 行為，如快速連續操作或嘗試繞過安全檢查。

### 使用方式

```python
from anti_shortcut.audit_logger import AIAuditLogger, ActionType

audit = AIAuditLogger(storage_path="./data/audit")

# 模擬快速連續操作（異常行為）
for i in range(15):
    audit.log_cli(
        agent_id="suspicious_agent",
        command=f"curl http://internal-api/{i}",
        result="success"
    )

# 嘗試繞過安全檢查（嚴重異常）
audit.log_cli(
    agent_id="suspicious_agent",
    command="guardrails --bypass --force",
    result="blocked"
)
```

### 輸出
```
# 查看異常
audit anomalies

# 輸出：
Anomalies Detected:
1. [HIGH] rapid_sequence: 15 operations in 60s by suspicious_agent
2. [CRITICAL] bypass_attempt: Bypass attempt detected: CLI: guardrails --bypass --force

Total: 2 anomalies (1 critical, 1 high)
```

### 偵測規則

| 異常類型 | 條件 | 嚴重程度 |
|---------|------|---------|
| `rapid_sequence` | 60秒內執行10+操作 | high |
| `bypass_attempt` | 描述中包含 "bypass" 或 "skip" | critical |
| `large_delete` | 大量刪除檔案 | high |
| `unauthorized_access` | 未授權訪問資源 | critical |
| `self_approval` | 自己批准自己的操作 | high |

---

## 案例 46.3：審計報告生成

### 背景
生成符合合規要求的審計報告。

### 使用方式

```python
from anti_shortcut.audit_logger import AIAuditLogger

audit = AIAuditLogger(storage_path="./data/audit")

# 生成完整報告
report = audit.get_audit_report()
print(audit.export_report(format="json"))

# 按 Agent 篩選
agent_report = audit.get_audit_report(agent_id="dev_agent_001")
print(json.dumps(agent_report, indent=2))

# 只看關鍵異常
critical_anomalies = audit.get_anomalies(severity="critical")
```

### 報告格式

```json
{
  "agent_id": "all",
  "period": {
    "start": "2024-01-15T10:00:00",
    "end": "2024-01-15T18:00:00"
  },
  "total_operations": 127,
  "by_type": {
    "cli_command": 45,
    "file_create": 23,
    "file_modify": 38,
    "file_delete": 8,
    "approval": 13
  },
  "anomalies": {
    "total": 3,
    "critical": 1,
    "high": 2
  }
}
```

---

## 案例 46.4：CLI 命令整合

### 背景
透過 CLI 命令快速查詢審計狀態。

### CLI 命令

```bash
# 查看審計狀態
methodology-v2 audit status

# 查看異常列表
methodology-v2 audit anomalies

# 查看特定 Agent 的異常
methodology-v2 audit anomalies --agent suspicious_agent

# 生成完整報告
methodology-v2 audit report

# 按 Agent 生成報告
methodology-v2 audit report --agent dev_agent_001
```

### 輸出範例

```
$ methodology-v2 audit status

AI Audit Status
================
Total Operations: 127
Agents Active: 3

By Type:
  - CLI Commands: 45
  - File Create: 23
  - File Modify: 38
  - File Delete: 8
  - Approvals: 13

Anomalies: 3 (1 critical, 2 high)
```

---

## 整合架構

```
┌─────────────────────────────────────────────────────┐
│                   AI Agent                          │
├─────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐ │
│  │ CLI Executor│  │File Manager │  │API Caller   │ │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘ │
│         │                │                │         │
│         └────────────────┼────────────────┘         │
│                          ▼                          │
│              ┌─────────────────────┐                 │
│              │  AIAuditLogger      │                 │
│              │  - log_cli()        │                 │
│              │  - log_file_change()│                 │
│              │  - log_approval()   │                 │
│              └──────────┬──────────┘                 │
│                         │                            │
│         ┌───────────────┼───────────────┐           │
│         ▼               ▼               ▼           │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐    │
│  │ Audit JSONL │ │ Anomalies   │ │  Report     │    │
│  │   Storage   │ │  Detector   │ │  Generator  │    │
│  └─────────────┘ └─────────────┘ └─────────────┘    │
└─────────────────────────────────────────────────────┘
```

---

## 與其他模組的整合

### 與 Gatekeeper 整合

```python
from anti_shortcut.gatekeeper import Gatekeeper
from anti_shortcut.audit_logger import AIAuditLogger

gatekeeper = Gatekeeper()
audit = AIAuditLogger()

# 請求審批時記錄
request = gatekeeper.request_approval(
    agent_id="agent_001",
    action="deploy",
    target="production"
)

audit.log_approval(
    agent_id="agent_001",
    approver="admin",
    target="production",
    status="pending" if request else "auto_denied"
)
```

### 與 Blacklist 整合

```python
from anti_shortcut.blacklist import CommandBlacklist
from anti_shortcut.audit_logger import AIAuditLogger

blacklist = CommandBlacklist()
audit = AIAuditLogger()

# 檢查並記錄
result = blacklist.check("rm -rf /")
if result:
    audit.log_cli("agent_001", "rm -rf /", "blocked")
    audit._check_anomaly(...)  # 手動觸發異常偵測
```

---

## 最佳實踐

1. **所有 AI 操作都應該被記錄** - 不要只記錄"重要"操作，異常行為往往來自看似平常的操作
2. **設置合理的異常閾值** - 60秒內10次操作是預設值，可根據實際情況調整
3. **及時審查 Critical 異常** - 這表示有嘗試繞過安全機制的行為
4. **定期生成報告** - 建議每日生成一次審計報告用於合規保存
5. **日誌保留策略** - 建議至少保留 90 天的審計日誌

---

## 總結

AI Agent Audit Logger 提供了：

| 功能 | 說明 |
|------|------|
| 操作記錄 | 記錄所有 CLI、檔案、API、審批操作 |
| 異常偵測 | 自動偵測快速操作、繞過嘗試等異常 |
| 報告生成 | 生成符合合規要求的審計報告 |
| CLI 工具 | 快速查詢狀態、異常、報告 |
| 存儲格式 | JSONL 格式，方便長期保存和分析 |