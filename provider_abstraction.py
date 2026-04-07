#!/usr/bin/env python3
"""
Multi-Provider Abstraction Layer

統一的 Provider 介面，支持 Anthropic / OpenAI / GLM

用法：
    from provider_abstraction import Provider, ModelRouter
    
    router = ModelRouter()
    provider = router.route(phase=3, state_path=".methodology/state.json")
    response = provider.chat(messages=[{"role": "user", "content": "..."}])
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
import os


class ProviderType(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GLM = "glm"


@dataclass
class ModelInfo:
    """模型資訊"""
    name: str
    provider: ProviderType
    cost_per_1k_input: float
    cost_per_1k_output: float
    context_window: int
    strengths: List[str] = field(default_factory=list)


class BaseProvider(ABC):
    """Provider 抽象基類"""
    
    @abstractmethod
    def chat(self, messages: List[Dict], **kwargs) -> str:
        """發送聊天請求"""
        pass
    
    @abstractmethod
    def chat_stream(self, messages: List[Dict], **kwargs):
        """流式聊天請求"""
        pass
    
    @abstractmethod
    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        """計算成本"""
        pass


class AnthropicProvider(BaseProvider):
    """Anthropic Claude Provider"""
    
    def __init__(self, api_key: str = None, base_url: str = None, default_model: str = "claude-sonnet-4"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.base_url = base_url or "https://api.anthropic.com"
        self.default_model = default_model
        self.models = {
            "claude-opus-4": ModelInfo(
                name="claude-opus-4",
                provider=ProviderType.ANTHROPIC,
                cost_per_1k_input=0.015,
                cost_per_1k_output=0.075,
                context_window=200000,
                strengths=["coding", "reasoning", "analysis"]
            ),
            "claude-sonnet-4": ModelInfo(
                name="claude-sonnet-4",
                provider=ProviderType.ANTHROPIC,
                cost_per_1k_input=0.003,
                cost_per_1k_output=0.015,
                context_window=200000,
                strengths=["coding", "balanced"]
            ),
        }
    
    def chat(self, messages: List[Dict], model: str = None, **kwargs) -> str:
        """發送聊天請求"""
        # 實際實現會調用 Anthropic API
        model = model or self.default_model
        # TODO: 實現實際 API 調用
        return f"[Anthropic {model}] Response"
    
    def chat_stream(self, messages: List[Dict], model: str = None, **kwargs):
        model = model or self.default_model
        # TODO: 實現實際流式 API 調用
        yield f"[Anthropic {model}] Stream response"
    
    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        model_info = self.models.get(self.default_model)
        if not model_info:
            return 0.0
        return (input_tokens / 1000) * model_info.cost_per_1k_input + \
               (output_tokens / 1000) * model_info.cost_per_1k_output


class OpenAIProvider(BaseProvider):
    """OpenAI GPT Provider"""
    
    def __init__(self, api_key: str = None, base_url: str = None, default_model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or "https://api.openai.com/v1"
        self.default_model = default_model
        self.models = {
            "gpt-4o": ModelInfo(
                name="gpt-4o",
                provider=ProviderType.OPENAI,
                cost_per_1k_input=0.005,
                cost_per_1k_output=0.015,
                context_window=128000,
                strengths=["multimodal", "balanced"]
            ),
            "gpt-4o-mini": ModelInfo(
                name="gpt-4o-mini",
                provider=ProviderType.OPENAI,
                cost_per_1k_input=0.00015,
                cost_per_1k_output=0.0006,
                context_window=128000,
                strengths=["fast", "cheap"]
            ),
            "o3-mini": ModelInfo(
                name="o3-mini",
                provider=ProviderType.OPENAI,
                cost_per_1k_input=0.001,
                cost_per_1k_output=0.004,
                context_window=200000,
                strengths=["reasoning", "cheap"]
            ),
        }
    
    def chat(self, messages: List[Dict], model: str = None, **kwargs) -> str:
        model = model or self.default_model
        return f"[OpenAI {model}] Response"
    
    def chat_stream(self, messages: List[Dict], model: str = None, **kwargs):
        model = model or self.default_model
        yield f"[OpenAI {model}] Stream response"
    
    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        model_info = self.models.get(self.default_model)
        if not model_info:
            return 0.0
        return (input_tokens / 1000) * model_info.cost_per_1k_input + \
               (output_tokens / 1000) * model_info.cost_per_1k_output


class GLMProvider(BaseProvider):
    """Zhipu GLM Provider"""
    
    def __init__(self, api_key: str = None, base_url: str = None, default_model: str = "glm-4"):
        self.api_key = api_key or os.getenv("GLM_API_KEY")
        self.base_url = base_url or "https://open.bigmodel.cn/api/paas/v4"
        self.default_model = default_model
        self.models = {
            "glm-4": ModelInfo(
                name="glm-4",
                provider=ProviderType.GLM,
                cost_per_1k_input=0.001,
                cost_per_1k_output=0.001,
                context_window=128000,
                strengths=["chinese", "cheap"]
            ),
            "glm-4-flash": ModelInfo(
                name="glm-4-flash",
                provider=ProviderType.GLM,
                cost_per_1k_input=0.0001,
                cost_per_1k_output=0.0001,
                context_window=128000,
                strengths=["fast", "very cheap"]
            ),
        }
    
    def chat(self, messages: List[Dict], model: str = None, **kwargs) -> str:
        model = model or self.default_model
        return f"[GLM {model}] Response"
    
    def chat_stream(self, messages: List[Dict], model: str = None, **kwargs):
        model = model or self.default_model
        yield f"[GLM {model}] Stream response"
    
    def get_cost(self, input_tokens: int, output_tokens: int) -> float:
        model_info = self.models.get(self.default_model)
        if not model_info:
            return 0.0
        return (input_tokens / 1000) * model_info.cost_per_1k_input + \
               (output_tokens / 1000) * model_info.cost_per_1k_output


class ModelRouter:
    """
    模型路由器
    
    根據 Phase 和其他維度自動選擇最適合的 Provider + Model
    """
    
    # Phase → Provider/Model 映射
    PHASE_MODEL_MAP = {
        1: {"provider": ProviderType.ANTHROPIC, "model": "claude-sonnet-4", "reasoning": "長上下文、便宜"},
        2: {"provider": ProviderType.ANTHROPIC, "model": "claude-opus-4", "reasoning": "深度推理"},
        3: {"provider": ProviderType.ANTHROPIC, "model": "claude-sonnet-4", "reasoning": "代碼能力強、性價比高"},
        4: {"provider": ProviderType.OPENAI, "model": "gpt-4o", "reasoning": "多模態平衡"},
        5: {"provider": ProviderType.ANTHROPIC, "model": "claude-sonnet-4", "reasoning": "性價比高"},
        6: {"provider": ProviderType.ANTHROPIC, "model": "claude-opus-4", "reasoning": "深度分析"},
        7: {"provider": ProviderType.OPENAI, "model": "o3-mini", "reasoning": "推理+便宜"},
        8: {"provider": ProviderType.OPENAI, "model": "gpt-4o-mini", "reasoning": "簡單任務"},
    }
    
    PROVIDERS = {
        ProviderType.ANTHROPIC: AnthropicProvider,
        ProviderType.OPENAI: OpenAIProvider,
        ProviderType.GLM: GLMProvider,
    }
    
    def __init__(self):
        self._providers = {}
    
    def get_provider(self, provider_type: ProviderType) -> BaseProvider:
        """取得 Provider 實例"""
        if provider_type not in self._providers:
            self._providers[provider_type] = self.PROVIDERS[provider_type]()
        return self._providers[provider_type]
    
    def route(self, phase: int, task_hint: str = None, state_path: str = None) -> BaseProvider:
        """
        根據 Phase 路由到最適合的 Provider
        
        Args:
            phase: 當前 Phase (1-8)
            task_hint: 可選，任務提示（如 "coding", "review"）
            state_path: 可選，state.json 路徑
            
        Returns:
            BaseProvider: 最適合的 Provider 實例
        """
        # 如果有 task_hint，降級到更便宜的模型
        if task_hint in ("simple", "config", "docs"):
            return self.get_provider(ProviderType.OPENAI)
        
        choice = self.PHASE_MODEL_MAP.get(phase, self.PHASE_MODEL_MAP[3])
        return self.get_provider(choice["provider"])
    
    def route_with_info(self, phase: int, task_hint: str = None, state_path: str = None) -> Dict:
        """路由並返回詳細資訊"""
        choice = self.PHASE_MODEL_MAP.get(phase, self.PHASE_MODEL_MAP[3])
        provider = self.get_provider(choice["provider"])
        
        result = {
            "provider": choice["provider"].value,
            "model": choice["model"],
            "reasoning": choice["reasoning"],
            "cost_estimate": "$$"
        }
        
        # 如果有 state_path，讀取更多資訊
        if state_path:
            import json
            from pathlib import Path
            sp = Path(state_path)
            if sp.exists():
                try:
                    state = json.loads(sp.read_text())
                    result["step"] = state.get("current_step", "?")
                    result["module"] = state.get("current_module", "?")
                except:
                    pass
        
        return result


def main():
    """CLI 入口"""
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Model Router CLI")
    parser.add_argument("--phase", type=int, required=True, help="Phase number (1-8)")
    parser.add_argument("--provider", action="store_true", help="Show provider info")
    parser.add_argument("--state-path", help="Path to state.json")
    parser.add_argument("--task-hint", help="Task hint (simple/coding/review)")
    
    args = parser.parse_args()
    
    router = ModelRouter()
    
    if args.provider:
        info = router.route_with_info(args.phase, args.task_hint, args.state_path)
        print(json.dumps(info, indent=2))
    else:
        p = router.route(args.phase, args.task_hint, args.state_path)
        info = router.route_with_info(args.phase, args.task_hint, args.state_path)
        print(f"Phase {args.phase} → {info['provider']}/{info['model']}")
        print(f"Reasoning: {info['reasoning']}")


if __name__ == "__main__":
    main()
