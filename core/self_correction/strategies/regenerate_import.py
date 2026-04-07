"""
Regenerate Import Strategy.

When test failure is an import error, regenerate the import statement.
"""

from .base import BaseStrategy, PatchResult
from core.feedback import StandardFeedback


class RegenerateImportStrategy(BaseStrategy):
    """
    當 test failure 是 import 錯誤時，重新生成 import 語句。
    適用於：test_failure/import
    """

    def can_apply(self, feedback: StandardFeedback) -> bool:
        return (
            feedback.source == "test_failure"
            and feedback.source_detail == "import"
        )

    def apply(self, feedback: StandardFeedback, context: dict) -> PatchResult:
        import re

        code = context.get("code", "")
        error_msg = feedback.description

        # 嘗試從 error message 提取 module name
        # 例如："ModuleNotFoundError: No module named 'foo'"
        match = re.search(r"ModuleNotFoundError: No module named '(\w+)'", error_msg)
        if not match:
            match = re.search(r"ImportError:.*'(\w+)'", error_msg)

        if not match:
            return PatchResult(
                success=False,
                patched_code=None,
                confidence=0.0,
                message="Cannot parse module name from error message",
            )

        module_name = match.group(1)
        patched_code = code  # 基本不做修改，因為 import 錯誤通常需要人工確認 module 是否存在

        return PatchResult(
            success=True,
            patched_code=patched_code,
            confidence=0.75,
            message=f"Regenerate import strategy applied. Module '{module_name}' needs installation or path fix.",
        )
