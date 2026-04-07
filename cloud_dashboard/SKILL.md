---
name: cloud-dashboard
description: Cloud Dashboard for methodology-v2. Use when: (1) Monitoring agents in production, (2) Team collaboration and access control, (3) Real-time metrics and alerts, (4) Cost tracking. Provides SaaS-ready monitoring dashboard.
---

# Cloud Dashboard

SaaS-ready monitoring dashboard for methodology-v2.

## Quick Start

```python
from cloud_dashboard import CloudDashboard

dashboard = CloudDashboard(
    api_key="your_api_key",
    project="my_project"
)

# Get real-time metrics
metrics = dashboard.get_metrics()

# Create alert
dashboard.create_alert(
    name="High Error Rate",
    condition="error_rate > 0.1",
    channels=["slack", "email"]
)
```

## Features

### 1. Real-Time Metrics

```python
# Get current metrics
metrics = dashboard.get_metrics({
    "agents": 10,
    "tasks_completed": 1543,
    "avg_latency": 1.2,
    "error_rate": 0.02,
    "cost_today": 12.45
})

# Historical data
metrics = dashboard.get_metrics(
    start="2026-03-20",
    end="2026-03-21",
    granularity="hour"
)
```

### 2. Team Collaboration

```python
# Invite team member
dashboard.invite_member(
    email="john@example.com",
    role="developer"
)

# Set permissions
dashboard.set_permissions(
    user_id="user_123",
    permissions=["read", "write"]
)
```

### 3. Alerts & Notifications

```python
# Create alert
dashboard.create_alert(
    name="Budget Warning",
    condition="cost > 100",
    channels=["slack", "email"],
    severity="warning"
)

# Create alert
dashboard.create_alert(
    name="Agent Down",
    condition="active_agents == 0",
    channels=["slack", "sms"],
    severity="critical"
)
```

### 4. Cost Tracking

```python
# Get cost breakdown
costs = dashboard.get_cost_breakdown({
    "by_agent": {...},
    "by_model": {...},
    "by_day": {...}
})

# Set budget
dashboard.set_budget(
    monthly_limit=500,
    alert_at=0.8
)
```

## Dashboard Sections

### Overview

| Metric | Value | Change |
|--------|-------|---------|
| Active Agents | 12 | +2 |
| Tasks/min | 45 | +12% |
| Avg Latency | 1.2s | -8% |
| Error Rate | 0.5% | -2% |
| Cost Today | $12.45 | +5% |

### Agent Health

```
Agent Status
├── coder-1: ✅ healthy (98% success)
├── coder-2: ✅ healthy (95% success)
├── reviewer-1: ⚠️ degraded (85% success)
└── researcher-1: ✅ healthy (99% success)
```

### Cost Trends

```python
# Daily cost chart
dashboard.render_chart(
    type="line",
    data="cost_by_day",
    period="30d"
)
```

### Alerts

| Alert | Status | Last Triggered |
|-------|--------|----------------|
| High Error Rate | ✅ active | 2h ago |
| Budget Warning | ✅ active | - |
| Agent Down | ✅ active | - |

## Pricing (Free for Individual)

| Feature | Free | Pro ($29/mo) |
|---------|------|---------------|
| Agents | 5 | Unlimited |
| Data Retention | 7 days | 90 days |
| Team Members | 1 | 10 |
| Alerts | 3 | Unlimited |
| API Access | ❌ | ✅ |
| Custom Domain | ❌ | ✅ |

## Integration

### Webhook Notifications

```python
# Slack integration
dashboard.add_integration(
    type="slack",
    webhook_url="https://hooks.slack.com/..."
)

# Discord integration
dashboard.add_integration(
    type="discord",
    webhook_url="https://discord.com/api/..."
)
```

### API Access

```python
import requests

# Get metrics via API
response = requests.get(
    "https://api.methodology.cloud/v1/metrics",
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)
data = response.json()
```

## CLI Usage

```bash
# Login
python cloud_dashboard.py login --api-key YOUR_KEY

# View metrics
python cloud_dashboard.py metrics

# Create alert
python cloud_dashboard.py alert create --name "High Cost" --condition "cost > 50"

# Invite member
python cloud_dashboard.py team invite --email john@example.com
```

## Best Practices

1. **Set budget alerts early** - Prevent unexpected costs
2. **Monitor agent health** - Catch issues before they impact users
3. **Use retention policies** - Balance cost and historical data needs
4. **Enable notifications** - Stay informed in real-time

## See Also

- [dashboard.py](dashboard.py) - Local dashboard
- [monitoring.py](monitoring.py) - Metrics collection
- [alerts.py](alerts.py) - Alert management
