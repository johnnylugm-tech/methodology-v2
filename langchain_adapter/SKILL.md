---
name: langchain-adapter
description: LangChain Adapter for methodology-v2. Use when: (1) Migrating existing LangChain projects to methodology-v2, (2) Using LangChain LLMs and tools within methodology-v2, (3) Leveraging LangChain ecosystem while using methodology-v2 patterns. Provides chain migration, LLM wrapper, tool adapter, and memory bridge.
---

# LangChain Adapter

Bridge between LangChain ecosystem and methodology-v2.

## Quick Start

```python
import sys
sys.path.insert(0, '/workspace/methodology-v2')
sys.path.insert(0, '/workspace/langchain-adapter/scripts')

from langchain_adapter import LangChainMigrator, MethodologyLLMWrapper

# Migrate existing LangChain project
migrator = LangChainMigrator()
new_code = migrator.migrate("old_langchain_project.py")
print(new_code)

# Use LangChain LLM in methodology-v2
from langchain_openai import ChatOpenAI
llm = MethodologyLLMWrapper(ChatOpenAI())

# Use in Crew
from methodology import Crew
crew = Crew(agents=[llm_agent], process="sequential")
```

## Features

| Feature | Description |
|---------|-------------|
| ChainMigrator | Auto-convert LangChain chains to methodology-v2 |
| LLMWrapper | Use LangChain LLMs in methodology-v2 |
| ToolAdapter | Bridge LangChain tools |
| MemoryBridge | Migrate LangChain memory |

## Migration Guide

### Before (LangChain)

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

llm = ChatOpenAI()
prompt = PromptTemplate(template="{question}", input_variables=["question"])
chain = LLMChain(llm=llm, prompt=prompt)
result = chain.run("What is AI?")
```

### After (methodology-v2)

```python
from methodology import SmartRouter
from langchain_adapter import MethodologyLLMWrapper

# Wrap LangChain LLM
llm = MethodologyLLMWrapper(ChatOpenAI())

# Use with SmartRouter
router = SmartRouter()
result = router.complete("What is AI?")
```

## Integration Methods

### 1. Use LangChain LLM

```python
from langchain_adapter import MethodologyLLMWrapper
from langchain_anthropic import ChatAnthropic

# Wrap any LangChain LLM
wrapped = MethodologyLLMWrapper(ChatAnthropic(model="claude-3-sonnet"))
result = wrapped.invoke("Hello")
```

### 2. Use LangChain Tools

```python
from langchain.agents import load_tools
from langchain_adapter import ToolAdapter

# Load LangChain tools
tools = load_tools(["serpapi", "llm-math"])

# Convert to methodology-v2 format
adapter = ToolAdapter()
m2v2_tools = adapter.convert_tools(tools)
```

### 3. Migrate Memory

```python
from langchain.memory import ConversationBufferMemory
from langchain_adapter import MemoryBridge

# LangChain memory
lc_memory = ConversationBufferMemory()

# Convert to methodology-v2 storage
bridge = MemoryBridge()
m2v2_storage = bridge.migrate_memory(lc_memory)
```

## CLI Usage

```bash
# Analyze LangChain code
python langchain_adapter.py analyze old_chain.py

# Auto-migrate
python langchain_adapter.py migrate old_chain.py --output new_methodology.py

# Convert tools
python langchain_adapter.py convert-tools --input tools.json
```

## Supported LangChain Components

| Component | Status | Notes |
|-----------|--------|-------|
| LLMs (ChatOpenAI, ChatAnthropic, etc.) | ✅ Full | Via MethodologyLLMWrapper |
| Prompts | ✅ Full | Via migrate_prompt |
| Chains | ✅ Full | Via ChainMigrator |
| Agents | ✅ Full | Via AgentAdapter |
| Tools | ✅ Full | Via ToolAdapter |
| Memory | ✅ Full | Via MemoryBridge |
| DocumentLoaders | ⏳ Partial | Basic support |
| VectorStores | ⏳ Partial | Pinecone, Weaviate |

## Error Handling

| LangChain Error | methodology-v2 Equivalent |
|-----------------|---------------------------|
| APIError | L2 (retry 3x) |
| RateLimitError | L2 (exponential backoff) |
| AuthenticationError | L1 (return immediately) |
| TimeoutError | L3 (fallback model) |

## See Also

- [references/ langchain_patterns.md](references/langchain_patterns.md)
- [references/migration_examples.md](references/migration_examples.md)
