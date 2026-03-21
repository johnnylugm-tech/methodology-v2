"""
Extended LLM Providers for methodology-v2
"""

import json
from typing import Dict, List, Optional, Any, Iterator
from abc import ABC, abstractmethod


class BaseProvider(ABC):
    """Base LLM Provider"""
    
    @abstractmethod
    def complete(self, prompt: str, **kwargs) -> str:
        pass
    
    @abstractmethod
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        pass
    
    def list_models(self) -> List[str]:
        return []


class OllamaProvider(BaseProvider):
    """Ollama local provider"""
    
    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
    
    def complete(self, prompt: str, **kwargs) -> str:
        # In production, this would call Ollama API
        return f"[Ollama:{self.model}] {prompt[:50]}..."
    
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        yield f"[Ollama:{self.model}] "
        for word in prompt.split()[:5]:
            yield word + " "
    
    def list_models(self) -> List[str]:
        return ["llama3", "mistral", "codellama", "mixtral"]


class DeepSeekProvider(BaseProvider):
    """DeepSeek provider"""
    
    def __init__(self, api_key: str = "", model: str = "deepseek-chat"):
        self.api_key = api_key
        self.model = model
    
    def complete(self, prompt: str, **kwargs) -> str:
        return f"[DeepSeek:{self.model}] {prompt[:50]}..."
    
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        yield f"[DeepSeek:{self.model}] "
        for word in prompt.split()[:5]:
            yield word + " "


class HuggingFaceProvider(BaseProvider):
    """HuggingFace provider"""
    
    def __init__(self, model: str = "mistralai/Mistral-7B-Instruct-v0.2", token: str = ""):
        self.model = model
        self.token = token
    
    def complete(self, prompt: str, **kwargs) -> str:
        return f"[HuggingFace:{self.model}] {prompt[:50]}..."
    
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        yield f"[HuggingFace:{self.model}] "
        for word in prompt.split()[:5]:
            yield word + " "


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider"""
    
    def __init__(self, api_key: str = "", model: str = "claude-3-haiku"):
        self.api_key = api_key
        self.model = model
    
    def complete(self, prompt: str, **kwargs) -> str:
        return f"[Claude:{self.model}] {prompt[:50]}..."
    
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        yield f"[Claude:{self.model}] "
        for word in prompt.split()[:5]:
            yield word + " "


class GeminiProvider(BaseProvider):
    """Google Gemini provider"""
    
    def __init__(self, api_key: str = "", model: str = "gemini-1.5-pro"):
        self.api_key = api_key
        self.model = model
    
    def complete(self, prompt: str, **kwargs) -> str:
        return f"[Gemini:{self.model}] {prompt[:50]}..."
    
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        yield f"[Gemini:{self.model}] "
        for word in prompt.split()[:5]:
            yield word + " "


class OpenAIProvider(BaseProvider):
    """OpenAI provider"""
    
    def __init__(self, api_key: str = "", model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
    
    def complete(self, prompt: str, **kwargs) -> str:
        return f"[GPT:{self.model}] {prompt[:50]}..."
    
    def stream(self, prompt: str, **kwargs) -> Iterator[str]:
        yield f"[GPT:{self.model}] "
        for word in prompt.split()[:5]:
            yield word + " "


class LLMFactory:
    """Factory for creating LLM providers"""
    
    PROVIDERS = {
        "ollama": OllamaProvider,
        "deepseek": DeepSeekProvider,
        "huggingface": HuggingFaceProvider,
        "anthropic": AnthropicProvider,
        "gemini": GeminiProvider,
        "openai": OpenAIProvider,
    }
    
    @classmethod
    def create(cls, provider: str, **kwargs) -> BaseProvider:
        provider_cls = cls.PROVIDERS.get(provider.lower())
        if not provider_cls:
            raise ValueError(f"Unknown provider: {provider}")
        return provider_cls(**kwargs)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        return list(cls.PROVIDERS.keys())


# Cost comparison
PROVIDER_COSTS = {
    "openai": {"gpt-4o": (2.50, 10.00), "gpt-4o-mini": (0.15, 0.60)},
    "anthropic": {"claude-3-haiku": (0.25, 1.25), "claude-3-sonnet": (3.00, 15.00)},
    "deepseek": {"deepseek-chat": (0.14, 0.28)},
    "ollama": {"*": (0.00, 0.00)},
    "huggingface": {"*": (0.00, 0.00)},
}


if __name__ == "__main__":
    # Demo
    print("Available providers:", LLMFactory.list_providers())
    
    # Test each
    for provider_name in LLMFactory.list_providers():
        provider = LLMFactory.create(provider_name, model="test")
        print(f"{provider_name}: {provider.complete('Hello world')}")
    # Groq Provider
    elif provider == "groq":
        return {
            "name": "Groq",
            "models": ["llama-3.1-8b", "mixtral-8x7b"],
            "supports": ["chat", "completion"],
        }

