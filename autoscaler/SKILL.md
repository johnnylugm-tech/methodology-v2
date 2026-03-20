---
name: autoscaler
description: Auto-scaling module for methodology-v2. Use when: (1) Automatically scaling agent count based on load, (2) Optimizing cost during low traffic, (3) Handling traffic spikes. Provides automatic agent scaling with Kubernetes HPA support.
---

# AutoScaler

Automatic agent scaling for methodology-v2.

## Quick Start

```python
from autoscaler import AutoScaler

scaler = AutoScaler(
    min_agents=2,
    max_agents=10,
    scale_up_threshold=0.8,
    scale_down_threshold=0.2
)

# Check and scale
scaler.check_and_scale()
```

## Features

### 1. Load-Based Scaling

```python
scaler = AutoScaler(
    min_agents=2,
    max_agents=10,
    scale_up_threshold=0.8,  # Scale up when 80% load
    scale_down_threshold=0.2   # Scale down when 20% load
)
```

### 2. Time-Based Scaling

```python
scaler = AutoScaler()

# Scale up during business hours
scaler.add_schedule(
    start="09:00",
    end="18:00",
    min_agents=5,
    max_agents=20
)

# Scale down at night
scaler.add_schedule(
    start="18:00",
    end="09:00",
    min_agents=1,
    max_agents=5
)
```

### 3. Cost-Based Scaling

```python
scaler = AutoScaler(
    budget=1000,  # Monthly budget
    cost_per_agent=50,  # Cost per agent per month
    scale_down_threshold=0.1
)

# Auto-scale to stay within budget
scaler.scale_to_budget()
```

### 4. Kubernetes HPA Integration

```python
from autoscaler import K8sAutoscaler

k8s = K8sAutoscaler(
    deployment_name="methodology-agents",
    namespace="default"
)

# Create HPA
k8s.create_hpa(
    min_replicas=2,
    max_replicas=20,
    target_cpu_percent=80
)
```

## Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| min_agents | Minimum number of agents | 1 |
| max_agents | Maximum number of agents | 10 |
| scale_up_threshold | CPU/queue threshold to scale up | 0.8 |
| scale_down_threshold | CPU/queue threshold to scale down | 0.2 |
| cooldown_seconds | Seconds between scaling actions | 300 |

## Metrics

### Monitored Metrics

| Metric | Source |
|--------|--------|
| Queue Length | Message queue depth |
| CPU Usage | Agent process CPU |
| Memory Usage | Agent process memory |
| Response Time | Average response latency |
| Error Rate | Failed request rate |

### Scaling Decisions

```python
# Scale up if ANY metric exceeds threshold
if queue_length > threshold:
    scale_up()
elif cpu_usage > threshold:
    scale_up()

# Scale down if ALL metrics below threshold
if queue_length < down_threshold and cpu_usage < down_threshold:
    scale_down()
```

## CLI Usage

```bash
# Start autoscaler
python autoscaler.py start --min 2 --max 10

# View status
python autoscaler.py status

# Manual scale
python autoscaler.py scale --to 5
```

## Best Practices

1. **Start conservative** - Begin with higher min_agents
2. **Monitor costs** - Set budget and cost alerts
3. **Test scaling** - Simulate load before production
4. **Set cooldown** - Prevent rapid scaling oscillation

## Example Use Cases

### E-commerce Bot

```python
scaler = AutoScaler(
    min_agents=2,
    max_agents=50,
    scale_up_threshold=0.7
)

# Add time-based scaling for peak hours
scaler.add_schedule("12:00", "14:00", min_agents=10, max_agents=50)
scaler.add_schedule("18:00", "21:00", min_agents=10, max_agents=50)
```

### Data Processing Pipeline

```python
scaler = AutoScaler(
    min_agents=1,
    max_agents=100,
    scale_up_threshold=0.9,  # Higher threshold for batch processing
    cooldown_seconds=600
)
```

## See Also

- [failover_manager.py](failover_manager.py) - Failover handling
- [monitoring.py](monitoring.py) - Metrics collection
