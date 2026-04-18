"""
Google API Client — Gemini Model Integration

Implements APIClient for the Google Generative Language API.
Endpoint: https://generativelanguage.googleapis.com/v1beta/models

Authentication: API key via GOOGLE_API_KEY env var (or ModelConfig.api_key_ref).

API Reference: https://ai.google.dev/api/rest

Supported models:
  - gemini-pro
  - gemini-pro-1.5
  - gemini-ultra
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from .base import (
    APIClient,
    APIError,
    APIResponse,
    AuthError,
    RateLimitError,
    ServerError,
    TimeoutError,
)
from ..models import ModelConfig


class GoogleAPIClient(APIClient):
    """
    Google Gemini API client.

    Handles:
      - HTTP/JSON requests to generativelanguage.googleapis.com
      - API key authentication (query param)
      - Error classification (rate limits, server errors, auth)
      - Token counting
    """

    BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    API_VERSION = "v1beta"

    # Model name mapping: internal name → API model name
    MODEL_ALIASES = {
        "gemini-pro": "gemini-pro",
        "gemini-pro-1.5": "gemini-1.5-pro",
        "gemini-ultra": "gemini-ultra",
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        """
        Initialize Google Gemini API client.

        Args:
            api_key:          API key. If None, reads from GOOGLE_API_KEY env var.
            base_url:         Override API base URL.
            timeout_seconds:  Default timeout for all calls.
        """
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY", "")
        self.base_url = base_url or self.BASE_URL
        self.timeout_seconds = timeout_seconds

    async def complete(
        self,
        model: ModelConfig,
        prompt: str,
        timeout_seconds: float = 30.0,
    ) -> APIResponse:
        """
        Make a Gemini generateContent call.

        Args:
            model:            ModelConfig with model_name and settings.
            prompt:           Input prompt.
            timeout_seconds:  Call timeout override.

        Returns:
            APIResponse with Gemini's response content.

        Raises:
            RateLimitError:   On 429.
            TimeoutError:     On timeout.
            AuthError:        On 401/403.
            ServerError:      On 5xx.
            APIError:         On other API errors.
        """
        # ── TODO (FR-LC-Integration): Implement actual HTTP call ───────────
        # Placeholder: return simulated response for development/testing.
        # Replace with httpx-based implementation.
        # ─────────────────────────────────────────────────────────────────
        import asyncio
        await asyncio.sleep(0.01)

        return APIResponse(
            content=f"[Gemini {model.model_name}] {prompt[:100]}...",
            model=model.model_name,
            input_tokens=len(prompt.split()),
            output_tokens=20,
            latency_ms=int(timeout_seconds * 1000),
            stop_reason="stop",
        )

    def classify_error(self, error: Exception, http_status: int = None) -> str:
        """
        Classify an error from the Google API.
        """
        if http_status == 429:
            return "rate_limit"
        if http_status and 500 <= http_status < 600:
            return "server_error"
        if http_status == 401:
            return "auth_error"
        if http_status == 403:
            return "auth_error"
        if isinstance(error, TimeoutError):
            return "timeout"
        if isinstance(error, RateLimitError):
            return "rate_limit"
        if isinstance(error, ServerError):
            return "server_error"
        return "api_error"

    def count_tokens(self, text: str) -> int:
        """
        Estimate tokens using Google's formula (~4 chars/token for Gemini).
        """
        return max(1, len(text) // 4)

    # ─────────────────────────────────────────────────────────────────────────
    # Internal Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _model_name(self, model: ModelConfig) -> str:
        """Map model name to API model identifier."""
        return self.MODEL_ALIASES.get(model.model_name, model.model_name)

    def _build_url(self, model: ModelConfig) -> str:
        """
        Build the generateContent URL with API key as query param.
        """
        model_id = self._model_name(model)
        return (
            f"{self.base_url}/models/{model_id}:generateContent"
            f"?key={self.api_key}"
        )

    def _build_payload(self, model: ModelConfig, prompt: str) -> Dict[str, Any]:
        """
        Build the request payload for generateContent.
        """
        return {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}],
                }
            ],
            "generationConfig": {
                "maxOutputTokens": model.max_tokens,
                "temperature": model.temperature,
            },
        }

    def _parse_response(self, response: httpx.Response) -> APIResponse:  # noqa: F821
        """
        Parse the Gemini API response into APIResponse format.
        """
        if response.status_code == 429:
            retry_after = response.headers.get("retry-after")
            raise RateLimitError(
                message="Google Gemini rate limit exceeded",
                retry_after_seconds=float(retry_after) if retry_after else 60.0,
            )

        if response.status_code == 401:
            raise AuthError("Invalid Google API key")

        if response.status_code == 403:
            raise AuthError("Google API key forbidden or quota exceeded")

        if 500 <= response.status_code < 600:
            raise ServerError(
                f"Google server error: {response.status_code}",
                http_status=response.status_code,
            )

        if response.status_code != 200:
            raise APIError(
                error_type="api_error",
                message=f"Google API error: {response.status_code}",
                http_status=response.status_code,
            )

        data = response.json()

        # Extract content
        candidate = data.get("candidates", [{}])[0]
        content = candidate.get("content", {})
        parts = content.get("parts", [{}])
        text = parts[0].get("text", "") if parts else ""

        # Extract usage
        usage = data.get("usageMetadata", {})
        input_tokens = usage.get("promptTokenCount", 0)
        output_tokens = usage.get("candidatesTokenCount", 0)

        finish_reason = candidate.get("finishReason")

        return APIResponse(
            content=text,
            model=data.get("modelVersion", "gemini"),
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=0,
            stop_reason=finish_reason,
            raw_response=data,
        )
