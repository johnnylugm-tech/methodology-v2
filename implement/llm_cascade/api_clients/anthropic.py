"""
Anthropic API Client — Claude Model Integration

Implements APIClient for the Anthropic Claude API.
Endpoint: https://api.anthropic.com (v1/messages)

Authentication: Bearer token via ANTHROPIC_API_KEY env var (or ModelConfig.api_key_ref).

API Reference: https://docs.anthropic.com/en/api/messages

Supported models:
  - claude-opus-4
  - claude-sonnet-4
  - claude-3-opus
  - claude-3-sonnet
"""

from __future__ import annotations

import os
import time
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


class AnthropicAPIClient(APIClient):
    """
    Anthropic Claude API client.

    Handles:
      - HTTP/JSON requests to api.anthropic.com/v1/messages
      - Bearer token authentication
      - Streaming and non-streaming responses
      - Error classification (rate limits, server errors, auth)
      - Token counting via API response
    """

    BASE_URL = "https://api.anthropic.com"
    API_VERSION = "2023-06-01"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        """
        Initialize Anthropic API client.

        Args:
            api_key:          API key. If None, reads from ANTHROPIC_API_KEY env var.
            base_url:         Override API base URL (for proxies/testing).
            timeout_seconds:  Default timeout for all calls.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        self.base_url = base_url or self.BASE_URL
        self.timeout_seconds = timeout_seconds

    async def complete(
        self,
        model: ModelConfig,
        prompt: str,
        timeout_seconds: float = 30.0,
    ) -> APIResponse:
        """
        Make a Claude completion call via POST /v1/messages.

        Non-streaming by default. Pass stream=True to the model config
        for streaming responses.

        Args:
            model:            ModelConfig with model_name and settings.
            prompt:           Input prompt.
            timeout_seconds:  Call timeout override.

        Returns:
            APIResponse with Claude's response content.

        Raises:
            RateLimitError:   On 429.
            TimeoutError:     On timeout.
            AuthError:        On 401/403.
            ServerError:     On 5xx.
            APIError:         On other API errors.
        """
        # ── TODO (FR-LC-Integration): Implement actual HTTP call ───────────
        # Placeholder: return simulated response for development/testing.
        # Replace with:
        #   import httpx
        #   async with httpx.AsyncClient() as client:
        #       response = await client.post(
        #           f"{self.base_url}/v1/messages",
        #           headers=self._headers(model),
        #           json=self._build_payload(model, prompt),
        #           timeout=timeout_seconds,
        #       )
        #       return self._parse_response(response)
        # ─────────────────────────────────────────────────────────────────
        import asyncio
        await asyncio.sleep(0.01)  # Simulate network

        # Stub response
        return APIResponse(
            content=f"[Claude {model.model_name}] {prompt[:100]}...",
            model=model.model_name,
            input_tokens=len(prompt.split()),
            output_tokens=20,
            latency_ms=int(timeout_seconds * 1000),
            stop_reason="end_turn",
        )

    def classify_error(self, error: Exception, http_status: int = None) -> str:
        """
        Classify an error from the Anthropic API.
        """
        if http_status == 429:
            return "rate_limit"
        if http_status and 500 <= http_status < 600:
            return "server_error"
        if http_status in (401, 403):
            return "auth_error"
        if isinstance(error, TimeoutError):
            return "timeout"
        if isinstance(error, RateLimitError):
            return "rate_limit"
        if isinstance(error, ServerError):
            return "server_error"
        if isinstance(error, AuthError):
            return "auth_error"
        return "api_error"

    def count_tokens(self, text: str) -> int:
        """
        Estimate tokens using Anthropic's approximate formula.
        Claude tokenizes roughly at ~3.5 chars/token for English.
        """
        return max(1, len(text) // 4)

    # ─────────────────────────────────────────────────────────────────────────
    # Internal Helpers
    # ─────────────────────────────────────────────────────────────────────────

    def _headers(self, model: ModelConfig) -> Dict[str, str]:
        """Build request headers including auth."""
        return {
            "x-api-key": self.api_key or os.environ.get("ANTHROPIC_API_KEY", ""),
            "anthropic-version": self.API_VERSION,
            "content-type": "application/json",
        }

    def _build_payload(
        self,
        model: ModelConfig,
        prompt: str,
        stream: bool = False,
    ) -> Dict[str, Any]:
        """
        Build the request payload for /v1/messages.

        Anthropic uses a messages array format (not prompt string).
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
        Parse the Anthropic API response into APIResponse format.
        """
        if response.status_code == 429:
            retry_after = response.headers.get("retry-after")
            raise RateLimitError(
                message="Anthropic rate limit exceeded",
                retry_after_seconds=float(retry_after) if retry_after else 60.0,
            )

        if response.status_code == 401:
            raise AuthError("Invalid Anthropic API key")

        if response.status_code == 403:
            raise AuthError("Anthropic API key missing or forbidden")

        if 500 <= response.status_code < 600:
            raise ServerError(
                f"Anthropic server error: {response.status_code}",
                http_status=response.status_code,
            )

        if response.status_code != 200:
            raise APIError(
                error_type="api_error",
                message=f"Anthropic API error: {response.status_code}",
                http_status=response.status_code,
            )

        data = response.json()

        # Extract usage
        usage = data.get("usage", {})
        input_tokens = usage.get("input_tokens", 0)
        output_tokens = usage.get("output_tokens", 0)

        # Extract content
        content = data["content"][0]["text"] if data.get("content") else ""

        return APIResponse(
            content=content,
            model=data["model"],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=data.get("ms", 0),
            stop_reason=data.get("stop_reason"),
            raw_response=data,
        )
