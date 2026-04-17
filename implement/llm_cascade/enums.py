"""
Enumerations for LLM Cascade.
"""

from enum import Enum, auto
from typing import Optional


class CascadeStateEnum(Enum):
    """
    States in the cascade state machine.

    IDLE        → No active request; monitoring provider health
    ROUTING     → Selecting next model from chain
    MODEL_CALL  → Active HTTP call to selected model provider
    CASCADE_CHECK → Evaluating response quality and budget
    EXHAUSTED   → All models tried; preparing error response
    """

    IDLE = auto()
    ROUTING = auto()
    MODEL_CALL = auto()
    CASCADE_CHECK = auto()
    EXHAUSTED = auto()


class CascadeErrorType(Enum):
    """
    Types of cascade-level errors.
    """

    ALL_MODELS_FAILED = auto()
    ALL_MODELS_LOW_CONFIDENCE = auto()
    LATENCY_BUDGET_EXCEEDED = auto()
    COST_BUDGET_EXCEEDED = auto()
    NO_MODELS_AVAILABLE = auto()


class ModelProvider(Enum):
    """
    Supported LLM providers.
    """

    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    CUSTOM = "custom"

    @classmethod
    def from_string(cls, value: str) -> "ModelProvider":
        """Parse provider from string (case-insensitive)."""
        mapping = {p.value: p for p in cls}
        lower = value.lower()
        if lower in mapping:
            return mapping[lower]
        for p in cls:
            if p.name.lower() == lower:
                return p
        return cls.CUSTOM


class TriggerReason(Enum):
    """
    Reasons why a model response triggered escalation to the next model.
    Used in AttemptRecord.escalated_reason.
    """

    # API-level failures
    API_ERROR = "api_error"
    TIMEOUT = "timeout"
    RATE_LIMIT = "rate_limit"
    SERVER_ERROR = "server_error"
    MALFORMED_RESPONSE = "malformed_response"

    # Quality failures
    LOW_CONFIDENCE = "low_confidence"
    LATENCY_BUDGET_EXCEEDED = "latency_budget_exceeded"
    COST_BUDGET_EXCEEDED = "cost_budget_exceeded"

    # Provider health
    PROVIDER_UNHEALTHY = "provider_unhealthy"

    # Cascade exhaustion
    ALL_MODELS_EXHAUSTED = "all_models_exhausted"

    @classmethod
    def from_http_status(cls, status: int) -> "TriggerReason":
        """Infer trigger reason from HTTP status code."""
        if status == 429:
            return cls.RATE_LIMIT
        if 500 <= status < 600:
            return cls.SERVER_ERROR
        return cls.API_ERROR

    @classmethod
    def from_error_type(cls, error_type: Optional[str]) -> "TriggerReason":
        """Map error_type string to TriggerReason."""
        if error_type is None:
            return cls.MALFORMED_RESPONSE
        lower = error_type.lower()
        if "rate_limit" in lower or "429" in lower:
            return cls.RATE_LIMIT
        if "timeout" in lower:
            return cls.TIMEOUT
        if "server_error" in lower:
            return cls.SERVER_ERROR
        try:
            last_part = lower.split("_")[-1]
            if last_part.isdigit() and 500 <= int(last_part) < 600:
                return cls.SERVER_ERROR
        except (ValueError, IndexError):
            pass
        if "api_error" in lower:
            return cls.API_ERROR
        return cls.MALFORMED_RESPONSE


class ConfidenceComponent(Enum):
    """
    Components of the confidence scoring algorithm.
    Each component contributes a weighted score to the overall confidence.
    """

    ENTROPY = "entropy"           # Token entropy — randomness signal; weight 0.30
    REPETITION = "repetition"     # Repetition ratio — stuck-in-loop signal; weight 0.25
    LENGTH = "length"            # Length sanity — truncated/suspicious-length signal; weight 0.20
    PARSE_VALIDITY = "parse_validity"  # Structural validity — malformed output signal; weight 0.25

    @property
    def weight(self) -> float:
        """Return the weight for this component as defined in ARCHITECTURE.md."""
        weights = {
            ConfidenceComponent.ENTROPY: 0.30,
            ConfidenceComponent.REPETITION: 0.25,
            ConfidenceComponent.LENGTH: 0.20,
            ConfidenceComponent.PARSE_VALIDITY: 0.25,
        }
        return weights[self]
