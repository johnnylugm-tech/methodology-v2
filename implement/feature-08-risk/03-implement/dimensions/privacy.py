"""
D1: Data Privacy Risk Assessor [FR-R-1]

Evaluates risk of unauthorized data exposure or PII leakage.
"""

from __future__ import annotations

import re
from typing import Optional

from . import AbstractDimensionAssessor, DimensionResult


class PrivacyAssessor(AbstractDimensionAssessor):
    """
    D1: Data Privacy Risk Assessor [FR-R-1]

    Assessment Factors:
    - Presence of PII (Personally Identifiable Information)
    - Data classification level
    - Encryption status
    - Access control maturity
    """

    # Common PII patterns
    PII_PATTERNS = {
        "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        "phone": r'\b(\+?1?[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        "ssn": r'\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b',
        "credit_card": r'\b(?:\d{4}[-.\s]?){3}\d{4}\b',
        "ip_address": r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
    }

    # Data classification levels (higher = more sensitive)
    CLASSIFICATION_LEVELS = {
        "public": 0.1,
        "internal": 0.3,
        "confidential": 0.6,
        "restricted": 0.9,
        "top_secret": 1.0,
    }

    def assess(self, context: dict) -> float:
        """
        Calculate privacy risk score.

        Args:
            context: Must contain 'data' or 'content' with text to analyze

        Returns:
            Risk score 0.0-1.0
        """
        data = context.get("data", context.get("content", ""))
        if not data:
            return 0.0

        # Calculate PII score
        pii_score = self._detect_pii(data) * 0.4

        # Calculate classification score
        classification_score = self._get_classification_score(context) * 0.3

        # Calculate encryption score
        encryption_score = (1 - self._is_encrypted(context)) * 0.2

        # Calculate access control score
        access_score = self._evaluate_access_controls(context) * 0.1

        return min(1.0, pii_score + classification_score + encryption_score + access_score)

    def _detect_pii(self, text: str) -> float:
        """Detect presence of PII in text."""
        if not text:
            return 0.0

        pii_found = set()
        for pii_type, pattern in self.PII_PATTERNS.items():
            if re.search(pattern, text):
                pii_found.add(pii_type)

        # Score based on number of PII types found
        return min(1.0, len(pii_found) * 0.25)

    def _get_classification_score(self, context: dict) -> float:
        """Get classification level score."""
        classification = context.get("data_classification", "internal").lower()
        return self.CLASSIFICATION_LEVELS.get(classification, 0.3)

    def _is_encrypted(self, context: dict) -> float:
        """Check if data is encrypted."""
        if context.get("encrypted", False):
            return 1.0
        if context.get("encryption_type"):
            return 1.0
        return 0.0

    def _evaluate_access_controls(self, context: dict) -> float:
        """Evaluate access control maturity."""
        access_level = context.get("access_control", "standard")
        if access_level == "none":
            return 1.0
        elif access_level == "basic":
            return 0.6
        elif access_level == "standard":
            return 0.3
        elif access_level == "strict":
            return 0.1
        return 0.3

    def get_dimension_id(self) -> str:
        return "D1"

    def assess_with_details(self, context: dict) -> DimensionResult:
        """Perform detailed privacy risk assessment."""
        data = context.get("data", context.get("content", ""))
        evidence = []
        warnings = []

        pii_detected = set()
        if data:
            for pii_type, pattern in self.PII_PATTERNS.items():
                if re.search(pattern, data):
                    pii_detected.add(pii_type)

        if pii_detected:
            evidence.append(f"PII types detected: {', '.join(sorted(pii_detected))}")

        classification = context.get("data_classification", "internal")
        evidence.append(f"Data classification: {classification}")

        if not context.get("encrypted"):
            warnings.append("Data is not encrypted")

        score = self.assess(context)
        return DimensionResult(
            dimension_id=self.get_dimension_id(),
            score=score,
            evidence=evidence,
            metadata={
                "pii_types": list(pii_detected),
                "classification": classification,
                "encrypted": context.get("encrypted", False),
            },
            warnings=warnings,
        )