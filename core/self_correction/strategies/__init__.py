"""
Auto-Fix Strategies for Self-Correction Engine.
"""

from .base import BaseStrategy, PatchResult
from .patch_syntax import PatchSyntaxStrategy
from .isort_autofix import IsortAutofixStrategy
from .remove_unused import RemoveUnusedStrategy
from .ruff_format import RuffFormatStrategy
from .extract_function import ExtractFunctionStrategy
from .add_test_stub import AddTestStubStrategy

__all__ = [
    "BaseStrategy",
    "PatchResult",
    "PatchSyntaxStrategy",
    "IsortAutofixStrategy",
    "RemoveUnusedStrategy",
    "RuffFormatStrategy",
    "ExtractFunctionStrategy",
    "AddTestStubStrategy",
]
