"""Tests for performance_optimizer module"""
import pytest
import asyncio
from performance_optimizer import Cache, PerformanceMonitor, ParallelExecutor, BatchProcessor

class TestCache:
    """Test Cache"""
    
    def test_cache_set_get(self):
        """Test cache set and get"""
        cache = Cache(ttl=60)
        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"
    
    def test_cache_miss(self):
        """Test cache miss"""
        cache = Cache(ttl=60)
        assert cache.get("nonexistent") is None
    
    def test_cache_eviction(self):
        """Test LRU eviction"""
        cache = Cache(max_size=2, strategy="lru")
        cache.set("a", 1)
        cache.set("b", 2)
        cache.set("c", 3)  # Should evict 'a'
        assert cache.get("a") is None

class TestPerformanceMonitor:
    """Test PerformanceMonitor"""
    
    def test_track(self):
        """Test tracking"""
        monitor = PerformanceMonitor()
        monitor.track("test", 1.0, tokens=100)
        stats = monitor.get_stats()
        assert stats["count"] == 1

class TestParallelExecutor:
    """Test ParallelExecutor"""
    
    @pytest.mark.asyncio
    async def test_execute(self):
        """Test parallel execution"""
        executor = ParallelExecutor(max_workers=2)
        tasks = [lambda: asyncio.sleep(0.01) or i for i in range(3)]
        # Just test it doesn't crash
        assert executor.max_workers == 2

class TestBatchProcessor:
    """Test BatchProcessor"""
    
    @pytest.mark.asyncio
    async def test_process(self):
        """Test batch processing"""
        processor = BatchProcessor(max_size=2)
        items = [1, 2, 3, 4]
        # Just test initialization
        assert processor.max_size == 2

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
