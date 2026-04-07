---
name: performance-optimizer
description: Performance Optimization Module for methodology-v2. Provides latency optimization, caching strategies, batch processing, and performance monitoring for AI agents.
---

# Performance Optimizer

Performance optimization for methodology-v2 agents.

## Quick Start

```python
from performance_optimizer import PerformanceOptimizer, Cache, BatchProcessor

# Optimize latency
optimizer = PerformanceOptimizer()
result = await optimizer.optimize(agent, task)

# Smart caching
cache = Cache(ttl=3600)
result = cache.get(key) or cache.set(key, compute())

# Batch processing
batch = BatchProcessor(max_size=10, timeout=1.0)
results = await batch.process(items)
```

## Features

### 1. Latency Optimization

```python
# Parallel execution
from performance_optimizer import ParallelExecutor

executor = ParallelExecutor(max_workers=4)
results = await executor.run(tasks)

# Lazy loading
from performance_optimizer import LazyLoader

loader = LazyLoader(load_fn)
data = loader.get(key)  # Only loads when needed
```

### 2. Smart Caching

```python
cache = Cache(
    ttl=3600,  # 1 hour
    max_size=1000,
    strategy="lru"  # lru, lfu, fifo
)

# Cache agent responses
result = cache.get_or_set(cache_key, lambda: agent.run(task))
```

### 3. Batch Processing

```python
batch = BatchProcessor(
    max_size=10,
    timeout=1.0,
    aggregate=True
)

# Process multiple requests together
results = await batch.process(requests)
```

### 4. Performance Monitoring

```python
from performance_optimizer import PerformanceMonitor

monitor = PerformanceMonitor()
monitor.track("agent_run", duration=0.5, tokens=1000)

# Get stats
stats = monitor.get_stats()
```

## CLI Usage

```bash
# Run performance test
python performance_optimizer.py benchmark

# Analyze performance
python performance_optimizer.py analyze
```

## Best Practices

1. **Cache expensive computations** - Agent responses, embeddings
2. **Batch similar requests** - Reduce API calls
3. **Use parallel execution** - When tasks are independent
4. **Monitor performance** - Track latency and costs
