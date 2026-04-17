"""
OpenAI API Client — GPT Model Integration

Implements APIClient for the OpenAI Chat Completions API.
Endpoint: https://api.openai.com/v1/chat/completions

Authentication: Bearer token via OPENAI_API_KEY env var (or ModelConfig.api_key_ref).

API Reference: https://platform.openai.com/docs/api-reference/chat

Supported models:
  - gpt-4o
  - gpt-4o-mini
  - gpt-4-turbo
  - gpt-3.5-turbo
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


class OpenAIAPIClient(APIClient):
    """
    OpenAI Chat Completions API client.

    Handles:
      - HTTP/JSON requests to api.openai.com/v1/chat/completions
      - Bearer token authentication
      - Streaming and non-streaming responses
      - Error classification (rate limits, server errors, auth)
      - Token counting via tiktoken or API response
    """

    BASE_URL = "https://api.openai.com"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: float = 30.0,
        organization: Optional[str] = None,
    ) -> None:
        """
        Initialize OpenAI API client.

        Args:
            api_key:          API key. If None, reads from OPENAI_API_KEY env var.
            base_url:         Override API base URL (for proxies/testing).
            timeout_seconds:  Default timeout for all calls.
            organization:     OpenAI organization ID (optional).
        """
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self.base_url = base_url or self.BASE_URL
        self.timeout_seconds = timeout_seconds
        self.organization = organization or os.environ.get("OPENAI_ORG_ID")

    async def complete(
        self,
        model: ModelConfig,
        prompt: str,
        timeout_seconds: float = 30.0,
    ) -> APIResponse:
        """
        Make an OpenAI Chat Completions call via POST /v1/chat/completions.

        Args:
            model:            ModelConfig with model_name and settings.
            prompt:           Input prompt (converted to messages format).
            timeout_seconds:  Call timeout override.

        Returns:
            APIResponse with GPT's response content.

        Raises:
            RateLimitError:   On 429.
            TimeoutError:     On timeout.
            AuthError:        On 401/403.
            ServerError:      On 5xx.
            APIError:         On other API errors.
        """
        # ── TODO (FR-LC-Integration): Implement actual HTTP call ───────────
        # Placeholder: return simulated response for development/testing.
        # Replace with httpx-based implementation (see anthropic.py for pattern).
        # ─────────────────────────────────────────────────────────────────
        import asyncio
        await asyncio.sleep(0.01)

        return APIResponse(
            content=f"[GPT {model.model_name}] {prompt[:100]}...",
            model=model.model_name,
            input_tokens=len(prompt.split()),
            output_tokens=20,
            latency_ms=int(timeout_seconds * 1000),
            stop_reason="stop",
        )

    def classify_error(self, error: Exception, http_status: int = None) -> str:
        """
        Classify an error from the OpenAI API.
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
        Estimate tokens using OpenAI's approximate formula (~4 chars/token).
        """
        return max(1, len(text) // 4)

    # ─────────────────────────────────────────────────────────────────────────
    # Internal Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _headers(self) -> Dict[str, str]:
        """Build request headers including auth."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "content-type": "application/json",
        }
        if self.organization:
            headers["OpenAI-Organization"] = self.organization
        return headers

    def _build_payload(
        self,
        model: ModelConfig,
        prompt: str,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Build the request payload for /v1/chat/completions.
        """
        return {
            "model": model.model_name,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": model.max_tokens,
            "temperature": model.temperature,
            "stream": stream,
        }

    def _parse_response(self, response: httpx.Response) -> APIResponse:
        """
        Parse the OpenAI API response into APIResponse format.
        """
        if response.status_code == 429:
            retry_after = response.headers.get("retry-after")
            raise RateLimitError(
                message="OpenAI rate limit exceeded",
                retry_after_seconds=float(retry_after) if retry_after else 60.0,
            )

        if response.status_code == 401:
            raise AuthError("Invalid OpenAI API key")

        if response.status_code == 403:
            raise AuthError("OpenAI API key forbidden")

        if 500 <= response.status_code < 600:
            raise ServerError(
                f"OpenAI server error: {response.status_code}",
                http_status=response.status_code,
            )

        if response.status_code != 200:
            raise APIError(
                error_type="api_error",
                message=f"OpenAI API error: {response.status_code}",
                http_status=response.status_code,
            )

        data = response.json()
        choice = data["choices"][0]
        message = choice["message"]

        # Extract usage
        usage = data.get("usage", {})
        input_tokens = usage.get("prompt_tokens", 0)
        output_tokens = usage.get("completion_tokens", 0)

        return APIResponse(
            content=message.get("content", ""),
            model=data["model"],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=data.get("ms", 0),
            stop_reason=choice.get("finish_reason"),
            raw_response=data,
        )
