"""
ruff_format — Format Python files using ruff or black.

Applies automatic formatting to fix PEP 8 style issues.
"""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from .base import BaseStrategy, PatchResult


class RuffFormatStrategy:
    """
    Strategy for formatting Python code via ruff or black.

    Ruff is preferred (faster), with black as fallback.
    """

    def can_apply(self, feedback) -> bool:
        """Can apply when source is 'linter' and category is 'format' or 'pep8'."""
        return (
            feedback.source == "linter"
            and feedback.category in ("format", "pep8")
        )

    def apply(self, feedback, context: dict) -> PatchResult:
        """
        Format the file using ruff (preferred) or black.

        Context expected keys:
            file_path (str): Path to the file to format.
            file_content (str): Current file content.
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

        # Try ruff first
        result = self._try_ruff(file_path)
        if result is not None:
            return result

        # Fallback to black
        result = self._try_black(file_path)
        if result is not None:
            return result

        return PatchResult(
            success=False,
            patched_code=None,
            confidence=0.0,
            message="Neither ruff nor black available for formatting",
        )

    def _try_ruff(self, file_path: str) -> PatchResult | None:
        """Try formatting with ruff. Returns None if not available."""
        try:
            result = subprocess.run(
                ["ruff", "format", "--check", file_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                # Already formatted
                with open(file_path, "r") as f:
                    content = f.read()
                return PatchResult(
                    success=True,
                    patched_code=content,
                    confidence=0.95,
                    message=f"File already formatted (ruff): {file_path}",
                )

            # Try to apply fix
            fix_result = subprocess.run(
                ["ruff", "format", file_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if fix_result.returncode == 0:
                with open(file_path, "r") as f:
                    new_content = f.read()
                return PatchResult(
                    success=True,
                    patched_code=new_content,
                    confidence=0.90,
                    message=f"Formatted with ruff: {file_path}",
                )

        except FileNotFoundError:
            pass  # ruff not available
        except Exception as exc:
            return PatchResult(
                success=False,
                patched_code=None,
                confidence=0.0,
                message=f"ruff format failed: {exc}",
            )

        return None

    def _try_black(self, file_path: str) -> PatchResult | None:
        """Try formatting with black. Returns None if not available."""
        try:
            result = subprocess.run(
                ["black", "--check", file_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                with open(file_path, "r") as f:
                    content = f.read()
                return PatchResult(
                    success=True,
                    patched_code=content,
                    confidence=0.95,
                    message=f"File already formatted (black): {file_path}",
                )

            fix_result = subprocess.run(
                ["black", file_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if fix_result.returncode == 0:
                with open(file_path, "r") as f:
                    new_content = f.read()
                return PatchResult(
                    success=True,
                    patched_code=new_content,
                    confidence=0.90,
                    message=f"Formatted with black: {file_path}",
                )

        except FileNotFoundError:
            pass  # black not available
        except Exception as exc:
            return PatchResult(
                success=False,
                patched_code=None,
                confidence=0.0,
                message=f"black format failed: {exc}",
            )

        return None
