"""
MCP SAIF 2.0 Identity Propagation Module
"""
from .saif_identity_middleware import (
    SAIFToken,
    SAIFTokenPayload,
    SAIFTokenError,
    TokenExpiredError,
    InvalidSignatureError,
    InsufficientScopeError,
    SAIFMiddleware,
    ScopeValidator,
    JtiBlacklist,
    require_scopes,
    get_required_scopes,
)
from .data_perimeter import (
    PerimeterLevel,
    DeidentifiedPayload,
    deidentify,
    verify_evidence,
    auto_detect_and_deidentify,
    PII_PATTERNS,
)

__all__ = [
    # Token
    "SAIFToken",
    "SAIFTokenPayload",
    "SAIFTokenError",
    "TokenExpiredError",
    "InvalidSignatureError",
    "InsufficientScopeError",
    # Middleware
    "SAIFMiddleware",
    "ScopeValidator",
    "JtiBlacklist",
    "require_scopes",
    "get_required_scopes",
    # Data Perimeter
    "PerimeterLevel",
    "DeidentifiedPayload",
    "deidentify",
    "verify_evidence",
    "auto_detect_and_deidentify",
    "PII_PATTERNS",
]