# Case 24: Risk Registry - 風險登記表

## 情境

專案需要系統化管理風險，不能只靠 mental notes。

## 解決方案

```python
from risk_registry import RiskRegistry, RiskLevel, RiskStatus

registry = RiskRegistry()

# 新增風險
risk = registry.add_risk(
    title="API 依賴失效",
    description="第三方 API 可能中斷",
    level=RiskLevel.HIGH,
    owner="backend-team"
)

# 查詢風險
high_risks = registry.get_risks_by_level(RiskLevel.HIGH)

# 生成報告
report = registry.generate_report()
```

## 功能

| 功能 | 說明 |
|------|------|
| 風險新增 | 等級 (LOW/MEDIUM/HIGH/CRITICAL) |
| 風險查詢 | 按等級、狀態篩選 |
| 風險報告 | 自動生成風險摘要 |
| 追蹤管理 | mitigation plan 追蹤 |

## CLI

```bash
python cli.py risk add "API 失效" --level high --owner backend
python cli.py risk list --level high
```

## Related

- risk_registry.py
- PM_HANDBOOK.md
