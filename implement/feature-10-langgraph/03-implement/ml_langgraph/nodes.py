"""
nodes.py - Built-in node types for LangGraph workflow orchestration.

FR-102: Core node interface and built-in node implementations.
"""

from __future__ import annotations

import logging
from typing import Any, Callable, Literal

logger = logging.getLogger(__name__)

# Type alias: a node function takes StateT and returns StateT
StateT = dict[str, Any]
NodeFunction = Callable[[StateT], StateT]


# ---------------------------------------------------------------------------
# Base node interface
# ---------------------------------------------------------------------------

class BaseNode:
    """
    Abstract base for all node types.

    Subclasses must implement:
        __call__(self, state: StateT) -> StateT
    """

    name: str
    description: str | None

    def __init__(self, name: str, description: str | None = None) -> None:
        self.name = name
        self.description = description

    def __call__(self, state: StateT) -> StateT:
        raise NotImplementedError

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name!r}>"


# ---------------------------------------------------------------------------
# ToolNode
# ---------------------------------------------------------------------------

class ToolNode(BaseNode):
    """
    Node that wraps an external tool function.

    Executes ``tool_func`` with ``tool_args`` extracted from the current state,
    then appends the result to ``intermediate_results`` in state.

    Usage:
        tool_node = ToolNode(
            name="search",
            tool_func=my_search_api,
            description="Search external knowledge base",
        )
        state = graph.invoke({"query": "What is AI?", "intermediate_results": []})
        # state["intermediate_results"] now contains the tool output
    """

    def __init__(
        self,
        name: str,
        tool_func: Callable[..., Any],
        description: str | None = None,
        *,
        result_key: str = "result",
    ) -> None:
        """
        Args:
            name: Node identifier used in graph edges.
            tool_func: Arbitrary callable to invoke. It receives whatever
                keyword arguments are extracted from state (see ``arg_keys``).
            description: Human-readable description for documentation / viz.
            result_key: Key in state under which to store the tool's raw return
                value (default "result"). Set to None to discard the return.
        """
        super().__init__(name, description)
        self.tool_func = tool_func
        self.result_key = result_key

    def __call__(self, state: StateT) -> StateT:
        """
        Execute the wrapped tool and update state.

        Args:
            state: Current graph state. Must contain:
                - ``tool_args``: dict of kwargs passed to tool_func
                - ``intermediate_results``: list that this call appends to

        Returns:
            Updated state dict.
        """
        tool_args: dict[str, Any] = state.get("tool_args", {})
        intermediate: list[Any] = state.get("intermediate_results", [])

        try:
            logger.debug("[ToolNode:%s] invoking with args=%s", self.name, tool_args)
            result = self.tool_func(**tool_args)
            logger.debug("[ToolNode:%s] result=%s", self.name, result)

            if self.result_key is not None:
                state[self.result_key] = result

            intermediate.append({
                "node": self.name,
                "tool": getattr(self.tool_func, "__name__", repr(self.tool_func)),
                "result": result,
            })
            state["intermediate_results"] = intermediate
            state["last_node"] = self.name

        except Exception as exc:  # pragma: no cover – error handling varies by tool
            logger.exception("[ToolNode:%s] tool raised %s", self.name, exc)
            state["error"] = repr(exc)
            state["last_node"] = self.name

        return state

    def with_args(self, **fixed_args: Any) -> Callable[[StateT], StateT]:
        """
        Partially bind arguments to this tool node.

        Returns a new node that merges state-derived args with ``fixed_args``.
        """
        def bound_call(state: StateT) -> StateT:
            merged = {**fixed_args, **state.get("tool_args", {})}
            new_state = {**state, "tool_args": merged}
            return self(new_state)
        return bound_call


# ---------------------------------------------------------------------------
# LLMNode
# ---------------------------------------------------------------------------

