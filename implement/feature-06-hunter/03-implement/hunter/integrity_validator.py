"""Integrity validation for Hunter Agent (FR-H-1, FR-H-5)."""
import re
import hashlib
from typing import Optional

from .enums import Severity
from .models import TamperResult
from .patterns import TAMPER_PATTERNS, PATTERN_SEVERITY


class IntegrityValidator:
    """FR-H-1: Instruction tampering detection. FR-H-5: Hash verification."""

    def __init__(self, config: Optional[dict] = None) -> None:
        """Initialize with patterns and hash algorithm."""
        self._config = config or {}
        self._compiled_patterns: dict = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Pre-compile all tamper patterns for performance."""
        for pattern, regexes in TAMPER_PATTERNS.items():
            self._compiled_patterns[pattern] = [
                re.compile(r, re.IGNORECASE) for r in regexes
            ]

    def detect_tampering(self, content: str) -> TamperResult:
        """
        Scan content for instruction tampering patterns.

        Args:
            content: Raw message content string

        Returns:
            TamperResult with is_tampered=True if any pattern matches
        """
        if not content:
            return TamperResult(
                is_tampered=False,
                pattern_type=None,
                severity=Severity.LOW,
                matched_tokens=[],
                evidence_hash=self._compute_hash("")
            )

        for pattern_type, regexes in self._compiled_patterns.items():
            for regex in regexes:
                match = regex.search(content)
                if match:
                    matched = list(match.groups()) if match.groups() else []
                    hash_val = self._compute_hash(content)
                    severity = PATTERN_SEVERITY[pattern_type]
                    return TamperResult(
                        is_tampered=True,
                        pattern_type=pattern_type,
                        severity=severity,
                        matched_tokens=matched,
                        evidence_hash=hash_val
                    )

        return TamperResult(
            is_tampered=False,
            pattern_type=None,
            severity=Severity.LOW,
            matched_tokens=[],
            evidence_hash=self._compute_hash(content)
        )

    def verify_hash(self, source: str, expected: str) -> bool:
        """
        Verify source hash matches expected.

        Args:
            source: Content string
            expected: Expected hash (hex string)

        Returns:
            True if hashes match
        """
        actual = self._compute_hash(source)
        return actual == expected

    def compute_hash(self, source: str) -> str:
        """
        Compute SHA-256 hash of source content.

        Args:
            source: Content string

        Returns:
            Hex-encoded hash string
        """
        return self._compute_hash(source)

    def _compute_hash(self, content: str) -> str:
        """Compute SHA-256 hash."""
        try:
            return hashlib.sha256(content.encode()).hexdigest()
        except (TypeError, UnicodeEncodeError):
            return ""
        except Exception:
            return ""
