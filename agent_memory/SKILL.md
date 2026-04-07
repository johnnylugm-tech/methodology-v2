---
name: agent-memory
description: Agent Memory System for methodology-v2. Provides long-term memory, context management, retrieval, and memory optimization for AI agents.
---

# Agent Memory

Long-term memory and context management for AI agents.

## Quick Start

```python
from agent_memory import AgentMemory, MemoryStore, ContextManager

# Create memory
memory = AgentMemory(agent_id="coder")

# Store memory
memory.store("user_preference", {"language": "zh-TW"})

# Retrieve
prefs = memory.retrieve("user_preference")

# Context window management
ctx = ContextManager(max_tokens=8000)
context = ctx.build_context(conversation_history)
```

## Features

### 1. Memory Types

```python
from agent_memory import ShortTermMemory, LongTermMemory, WorkingMemory

# Short-term: Current conversation
stm = ShortTermMemory(max_items=10)

# Long-term: Persistent across sessions
ltm = LongTermMemory(storage="sqlite")

# Working: Task-specific
wm = WorkingMemory(task_id="task_123")
```

### 2. Memory Retrieval

```python
from agent_memory import MemoryRetriever

retriever = MemoryRetriever(memory)
results = retriever.search("user preferences", top_k=5)
results = retriever.get_recent(limit=10)
```

### 3. Context Management

```python
from agent_memory import ContextManager

ctx = ContextManager(
    max_tokens=8000,
    strategy="summarize"  # or "truncate", "prioritize"
)

# Build context from memory
context = ctx.build_context(
    conversation=history,
    memories=memories,
    system_prompt=system
)
```

### 4. Memory Optimization

```python
from agent_memory import MemoryOptimizer

optimizer = MemoryOptimizer()

# Compress old memories
optimizer.compress(memory, threshold=0.7)

# Clean up duplicate memories
optimizer.deduplicate(memory)

# Archive old data
optimizer.archive(memory, older_than_days=30)
```

## CLI Usage

```bash
# Search memory
python agent_memory.py search "preference"

# Stats
python agent_memory.py stats

# Optimize
python agent_memory.py optimize
```

## Memory Architecture

```
┌─────────────────────────────────────┐
│           Agent Memory               │
├─────────────────────────────────────┤
│  ShortTerm  │  LongTerm  │ Working  │
│  - History  │  - Facts   │ - Task  │
│  - Context  │  - Prefs   │ - Temp  │
├─────────────────────────────────────┤
│       Context Manager                │
│  - Token limit                      │
│  - Summarization                    │
│  - Prioritization                   │
├─────────────────────────────────────┤
│       Memory Retriever               │
│  - Semantic search                  │
│  - Relevance ranking                │
└─────────────────────────────────────┘
```

## Best Practices

1. **Summarize long context** - Don't keep everything
2. **Prioritize important memories** - Not all memories are equal
3. **Compress old data** - Save storage
4. **Clear working memory** - Between tasks
