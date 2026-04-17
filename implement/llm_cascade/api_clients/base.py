"""
Base API Client — Abstract Interface for LLM Providers

All provider-specific clients (Anthropic, OpenAI, Google) inherit from APIClient.
Defines the interface that CascadeEngine uses to make model calls.

See ARCHITECTURE.md Section 9 for external API endpoints.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..models import ModelConfig


@dataclass
class APIResponse:
    """
    Normalized response from an LLM API call.

    All provider-specific responses are converted to this format
    before being returned to CascadeEngine.
    """

    content: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: int
    stop_reason: Optional[str] = None
    raw_response: Optional[Any] = None


@dataclass
class APIError:
    """
    Normalized error from an LLM API call.
    """

    error_type: str  # "rate_limit", "timeout", "server_error", "auth_error", "api_error"
    message: str
    http_status: Optional[int] = None
    retry_after_seconds: Optional[float] = None
    raw_error: Optional[Any] = None


class APIClient(ABC):
    """
    Abstract base class for LLM API clients.

    Implementations must provide:
      - complete(): Make a model completion call
      - classify_error(): Map provider-specific errors to APIClient error types
      - count_tokens(): Estimate token count for a string

    Thread-safety: Implementations should be thread-safe for concurrent use.
    """

    @abstractmethod
    async def complete(
        self,
        model: ModelConfig,
        prompt: str,
        timeout_seconds: float = 30.0,
    ) -> APIResponse:
        """
        Make a model completion call.

        Args:
            model:            ModelConfig with provider, name, and settings.
            prompt:           Input prompt.
            timeout_seconds:  Call timeout.

        Returns:
            APIResponse with content, token counts, and latency.

        Raises:
            RateLimitError:   On 429 responses.
            TimeoutError:     On timeout.
            APIError:         On other API errors.
        """
        ...

    @abstractmethod
    def classify_error(self, error: Exception, http_status: int = None) -> str:
        """
        Classify an exception into an APIClient error type.

        Args:
            error:       The exception that was raised.
            http_status: HTTP status code if available.

        Returns:
            One of: "rate_limit", "timeout", "server_error", "auth_error", "api_error"
        """
        ...

    def count_tokens(self, text: str) -> int:
        """
        Estimate token count for a string.

        Default implementation: simple character-based estimate.
        Providers with built-in tokenizers should override.

        Args:
            text: Input text.

        Returns:
            Estimated token count.
        """
        # Rough estimate: ~4 characters per token for English
        return max(1, len(text) // 4)


# ─────────────────────────────────────────────────────────────────────────────
# Shared Exceptions
# ─────────────────────────────────────────────────────────────────────────────


class RateLimitError(Exception):
    """Raised when provider returns a 429 rate limit response."""

    def __init__(self, message: str, retry_after_seconds: float = None, latency_ms: int = 0):
        super().__init__(message)
        self.retry_after_seconds = retry_after_seconds
        self.latency_ms = latency_ms


class TimeoutError(Exception):
    """Raised when an API call times out."""

    def __init__(self, message: str, timeout_seconds: float = None):
        super().__init__(message)
        self.timeout_seconds = timeout_seconds


class AuthError(Exception):
    """Raised when authentication fails (401, 403)."""

    def __init__(self, message: str):
        super().__init__(message)


class ServerError(Exception):
    """Raised when provider returns a 5xx error."""

    def __init__(self, message: str, http_status: int = None):
        super().__init__(message)
        self.http_status = http_status
