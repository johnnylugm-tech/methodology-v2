"""Performance Optimizer Module for methodology-v2 with framework integration"""
import time, asyncio

# Framework integration
try:
    import sys
    sys.path.insert(0, '/workspace/methodology-v2')
    from methodology import Monitor, QualityGate
    FRAMEWORK_AVAILABLE = True
except ImportError:
    FRAMEWORK_AVAILABLE = False
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field
from collections import OrderedDict
from datetime import datetime

@dataclass
class PerformanceMetrics:
    """Performance metrics"""
    operation: str
    duration: float
    tokens: int = 0
    cost: float = 0.0
    timestamp: float = field(default_factory=time.time)

class Cache:
    """Smart caching with multiple strategies"""
    
    def __init__(self, ttl: int = 3600, max_size: int = 1000, strategy: str = "lru"):
        self.ttl = ttl
        self.max_size = max_size
        self.strategy = strategy
        self._cache: OrderedDict = OrderedDict()
        self._timestamps: Dict[str, float] = {}
    
    def get(self, key: str) -> Optional[Any]:
        if key not in self._cache:
            return None
        
        # Check TTL
        if time.time() - self._timestamps[key] > self.ttl:
            del self._cache[key]
            del self._timestamps[key]
            return None
        
        # Move to end (LRU)
        if self.strategy == "lru":
            self._cache.move_to_end(key)
        
        return self._cache[key]
    
    def set(self, key: str, value: Any):
        # Evict if full
        if len(self._cache) >= self.max_size:
            if self.strategy == "lru":
                self._cache.popitem(last=False)
            elif self.strategy == "fifo":
                self._cache.popitem(last=False)
        
        self._cache[key] = value
        self._timestamps[key] = time.time()
    
    def get_or_set(self, key: str, compute_fn: Callable) -> Any:
        """Get from cache or compute and cache"""
        result = self.get(key)
        if result is None:
            result = compute_fn()
            self.set(key, result)
        return result
    
    def clear(self):
        self._cache.clear()
        self._timestamps.clear()

class PerformanceMonitor:
    """Monitor performance metrics"""
    
    def __init__(self):
        self._metrics: List[PerformanceMetrics] = []
    
    def track(self, operation: str, duration: float, tokens: int = 0, cost: float = 0.0):
        self._metrics.append(PerformanceMetrics(
            operation=operation,
            duration=duration,
            tokens=tokens,
            cost=cost
        ))
    
    def get_stats(self) -> Dict:
        if not self._metrics:
            return {"count": 0}
        
        durations = [m.duration for m in self._metrics]
        tokens = sum(m.tokens for m in self._metrics)
        
        return {
            "count": len(self._metrics),
            "avg_duration": sum(durations) / len(durations),
            "min_duration": min(durations),
            "max_duration": max(durations),
            "total_tokens": tokens,
            "total_cost": sum(m.cost for m in self._metrics)
        }
    
    def clear(self):
        self._metrics.clear()

class ParallelExecutor:
    """Execute tasks in parallel"""
    
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
    
    async def run(self, tasks: List[Callable]) -> List[Any]:
        semaphore = asyncio.Semaphore(self.max_workers)
        
        async def bounded_task(task):
            async with semaphore:
                return await task()
        
        return await asyncio.gather(*[bounded_task(t) for t in tasks])

class BatchProcessor:
    """Batch process multiple requests"""
    
    def __init__(self, max_size: int = 10, timeout: float = 1.0, aggregate: bool = True):
        self.max_size = max_size
        self.timeout = timeout
        self.aggregate = aggregate
        self._queue: List[Any] = []
    
    async def process(self, items: List[Any]) -> List[Any]:
        """Process items in batches"""
        results = []
        
        for i in range(0, len(items), self.max_size):
            batch = items[i:i + self.max_size]
            # Simulate batch processing
            await asyncio.sleep(0.01)
            results.extend(batch)
        
        return results

class PerformanceOptimizer:
    """Main performance optimizer"""
    
    def __init__(self):
        self.cache = Cache()
        self.monitor = PerformanceMonitor()
        self.executor = ParallelExecutor()
        self.batch = BatchProcessor()
    
    async def optimize(self, agent: Any, task: Any) -> Any:
        """Optimize agent execution"""
        start = time.time()
        
        # Execute
        result = agent.run(task)
        
        # Track
        self.monitor.track("agent_run", time.time() - start)
        
        return result

# Demo
if __name__ == "__main__":
    # Cache demo
    cache = Cache(ttl=60)
    cache.set("key1", "value1")
# # #     print(f"Cache get: {cache.get('key1')}")
    
    # Monitor demo
    monitor = PerformanceMonitor()
    monitor.track("test", 0.5, tokens=100, cost=0.001)
# # #     print(f"Stats: {monitor.get_stats()}")
    
# # #     print("\n✅ Performance Optimizer ready!")
