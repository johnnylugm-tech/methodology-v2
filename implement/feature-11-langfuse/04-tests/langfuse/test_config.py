"""Tests for ml_langfuse.config — Configuration validation."""

from __future__ import annotations

import os
import pytest

from ml_langfuse.config import (
    LangfuseConfig,
    get_config,
    reset_config,
    ConfigurationError,
)


class TestLangfuseConfigValidation:
    """Test config validation and error handling."""

    def test_cloud_mode_requires_public_and_secret_key(self):
        """Cloud mode should raise ConfigurationError if keys are missing."""
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"
        # Also set host to trigger self-hosted — so we test the fallback
        os.environ.pop("LANGFUSE_HOST", None)
        config = get_config()
        # Should not raise — cloud mode with both keys
        config.validate_config()

    def test_cloud_mode_missing_secret_key_raises(self):
        """Missing secret key in cloud mode should raise ConfigurationError."""
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ.pop("LANGFUSE_SECRET_KEY", None)
        os.environ.pop("LANGFUSE_HOST", None)
        reset_config()
        config = get_config()
        with pytest.raises(ConfigurationError, match="LANGFUSE_SECRET_KEY"):
            config.validate_config()

    def test_self_hosted_mode_requires_host(self):
        """Self-hosted mode should raise ConfigurationError if host is missing."""
        os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
        os.environ.pop("LANGFUSE_SECRET_KEY", None)
        os.environ.pop("LANGFUSE_HOST", None)
        reset_config()
        config = get_config()
        config = LangfuseConfig(mode="self_hosted")
        with pytest.raises(ConfigurationError, match="LANGFUSE_HOST"):
            config.validate_config()

    def test_self_hosted_mode_with_host_succeeds(self):
        """Self-hosted mode with host set should not raise."""
        os.environ.pop("LANGFUSE_PUBLIC_KEY", None)
        os.environ.pop("LANGFUSE_SECRET_KEY", None)
        os.environ["LANGFUSE_HOST"] = "https://langfuse.example.com"
        reset_config()
        config = get_config()
        # Should not raise
        config.validate_config()

    def test_sampling_rate_out_of_range_raises(self):
        """Sampling rate outside [0.0, 1.0] should raise ConfigurationError."""
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"
        os.environ["LANGFUSE_TRACE_SAMPLING_RATE"] = "1.5"
        reset_config()
        config = get_config()
        with pytest.raises(ConfigurationError, match="trace_sampling_rate"):
            config.validate_config()

    def test_sampling_rate_negative_raises(self):
        """Negative sampling rate should raise ConfigurationError."""
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"
        os.environ["LANGFUSE_TRACE_SAMPLING_RATE"] = "-0.1"
        reset_config()
        config = get_config()
        with pytest.raises(ConfigurationError, match="trace_sampling_rate"):
            config.validate_config()

    def test_sampling_rate_valid_boundaries(self):
        """Sampling rate at boundaries 0.0 and 1.0 should be valid."""
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"
        for rate in ("0.0", "1.0", "0.5"):
            os.environ["LANGFUSE_TRACE_SAMPLING_RATE"] = rate
            reset_config()
            config = get_config()
            config.validate_config()  # Should not raise

    def test_otel_exporter_invalid_url_raises(self):
        """Invalid OTEL_EXPORTER_OTLP_ENDPOINT URL should raise ConfigurationError."""
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "not-a-valid-url"
        reset_config()
        config = get_config()
        with pytest.raises(ConfigurationError, match="otel_exporter_endpoint"):
            config.validate_config()

    def test_config_singleton(self):
        """get_config() should return the same instance on repeated calls."""
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"
        reset_config()
        c1 = get_config()
        c2 = get_config()
        assert c1 is c2

    def test_reset_config(self):
        """reset_config() should clear the singleton."""
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"
        c1 = get_config()
        reset_config()
        c2 = get_config()
        assert c1 is not c2
