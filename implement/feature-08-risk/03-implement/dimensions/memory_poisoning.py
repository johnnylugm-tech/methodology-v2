"""
D5: Memory Poisoning Risk Assessor [FR-R-5]

Evaluates risk of corrupted or manipulated agent memory/context.
"""

from __future__ import annotations

import hashlib
from typing import Optional

from . import AbstractDimensionAssessor, DimensionResult


class MemoryPoisoningAssessor(AbstractDimensionAssessor):
    """
    D5: Memory Poisoning Risk Assessor [FR-R-5]

    Assessment Factors:
    - Memory source verification
    - Content authenticity checks
    - Tampering detection
    - Historical consistency validation
    """

    def assess(self, context: dict) -> float:
        """
        Calculate memory poisoning risk score.

        Args:
            context: Must contain memory state information

        Returns:
            Risk score 0.0-1.0
        """
        # Source verification score
        source_verification = self._verify_memory_sources(context) * 0.3

        # Authenticity score
        authenticity_score = self._check_content_authenticity(context) * 0.3

        # Tampering score
        tampering_score = self._detect_tampering(context) * 0.25

        # Consistency score
        consistency_score = self._validate_historical_consistency(context) * 0.15

        return source_verification + authenticity_score + tampering_score + consistency_score

    def _verify_memory_sources(self, context: dict) -> float:
        """Verify sources of memory content."""
        source_verified = context.get("memory_source_verified", False)
        sources_count = context.get("memory_sources_count", 0)

        if source_verified and sources_count > 0:
            return 0.0
        elif source_verified:
            return 0.2
        elif sources_count > 1:
            return 0.6
        elif sources_count == 1:
            return 0.4
        return 0.8  # Single unverified source

    def _check_content_authenticity(self, context: dict) -> float:
        """Check content authenticity."""
        content_hash = context.get("content_hash")
        expected_hash = context.get("expected_hash")

        if content_hash and expected_hash:
            if content_hash != expected_hash:
                return 1.0  # Hash mismatch = high risk
            return 0.0

        # Check for signature/verification
        if context.get("content_signed", False):
            return 0.0
        if context.get("content_verified", False):
            return 0.1

        return 0.5  # Unknown authenticity

    def _detect_tampering(self, context: dict) -> float:
        """Detect evidence of tampering."""
        tampering_indicators = context.get("tampering_indicators", [])

        if not tampering_indicators:
            # Check for implicit tampering signs
            if context.get("memory_modified", False):
                return 0.7
            if context.get("unexpected_edits", False):
                return 0.8
            return 0.0

        # Direct indicators
        return min(1.0, len(tampering_indicators) * 0.25)

    def _validate_historical_consistency(self, context: dict) -> float:
        """Validate consistency with historical patterns."""
        consistency_score = context.get("historical_consistency_score", 1.0)

        if consistency_score >= 0.9:
            return 0.0
        elif consistency_score >= 0.7:
            return 0.3
        elif consistency_score >= 0.5:
            return 0.6
        elif consistency_score >= 0.3:
            return 0.8
        return 1.0

    def get_dimension_id(self) -> str:
        return "D5"

    def assess_with_details(self, context: dict) -> DimensionResult:
        """Perform detailed memory poisoning assessment."""
        evidence = []
        warnings = []
        metadata = {}

        source_verified = context.get("memory_source_verified", False)
        evidence.append(f"Source verified: {source_verified}")

        content_hash = context.get("content_hash")
        if content_hash:
            evidence.append(f"Content hash: {content_hash[:16]}...")

        tampering_indicators = context.get("tampering_indicators", [])
        if tampering_indicators:
            warnings.append(f"Tampering indicators: {len(tampering_indicators)}")
            metadata["tampering_indicators"] = tampering_indicators

        consistency = context.get("historical_consistency_score", 1.0)
        evidence.append(f"Historical consistency: {consistency:.2%}")

        score = self.assess(context)
        return DimensionResult(
            dimension_id=self.get_dimension_id(),
            score=score,
            evidence=evidence,
            metadata=metadata,
            warnings=warnings,
        )