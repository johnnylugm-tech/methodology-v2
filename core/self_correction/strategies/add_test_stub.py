"""
add_test_stub — Add test stubs for coverage gaps.

Creates placeholder test functions for code paths that lack coverage.
"""

from __future__ import annotations

import os
import re
from typing import Any

from .base import BaseStrategy, PatchResult


class AddTestStubStrategy:
    """
    Strategy for adding test stubs to fill coverage gaps.

    Creates simple placeholder test functions that can be expanded later.
    """

    def can_apply(self, feedback) -> bool:
        """Can apply when source is 'coverage' and category is 'gap'."""
        return (
            feedback.source == "coverage"
            and feedback.category == "gap"
        )

    def apply(self, feedback, context: dict) -> PatchResult:
        """
        Add a test stub for an uncovered code path.

        Context expected keys:
            test_file_path (str): Path to the test file.
            test_file_content (str): Current test file content.
            uncovered_function (str, optional): Function/class being tested.
            uncovered_line (int, optional): Line number of uncovered code.
        """
        test_file_path = context.get("test_file_path", "")
        test_file_content = context.get("test_file_content", "")
        uncovered_function = context.get("uncovered_function", "test_target")
        uncovered_line = context.get("uncovered_line", 0)

        # If no test file exists, we can't add stubs
        if not test_file_content:
            # Try to find or create a test file
            if not test_file_path:
                return PatchResult(
                    success=False,
                    patched_code=None,
                    confidence=0.0,
                    message="No test file path or content provided",
                )
            # Check if file exists
            if not os.path.exists(test_file_path):
                return PatchResult(
                    success=False,
                    patched_code=None,
                    confidence=0.0,
                    message=f"Test file does not exist: {test_file_path}",
                )

        # Generate a stub test function
        stub = self._generate_stub(uncovered_function, uncovered_line)

        if test_file_content:
            # Append stub to existing test file
            new_content = test_file_content.rstrip() + "\n\n" + stub
        else:
            new_content = stub

        return PatchResult(
            success=True,
            patched_code=new_content,
            confidence=0.70,
            message=f"Added test stub for '{uncovered_function}'",
        )

    def _generate_stub(self, function_name: str, line_number: int) -> str:
        """Generate a test stub for the given function."""
        # Sanitize function name for use as test name
        test_name = function_name
        if test_name.startswith("test_"):
            test_name = test_name[5:]

        stub = f'''
def test_{test_name}_stub():
    """Test stub for {function_name} (line {line_number})."""
    # TODO: Implement actual test
    # This is a placeholder stub to increase coverage
    pass


'''
        return stub

    def _create_test_file(self, file_path: str, content: str) -> PatchResult:
        """Create a new test file with a stub."""
        dir_path = os.path.dirname(file_path)
        if dir_path and not os.path.exists(dir_path):
            try:
                os.makedirs(dir_path, exist_ok=True)
            except OSError:
                return PatchResult(
                    success=False,
                    patched_code=None,
                    confidence=0.0,
                    message=f"Cannot create directory: {dir_path}",
                )

        try:
            with open(file_path, "w") as f:
                f.write(content)
            return PatchResult(
                success=True,
                patched_code=content,
                confidence=0.70,
                message=f"Created test file: {file_path}",
            )
        except OSError as exc:
            return PatchResult(
                success=False,
                patched_code=None,
                confidence=0.0,
                message=f"Cannot write test file: {exc}",
            )
