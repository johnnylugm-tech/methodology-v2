"""
SAIF 2.0 Identity Propagation Middleware
"""
import base64
import hashlib
import hmac
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable, Optional

import yaml


class SAIFTokenError(Exception):
    """Base exception for SAIF token errors"""
    pass


class TokenExpiredError(SAIFTokenError):
    pass


class InvalidSignatureError(SAIFTokenError):
    pass


class InsufficientScopeError(SAIFTokenError):
    def __init__(self, required: list, actual: list):
        self.required = required
        self.actual = actual
        super().__init__(f"Required scopes {required}, got {actual}")


@dataclass
class SAIFTokenPayload:
    iss: str          # Issuer
    sub: str          # Subject
    aud: str          # Audience
    scopes: list[str]  # Permissions
    risk_tier: str    # HITL | HOTL | HOOTL
    exp: datetime     # Expiry
    iat: datetime     # Issued at
    jti: str          # JWT ID
    algorithm: str = "Ed25519"
    
    def to_dict(self) -> dict:
        return {
            "iss": self.iss,
            "sub": self.sub,
            "aud": self.aud,
            "scopes": self.scopes,
            "risk_tier": self.risk_tier,
            "exp": self.exp.isoformat(),
            "iat": self.iat.isoformat(),
            "jti": self.jti,
            "algorithm": self.algorithm,
        }


class SAIFToken:
    """SAIF Token creation and verification"""
    
    DEFAULT_TTL_SECONDS = 600  # 10 minutes
    
    @staticmethod
    def create(
        iss: str,
        sub: str,
        aud: str,
        scopes: list[str],
        risk_tier: str = "HOTL",
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        one_time: bool = False,
        algorithm: str = "Ed25519",
        signing_key: Optional[bytes] = None,
    ) -> str:
        """
        Create a SAIF token. Returns base64-encoded token string.
        """
        now = datetime.now(timezone.utc)
        exp = now + timedelta(seconds=ttl_seconds)
        jti = str(uuid.uuid4())
        
        payload = SAIFTokenPayload(
            iss=iss,
            sub=sub,
            aud=aud,
            scopes=scopes,
            risk_tier=risk_tier,
            exp=exp,
            iat=now,
            jti=jti,
            algorithm=algorithm,
        )
        
        # Use HMAC-SHA256 for simplicity (Ed25519 requires specific libs)
        if signing_key is None:
            signing_key = b"dev-signing-key-change-in-production"
        
        payload_json = json.dumps(payload.to_dict(), sort_keys=True)
        payload_bytes = payload_json.encode("utf-8")
        
        signature = hmac.new(signing_key, payload_bytes, hashlib.sha256).digest()
        signature_b64 = base64.urlsafe_b64encode(signature).decode()
        
        # Combine payload and signature
        token_data = base64.urlsafe_b64encode(payload_bytes).decode()
        return f"{token_data}.{signature_b64}"
    
    @staticmethod
    def verify(
        token: str,
        verification_key: Optional[bytes] = None,
        audience: Optional[str] = None,
    ) -> SAIFTokenPayload:
        """
        Verify and decode a SAIF token. Returns payload if valid.
        Raises SAIFTokenError if invalid.
        """
        if verification_key is None:
            verification_key = b"dev-signing-key-change-in-production"
        
        try:
            token_part, signature_part = token.split(".")
            payload_bytes = base64.urlsafe_b64decode(token_part)
            expected_signature = base64.urlsafe_b64decode(signature_part)
        except Exception as e:
            raise InvalidSignatureError(f"Token format error: {e}")
        
        # Verify signature
        expected_sig = hmac.new(verification_key, payload_bytes, hashlib.sha256).digest()
        if not hmac.compare_digest(expected_signature, expected_sig):
            raise InvalidSignatureError("Signature mismatch")
        
        # Decode payload
        payload_dict = json.loads(payload_bytes)
        
        # Check expiry
        exp = datetime.fromisoformat(payload_dict["exp"])
        if exp.tzinfo is None:
            exp = exp.replace(tzinfo=timezone.utc)
        if datetime.now(timezone.utc) > exp:
            raise TokenExpiredError(f"Token expired at {exp}")
        
        # Check audience if specified
        if audience and payload_dict["aud"] != audience:
            raise SAIFTokenError(f"Audience mismatch: expected {audience}, got {payload_dict['aud']}")
        
        return SAIFTokenPayload(
            iss=payload_dict["iss"],
            sub=payload_dict["sub"],
            aud=payload_dict["aud"],
            scopes=payload_dict["scopes"],
            risk_tier=payload_dict["risk_tier"],
            exp=exp,
            iat=datetime.fromisoformat(payload_dict["iat"]),
            jti=payload_dict["jti"],
            algorithm=payload_dict.get("algorithm", "Ed25519"),
        )
    
    @staticmethod
    def refresh(
        old_token: str,
        ttl_seconds: int = DEFAULT_TTL_SECONDS,
        signing_key: Optional[bytes] = None,
    ) -> str:
        """Create a new token with refreshed expiry, same claims"""
        payload = SAIFToken.verify(old_token, signing_key)
        return SAIFToken.create(
            iss=payload.iss,
            sub=payload.sub,
            aud=payload.aud,
            scopes=payload.scopes,
            risk_tier=payload.risk_tier,
            ttl_seconds=ttl_seconds,
            one_time=False,
            algorithm=payload.algorithm,
            signing_key=signing_key,
        )
    
    @staticmethod
    def revoke(jti: str, blacklist: Optional[dict] = None) -> None:
        """Add JTI to blacklist (caller's responsibility to persist)"""
        if blacklist is None:
            blacklist = {}
        blacklist[jti] = True


