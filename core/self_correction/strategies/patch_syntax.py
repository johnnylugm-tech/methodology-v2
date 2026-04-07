"""
patch_syntax — Fix Python syntax errors.

Applies targeted patches to fix common Python syntax errors detected by linters.
"""

from __future__ import annotations

import re
from typing import Any

from .base import BaseStrategy, PatchResult

# Common syntax error patterns and their fixes
_SYNTAX_FIXES: list[tuple[str, str, str]] = [
    # (pattern, replacement, description)
    (
        r"(\w+)\s*\(\s*\)",
        r"\1()",
        "balanced parens"
    ),
    # Missing colon after def/if/for/while/class
    (r"^\s*(def\s+\w+\s*\([^)]*\))\s*$", r"\1:", "add colon after def"),
    (r"^\s*(class\s+\w+)\s*$", r"\1:", "add colon after class"),
    (r"^\s*(if\s+.+)\s*$", r"\1:", "add colon after if"),
    (r"^\s*(for\s+.+)\s*$", r"\1:", "add colon after for"),
    (r"^\s*(while\s+.+)\s*$", r"\1:", "add colon after while"),
    (r"^\s*(elif\s+.+)\s*$", r"\1:", "add colon after elif"),
    (r"^\s*(else)\s*$", r"\1:", "add colon after else"),
]


class PatchSyntaxStrategy:
    """
    Strategy for fixing Python syntax errors.

    Applies regex-based patches targeting common syntax mistakes
    like missing colons, unclosed brackets, etc.
    """

    def can_apply(self, feedback) -> bool:
        """Can apply when source is 'linter' and category is 'syntax'."""
        return (
            feedback.source == "linter"
            and feedback.category == "syntax"
        )

    def apply(self, feedback, context: dict) -> PatchResult:
        """
        Attempt to fix a syntax error.

        Context expected keys:
            file_path (str): Path to the file to patch.
            file_content (str): Current file content.
            error_location (str, optional): Line number or range (e.g., "line 42").
            error_message (str, optional): The linter error message.
        """
        file_path = context.get("file_path", "unknown")
        file_content = context.get("file_content", "")

        if not file_content:
            return PatchResult(
                success=False,
                patched_code=None,
                confidence=0.0,
                message=f"No file content provided for {file_path}",
            )

        error_msg = context.get("error_message", "")
        error_loc = context.get("error_location", "")

        # Try to extract line number from error location
        line_num = None
        if error_loc:
            match = re.search(r"line\s+(\d+)", error_loc, re.IGNORECASE)
            if match:
                line_num = int(match.group(1))

        # Try to extract line number from error message
        if line_num is None and error_msg:
            match = re.search(r"line\s+(\d+)", error_msg, re.IGNORECASE)
            if match:
                line_num = int(match.group(1))

        lines = file_content.split("\n")

        # Apply syntax fixes based on error message patterns
        patched_lines = list(lines)
        confidence = 0.50  # Base confidence for syntax patches

        # Handle missing colon patterns
        if "expected ':'" in error_msg.lower() or "missing ':'" in error_msg.lower():
            for i, line in enumerate(patched_lines):
                stripped = line.rstrip()
                # Only consider non-empty, non-comment, non-string lines
                if stripped and not stripped.strip().startswith("#"):
                    # Check if line ends with colon already
                    if not stripped.endswith(":") and not stripped.endswith("\\"):
                        # Try matching function/class/if/for/while/def patterns
                        for pattern, replacement, desc in _SYNTAX_FIXES:
                            if re.match(pattern, stripped):
                                patched_lines[i] = line + ":"
                                confidence = 0.85
                                return PatchResult(
                                    success=True,
                                    patched_code="\n".join(patched_lines),
                                    confidence=confidence,
                                    message=f"Added missing colon to line {i + 1}",
                                )

        # Handle unmatched parentheses/brackets
        if "unmatched" in error_msg.lower() or "paren" in error_msg.lower():
            open_count = 0
            close_count = 0
            for char in file_content:
                if char == "(":
                    open_count += 1
                elif char == ")":
                    close_count += 1

            if open_count > close_count:
                confidence = 0.60
                # Can't safely auto-fix unmatched parens without AST
                return PatchResult(
                    success=False,
                    patched_code=None,
                    confidence=confidence,
                    message="Unmatched parentheses detected — manual fix required",
                )

        # If we can't determine a specific fix
        return PatchResult(
            success=False,
            patched_code=None,
            confidence=0.30,
            message=f"Syntax error at {error_loc or 'unknown'} — could not determine patch",
        )
