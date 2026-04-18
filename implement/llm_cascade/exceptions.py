"""
Custom exceptions for LLM Cascade.
"""


class CascadeError(Exception):
    """Base exception for all LLM Cascade errors."""

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class CascadeExhaustedError(CascadeError):
    """
    Raised when all models in the cascade chain have been tried
    and none produced an acceptable response.
    """

    def __init__(self, message: str = "All models in cascade chain exhausted", details: dict = None):
        super().__init__(message, details)


class ProviderRateLimitError(CascadeError):
    """
    Raised when a model provider returns a 429 rate limit response.
    The provider should be placed in cooldown.
    """

    def __init__(
        self,
        provider: str,
        message: str = None,
        retry_after_seconds: float = None,
        details: dict = None,
    ):
        self.provider = provider
        self.retry_after_seconds = retry_after_seconds
        msg = message or f"Rate limit exceeded for provider: {provider}"
        super().__init__(msg, details)


class ConfidenceThresholdError(CascadeError):
    """
    Raised when a model response confidence score is below
    the configured threshold, triggering escalation.
    """

    def __init__(
        self,
        confidence: float,
        threshold: float,
        model_name: str = None,
        details: dict = None,
    ):
        self.confidence = confidence
        self.threshold = threshold
        self.model_name = model_name
        msg = (
            f"Confidence {confidence:.3f} below threshold {threshold:.3f}"
            + (f" for model {model_name}" if model_name else "")
        )
        super().__init__(msg, details)


class LatencyBudgetExceededError(CascadeError):
    """
    Raised when the total cascade latency exceeds the configured budget.
    """

    def __init__(
        self,
        elapsed_ms: int,
        budget_ms: int,
        details: dict = None,
    ):
        self.elapsed_ms = elapsed_ms
        self.budget_ms = budget_ms
        msg = f"Latency budget exceeded: {elapsed_ms}ms > {budget_ms}ms budget"
        super().__init__(msg, details)


class CostBudgetExceededError(CascadeError):
    """
    Raised when the total cascade cost exceeds the configured cap.
    """

    def __init__(
        self,
        total_cost_usd: float,
        cap_usd: float,
        details: dict = None,
    ):
        self.total_cost_usd = total_cost_usd
        self.cap_usd = cap_usd
        msg = f"Cost budget exceeded: ${total_cost_usd:.4f} > ${cap_usd:.4f} cap"
        super().__init__(msg, details)


class CascadeConfigurationError(CascadeError):
    """
    Raised when the cascade configuration is invalid.
    """

    def __init__(self, message: str, details: dict = None):
        super().__init__(f"Configuration error: {message}", details)


class AllModelsExhaustedError(CascadeExhaustedError):
    """
    Raised when all models in the cascade chain have been tried
    and all attempts resulted in errors (not just low confidence).
    """

    def __init__(self, attempt_count: int = 0, details: dict = None):
        self.attempt_count = attempt_count
        msg = f"All {attempt_count} models exhausted due to errors"
        super().__init__(msg, details)
