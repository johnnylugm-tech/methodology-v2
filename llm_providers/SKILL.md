---
name: llm-providers
description: Extended LLM Providers for methodology-v2. Use when: (1) Using Ollama for local models, (2) Integrating DeepSeek, (3) Using HuggingFace models, (4) Adding custom LLM providers. Provides unified interface for multiple LLM providers.
---

# Extended LLM Providers

Unified interface for multiple LLM providers.

## Quick Start

```python
from llm_providers import OllamaProvider, DeepSeekProvider, HuggingFaceProvider

# Ollama (local)
ollama = OllamaProvider(model="llama3")
result = ollama.complete("Hello")

# DeepSeek
deepseek = DeepSeekProvider(api_key="sk-xxx")
result = deepseek.complete("Write a poem")

# HuggingFace
hf = HuggingFaceProvider(model="mistralai/Mistral-7B-Instruct-v0.2")
result = hf.complete("Translate this")
```

## Providers

### 1. Ollama (Local)

```python
ollama = OllamaProvider(
    model="llama3",
    base_url="http://localhost:11434"
)

# List available models
models = ollama.list_models()

# Stream response
for chunk in ollama.stream("Tell me a story"):
    print(chunk)
```

### 2. DeepSeek

```python
deepseek = DeepSeekProvider(
    api_key="sk-xxx",
    model="deepseek-chat"
)

result = deepseek.complete("What is AI?")
```

### 3. HuggingFace

```python
hf = HuggingFaceProvider(
    model="mistralai/Mistral-7B-Instruct-v0.2",
    token="hf_xxx"
)

result = hf.complete("Explain quantum computing")
```

### 4. Anthropic (Claude)

```python
from llm_providers import AnthropicProvider

claude = AnthropicProvider(
    api_key="sk-ant-xxx",
    model="claude-3-haiku"
)

result = claude.complete("Hello!")
```

### 5. Google Gemini

```python
from llm_providers import GeminiProvider

gemini = GeminiProvider(
    api_key="xxx",
    model="gemini-1.5-pro"
)

result = gemini.complete("Write code")
```

## Unified Interface

```python
from llm_providers import LLMFactory

# Create any provider
llm = LLMFactory.create("ollama", model="llama3")
llm = LLMFactory.create("openai", model="gpt-4")
llm = LLMFactory.create("anthropic", model="claude-3")

# Same interface
result = llm.complete(prompt)
```

## Configuration

```python
# Configure multiple providers
config = {
    "providers": {
        "openai": {"api_key": "sk-xxx"},
        "anthropic": {"api_key": "sk-ant-xxx"},
        "ollama": {"model": "llama3"},
        "deepseek": {"api_key": "sk-xxx"},
        "huggingface": {"token": "hf_xxx"}
    },
    "default": "openai",
    "fallback": "ollama"
}
```

## Cost Comparison

| Provider | Model | Input/1K | Output/1K |
|----------|-------|-----------|-------------|
| OpenAI | gpt-4o | $2.50 | $10.00 |
| Anthropic | claude-3-haiku | $0.25 | $1.25 |
| DeepSeek | deepseek-chat | $0.14 | $0.28 |
| Ollama | llama3 | $0 | $0 |
| HuggingFace | mistral-7b | $0 | $0 |

## CLI Usage

```bash
# Test provider
python llm_providers.py test --provider ollama

# Compare costs
python llm_providers.py cost --prompt "Hello world"

# List models
python llm_providers.py list --provider openai
```

## Best Practices

1. **Use local for dev** - Ollama for development
2. **Fallback strategy** - Set fallback provider
3. **Cost optimization** - Route to cheaper models for simple tasks
4. **Rate limits** - Handle rate limits gracefully

## See Also

- [smart_router.py](smart_router.py) - Intelligent routing
- [cost_optimizer.py](cost_optimizer.py) - Cost tracking
