"""
Fault Tolerance - Retry Handler with Dynamic Prompt Adjustment

Provides:
- RetryHandler: Exponential backoff retry with dynamic prompt constraint injection
- DynamicPromptAdjuster: Progressive constraint injection for retries
"""

import time


class DynamicPromptAdjuster:
    """
    動態調整 Prompt 約束

    當重試發生時，自動注入更嚴格的約束：
    - 第 1 次重試：「請更加簡潔」（10s 退避）
    - 第 2 次重試：「必須在 50 字內回答」（20s 退避）
    - 第 3 次重試：「輸出不超過 5 行」（40s 退避）
    """

    RETRY_CONSTRAINTS = [
        "",  # 第 0 次（無約束）
        "請更加簡潔，只輸出關鍵資訊，不超過 100 字。",  # 第 1 次
        "必須在 50 字內回答，只說結論。",  # 第 2 次
        "輸出不超過 5 行，直接給答案，不要解釋。",  # 第 3 次
        "只回覆 OK 或 ERROR，不要其他文字。"  # 第 4 次+
    ]

    @classmethod
    def get_constraint(cls, retry_count: int) -> str:
        """取得第 N 次重試的約束"""
        idx = min(retry_count, len(cls.RETRY_CONSTRAINTS) - 1)
        return cls.RETRY_CONSTRAINTS[idx]

    @classmethod
    def inject_constraint(cls, original_prompt: str, retry_count: int) -> str:
        """注入約束到 Prompt"""
        constraint = cls.get_constraint(retry_count)
        if not constraint:
            return original_prompt

        # 在 Prompt 末尾加入約束
        return f"{original_prompt}\n\n[約束-{retry_count}]: {constraint}"


class RetryHandler:
    """
    重試處理器，帶指數退避和動態 Prompt 調整

    用法：
        handler = RetryHandler(max_retries=3, base_delay=10)
        result = handler.execute(
            task_fn,
            args=(),
            on_retry=lambda count, error: print(f"Retry {count}: {error}")
        )
    """

    def __init__(self, max_retries: int = 3, base_delay: float = 10.0, max_delay: float = 120.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.adjuster = DynamicPromptAdjuster()

    def calculate_delay(self, retry_count: int) -> float:
        """計算指數退避延遲"""
        delay = self.base_delay * (2 ** retry_count)
        return min(delay, self.max_delay)

    def execute(self, task_fn, args=(), kwargs=None, prompt: str = None, on_retry=None):
        """
        執行任務，自動重試

        Args:
            task_fn: 要執行的任務函數
            args: 位置參數
            kwargs: 關鍵字參數
            prompt: 原始 prompt（用於動態調整）
            on_retry: 重試時的回調函數 (retry_count, error) -> None
        """
        kwargs = kwargs or {}
        last_error = None

        for attempt in range(self.max_retries + 1):
            try:
                # 如果有 prompt 且是重試，注入約束
                if prompt and attempt > 0:
                    adjusted_prompt = self.adjuster.inject_constraint(prompt, attempt)
                    kwargs["prompt"] = adjusted_prompt

                result = task_fn(*args, **kwargs)
                return result

            except Exception as e:
                last_error = e

                if attempt < self.max_retries:
                    delay = self.calculate_delay(attempt)
                    if on_retry:
                        on_retry(attempt + 1, str(e))
                    time.sleep(delay)
                else:
                    raise last_error

        raise last_error