class LLMNode(BaseNode):
    """
    Node that calls an LLM (or any chat model) and writes the response to state.

    Example::

        llm_node = LLMNode(
            name="generate",
            llm=my_llm,
            prompt_template="Answer: {query}",
            output_key="answer",
        )
        state = llm_node({"query": "What is 2+2?", "answer": None})
        assert state["answer"] == "4"
    """

    def __init__(
        self,
        name: str,
        llm: Any,  # duck-typed: supports .invoke() or .chat()
        prompt_template: str,
        output_key: str = "llm_output",
        *,
        system_prompt: str | None = None,
        max_tokens: int | None = None,
        temperature: float | None = None,
    ) -> None:
        """
        Args:
            name: Node identifier.
            llm: Any model client with a ``.invoke(messages)`` method
                (compatible with langchain.ChatModel, OpenAI client, etc.).
            prompt_template: f-string style template. Fields are filled from state.
            output_key: Key in state where the LLM response text is stored.
            system_prompt: Optional system message prepended to the prompt.
            max_tokens: Optional token limit passed to the model.
            temperature: Optional sampling temperature.
        """
        super().__init__(name, description=None)
        self.llm = llm
        self.prompt_template = prompt_template
        self.output_key = output_key
        self.system_prompt = system_prompt
        self.max_tokens = max_tokens
        self.temperature = temperature

    def __call__(self, state: StateT) -> StateT:
        """
        Render the prompt from state and invoke the LLM.

        Returns:
            Updated state with ``output_key`` set to the model's response.
        """
        # Build messages
        prompt_text = self.prompt_template.format(**state)
        messages: list[dict[str, str]] = []
        if self.system_prompt:
            messages.append({"role": "system", "content": self.system_prompt})
        messages.append({"role": "user", "content": prompt_text})

        # Invoke
        try:
            logger.debug("[LLMNode:%s] prompt length=%d", self.name, len(prompt_text))

            kwargs: dict[str, Any] = {"messages": messages}
            if self.max_tokens is not None:
                kwargs["max_tokens"] = self.max_tokens
            if self.temperature is not None:
                kwargs["temperature"] = self.temperature

            # Support both .invoke() (langchain-style) and .chat() (OpenAI-style)
            if hasattr(self.llm, "invoke"):
                response = self.llm.invoke(**kwargs)
            elif hasattr(self.llm, "chat"):
                response = self.llm.chat(**kwargs)
            else:  # pragma: no cover
                raise TypeError(f"LLM object has neither .invoke nor .chat: {type(self.llm)}")

            # Extract text – handle common response shapes
            text = self._extract_text(response)
            state[self.output_key] = text
            state["last_node"] = self.name

            logger.debug("[LLMNode:%s] output length=%d", self.name, len(text))

        except Exception as exc:
            logger.exception("[LLMNode:%s] LLM call failed: %s", self.name, exc)
            state["error"] = repr(exc)
            state["last_node"] = self.name

        return state

    def _extract_text(self, response: Any) -> str:
        """Extract string content from a model response object."""
        # LangChain ChatResult
        if hasattr(response, "content"):
            return str(response.content)
        # OpenAI-style / dict response
        if isinstance(response, dict):
            for key in ("text", "message", "output", "result"):
                if key in response:
                    val = response[key]
                    if isinstance(val, str):
                        return val
                    if isinstance(val, dict) and "content" in val:
                        return str(val["content"])
        if isinstance(response, str):
            return response
        return str(response)


# ---------------------------------------------------------------------------
# HumanInTheLoopNode
# ---------------------------------------------------------------------------

class HumanInTheLoopNode(BaseNode):
    """
    Node that pauses the graph for human approval or input before continuing.

    Two interruption points are supported:
        - ``interrupt_before``: pause before this node's logic and wait for
          the human to set ``pending_human_review`` back to False/None.
        - ``interrupt_after``: pause after this node's logic and wait for
          human confirmation before the graph proceeds to the next node.

    Usage::

        hitl = HumanInTheLoopNode(
            name="approval",
            prompt="Do you approve this action?",
            interrupt_before=True,
            interrupt_after=False,
        )

        # In the runtime loop:
        #   if state.get("pending_human_review"):
        #       yield "WAIT"   # halt execution until human resolves
    """

    def __init__(
        self,
        name: str,
        prompt: str,
        interrupt_before: bool = True,
        interrupt_after: bool = False,
        *,
        approval_key: str = "approved",
        input_key: str = "human_input",
    ) -> None:
        """
        Args:
            name: Node identifier.
            prompt: Message shown to the human when interrupting.
            interrupt_before: If True, halt before processing and wait for
                ``pending_human_review`` to be cleared.
            interrupt_after: If True, halt after processing and wait for
                the human to set ``pending_human_review`` back to False/None.
            approval_key: Key in state storing the human's boolean decision.
            input_key: Key in state storing optional text input from the human.
        """
        super().__init__(name, description=prompt)
        self.prompt = prompt
        self.interrupt_before = interrupt_before
        self.interrupt_after = interrupt_after
        self.approval_key = approval_key
        self.input_key = input_key

    def __call__(self, state: StateT) -> StateT:
        """
        Check interruption flags and update state.

        The caller (runtime / graph executor) is responsible for actually
        yielding/suspending when this method returns with ``pending_human_review``
        still set.

        Returns:
            Updated state. If interrupted, ``pending_human_review`` remains True.
        """
        pending = state.get("pending_human_review", False)

        # Before interrupt
        if self.interrupt_before and pending:
            logger.info("[HumanInTheLoopNode:%s] waiting (interrupt_before)", self.name)
            state["interrupt_reason"] = self.prompt
            return state

        # Process – store prompt for the human to see
        state["hitl_prompt"] = self.prompt
        state["last_node"] = self.name

        # After interrupt
        if self.interrupt_after:
            pending = state.get("pending_human_review", False)
            state["pending_human_review"] = True
            state["interrupt_reason"] = self.prompt
            logger.info("[HumanInTheLoopNode:%s] waiting (interrupt_after)", self.name)

        return state

    def resolve(self, state: StateT, approved: bool, input_text: str | None = None) -> StateT:
        """
        Called by the application layer to resolve a pending interrupt.

        Args:
            state: Current graph state.
            approved: Human's approval decision.
            input_text: Optional free-text input.

        Returns:
            Updated state with ``pending_human_review`` cleared.
        """
        state[self.approval_key] = approved
        if input_text is not None:
            state[self.input_key] = input_text
        state["pending_human_review"] = False
        state["interrupt_reason"] = None
        return state


