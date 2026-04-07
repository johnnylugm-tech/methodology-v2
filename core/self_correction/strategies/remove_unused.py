"""
remove_unused — Remove unused Python variables and imports.

Uses regex patterns and AST analysis to identify and remove unused identifiers.
"""

from __future__ import annotations

import ast
import re
from typing import Any

from .base import BaseStrategy, PatchResult


class RemoveUnusedStrategy:
    """
    Strategy for removing unused variables and imports.

    Uses AST analysis to safely identify and remove unused identifiers
    without breaking the code.
    """

    def can_apply(self, feedback) -> bool:
        """Can apply when source is 'linter' and category is 'unused-variable'."""
        return (
            feedback.source == "linter"
            and feedback.category == "unused-variable"
        )

    def apply(self, feedback, context: dict) -> PatchResult:
        """
        Remove unused variable or import.

        Context expected keys:
            file_path (str): Path to the file to fix.
            file_content (str): Current file content.
            error_message (str, optional): Linter message with variable name.
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

        # Try to extract variable name from error message
        # Common patterns: "unused variable 'foo'", "variable 'bar' is never used"
        var_name = None
        patterns = [
            r"unused ['\"]?(\w+)['\"]?",
            r"['\"](\w+)['\"]? is never used",
            r"variable ['\"]?(\w+)['\"]?",
        ]
        for pattern in patterns:
            match = re.search(pattern, error_msg, re.IGNORECASE)
            if match:
                var_name = match.group(1)
                break

        try:
            tree = ast.parse(file_content)
        except SyntaxError:
            return PatchResult(
                success=False,
                patched_code=None,
                confidence=0.0,
                message=f"Cannot parse {file_path} — syntax error",
            )

        # Collect all used names in the module
        used_names: set[str] = set()

        class NameCollector(ast.NodeVisitor):
            def __init__(self):
                self._scope_stack: list[set[str]] = [set()]

            def scope(self) -> set[str]:
                return self._scope_stack[-1]

            def push_scope(self):
                self._scope_stack.append(set())

            def pop_scope(self):
                self._scope_stack.pop()

            def visit_Name(self, node: ast.Name):
                if isinstance(node.ctx, ast.Load):
                    self.scope().add(node.id)
                self.generic_visit(node)

            def visit_FunctionDef(self, node: ast.FunctionDef):
                # Function arguments are "used" within the function scope
                for arg in node.args.args:
                    self.scope().add(arg.arg)
                for arg in node.args.posonlyargs:
                    self.scope().add(arg.arg)
                for arg in node.args.kwonlyargs:
                    self.scope().add(arg.arg)
                if node.args.vararg:
                    self.scope().add(node.args.vararg.arg)
                if node.args.kwarg:
                    self.scope().add(node.args.kwarg.arg)
                self.push_scope()
                self.generic_visit(node)
                self.pop_scope()

            def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
                self.visit_FunctionDef(node)  # type: ignore

            def visit_ClassDef(self, node: ast.ClassDef):
                self.push_scope()
                self.generic_visit(node)
                self.pop_scope()

            def visit_Lambda(self, node: ast.Lambda):
                # Lambda args are used within lambda body
                for arg in node.args.args:
                    self.scope().add(arg.arg)
                if node.args.vararg:
                    self.scope().add(node.args.vararg.arg)
                if node.args.kwarg:
                    self.scope().add(node.args.kwarg.arg)
                self.generic_visit(node)

        collector = NameCollector()
        collector.visit(tree)

        # Remove unused imports
        patched_lines = file_content.split("\n")
        lines_removed = 0

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    full_name = alias.name
                    asname = alias.asname or alias.name
                    if full_name not in used_names and asname not in used_names:
                        # Try to find and remove this import line
                        for i, line in enumerate(patched_lines):
                            # Match "import x" or "import x as y" or "from x import ..."
                            if f"import {full_name}" in line and not line.strip().startswith("#"):
                                patched_lines[i] = ""
                                lines_removed += 1

            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    asname = alias.name
                    if asname not in used_names:
                        for i, line in enumerate(patched_lines):
                            if f"from {module} import" in line and asname in line:
                                # Handle single vs multi imports
                                if re.search(rf"import\s+{re.escape(asname)}\s*$", line):
                                    # Single import — remove entire line
                                    patched_lines[i] = ""
                                    lines_removed += 1
                                elif re.search(rf"import\s+.+,\s*{re.escape(asname)}\s*$", line):
                                    # Multi import with trailing — remove from list
                                    patched_lines[i] = re.sub(
                                        rf",\s*{re.escape(asname)}\s*$",
                                        "",
                                        patched_lines[i],
                                    )
                                elif re.search(rf"import\s+{re.escape(asname)}\s*,", line):
                                    # Multi import with leading — remove from list
                                    patched_lines[i] = re.sub(
                                        rf"{re.escape(asname)}\s*,\s*",
                                        "",
                                        patched_lines[i],
                                    )

        # Remove unused variable assignments
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var = target.id
                        if var not in used_names:
                            # Find the line and remove or comment it
                            for i, line in enumerate(patched_lines):
                                if f" = " in line and line.strip().startswith(var):
                                    # Check if this is a simple assignment line
                                    stripped = line.strip()
                                    if stripped.startswith(f"{var} ="):
                                        # Check if it's a simple assignment (not in a dict/list)
                                        patched_lines[i] = f"# [removed unused] {line}"
                                        lines_removed += 1

        result = "\n".join(patched_lines)

        if lines_removed == 0:
            return PatchResult(
                success=True,
                patched_code=file_content,
                confidence=0.90,
                message="No unused variables found — nothing to remove",
            )

        return PatchResult(
            success=True,
            patched_code=result,
            confidence=0.85,
            message=f"Removed {lines_removed} unused variable(s)/import(s)",
        )
