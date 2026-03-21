# Case 23: Approval UI - 人類審批 UI

## 情境

PM 需要在 AI Agent 執行關鍵任務前進行審批，確保人類監控到位。

## 解決方案

### 核心功能

| 功能 | 說明 |
|------|------|
| CLI 審批 | `approve <task_id>` / `reject <task_id> <reason>` |
| Streamlit UI | 視覺化審批介面 |
| 審批歷史 | 記錄所有審批操作 |

### 使用方式

```bash
# CLI 審批
python cli.py approve task-123
python cli.py reject task-123 "風險太高"

# Streamlit UI
streamlit run approval_ui.py
```

### 程式碼

```python
from approval_ui import ApprovalUI

ui = ApprovalUI()
ui.run()  # 啟動 Streamlit UI
```

## 整合

- 與 `approval_flow.py` 整合
- 支援 Webhook 通知
- 審批後自動執行後續流程

## Related

- approval_flow.py
- fault_tolerant.py
