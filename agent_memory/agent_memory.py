"""Agent Memory System for methodology-v2 with framework integration"""
import time, json
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum

# Framework integration
try:
    import sys
    sys.path.insert(0, '/workspace/methodology-v2')
    from methodology import TaskLifecycle, Monitor
    FRAMEWORK_AVAILABLE = True
except ImportError:
    FRAMEWORK_AVAILABLE = False

class MemoryType(Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    WORKING = "working"

@dataclass
class Memory:
    """Memory entry"""
    memory_id: str
    content: Any
    memory_type: MemoryType
    importance: float = 0.5  # 0-1
    created_at: float = field(default_factory=time.time)
    accessed_at: float = field(default_factory=time.time)
    tags: List[str] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

class ShortTermMemory:
    """Short-term memory for current conversation"""
    
    def __init__(self, max_items: int = 10):
        self.max_items = max_items
        self._items: List[Memory] = []
    
    def add(self, content: Any, tags: List[str] = None):
        memory = Memory(
            memory_id=f"stm_{len(self._items)}",
            content=content,
            memory_type=MemoryType.SHORT_TERM,
            tags=tags or []
        )
        self._items.append(memory)
        
        # Evict oldest if full
        if len(self._items) > self.max_items:
            self._items.pop(0)
    
    def get_all(self) -> List[Memory]:
        return self._items.copy()
    
    def clear(self):
        self._items.clear()

class LongTermMemory:
    """Long-term persistent memory"""
    
    def __init__(self, storage: str = "memory"):
        self.storage = storage
        self._memories: Dict[str, Memory] = {}
    
    def store(self, key: str, content: Any, importance: float = 0.5, tags: List[str] = None):
        memory = Memory(
            memory_id=key,
            content=content,
            memory_type=MemoryType.LONG_TERM,
            importance=importance,
            tags=tags or []
        )
        self._memories[key] = memory
    
    def retrieve(self, key: str) -> Optional[Memory]:
        memory = self._memories.get(key)
        if memory:
            memory.accessed_at = time.time()
        return memory
    
    def search(self, query: str, top_k: int = 5) -> List[Memory]:
        """Simple keyword search"""
        results = []
        query_lower = query.lower()
        
        for memory in self._memories.values():
            content_str = str(memory.content).lower()
            # Simple scoring
            score = sum(1 for word in query_lower.split() if word in content_str)
            if score > 0:
                results.append((score, memory))
        
        # Sort by score and importance
        results.sort(key=lambda x: (x[0], x[1].importance), reverse=True)
        return [m for _, m in results[:top_k]]
    
    def get_all(self) -> List[Memory]:
        return list(self._memories.values())

class WorkingMemory:
    """Task-specific working memory"""
    
    def __init__(self, task_id: str):
        self.task_id = task_id
        self._data: Dict[str, Any] = {}
    
    def put(self, key: str, value: Any):
        self._data[key] = value
    
    def get(self, key: str) -> Optional[Any]:
        return self._data.get(key)
    
    def clear(self):
        self._data.clear()

class ContextManager:
    """Manage context window"""
    
    def __init__(self, max_tokens: int = 8000, strategy: str = "summarize"):
        self.max_tokens = max_tokens
        self.strategy = strategy
    
    def estimate_tokens(self, text: str) -> int:
        """Rough token estimation"""
        return len(text) // 4
    
    def build_context(self, conversation: List[Dict], memories: List[Memory] = None, system_prompt: str = "") -> str:
        """Build context within token limit"""
        context_parts = [system_prompt] if system_prompt else []
        
        # Add memories (high priority)
        if memories:
            memory_text = "## Relevant Memories\n"
            for m in memories[:3]:
                memory_text += f"- {m.content}\n"
            
            if self.estimate_tokens("\n".join(context_parts) + memory_text) < self.max_tokens * 0.3:
                context_parts.append(memory_text)
        
        # Add conversation
        for msg in conversation:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            
            # Check token limit
            test_context = "\n".join(context_parts) + f"\n{role}: {content}"
            if self.estimate_tokens(test_context) > self.max_tokens:
                break
            
            context_parts.append(f"{role}: {content}")
        
        return "\n\n".join(context_parts)
    
    def summarize(self, text: str, max_length: int = 500) -> str:
        """Summarize text"""
        # Simple truncation for demo
        if len(text) <= max_length:
            return text
        return text[:max_length] + "..."

class MemoryOptimizer:
    """Optimize memory usage"""
    
    @staticmethod
    def compress(memory: LongTermMemory, threshold: float = 0.7):
        """Compress low-importance memories"""
        for mem in memory.get_all():
            if mem.importance < threshold and mem.memory_type == MemoryType.LONG_TERM:
                # Mark for compression
                mem.content = f"[Compressed] {mem.content}"[:200]
    
    @staticmethod
    def deduplicate(memory: LongTermMemory):
        """Remove duplicate memories"""
        seen = set()
        to_remove = []
        
        for mem in memory.get_all():
            content_hash = hash(str(mem.content))
            if content_hash in seen:
                to_remove.append(mem.memory_id)
            else:
                seen.add(content_hash)
        
        for key in to_remove:
            del memory._memories[key]
    
    @staticmethod
    def archive(memory: LongTermMemory, older_than_days: int = 30):
        """Archive old memories"""
        cutoff = time.time() - (older_than_days * 86400)
        
        for mem in memory.get_all():
            if mem.created_at < cutoff:
                mem.metadata["archived"] = True

class AgentMemory:
    """Main agent memory interface"""
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.short_term = ShortTermMemory()
        self.long_term = LongTermMemory()
        self.working = WorkingMemory(agent_id)
        self.context = ContextManager()
    
    def store(self, key: str, content: Any, memory_type: str = "long_term", importance: float = 0.5):
        """Store memory"""
        if memory_type == "short_term":
            self.short_term.add(content)
        elif memory_type == "working":
            self.working.put(key, content)
        else:
            self.long_term.store(key, content, importance)
    
    def retrieve(self, key: str) -> Optional[Any]:
        """Retrieve memory"""
        # Check working first
        val = self.working.get(key)
        if val:
            return val
        
        # Check long-term
        mem = self.long_term.retrieve(key)
        if mem:
            return mem.content
        
        return None
    
    def search(self, query: str, top_k: int = 5) -> List[Memory]:
        """Search memories"""
        return self.long_term.search(query, top_k)

# Demo
if __name__ == "__main__":
    agent = AgentMemory("coder")
    
    # Store
    agent.store("user_pref", {"language": "zh-TW"}, importance=0.8)
    agent.store("project_context", {"file": "main.py"}, importance=0.6)
    
    # Short-term
    agent.short_term.add("User asked about function syntax")
    agent.short_term.add("User prefers Chinese responses")
    
    # Search
    results = agent.search("preference")
    print("Search results:")
    for r in results:
        print(f"  - {r.content}")
    
    # Context
    conversation = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi!"},
        {"role": "user", "content": "Help me write code"}
    ]
    context = agent.context.build_context(conversation, results)
    print(f"\nContext length: {len(context)} chars")
    
    print("\n✅ Agent Memory ready!")
