"""Tests for ml_langfuse.client — Langfuse client singleton."""

from __future__ import annotations

import os
import pytest

from ml_langfuse.client import (
    get_langfuse_client,
    reset_client,
    LangfuseClient,
    ConfigurationError,
)
from ml_langfuse.config import reset_config


class TestGetLangfuseClient:
    """Tests for the client singleton."""

    def test_client_init_cloud_mode(self):
        """Valid cloud credentials should initialize a client."""
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test_12345"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test_67890"
        reset_config()
        client = get_langfuse_client()
        assert client is not None
        assert isinstance(client, LangfuseClient)

    def test_client_init_self_hosted_mode(self):
        """Self-hosted mode with LANGFUSE_HOST should initialize a client."""
        os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
        os.environ.pop("LANGFUSE_SECRET_KEY", None)
        os.environ["LANGFUSE_HOST"] = "https://langfuse.example.com"
        reset_config()
        client = get_langfuse_client()
        assert client is not None
        assert isinstance(client, LangfuseClient)

    def test_client_init_missing_vars_raises(self):
        """Missing all credentials should raise ConfigurationError."""
        os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
        os.environ.pop("LANGFUSE_SECRET_KEY", None)
        os.environ.pop("LANGFUSE_HOST", None)
        reset_config()
        with pytest.raises(ConfigurationError):
            get_langfuse_client()

    def test_client_singleton_identity(self):
        """Two calls to get_langfuse_client() should return the same object."""
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"
        reset_config()
        reset_client()
        c1 = get_langfuse_client()
        c2 = get_langfuse_client()
        assert c1 is c2

    def test_client_get_tracer(self):
        """get_tracer() should return an OTel Tracer."""
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"
        reset_config()
        client = get_langfuse_client()
        tracer = client.get_tracer("test.scope")
        assert tracer is not None
        assert hasattr(tracer, "start_span")

    def test_client_flush(self):
        """flush() should not raise."""
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"
        reset_config()
        client = get_langfuse_client()
        # Should not raise even if no real Langfuse connection
        client.flush()

    def test_client_config_property(self):
        """config property should return the LangfuseConfig."""
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"
        reset_config()
        client = get_langfuse_client()
        assert client.config is not None
        assert client.config.public_key == "pk_test"
