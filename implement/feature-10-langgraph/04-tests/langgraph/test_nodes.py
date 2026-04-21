"""
Tests for nodes.py (ToolNode, LLMNode, HumanInTheLoopNode, ConditionalRouterNode).

These tests do NOT require the actual langgraph package.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


# ─────────────────────────────────────────────────────────────────────────────
# Import modules directly (no langgraph dependency in these classes)
# ─────────────────────────────────────────────────────────────────────────────

from ml_langgraph.nodes import (
    ToolNode,
    LLMNode,
    HumanInTheLoopNode,
    ConditionalRouterNode,
    passthrough_node,
    map_node,
)


# ─────────────────────────────────────────────────────────────────────────────
# ToolNode Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestToolNode:
    def test_tool_node_executes(self):
        """ToolNode should call tool_func with state tool_args and store result."""
        mock_tool = MagicMock(return_value="search results")
        node = ToolNode(name="search", tool_func=mock_tool, result_key="search_result")

        state = {
            "tool_args": {"query": "AI", "limit": 5},
            "intermediate_results": [],
            "last_node": None,
        }

        result_state = node(state)

        mock_tool.assert_called_once_with(query="AI", limit=5)
        assert result_state["search_result"] == "search results"
        assert result_state["last_node"] == "search"
        assert len(result_state["intermediate_results"]) == 1
        assert result_state["intermediate_results"][0]["tool"] == "mock_tool"

    def test_tool_node_handles_exception(self):
        """ToolNode should catch exceptions and store them in state."""
        mock_tool = MagicMock(side_effect=RuntimeError("tool failed"))
        node = ToolNode(name="risky", tool_func=mock_tool)

        state = {"tool_args": {}, "intermediate_results": [], "last_node": None}
        result_state = node(state)

        assert "error" in result_state
        assert "RuntimeError" in result_state["error"]
        assert result_state["last_node"] == "risky"

    def test_tool_node_result_key_none(self):
        """ToolNode with result_key=None should not store result in state."""
        mock_tool = MagicMock(return_value="discarded")
        node = ToolNode(name="void", tool_func=mock_tool, result_key=None)

        state = {"tool_args": {}, "intermediate_results": []}
        result_state = node(state)

        assert "result" not in result_state
        assert len(result_state["intermediate_results"]) == 1

    def test_tool_node_with_fixed_args(self):
        """with_args() should merge fixed args with state-derived args."""
        mock_tool = MagicMock(return_value="done")
        node = ToolNode(name="fixed", tool_func=mock_tool)

        bound = node.with_args(api_key="secret")
        state = {"tool_args": {"query": "test"}, "intermediate_results": []}
        result = bound(state)

        mock_tool.assert_called_once_with(api_key="secret", query="test")


# ─────────────────────────────────────────────────────────────────────────────
# LLMNode Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestLLMNode:
    def test_llm_node_calls_invoke(self):
        """LLMNode should call llm.invoke() with rendered messages."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Hello, world!"
        mock_llm.invoke = MagicMock(return_value=mock_response)

        node = LLMNode(
            name="chat",
            llm=mock_llm,
            prompt_template="You are a helpful assistant. Query: {query}",
            output_key="answer",
        )

        state = {"query": "What is AI?", "answer": None, "last_node": None}
        result = node(state)

        mock_llm.invoke.assert_called_once()
        call_kwargs = mock_llm.invoke.call_args.kwargs
        assert len(call_kwargs["messages"]) == 1
        assert "What is AI?" in call_kwargs["messages"][0]["content"]
        assert result["answer"] == "Hello, world!"
        assert result["last_node"] == "chat"

    def test_llm_node_calls_chat_fallback(self):
        """LLMNode should fall back to .chat() if .invoke() not available."""
        mock_llm = MagicMock(spec=[])  # neither invoke nor chat
        mock_llm.chat = MagicMock(return_value=MagicMock(content="fallback"))

        node = LLMNode(
            name="alt",
            llm=mock_llm,
            prompt_template="Say {word}",
            output_key="out",
        )
        state = {"word": "hi", "out": None, "last_node": None}
        result = node(state)

        assert result["out"] == "fallback"

    def test_llm_node_handles_exception(self):
        """LLMNode should catch LLM errors and store in state."""
        mock_llm = MagicMock()
        mock_llm.invoke = MagicMock(side_effect=RuntimeError("LLM unavailable"))

        node = LLMNode(name="faulty", llm=mock_llm, prompt_template="Hello {name}")
        state = {"name": "World", "last_node": None}
        result = node(state)

        assert "error" in result
        assert result["last_node"] == "faulty"

    def test_llm_node_with_system_prompt(self):
        """LLMNode should prepend system prompt when provided."""
        mock_llm = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "response"
        mock_llm.invoke = MagicMock(return_value=mock_response)

        node = LLMNode(
            name="sys",
            llm=mock_llm,
            prompt_template="Answer: {q}",
            output_key="out",
            system_prompt="You are a mathematician.",
        )
        state = {"q": "2+2?", "out": None}
        node(state)

        call_kwargs = mock_llm.invoke.call_args.kwargs
        messages = call_kwargs["messages"]
        assert messages[0]["role"] == "system"
        assert "mathematician" in messages[0]["content"]


