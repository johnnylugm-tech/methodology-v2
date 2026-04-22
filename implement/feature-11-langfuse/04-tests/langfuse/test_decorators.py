"""Tests for ml_langfuse.decorators — Auto-instrumentation decorators."""

from __future__ import annotations

import os
import pytest

from ml_langfuse.decorators import (
    observe_llm_call,
    observe_decision_point,
    observe_decision_point_async,
    observe_tool_call,
    observe_span,
)


class TestObserveLlmCall:
    """Tests for @observe_llm_call decorator."""

    @pytest.fixture(autouse=True)
    def setup(self):
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"

    async def test_observe_llm_call_async(self):
        """@observe_llm_call on async function should not raise."""
        @observe_llm_call(model_name="claude-3-opus")
        async def dummy_llm(prompt: str) -> str:
            return f"response to: {prompt}"

        result = await dummy_llm("hello")
        assert result == "response to: hello"

    def test_observe_llm_call_sync(self):
        """@observe_llm_call on sync function should not raise."""
        @observe_llm_call(model_name="claude-3-opus", model_version="2024-06")
        def dummy_llm_sync(prompt: str) -> str:
            return f"sync response to: {prompt}"

        result = dummy_llm_sync("hello")
        assert result == "sync response to: hello"

    async def test_observe_llm_call_propagates_exception(self):
        """@observe_llm_call should re-raise exceptions from wrapped function."""
        @observe_llm_call(model_name="claude-3-opus")
        async def failing_llm(prompt: str) -> str:
            raise RuntimeError("LLM error")

        with pytest.raises(RuntimeError, match="LLM error"):
            await failing_llm("hello")


class TestObserveDecisionPoint:
    """Tests for @observe_decision_point decorator."""

    @pytest.fixture(autouse=True)
    def setup(self):
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"

    def test_observe_decision_point_sync_returns_dict(self):
        """@observe_decision_point on sync function should work with dict return."""
        @observe_decision_point(point="risk_evaluation", phase="phase6")
        def sync_risk_eval(state: dict) -> dict:
            score = 0.42
            return {
                "uaf_score": 0.85,
                "clap_flag": True,
                "risk_score": score,
                "hitl_gate": "review",
                "human_decision": None,
                "decided_by": "agent",
                "compliance_tags": ["GDPR Art.22"],
            }

        result = sync_risk_eval({})
        assert isinstance(result, dict)
        assert result["risk_score"] == 0.42

    async def test_observe_decision_point_async(self):
        """@observe_decision_point_async on async function should work."""
        @observe_decision_point_async(point="uaf_check", phase="phase7")
        async def async_uaf_check(state: dict) -> dict:
            return {
                "uaf_score": 0.90,
                "clap_flag": True,
                "risk_score": 0.10,
                "hitl_gate": "pass",
                "human_decision": None,
                "decided_by": "agent",
                "compliance_tags": ["SOX"],
            }


        result = await async_uaf_check({})
        assert result["hitl_gate"] == "pass"

    def test_observe_decision_point_non_dict_return_logs_warning(self):
        """If decorated function returns non-dict, decorator should not raise."""
        @observe_decision_point(point="some_check", phase="phase6")
        def bad_fn(state: dict) -> str:
            return "not a dict"

        result = bad_fn({})
        assert result == "not a dict"  # Should return without raising

    def test_observe_decision_point_propagates_exception(self):
        """Exceptions from decorated function should propagate."""
        @observe_decision_point(point="failing_check", phase="phase6")
        def failing_check(state: dict) -> dict:
            raise ValueError("check failed")

        with pytest.raises(ValueError, match="check failed"):
            failing_check({})


class TestObserveToolCall:
    """Tests for @observe_tool_call decorator."""

    @pytest.fixture(autouse=True)
    def setup(self):
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"

    def test_observe_tool_call_sync(self):
        """@observe_tool_call on sync function should work."""
        @observe_tool_call(tool_name="search")
        def search_tool(query: str) -> dict:
            return {"result": f"found: {query}"}

        result = search_tool("LLM")
        assert "found" in result["result"]

    async def test_observe_tool_call_async(self):
        """@observe_tool_call on async function should work."""
        @observe_tool_call(tool_name="db_query")
        async def db_query(sql: str) -> dict:
            return {"rows": []}

        result = await db_query("SELECT * FROM logs")
        assert result["rows"] == []

    async def test_observe_tool_call_propagates_exception(self):
        """Exceptions from tool calls should propagate."""
        @observe_tool_call(tool_name="fail_tool")
        async def failing_tool() -> dict:
            raise RuntimeError("tool failed")

        with pytest.raises(RuntimeError, match="tool failed"):
            await failing_tool()


class TestObserveSpan:
    """Tests for @observe_span decorator."""

    @pytest.fixture(autouse=True)
    def setup(self):
        os.environ["LANGFUSE_PUBLIC_KEY"] = "pk_test"
        os.environ["LANGFUSE_SECRET_KEY"] = "sk_test"

    def test_observe_span_sync(self):
        """@observe_span on sync function should work."""
        @observe_span(name="custom_op", attributes={"custom.attr": "val"})
        def custom_op(x: int) -> int:
            return x * 2

        result = custom_op(21)
        assert result == 42

    async def test_observe_span_async(self):
        """@observe_span on async function should work."""
        @observe_span(name="async_custom_op")
        async def async_custom_op(x: int) -> int:
            return x + 1

        result = await async_custom_op(41)
        assert result == 42

    async def test_observe_span_propagates_exception(self):
        """Exceptions from @observe_span should propagate."""
        @observe_span(name="failing_op")
        async def failing_op() -> None:
            raise RuntimeError("op failed")

        with pytest.raises(RuntimeError, match="op failed"):
            await failing_op()
