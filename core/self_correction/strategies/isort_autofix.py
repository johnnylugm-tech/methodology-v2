"""
isort_autofix — Automatically sort Python import statements.

Uses the `isort` library to fix import ordering and grouping issues.
"""

from __future__ import annotations

from typing import Any

from .base import BaseStrategy, PatchResult


class IsortAutofixStrategy:
    """
    Strategy for fixing import ordering via isort.

    Applies `isort` to automatically sort and group import statements
    according to PEP 8 conventions.
    """

    def can_apply(self, feedback) -> bool:
        """Can apply when source is 'linter' and category is 'unused-import'."""
        return (
            feedback.source == "linter"
            and feedback.category == "unused-import"
        )

    def apply(self, feedback, context: dict) -> PatchResult:
        """
        Run isort on the target file.

        Context expected keys:
            file_path (str): Path to the file to fix.
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

        try:
            import isort

            # Apply isort with standard configuration
            sorted_content = isort.code(
                file_content,
                file_path=file_path,
                show_diff=False,
            )

            if sorted_content == file_content:
                return PatchResult(
                    success=True,
                    patched_code=file_content,
                    confidence=0.95,
                    message="Import order unchanged — already sorted",
                )

            return PatchResult(
                success=True,
                patched_code=sorted_content,
                confidence=0.90,
                message=f"Import statements sorted in {file_path}",
            )

        except ImportError:
            # isort not installed — try using system ruff or black as fallback
            return self._fallback_format(context)

        except Exception as exc:
            return PatchResult(
                success=False,
                patched_code=None,
                confidence=0.0,
                message=f"isort failed: {exc}",
            )

    def _fallback_format(self, context: dict) -> PatchResult:
        """Fallback using ruff or black when isort is not available."""
        file_path = context.get("file_path", "unknown")
        file_content = context.get("file_content", "")

        # Try ruff check --select I --fix first
        import subprocess

        try:
            result = subprocess.run(
                ["ruff", "check", "--select", "I", "--fix", file_path],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0:
                # Re-read file after ruff fix
                with open(file_path, "r") as f:
                    new_content = f.read()
                return PatchResult(
                    success=True,
                    patched_code=new_content,
                    confidence=0.85,
                    message=f"Ruff isort fix applied to {file_path}",
                )
        except FileNotFoundError:
            pass  # ruff not available

        return PatchResult(
            success=False,
            patched_code=None,
            confidence=0.0,
            message="Neither isort nor ruff available for import fixes",
        )
