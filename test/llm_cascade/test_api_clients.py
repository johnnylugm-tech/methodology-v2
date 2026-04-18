"""API Client tests - stub coverage for llm_cascade API clients."""
import pytest
from implement.llm_cascade.api_clients.anthropic import AnthropicAPIClient
from implement.llm_cascade.api_clients.google import GoogleAPIClient
from implement.llm_cascade.api_clients.openai import OpenAIAPIClient


class TestAnthropicClient:
    """Test Anthropic API client initialization."""

    def test_client_init(self):
        """Test AnthropicAPIClient can be instantiated."""
        client = AnthropicAPIClient(api_key="test-key")
        assert client.api_key == "test-key"


class TestGoogleClient:
    """Test Google API client initialization."""

    def test_client_init(self):
        """Test GoogleAPIClient can be instantiated."""
        client = GoogleAPIClient(api_key="test-key")
        assert client.api_key == "test-key"


class TestOpenAIClient:
    """Test OpenAI API client initialization."""

    def test_client_init(self):
        """Test OpenAIAPIClient can be instantiated."""
        client = OpenAIAPIClient(api_key="test-key")
        assert client.api_key == "test-key"
