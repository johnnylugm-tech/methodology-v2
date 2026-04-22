"""
pytest configuration for ml_langfuse tests.

Provides autouse fixtures that reset the client/config singletons
between tests to ensure full isolation.
"""

from __future__ import annotations

import os
import pytest

# Reset environment before importing ml_langfuse modules
@pytest.fixture(autouse=True)
def clean_env():
    """Clear Langfuse-related env vars before each test."""
    env_vars = [
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_HOST",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "OTEL_SERVICE_NAME",
        "LANGFUSE_TRACE_SAMPLING_RATE",
        "LANGFUSE_DASHBOARD_POLL_INTERVAL_SECONDS",
        "LANGFUSE_AUDIT_RETENTION_DAYS",
    ]
    original = {k: os.environ.get(k) for k in env_vars}
    for k in env_vars:
        os.environ.pop(k, None)
    yield
    # Restore
    for k, v in original.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset client/config singletons before each test."""
    # Import here to avoid import-order issues
    import ml_langfuse.client as _client_module
    import ml_langfuse.config as _config_module

    _client_module._client = None
    _client_module._initialized = False
    _config_module._config = None
    yield
    _client_module._client = None
    _client_module._initialized = False
    _config_module._config = None
