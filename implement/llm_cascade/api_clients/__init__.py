"""
API Clients — Provider-Specific LLM API Integrations

Provides provider-specific API clients for:
  - Anthropic (Claude)
  - OpenAI (GPT)
  - Google (Gemini)

Each client implements the APIClient interface and handles:
  - Authentication (API key injection)
  - Request formatting
  - Response parsing
  - Error classification
  - Token counting

See ARCHITECTURE.md Section 8.3 for file structure.
"""

from .base import APIClient
from .anthropic import AnthropicAPIClient
from .openai import OpenAIAPIClient
from .google import GoogleAPIClient

__all__ = [
    "APIClient",
    "AnthropicAPIClient",
    "OpenAIAPIClient",
    "GoogleAPIClient",
]
