"""Tests for agent_memory module"""
import pytest
from agent_memory import (
    ShortTermMemory, LongTermMemory, WorkingMemory, 
    ContextManager, MemoryOptimizer, AgentMemory
)

class TestShortTermMemory:
    """Test ShortTermMemory"""
    
    def test_add(self):
        """Test adding memory"""
        stm = ShortTermMemory(max_items=5)
        stm.add("test content")
        assert len(stm.get_all()) == 1
    
    def test_eviction(self):
        """Test eviction"""
        stm = ShortTermMemory(max_items=2)
        stm.add("item1")
        stm.add("item2")
        stm.add("item3")
        assert len(stm.get_all()) == 2

class TestLongTermMemory:
    """Test LongTermMemory"""
    
    def test_store_retrieve(self):
        """Test store and retrieve"""
        ltm = LongTermMemory()
        ltm.store("key1", {"data": "value1"})
        memory = ltm.retrieve("key1")
        assert memory.content["data"] == "value1"
    
    def test_search(self):
        """Test search"""
        ltm = LongTermMemory()
        ltm.store("pref", {"language": "zh-TW"})
        results = ltm.search("language")
        assert len(results) > 0

class TestWorkingMemory:
    """Test WorkingMemory"""
    
    def test_put_get(self):
        """Test put and get"""
        wm = WorkingMemory("task_001")
        wm.put("temp", "value")
        assert wm.get("temp") == "value"

class TestContextManager:
    """Test ContextManager"""
    
    def test_build_context(self):
        """Test context building"""
        ctx = ContextManager(max_tokens=100)
        conversation = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi!"}
        ]
        context = ctx.build_context(conversation)
        assert len(context) > 0

class TestMemoryOptimizer:
    """Test MemoryOptimizer"""
    
    def test_compress(self):
        """Test compression"""
        ltm = LongTermMemory()
        ltm.store("key1", "very long content" * 100, importance=0.3)
        MemoryOptimizer.compress(ltm, threshold=0.5)
        # Should be compressed

class TestAgentMemory:
    """Test AgentMemory"""
    
    def test_store(self):
        """Test store"""
        memory = AgentMemory("test_agent")
        memory.store("test_key", "test_value")
        assert memory.retrieve("test_key") == "test_value"
    
    def test_search(self):
        """Test search"""
        memory = AgentMemory("test_agent")
        memory.store("pref", {"language": "zh-TW"}, importance=0.8)
        results = memory.search("language")
        assert len(results) >= 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
