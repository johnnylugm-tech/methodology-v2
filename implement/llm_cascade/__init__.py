"""
LLM Cascade — Multi-Model Routing with Automatic Fallback

A priority-ordered chain of LLM models. When the primary model fails,
times out, or returns low-confidence output, the system transparently
escalates to backup models until a successful response is obtained
or the cascade is exhausted.

Cost Philosophy: "Use expensive models only when necessary"
"""

from .enums import CascadeStateEnum, CascadeErrorType, ModelProvider, TriggerReason, ConfidenceComponent
from .models import (
    CascadeConfig,
    CascadeResult,
    ProviderHealth,
    ModelConfig,
    AttemptRecord,
    AttemptCost,
    ModelPricing,
    ModelCallResult,
    CascadeState,
    CascadeStats,
    LLMCascadeConfig,
)
from .exceptions import (
    CascadeError,
    CascadeExhaustedError,
    ProviderRateLimitError,
    ConfidenceThresholdError,
    LatencyBudgetExceededError,
    CascadeConfigurationError,
    CostBudgetExceededError,
    AllModelsExhaustedError,
)
from .confidence_scorer import ConfidenceScorer
from .health_tracker import HealthTracker
from .cost_tracker import CostTracker
from .cascade_engine import CascadeEngine
from .cascade_router import CascadeRouter
from .api import LLMCascade

__all__ = [
    # Enums
    "CascadeStateEnum",
    "CascadeErrorType",
    "ModelProvider",
    "TriggerReason",
    "ConfidenceComponent",
    # Models
    "CascadeConfig",
    "CascadeResult",
    "ProviderHealth",
    "ModelConfig",
    "AttemptRecord",
    "AttemptCost",
    "ModelPricing",
    "ModelCallResult",
    "CascadeState",
    "CascadeStats",
    "LLMCascadeConfig",
    # Exceptions
    "CascadeError",
    "CascadeExhaustedError",
    "ProviderRateLimitError",
    "ConfidenceThresholdError",
    "LatencyBudgetExceededError",
    "CascadeConfigurationError",
    "CostBudgetExceededError",
    "AllModelsExhaustedError",
    # Components
    "ConfidenceScorer",
    "HealthTracker",
    "CostTracker",
    "CascadeEngine",
    "CascadeRouter",
    "LLMCascade",
]

__version__ = "1.0.0"