# ─────────────────────────────────────────────────────────────────────────────
# HumanInTheLoopNode Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestHumanInTheLoopNode:
    def test_hil_node_interrupt_before(self):
        """When interrupt_before=True and pending_human_review=True, node should return early."""
        node = HumanInTheLoopNode(
            name="approval",
            prompt="Do you approve?",
            interrupt_before=True,
            interrupt_after=False,
        )

        state = {
            "pending_human_review": True,
            "hitl_prompt": None,
            "last_node": None,
        }

        result = node(state)

        assert result["interrupt_reason"] == "Do you approve?"
        assert result["last_node"] == "approval"

    def test_hil_node_no_interrupt_passes_through(self):
        """When pending_human_review=False, node should store prompt and proceed."""
        node = HumanInTheLoopNode(
            name="ask",
            prompt="Enter input",
            interrupt_before=True,
            interrupt_after=False,
        )

        state = {"pending_human_review": False, "hitl_prompt": None, "last_node": None}
        result = node(state)

        assert result["hitl_prompt"] == "Enter input"
        assert result["last_node"] == "ask"

    def test_hil_node_interrupt_after_sets_pending(self):
        """When interrupt_after=True, node should set pending_human_review=True."""
        node = HumanInTheLoopNode(
            name="check",
            prompt="Review output",
            interrupt_before=False,
            interrupt_after=True,
        )

        state = {"pending_human_review": False, "interrupt_reason": None, "last_node": None}
        result = node(state)

        assert result["pending_human_review"] is True
        assert result["interrupt_reason"] == "Review output"

    def test_hil_resolve(self):
        """resolve() should clear flags and store approval/input."""
        node = HumanInTheLoopNode(name="hilt")

        state = {"pending_human_review": True, "approved": None, "human_input": None}
        result = node.resolve(state, approved=True, input_text="looks good")

        assert result["approved"] is True
        assert result["human_input"] == "looks good"
        assert result["pending_human_review"] is False
        assert result["interrupt_reason"] is None


# ─────────────────────────────────────────────────────────────────────────────
# ConditionalRouterNode Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestConditionalRouterNode:
    def test_conditional_router_routes_high(self):
        """Router should set __next_node__ based on routing function return."""
        def routing_fn(state):
            confidence = state.get("confidence", 0.0)
            return "high" if confidence >= 0.8 else "low"

        node = ConditionalRouterNode(
            name="router",
            routing_fn=routing_fn,
            mapping={"high": "execute", "low": "retry"},
            default="retry",
        )

        state = {"confidence": 0.9, "__next_node__": None, "last_node": None}
        result = node(state)

        assert result["__next_node__"] == "execute"
        assert result["route_key"] == "high"
        assert result["last_node"] == "router"

    def test_conditional_router_routes_low(self):
        """Router should fall back to default when key not in mapping."""
        def routing_fn(state):
            return "medium"

        node = ConditionalRouterNode(
            name="router2",
            routing_fn=routing_fn,
            mapping={"high": "exec", "low": "retry"},
            default="retry",
        )

        state = {"confidence": 0.3, "__next_node__": None}
        result = node(state)

        assert result["__next_node__"] == "retry"

    def test_conditional_router_handles_exception(self):
        """Router should use default when routing_fn raises."""
        def bad_router(state):
            raise RuntimeError("routing failed")

        node = ConditionalRouterNode(
            name="bad",
            routing_fn=bad_router,
            mapping={},
            default="fallback",
        )

        state = {"__next_node__": None}
        result = node(state)

        assert result["__next_node__"] == "fallback"


# ─────────────────────────────────────────────────────────────────────────────
# Node Factories
# ─────────────────────────────────────────────────────────────────────────────

class TestNodeFactories:
    def test_passthrough_node(self):
        """passthrough_node should return state with last_node set."""
        fn = passthrough_node("passthrough")
        state = {"data": "value", "last_node": None}
        result = fn(state)
        assert result["last_node"] == "passthrough"
        assert result["data"] == "value"

    def test_map_node(self):
        """map_node should apply fn to state[key]."""
        fn = map_node("doubler", "value", lambda x: x * 2)
        state = {"value": 21, "last_node": None}
        result = fn(state)
        assert result["value"] == 42
        assert result["last_node"] == "doubler"

    def test_map_node_handles_error(self):
        """map_node should handle fn exceptions gracefully."""
        fn = map_node("crasher", "value", lambda x: x / 0)
        state = {"value": 1, "last_node": None}
        result = fn(state)
        assert "error" in result
        assert result["last_node"] == "crasher"
