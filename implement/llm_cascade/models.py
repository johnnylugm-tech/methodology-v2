"""
Data models for LLM Cascade.

All dataclass definitions as specified in ARCHITECTURE.md.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple


# ─────────────────────────────────────────────────────────────────────────────
# Enums (inline to avoid circular imports at this level)
# ─────────────────────────────────────────────────────────────────────────────


class CascadeStateEnum(Enum):
    IDLE = auto()
    ROUTING = auto()
    MODEL_CALL = auto()
    CASCADE_CHECK = auto()
    EXHAUSTED = auto()


class CascadeErrorType(Enum):
    ALL_MODELS_FAILED = auto()
    ALL_MODELS_LOW_CONFIDENCE = auto()
    LATENCY_BUDGET_EXCEEDED = auto()
    COST_BUDGET_EXCEEDED = auto()
    NO_MODELS_AVAILABLE = auto()


class ModelProvider(Enum):
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    CUSTOM = "custom"


class TriggerReason(Enum):
    API_ERROR = "api_error"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server_error"
    MALFORMED_RESPONSE = "malformed_response"
    LOW_CONFIDENCE = "low_confidence"
    LATENCY_BUDGET_EXCEEDED = "latency_budget_exceeded"
    COST_BUDGET_EXCEEDED = "cost_budget_exceeded"
    PROVIDER_UNHEALTHY = "provider_unhealthy"
    ALL_MODELS_EXHAUSTED = "all_models_exhausted"


# ─────────────────────────────────────────────────────────────────────────────
# Model Pricing (defaults from ARCHITECTURE.md Section 2.3)
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_MODEL_PRICING: Dict[str, Tuple[float, float]] = {
    # (input_cost_per_1k, output_cost_per_1k)
    "claude-opus-4": (0.015, 0.075),
    "claude-sonnet-4": (0.003, 0.015),
    "gpt-4o": (0.005, 0.015),
    "gpt-4o-mini": (0.00015, 0.0006),
    "gemini-pro": (0.00125, 0.005),
}


# ─────────────────────────────────────────────────────────────────────────────
# Config Models
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ModelConfig:
    """
    Configuration for a single model in the cascade chain.

    Attributes:
        provider:        The LLM provider (ANTHROPIC, OPENAI, GOOGLE, CUSTOM)
        model_name:      Provider-specific model identifier
        api_key_ref:     Reference to key storage (env var name or vault path)
        endpoint:        Optional override endpoint URL
        max_tokens:      Maximum tokens in response
        temperature:     Sampling temperature (0.0–2.0)
        cost_per_1k_input:  Override default input pricing (USD)
        cost_per_1k_output: Override default output pricing (USD)
        priority:        Position priority (1 = highest / primary)
    """

    provider: ModelProvider
    model_name: str
    api_key_ref: str = "env"
    endpoint: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.7
    cost_per_1k_input: float = 0.0
    cost_per_1k_output: float = 0.0
    priority: int = 1

    def get_pricing(self) -> Tuple[float, float]:
        """
        Return (input, output) cost per 1K tokens.
        Uses override if set, otherwise looks up defaults.
        """
        if self.cost_per_1k_input > 0 or self.cost_per_1k_output > 0:
            return (self.cost_per_1k_input, self.cost_per_1k_output)
        return DEFAULT_MODEL_PRICING.get(
            self.model_name.lower(), (0.0, 0.0)
        )

    @classmethod
    def default_chain(cls) -> List["ModelConfig"]:
        """
        Return the default cascade chain as defined in ARCHITECTURE.md:
        Claude Opus → Claude Sonnet → GPT-4o → GPT-4o-mini → Gemini-Pro
        """
        return [
            cls(provider=ModelProvider.ANTHROPIC, model_name="claude-opus-4", priority=1),
            cls(provider=ModelProvider.ANTHROPIC, model_name="claude-sonnet-4", priority=2),
            cls(provider=ModelProvider.OPENAI, model_name="gpt-4o", priority=3),
            cls(provider=ModelProvider.OPENAI, model_name="gpt-4o-mini", priority=4),
            cls(provider=ModelProvider.GOOGLE, model_name="gemini-pro", priority=5),
        ]


@dataclass
class CascadeConfig:
    """
    Configuration for a single cascade routing request.

    Attributes:
        chain:                    Ordered list of models to try
        latency_budget_ms:        Maximum total cascade time (ms)
        cost_cap_usd:             Maximum cost per request (USD)
        confidence_threshold:     Minimum acceptable confidence score (0.0–1.0)
        timeout_per_call_ms:      Maximum wait per individual model call (ms)
        rate_limit_cooldown_seconds: Cooldown period after a 429 response (s)
    """

    chain: List[ModelConfig]
    latency_budget_ms: int = 10000
    cost_cap_usd: float = 0.50
    confidence_threshold: float = 0.7
    timeout_per_call_ms: int = 5000
    rate_limit_cooldown_seconds: float = 60.0

    def validate(self) -> None:
        """Validate configuration. Raises ValueError on invalid state."""
        if not self.chain:
            raise ValueError("cascade chain cannot be empty")
        if self.confidence_threshold < 0 or self.confidence_threshold > 1:
            raise ValueError("confidence_threshold must be between 0 and 1")
        if self.cost_cap_usd <= 0:
            raise ValueError("cost_cap_usd must be positive")
        if self.latency_budget_ms <= 0:
            raise ValueError("latency_budget_ms must be positive")
        if self.timeout_per_call_ms <= 0:
            raise ValueError("timeout_per_call_ms must be positive")


# ─────────────────────────────────────────────────────────────────────────────
# Result Models
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class AttemptRecord:
    """
    Record of a single model attempt within a cascade.

    Attributes:
        model_name:       The model that was called
        provider:         Provider name (e.g., "anthropic", "openai")
        latency_ms:      Time taken for this attempt (ms)
        success:          Whether the attempt succeeded
        error_type:       Error classification if failed
        http_status:      HTTP status code if applicable
        confidence:       Confidence score of the response (0.0–1.0)
        cost_usd:         Cost incurred for this attempt (USD)
        input_tokens:    Input tokens consumed
        output_tokens:   Output tokens consumed
        escalated_reason: Why this attempt escalated to the next model
        timestamp:        When this attempt occurred
    """

    model_name: str
    provider: str
    latency_ms: int
    success: bool
    error_type: Optional[str] = None
    http_status: Optional[int] = None
    confidence: Optional[float] = None
    cost_usd: float = 0.0
    input_tokens: int = 0
    output_tokens: int = 0
    escalated_reason: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    response: Optional[str] = None  # The response text from this attempt

    def to_dict(self) -> Dict[str, Any]:
        return {
            "model_name": self.model_name,
            "provider": self.provider,
            "latency_ms": self.latency_ms,
            "success": self.success,
            "error_type": self.error_type,
            "http_status": self.http_status,
            "confidence": self.confidence,
            "cost_usd": self.cost_usd,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "escalated_reason": self.escalated_reason,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class CascadeResult:
    """
    Result of a full cascade routing operation.

    Attributes:
        response:          Final response text (None if cascade exhausted)
        model_used:         Model name that produced the response
        cascade_depth:      Index in chain that succeeded (0 = primary)
        total_cost_usd:    Total cost incurred (USD)
        latency_ms:        Total elapsed time (ms)
        confidence:        Confidence score of the response (0.0–1.0)
        attempt_history:   Per-model attempt records
        error:             Error message if cascade exhausted
        cascade_failure:   True if all models failed
        cascade_exhausted: True if chain was fully attempted
    """

    response: Optional[str]
    model_used: Optional[str]
    cascade_depth: int
    total_cost_usd: float
    latency_ms: int
    confidence: float
    attempt_history: List[AttemptRecord]
    error: Optional[str] = None
    cascade_failure: bool = False
    cascade_exhausted: bool = False

    @property
    def success(self) -> bool:
        """Return True if cascade produced a valid response."""
        return not self.cascade_failure and self.response is not None

    @property
    def cascade_hit(self) -> bool:
        """Return True if a fallback model was used (depth > 0)."""
        return self.cascade_depth > 0 and self.success

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response": self.response,
            "model_used": self.model_used,
            "cascade_depth": self.cascade_depth,
            "total_cost_usd": self.total_cost_usd,
            "latency_ms": self.latency_ms,
            "confidence": self.confidence,
            "attempt_history": [r.to_dict() for r in self.attempt_history],
            "error": self.error,
            "cascade_failure": self.cascade_failure,
            "cascade_exhausted": self.cascade_exhausted,
            "success": self.success,
            "cascade_hit": self.cascade_hit,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Provider Health
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ProviderHealth:
    """
    Rolling health metrics for a single model provider.

    Attributes:
        provider:           Provider name
        success_rate:       Rolling 24h success rate (0.0–1.0)
        median_latency_ms: Rolling median latency (ms)
        error_types:        Count of errors by type
        rate_limit_count:   429 responses in rolling window
        last_checked:       Timestamp of last health check
        is_in_cooldown:     Whether provider is currently rate-limited
        cooldown_ends_at:   When the cooldown period ends
    """

    provider: str
    success_rate: float = 1.0
    median_latency_ms: int = 0
    error_types: Dict[str, int] = field(default_factory=dict)
    rate_limit_count: int = 0
    last_checked: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    is_in_cooldown: bool = False
    cooldown_ends_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "success_rate": self.success_rate,
            "median_latency_ms": self.median_latency_ms,
            "error_types": self.error_types,
            "rate_limit_count": self.rate_limit_count,
            "last_checked": self.last_checked.isoformat(),
            "is_in_cooldown": self.is_in_cooldown,
            "cooldown_ends_at": self.cooldown_ends_at.isoformat() if self.cooldown_ends_at else None,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Cost Tracking
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class AttemptCost:
    """
    Cost record for a single model attempt.
    """

    model_name: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class ModelPricing:
    """
    Token pricing for a specific model.
    """

    provider: str
    model_name: str
    cost_per_1k_input: float
    cost_per_1k_output: float


# ─────────────────────────────────────────────────────────────────────────────
# Cascade Engine Internal Models
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class ModelCallResult:
    """
    Result of a single model API call (internal to CascadeEngine).
    """

    success: bool
    response: Optional[str] = None
    error_type: Optional[str] = None
    http_status: Optional[int] = None
    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    raw_error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Cascade State (internal)
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class CascadeState:
    """
    Internal state for cascade execution.
    Tracks progress through the cascade chain.
    """

    state: CascadeStateEnum = CascadeStateEnum.IDLE
    current_depth: int = 0
    attempt_history: List[AttemptRecord] = field(default_factory=list)
    total_latency_ms: int = 0
    total_cost_usd: float = 0.0
    best_response: Optional[str] = None
    best_confidence: float = 0.0
    error: Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# Statistics
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class CascadeStats:
    """
    Aggregate statistics across cascade requests.
    Used for monitoring and reporting.
    """

    total_requests: int = 0
    successful_requests: int = 0
    cascade_hit_count: int = 0
    cascade_hit_rate: float = 0.0
    average_cascade_depth: float = 0.0
    average_latency_ms: int = 0
    average_cost_usd: float = 0.0
    total_cost_usd: float = 0.0
    provider_usage: Dict[str, int] = field(default_factory=dict)
    provider_success_rate: Dict[str, float] = field(default_factory=dict)
    cost_reduction_vs_baseline_pct: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "cascade_hit_count": self.cascade_hit_count,
            "cascade_hit_rate": self.cascade_hit_rate,
            "average_cascade_depth": self.average_cascade_depth,
            "average_latency_ms": self.average_latency_ms,
            "average_cost_usd": self.average_cost_usd,
            "total_cost_usd": self.total_cost_usd,
            "provider_usage": self.provider_usage,
            "provider_success_rate": self.provider_success_rate,
            "cost_reduction_vs_baseline_pct": self.cost_reduction_vs_baseline_pct,
        }


# ─────────────────────────────────────────────────────────────────────────────
# Global Configuration
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class LLMCascadeConfig:
    """
    Global LLM Cascade configuration.
    Applied at the LLMCascade facade level.
    """

    default_chain: List[ModelConfig]
    default_latency_budget_ms: int = 10000
    default_cost_cap_usd: float = 0.50
    default_confidence_threshold: float = 0.7
    default_timeout_per_call_ms: int = 5000
    health_window_seconds: int = 86400
    rate_limit_cooldown_seconds: float = 60.0
    min_provider_success_rate: float = 0.8
    enable_request_isolation: bool = True
