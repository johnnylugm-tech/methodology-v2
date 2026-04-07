"""
extract_function — Reduce cyclomatic complexity by extracting functions.

Identifies high-complexity code blocks and extracts them into separate functions.
"""

from __future__ import annotations

import ast
import re
from typing import Any

from .base import BaseStrategy, PatchResult


class ExtractFunctionStrategy:
    """
    Strategy for reducing cyclomatic complexity by extracting functions.

    Identifies high-complexity functions and attempts to extract nested
    logic blocks into helper functions.
    """

    def can_apply(self, feedback) -> bool:
        """Can apply when type is 'complexity' and category is 'cc_high'."""
        return (
            feedback.type == "complexity"
            and feedback.category == "cc_high"
        )

    def apply(self, feedback, context: dict) -> PatchResult:
        """
        Attempt to extract a high-complexity function.

        Context expected keys:
            file_path (str): Path to the file to refactor.
            file_content (str): Current file content.
            function_name (str, optional): Name of the function to refactor.
            complexity_score (int, optional): Cyclomatic complexity score.
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

        function_name = context.get("function_name", "")
        cc_score = context.get("complexity_score", 0)

        try:
            tree = ast.parse(file_content)
        except SyntaxError:
            return PatchResult(
                success=False,
                patched_code=None,
                confidence=0.0,
                message=f"Cannot parse {file_path} — syntax error",
            )

        # Find the target function (by name or highest complexity)
        target_func = None
        max_complexity = 0

        class ComplexityVisitor(ast.NodeVisitor):
            def __init__(self):
                self.functions: list[ast.FunctionDef] = []

            def visit_FunctionDef(self, node: ast.FunctionDef):
                cc = self._compute_complexity(node)
                if cc > max_complexity:
                    max_complexity = cc
                    target_func = node  # type: ignore
                if function_name and node.name == function_name:
                    target_func = node  # type: ignore
                self.generic_visit(node)

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
                self.visit_FunctionDef(node)  # type: ignore

            @staticmethod
            def _compute_complexity(node: ast.FunctionDef) -> int:
                """Compute cyclomatic complexity of a function."""
                complexity = 1  # base complexity
                for child in ast.walk(node):
                    if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                        complexity += 1
                    elif isinstance(child, ast.BoolOp):
                        complexity += len(child.values) - 1
                    elif isinstance(child, ast.ExceptHandler):
                        complexity += 1
                return complexity

        visitor = ComplexityVisitor()
        visitor.visit(tree)

        if target_func is None:
            return PatchResult(
                success=False,
                patched_code=None,
                confidence=0.50,
                message="Could not locate target function for complexity refactor",
            )

        func_name = target_func.name
        lines = file_content.split("\n")

        # Extract simple if-else chains into early returns
        # This is a basic heuristic that works for common patterns
        refactored = False
        new_lines = list(lines)

        # Look for if-elif-else chains that can be converted to early returns
        for i, line in enumerate(new_lines):
            stripped = line.strip()
            # Simple pattern: long if-elif chain (3+ branches)
            if stripped.startswith("if ") and i + 2 < len(new_lines):
                # Check if this is part of an if-elif chain
                chain_length = 1
                j = i + 1
                while j < len(new_lines):
                    next_stripped = new_lines[j].strip()
                    if next_stripped.startswith("elif ") or next_stripped.startswith("else:"):
                        chain_length += 1
                        j += 1
                    else:
                        break

                if chain_length >= 3:
                    # Heuristic: suggest extraction but can't safely auto-fix
                    return PatchResult(
                        success=False,
                        patched_code=None,
                        confidence=0.60,
                        message=(
                            f"Function '{func_name}' has high complexity ({cc_score}). "
                            "Auto-extraction requires manual refactoring — "
                            "complex control flow structures cannot be safely automated."
                        ),
                    )

        # Look for repeated code patterns that could be extracted
        # This is a simplified version
        if not refactored:
            return PatchResult(
                success=False,
                patched_code=None,
                confidence=0.60,
                message=(
                    f"Function '{func_name}' complexity is {cc_score}. "
                    "Manual refactoring recommended: "
                    "extract conditional branches into helper functions."
                ),
            )
        else:
            return PatchResult(
                success=True,
                patched_code="\n".join(new_lines),
                confidence=0.70,
                message=f"Refactored '{func_name}' — complexity reduced",
            )

    def _compute_complexity(self, node: ast.FunctionDef) -> int:
        """Compute cyclomatic complexity of a function."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
        return complexity
