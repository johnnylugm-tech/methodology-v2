"""
D2: Injection Risk Assessor [FR-R-2]

Evaluates risk of prompt injection, code injection, or malicious input.
"""

from __future__ import annotations

import re
from typing import Optional

from . import AbstractDimensionAssessor, DimensionResult


class InjectionAssessor(AbstractDimensionAssessor):
    """
    D2: Injection Risk Assessor [FR-R-2]

    Assessment Factors:
    - User input sanitization
    - Code execution scope
    - External content rendering
    - Dynamic prompt construction
    """

    # Injection patterns
    INJECTION_PATTERNS = {
        "prompt_injection": [
            r"ignore\s+(previous|above|prior|all)\s+(instructions?|rules?|constraints?)",
            r"(system|assistant|human)\s*:",
            r"\[\s*INST\s*\]",
            r"<\s*system\s*>",
        ],
        "code_injection": [
            r"<\?php",
            r"<%.*%>",
            r"\$\{.*\}",
            r"\$\w+\s*\(",
            r"eval\s*\(",
            r"exec\s*\(",
            r"subprocess",
            r"os\.system",
        ],
        "path_injection": [
            r"\.\.\/",
            r"\.\.\\",
            r"%2e%2e",
            r"\.\.%2f",
        ],
        "sql_injection": [
            r"'\s*OR\s*'1'\s*=\s*'1",
            r"'\s*OR\s*'",
            r"UNION\s+SELECT",
            r"DROP\s+TABLE",
        ],
    }

    def assess(self, context: dict) -> float:
        """
        Calculate injection risk score.

        Args:
            context: Must contain 'input' or 'user_content'

        Returns:
            Risk score 0.0-1.0
        """
        input_text = context.get("input", context.get("user_content", ""))
        if not input_text:
            return 0.0

        # Sanitization score
        sanitization_score = (1 - self._sanitize_inputs(context)) * 0.35

        # Execution scope score
        execution_scope_score = self._evaluate_execution_scope(context) * 0.25

        # External content score
        external_content_score = self._detect_external_content(context) * 0.25

        # Dynamic prompt complexity
        dynamic_prompt_score = self._measure_dynamic_prompt_complexity(context) * 0.15

        return min(1.0, sanitization_score + execution_scope_score + external_content_score + dynamic_prompt_score)

    def _sanitize_inputs(self, context: dict) -> float:
        """Check input sanitization status."""
        if context.get("sanitized", False):
            return 1.0
        if context.get("input_validation"):
            return 0.8
        return 0.0

    def _evaluate_execution_scope(self, context: dict) -> float:
        """Evaluate code execution scope safety."""
        scope = context.get("execution_scope", "sandboxed")
        if scope == "none":
            return 0.9
        elif scope == "limited":
            return 0.5
        elif scope == "sandboxed":
            return 0.1
        elif scope == "isolated":
            return 0.0
        return 0.3

    def _detect_external_content(self, context: dict) -> float:
        """Detect external content rendering risks."""
        if context.get("has_external_content", False):
            return 0.7
        if context.get("renders_html", False):
            return 0.6
        if context.get("renders_markdown", False):
            return 0.3
        return 0.0

    def _measure_dynamic_prompt_complexity(self, context: dict) -> float:
        """Measure complexity of dynamic prompt construction."""
        complexity = context.get("prompt_complexity", "low")
        if complexity == "high":
            return 0.5
        elif complexity == "medium":
            return 0.25
        elif complexity == "low":
            return 0.05
        return 0.1

    def get_dimension_id(self) -> str:
        return "D2"

    def _detect_injection_patterns(self, text: str) -> list[str]:
        """Detect injection patterns in text."""
        findings = []
        text_lower = text.lower()

        for category, patterns in self.INJECTION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    findings.append(f"{category}: matched pattern")

        return findings

    def assess_with_details(self, context: dict) -> DimensionResult:
        """Perform detailed injection risk assessment."""
        input_text = context.get("input", context.get("user_content", ""))
        evidence = []
        warnings = []
        metadata = {}

        injection_findings = []
        if input_text:
            injection_findings = self._detect_injection_patterns(input_text)

        if injection_findings:
            evidence.append(f"Injection patterns detected: {len(injection_findings)}")
            metadata["injection_patterns"] = injection_findings

        execution_scope = context.get("execution_scope", "unknown")
        evidence.append(f"Execution scope: {execution_scope}")

        if context.get("has_external_content"):
            warnings.append("Contains external content - higher injection risk")

        score = self.assess(context)
        return DimensionResult(
            dimension_id=self.get_dimension_id(),
            score=score,
            evidence=evidence,
            metadata=metadata,
            warnings=warnings,
        )