# ---------------------------------------------------------------------------
# ConditionalRouterNode
# ---------------------------------------------------------------------------

class ConditionalRouterNode(BaseNode):
    """
    Node that inspects the current state and decides which named node to run next.

    The routing function returns a key, which is looked up in ``mapping``
    to produce the name of the next node.

    Usage::

        def route_by_intent(state):
            intent = state.get("intent", "unknown")
            if intent in ("search", "lookup"):
                return "search_node"
            elif intent == "generate":
                return "llm_node"
            return "fallback_node"

        router = ConditionalRouterNode(
            name="router",
            routing_fn=route_by_intent,
            mapping={
                "search_node": "search_node",
                "llm_node": "llm_node",
                "fallback_node": "fallback_node",
            },
        )

        state = router({"intent": "generate", "__next_node__": None})
        assert state["__next_node__"] == "llm_node"
    """

    def __init__(
        self,
        name: str,
        routing_fn: Callable[[StateT], str],
        mapping: dict[str, str],
        *,
        default: str | None = None,
    ) -> None:
        """
        Args:
            name: Node identifier.
            routing_fn: Function ``StateT -> str`` returning a routing key.
            mapping: Maps routing keys to target node names.
            default: Default target node name if routing key not in mapping.
        """
        super().__init__(name, description=None)
        self.routing_fn = routing_fn
        self.mapping = mapping
        self.default = default

    def __call__(self, state: StateT) -> StateT:
        """
        Evaluate the routing function and set ``__next_node__`` in state.

        Returns:
            Updated state with ``__next_node__`` set to the chosen node name.
        """
        try:
            key = self.routing_fn(state)
        except Exception as exc:
            logger.exception("[ConditionalRouterNode:%s] routing_fn raised: %s", self.name, exc)
            key = self.default

        target = self.mapping.get(key, self.default)
        if target is None:
            logger.warning(
                "[ConditionalRouterNode:%s] routing key %r not in mapping "
                "and no default set. state=%s",
                self.name, key, state,
            )

        state["__next_node__"] = target
        state["last_node"] = self.name
        state["route_key"] = key

        logger.debug("[ConditionalRouterNode:%s] key=%r -> target=%r", self.name, key, target)
        return state


# ---------------------------------------------------------------------------
# Utility node factories
# ---------------------------------------------------------------------------

def passthrough_node(name: str) -> NodeFunction:
    """Return a node that simply returns state unchanged (identity function)."""
    def node(state: StateT) -> StateT:
        state["last_node"] = name
        return state
    return node


def map_node(
    name: str,
    key: str,
    fn: Callable[[Any], Any],
) -> NodeFunction:
    """
    Return a node that applies ``fn`` to ``state[key]`` and stores the result
    back in the same key.

    Args:
        name: Node name (used for ``last_node``).
        key: State key whose value is transformed.
        fn: Transform function applied to the value at ``key``.
    """
    def node(state: StateT) -> StateT:
        try:
            state[key] = fn(state[key])
        except Exception as exc:
            logger.exception("[map_node:%s] failed: %s", name, exc)
            state["error"] = repr(exc)
        state["last_node"] = name
        return state
    return node