class ScopeValidator:
    """Validates agent scopes against Agents.md configuration"""
    
    def __init__(self, agents_dir: str):
        self.agents_dir = agents_dir
        self._cache: dict = {}
        self._cache_time: float = 0
        self._cache_ttl: float = 60  # seconds
    
    def _load_agents_config(self, agent_id: str) -> dict:
        """Load Agents.md for a specific agent"""
        import os
        cache_key = f"{agent_id}"
        now = time.time()
        
        if cache_key in self._cache and (now - self._cache_time) < self._cache_ttl:
            return self._cache[cache_key]
        
        # Try to load from agents directory
        agent_file = os.path.join(self.agents_dir, agent_id, "Agents.md")
        if not os.path.exists(agent_file):
            # Try parent directory
            agent_file = os.path.join(self.agents_dir, f"{agent_id}.yaml")
        
        # For demo purposes, return permissive config if file doesn't exist
        if not os.path.exists(agent_file):
            return {"allowed_scopes": ["*"]}  # Permissive fallback
        
        with open(agent_file) as f:
            config = yaml.safe_load(f)
        
        self._cache[cache_key] = config
        self._cache_time = now
        return config
    
    def check(self, agent_id: str, required_scopes: list[str]) -> bool:
        """
        Check if agent has all required scopes.
        Returns True if allowed, raises InsufficientScopeError if not.
        """
        config = self._load_agents_config(agent_id)
        allowed = config.get("allowed_scopes", [])
        
        if "*" in allowed:
            return True
        
        for required in required_scopes:
            if required not in allowed:
                raise InsufficientScopeError(required_scopes, allowed)
        
        return True


class JtiBlacklist:
    """In-memory JTI blacklist for one-time token deduplication"""
    
    def __init__(self):
        self._blacklist: dict[str, bool] = {}
    
    def is_used(self, jti: str) -> bool:
        """Check if JTI has been used"""
        return jti in self._blacklist
    
    def mark_used(self, jti: str) -> None:
        """Mark JTI as used"""
        self._blacklist[jti] = True


class SAIFMiddleware:
    """
    SAIF Middleware for MCP servers.
    Extracts and validates agent tokens from Authorization header.
    """
    
    def __init__(
        self,
        agents_dir: str,
        verification_key: Optional[bytes] = None,
        require_auth: bool = True,
    ):
        self.scope_validator = ScopeValidator(agents_dir)
        self.verification_key = verification_key or b"dev-signing-key-change-in-production"
        self.require_auth = require_auth
    
    def __call__(self, request: dict) -> dict:
        """
        Process MCP request. Extracts token, validates, injects context.
        Returns modified request with 'saif_context' key.
        """
        auth_header = request.get("headers", {}).get("Authorization", "")
        
        if not auth_header.startswith("Bearer "):
            if self.require_auth:
                raise SAIFTokenError("Missing or invalid Authorization header")
            request["saif_context"] = None
            return request
        
        token = auth_header[7:]  # Strip "Bearer "
        
        payload = SAIFToken.verify(token, self.verification_key)
        
        # Inject validated payload into request context
        request["saif_context"] = {
            "iss": payload.iss,
            "sub": payload.sub,
            "aud": payload.aud,
            "scopes": payload.scopes,
            "risk_tier": payload.risk_tier,
            "jti": payload.jti,
        }
        
        return request


def require_scopes(*required_scopes: str) -> Callable:
    """
    Decorator to enforce scope requirements on MCP tools.
    Usage:
        @require_scopes("spec.read", "audit.write")
        def read_spec(path: str):
            ...
    """
    def decorator(func: Callable) -> Callable:
        func._required_scopes = required_scopes
        return func
    return decorator


def get_required_scopes(func: Callable) -> list[str]:
    """Extract required scopes from decorated function"""
    return getattr(func, "_required_scopes", [])