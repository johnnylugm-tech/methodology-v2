"""
pytest configuration and fixtures for MCP tests.
"""
import sys
import os

# Add implement/ to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "implement"))

import pytest
from implement.mcp.saif_identity_middleware import (
    SAIFToken,
    SAIFMiddleware,
    JtiBlacklist,
    ScopeValidator,
)


@pytest.fixture
def signing_key():
    return b"test-signing-key-32-bytes-long!!!!"


@pytest.fixture
def verification_key():
    return b"test-signing-key-32-bytes-long!!!!"


@pytest.fixture
def valid_token(signing_key):
    return SAIFToken.create(
        iss="planner",
        sub="spec_critic",
        aud="harness-spec",
        scopes=["spec.read"],
        risk_tier="HOTL",
        ttl_seconds=600,
        one_time=False,
        signing_key=signing_key,
    )


@pytest.fixture
def expired_token(signing_key):
    return SAIFToken.create(
        iss="planner",
        sub="spec_critic",
        aud="harness-spec",
        scopes=["spec.read"],
        risk_tier="HOTL",
        ttl_seconds=-1,  # Already expired
        signing_key=signing_key,
    )


@pytest.fixture
def one_time_token(signing_key):
    return SAIFToken.create(
        iss="planner",
        sub="spec_critic",
        aud="harness-spec",
        scopes=["spec.read"],
        risk_tier="HOTL",
        ttl_seconds=600,
        one_time=True,
        signing_key=signing_key,
    )


@pytest.fixture
def blacklist():
    return JtiBlacklist()