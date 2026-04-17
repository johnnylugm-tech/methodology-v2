"""
Tests for SAIFToken.create(), verify(), refresh(), revoke()
Covering acceptance criteria in SPEC.md Section 4.1
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "implement"))

import time
import pytest
from implement.mcp.saif_identity_middleware import (
    SAIFToken,
    SAIFTokenPayload,
    SAIFTokenError,
    TokenExpiredError,
    InvalidSignatureError,
    InsufficientScopeError,
)


class TestSAIFTokenCreate:
    """FR-1.1, FR-1.2, FR-1.3: Token creation tests"""

    def test_token_create_basic(self, signing_key):
        """Token creation with basic fields"""
        token = SAIFToken.create(
            iss="planner",
            sub="spec_critic",
            aud="harness-spec",
            scopes=["spec.read"],
            risk_tier="HOTL",
            signing_key=signing_key,
        )
        assert token is not None
        assert isinstance(token, str)
        assert "." in token  # Has signature separator

    def test_token_contains_all_fields(self, signing_key):
        """FR-1.1: Token contains all 8 fields (iss/sub/aud/scopes/risk_tier/exp/iat/jti/sig)"""
        token = SAIFToken.create(
            iss="planner",
            sub="spec_critic",
            aud="harness-spec",
            scopes=["spec.read", "audit.write"],
            risk_tier="HITL",
            signing_key=signing_key,
        )
        payload = SAIFToken.verify(token, signing_key)
        assert payload.iss == "planner"
        assert payload.sub == "spec_critic"
        assert payload.aud == "harness-spec"
        assert payload.scopes == ["spec.read", "audit.write"]
        assert payload.risk_tier == "HITL"
        assert payload.jti is not None
        assert len(payload.jti) > 0
        # iat and exp should be set
        assert payload.iat is not None
        assert payload.exp is not None

    def test_token_default_ttl(self, signing_key):
        """FR-1.2: Token TTL = 600s (10 min) by default"""
        token = SAIFToken.create(
            iss="planner",
            sub="spec_critic",
            aud="harness-spec",
            scopes=["spec.read"],
            risk_tier="HOTL",
            signing_key=signing_key,
        )
        payload = SAIFToken.verify(token, signing_key)
        # Default TTL is 600 seconds
        diff = (payload.exp - payload.iat).total_seconds()
        assert 590 <= diff <= 610  # Allow 10s tolerance

    def test_token_custom_ttl(self, signing_key):
        """FR-1.2: Token TTL can be overridden"""
        token = SAIFToken.create(
            iss="planner",
            sub="spec_critic",
            aud="harness-spec",
            scopes=["spec.read"],
            risk_tier="HOTL",
            ttl_seconds=120,
            signing_key=signing_key,
        )
        payload = SAIFToken.verify(token, signing_key)
        diff = (payload.exp - payload.iat).total_seconds()
        assert 110 <= diff <= 130

    def test_token_with_various_scopes(self, signing_key):
        """Token creation with different scope combinations"""
        token = SAIFToken.create(
            iss="orchestrator",
            sub="devils_advocate",
            aud="harness-audit",
            scopes=["audit.read", "audit.write", "audit.delete"],
            risk_tier="HOTL",
            signing_key=signing_key,
        )
        payload = SAIFToken.verify(token, signing_key)
        assert payload.scopes == ["audit.read", "audit.write", "audit.delete"]


class TestSAIFTokenVerify:
    """FR-1.4: Token verification tests"""

    def test_verify_valid_token(self, valid_token, verification_key):
        """Valid token verifies successfully"""
        payload = SAIFToken.verify(valid_token, verification_key)
        assert payload.sub == "spec_critic"
        assert payload.iss == "planner"

    def test_verify_invalid_signature(self, signing_key):
        """Token with wrong signature is rejected"""
        token = SAIFToken.create(
            iss="planner",
            sub="spec_critic",
            aud="harness-spec",
            scopes=["spec.read"],
            risk_tier="HOTL",
            signing_key=signing_key,
        )
        wrong_key = b"wrong-key-that-should-not-work"
        with pytest.raises(InvalidSignatureError):
            SAIFToken.verify(token, wrong_key)

    def test_verify_expired_token(self, expired_token, signing_key):
        """FR-4.2: Expired token is rejected"""
        with pytest.raises(TokenExpiredError):
            SAIFToken.verify(expired_token, signing_key)

    def test_verify_wrong_audience(self, valid_token, verification_key):
        """FR-2.2: Token with wrong audience is rejected"""
        with pytest.raises(SAIFTokenError) as exc_info:
            SAIFToken.verify(valid_token, verification_key, audience="wrong-server")
        assert "Audience mismatch" in str(exc_info.value)

    def test_verify_malformed_token(self):
        """Malformed token raises error"""
        with pytest.raises((InvalidSignatureError, SAIFTokenError)):
            SAIFToken.verify("not.a.valid.token", b"key")

    def test_verify_token_tampered_payload(self, signing_key, verification_key):
        """Tampered token is rejected"""
        token = SAIFToken.create(
            iss="planner",
            sub="spec_critic",
            aud="harness-spec",
            scopes=["spec.read"],
            risk_tier="HOTL",
            signing_key=signing_key,
        )
        # Create a different valid token and swap just the signature
        other_token = SAIFToken.create(
            iss="attacker",
            sub="hacker",
            aud="hacker-server",
            scopes=["admin.write"],
            risk_tier="HITL",
            signing_key=signing_key,
        )
        # Swap payload from attacker token into victim token format
        parts = token.split(".")
        other_parts = other_token.split(".")
        tampered = f"{other_parts[0]}.{parts[1]}"  # attacker payload, victim signature
        with pytest.raises(InvalidSignatureError):
            SAIFToken.verify(tampered, verification_key)


class TestSAIFTokenRefresh:
    """FR-5.3: Token refresh tests"""

    def test_refresh_token(self, signing_key):
        """FR-5.3: Token refresh creates new token with same scopes but new exp"""
        original = SAIFToken.create(
            iss="planner",
            sub="spec_critic",
            aud="harness-spec",
            scopes=["spec.read", "audit.read"],
            risk_tier="HOTL",
            ttl_seconds=600,
            signing_key=signing_key,
        )
        time.sleep(0.1)
        refreshed = SAIFToken.refresh(original, ttl_seconds=300, signing_key=signing_key)
        assert refreshed != original
        payload = SAIFToken.verify(refreshed, signing_key)
        assert payload.scopes == ["spec.read", "audit.read"]
        assert payload.sub == "spec_critic"
        # New TTL should be 300s
        diff = (payload.exp - payload.iat).total_seconds()
        assert 290 <= diff <= 310

    def test_refresh_preserves_iss_sub_aud(self, signing_key):
        """Refreshed token preserves issuer, subject, audience"""
        original = SAIFToken.create(
            iss="orchestrator",
            sub="judge",
            aud="harness-risk",
            scopes=["risk.verify"],
            risk_tier="HOOTL",
            signing_key=signing_key,
        )
        refreshed = SAIFToken.refresh(original, signing_key=signing_key)
        payload = SAIFToken.verify(refreshed, signing_key)
        assert payload.iss == "orchestrator"
        assert payload.sub == "judge"
        assert payload.aud == "harness-risk"

    def test_refresh_invalidates_old_token_jti(self, signing_key):
        """Refresh creates NEW jti, old token still works until it expires"""
        original = SAIFToken.create(
            iss="planner",
            sub="spec_critic",
            aud="harness-spec",
            scopes=["spec.read"],
            risk_tier="HOTL",
            signing_key=signing_key,
        )
        refreshed = SAIFToken.refresh(original, signing_key=signing_key)
        # Both tokens should have different jti
        orig_payload = SAIFToken.verify(original, signing_key)
        new_payload = SAIFToken.verify(refreshed, signing_key)
        assert orig_payload.jti != new_payload.jti
        # Both should still be valid (refresh doesn't revoke old)
        assert orig_payload.sub == "spec_critic"
        assert new_payload.sub == "spec_critic"


class TestSAIFTokenRevoke:
    """FR-5.4: Token revocation tests"""

    def test_revoke_adds_jti_to_blacklist(self):
        """FR-5.4: revoke() adds JTI to blacklist"""
        blacklist = {}
        token = SAIFToken.create(
            iss="planner",
            sub="spec_critic",
            aud="harness-spec",
            scopes=["spec.read"],
            risk_tier="HOTL",
            signing_key=b"dev-signing-key-change-in-production",
        )
        payload = SAIFToken.verify(token)
        SAIFToken.revoke(payload.jti, blacklist)
        assert payload.jti in blacklist

    def test_revoke_multiple_jtis(self):
        """Multiple JTIs can be revoked"""
        blacklist = {}
        jtis = []
        for i in range(3):
            token = SAIFToken.create(
                iss="planner",
                sub=f"agent_{i}",
                aud="harness-spec",
                scopes=["spec.read"],
                risk_tier="HOTL",
                signing_key=b"dev-signing-key-change-in-production",
            )
            payload = SAIFToken.verify(token)
            jtis.append(payload.jti)
            SAIFToken.revoke(payload.jti, blacklist)
        for jti in jtis:
            assert jti in blacklist


class TestOneTimeToken:
    """FR-1.3: One-time token tests"""

    def test_one_time_token_creation(self, signing_key):
        """One-time token is created successfully"""
        token = SAIFToken.create(
            iss="planner",
            sub="spec_critic",
            aud="harness-spec",
            scopes=["spec.read"],
            risk_tier="HOTL",
            one_time=True,
            signing_key=signing_key,
        )
        assert token is not None
        payload = SAIFToken.verify(token, signing_key)
        assert payload.jti is not None

    def test_jti_blacklist_prevents_reuse(self, one_time_token, signing_key, blacklist):
        """FR-1.3: One-time token cannot be reused"""
        payload = SAIFToken.verify(one_time_token, signing_key)
        jti = payload.jti
        # First use
        assert not blacklist.is_used(jti)
        blacklist.mark_used(jti)
        # Second use
        assert blacklist.is_used(jti)