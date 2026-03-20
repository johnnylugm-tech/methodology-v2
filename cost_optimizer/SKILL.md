---
name: cost-optimizer
description: Cost Optimization Suite for methodology-v2. Use when: (1) Tracking token usage and API costs, (2) Optimizing LLM costs for small teams, (3) Setting budget alerts, (4) Building cost-effective AI agents. Provides token tracking, model routing, budget alerts, and usage analytics.
---

# Cost Optimization Suite

This skill helps small teams optimize AI costs with intelligent tracking and model selection.

## Quick Start

```python
import sys
sys.path.insert(0, '/workspace/methodology-v2')
sys.path.insert(0, '/workspace/cost-optimizer/scripts')

from cost_optimizer import CostOptimizer

# Initialize with monthly budget
optimizer = CostOptimizer(monthly_budget=100)

# Track usage
optimizer.track(
    prompt_tokens=1000,
    completion_tokens=500,
    model="gpt-4"
)

# Get cost-efficient model for task
best_model = optimizer.select_model(
    task="simple_summary",
    required_quality="medium"
)
print(f"Use {best_model} - saves ~70% vs gpt-4")
```

## Features

| Feature | Description |
|---------|-------------|
| Token Tracker | Real-time token and cost tracking |
| Model Router | Auto-select cheapest adequate model |
| Budget Alert | Warn when approaching budget |
| Usage Analytics | Weekly/monthly cost reports |
| Cost Prediction | Predict next month's spend |

## Model Pricing (per 1M tokens)

| Model | Input | Output | Relative Cost |
|-------|-------|--------|---------------|
| gpt-4o | $2.50 | $10.00 | 1x |
| gpt-4o-mini | $0.15 | $0.60 | 0.06x |
| claude-3.5-sonnet | $3.00 | $15.00 | 1.2x |
| claude-3-haiku | $0.25 | $1.25 | 0.1x |
| gemini-1.5-pro | $1.25 | $5.00 | 0.5x |
| gemini-1.5-flash | $0.075 | $0.30 | 0.03x |

## Usage Examples

### Track Every Call

```python
optimizer = CostOptimizer(monthly_budget=100)

# After each LLM call
optimizer.track(
    model="gpt-4",
    prompt_tokens=1500,
    completion_tokens=800,
    latency_ms=2000
)

# Check current spend
current = optimizer.get_current_spend()
print(f"Spent: ${current:.2f} / $100")
```

### Auto-Select Model

```python
# Map task complexity to model
model = optimizer.select_model(
    task="分析這段文字的情緒",
    required_quality="high"  # or "medium", "low"
)
# → claude-3.5-sonnet (high quality needed)
# → gpt-4o-mini (medium quality, much cheaper)
```

### Budget Alerts

```python
optimizer = CostOptimizer(
    monthly_budget=100,
    alert_threshold=0.8  # Alert at 80%
)

# Check if over budget
if optimizer.is_over_budget():
    optimizer.alert()  # Sends notification
```

### Cost Prediction

```python
prediction = optimizer.predict_next_month()
print(f"Next month: ${prediction:.2f}")
# Based on current usage patterns
```

## Integration with methodology-v2

```python
from methodology import SmartRouter
from cost_optimizer import CostOptimizer

# Combine SmartRouter with cost optimization
router = SmartRouter(budget="low")  # Uses cheaper models
optimizer = CostOptimizer(monthly_budget=50)

# Wrap LLM calls
def cost_tracked_completion(prompt, model=None):
    result = router.complete(prompt, model=model)
    optimizer.track(
        model=result.model,
        prompt_tokens=result.prompt_tokens,
        completion_tokens=result.completion_tokens
    )
    return result
```

## CLI Usage

```bash
# Show current costs
python cost_optimizer.py status

# Set budget
python cost_optimizer.py budget --monthly 100

# Generate report
python cost_optimizer.py report --weekly
```

## Expected Savings

| Scenario | Before | After | Savings |
|----------|--------|-------|---------|
| Simple QA (1000/day) | $45/mo | $3/mo | 93% |
| Code review (500/day) | $150/mo | $25/mo | 83% |
| Content generation | $300/mo | $90/mo | 70% |

## See Also

- [references/pricing_models.md](references/pricing_models.md) - Latest model pricing
- [references/cost_patterns.md](references/cost_patterns.md) - Common cost patterns
