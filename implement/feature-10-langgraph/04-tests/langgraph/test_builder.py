"""
Tests for GraphBuilder (builder.py).

These tests mock the langgraph import to avoid requiring the actual package.
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import MagicMock, patch, Mock


# ─────────────────────────────────────────────────────────────────────────────
# Mock langgraph before importing the module under test
# ─────────────────────────────────────────────────────────────────────────────
_mock_StateGraph = MagicMock(name="StateGraph")
_mock_CompiledStateGraph = MagicMock(name="CompiledStateGraph")
_mock_END = MagicMock(name="END")

_pydantic_Field = MagicMock(name="pydantic.Field")

_module_patcher = patch.dict(
    "sys.modules",
    {
        "langgraph": MagicMock(),
        "langgraph.graph": MagicMock(
            StateGraph=_mock_StateGraph,
            END=_mock_END,
        ),
        "langgraph.graph.state": MagicMock(
            CompiledStateGraph=_mock_CompiledStateGraph,
        ),
        "pydantic": MagicMock(
            BaseModel=object,
            Field=lambda *a, **k: MagicMock(),
            ConfigDict=lambda **k: type("ConfigDict", (), {}),
        ),
        "pydantic.Field": _pydantic_Field,
        "pydantic.ConfigDict": lambda **k: type("ConfigDict", (), {}),
    },
)


with _module_patcher:
    from ml_langgraph.builder import (
        GraphBuilder,
        NodeItem,
        EdgeItem,
        ConditionalEdgeItem,
        NodeConfig,
        GraphCompileConfig,
    )
    from ml_langgraph.exceptions import (
        DuplicateNodeError,
        NodeNotFoundError,
        GraphValidationError,
    )


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_state_schema():
    """Minimal mock state schema (Pydantic model-like)."""
    schema = MagicMock()
    return schema


@pytest.fixture
def builder(mock_state_schema):
    """Fresh GraphBuilder instance."""
    return GraphBuilder(state_schema=mock_state_schema, name="test-graph")


# ─────────────────────────────────────────────────────────────────────────────
# NodeItem Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestNodeItem:
    def test_to_dict_without_config(self):
        func = MagicMock()
        item = NodeItem(name="node_a", func=func)
        d = item.to_dict()
        assert d["name"] == "node_a"
        assert "config" not in d

    def test_to_dict_with_config(self):
        func = MagicMock()
        item = NodeItem(name="node_a", func=func, config={"timeout": 30})
        d = item.to_dict()
        assert d["name"] == "node_a"
        assert d["config"] == {"timeout": 30}

    def test_from_dict(self):
        func = MagicMock()
        data = {"name": "node_b", "config": {"retry": True}}
        item = NodeItem.from_dict(data, func)
        assert item.name == "node_b"
        assert item.func is func
        assert item.config == {"retry": True}


# ─────────────────────────────────────────────────────────────────────────────
# EdgeItem Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeItem:
    def test_to_dict(self):
        edge = EdgeItem(source="a", target="b")
        d = edge.to_dict()
        assert d["source"] == "a"
        assert d["target"] == "b"

    def test_from_dict(self):
        data = {"source": "x", "target": "y"}
        edge = EdgeItem.from_dict(data)
        assert edge.source == "x"
        assert edge.target == "y"


# ─────────────────────────────────────────────────────────────────────────────
# ConditionalEdgeItem Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestConditionalEdgeItem:
    def test_to_dict(self):
        func = MagicMock()
        cond = ConditionalEdgeItem(
            source="decide",
            routing_fn=func,
            mapping={"high": "execute", "low": "retry"},
            default="retry",
        )
        d = cond.to_dict()
        assert d["source"] == "decide"
        assert d["mapping"] == {"high": "execute", "low": "retry"}
        assert d["default"] == "retry"

    def test_from_dict(self):
        func = MagicMock()
        data = {
            "source": "route",
            "mapping": {"a": "node1", "b": "node2"},
            "default": "node1",
        }
        cond = ConditionalEdgeItem.from_dict(data, func)
        assert cond.source == "route"
        assert cond.routing_fn is func
        assert cond.mapping == {"a": "node1", "b": "node2"}
        assert cond.default == "node1"


# ─────────────────────────────────────────────────────────────────────────────
# GraphBuilder Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestGraphBuilderBasic:
    def test_name_property(self, mock_state_schema):
        b = GraphBuilder(state_schema=mock_state_schema, name="my-graph")
        assert b.name == "my-graph"

    def test_node_names_empty(self, builder):
        assert builder.node_names == []

    def test_repr(self, builder):
        r = repr(builder)
        assert "test-graph" in r


class TestAddNode:
    def test_add_node(self, builder):
        func = MagicMock()
        result = builder.add_node("research", func)
        assert result is builder
        assert "research" in builder.node_names

    def test_add_node_duplicate_raises(self, builder):
        func = MagicMock()
        builder.add_node("dup", func)
        with pytest.raises(DuplicateNodeError) as exc_info:
            builder.add_node("dup", func)
        assert "dup" in str(exc_info.value)

    def test_add_nodes(self, builder):
        funcs = {"node1": MagicMock(), "node2": MagicMock()}
        result = builder.add_nodes(funcs)
        assert result is builder
        assert "node1" in builder.node_names
        assert "node2" in builder.node_names


class TestAddEdge:
    def test_add_edge(self, builder):
        builder.add_node("a", MagicMock())
        builder.add_node("b", MagicMock())
        result = builder.add_edge("a", "b")
        assert result is builder

    def test_add_edge_source_not_found(self, builder):
        builder.add_node("exists", MagicMock())
        with pytest.raises(NodeNotFoundError):
            builder.add_edge("missing", "exists")

    def test_add_edge_target_not_found(self, builder):
        builder.add_node("exists", MagicMock())
        with pytest.raises(NodeNotFoundError):
            builder.add_edge("exists", "missing")


class TestAddConditionalEdges:
    def test_add_conditional_edges(self, builder):
        routing_fn = MagicMock(return_value="high")
        builder.add_node("decide", MagicMock())
        builder.add_node("execute", MagicMock())
        builder.add_node("retry", MagicMock())
        result = builder.add_conditional_edges(
            source="decide",
            routing_fn=routing_fn,
            mapping={"high": "execute", "low": "retry"},
            default="retry",
        )
        assert result is builder

    def test_add_conditional_edges_source_not_found(self, builder):
        routing_fn = MagicMock(return_value="x")
        with pytest.raises(NodeNotFoundError):
            builder.add_conditional_edges(
                source="missing",
                routing_fn=routing_fn,
                mapping={},
            )

    def test_add_conditional_edges_unknown_target(self, builder):
        builder.add_node("decide", MagicMock())
        routing_fn = MagicMock(return_value="x")
        with pytest.raises(NodeNotFoundError):
            builder.add_conditional_edges(
                source="decide",
                routing_fn=routing_fn,
                mapping={"unknown_node": "execute"},
            )


class TestCompile:
    def test_compile_empty_raises(self, builder):
        with pytest.raises(GraphValidationError):
            builder.compile()

    def test_compile_single_node(self, builder, mock_state_schema):
        """Compiling a graph with one node should not raise."""
        builder.add_node("lonely", MagicMock())
        compiled = builder.compile()
        assert compiled is not None

    def test_compile_sets_entry_point_automatically(self, builder):
        """When entry point is not set, compile should not raise."""
        builder.add_node("only", MagicMock())
        compiled = builder.compile()
        assert compiled is not None


class TestSerialization:
    def test_to_json(self, builder):
        builder.add_node("a", MagicMock())
        builder.add_node("b", MagicMock())
        builder.add_edge("a", "b")
        json_str = builder.to_json()
        data = json.loads(json_str)
        assert data["name"] == "test-graph"
        assert len(data["nodes"]) == 2
        assert len(data["edges"]) == 1

    def test_from_json(self, mock_state_schema):
        func_a = MagicMock()
        func_b = MagicMock()
        node_functions = {"node_a": func_a, "node_b": func_b}

        # Create a builder manually to get valid JSON
        b = GraphBuilder(state_schema=mock_state_schema)
        b.add_node("node_a", func_a)
        b.add_node("node_b", func_b)
        b.add_edge("node_a", "node_b")
        json_str = b.to_json()

        # Round-trip
        restored = GraphBuilder.from_json(
            json_str,
            node_functions=node_functions,
            state_schema=mock_state_schema,
        )
        assert "node_a" in restored.node_names
        assert "node_b" in restored.node_names

    def test_from_json_missing_state_schema_raises(self):
        func = MagicMock()
        with pytest.raises(GraphValidationError):
            GraphBuilder.from_json('{"state_schema": "Foo"}', node_functions={"n": func})

    def test_from_json_missing_function_raises(self, mock_state_schema):
        with pytest.raises(GraphValidationError):
            GraphBuilder.from_json(
                '{"nodes": [{"name": "missing"}], "state_schema": "Foo"}',
                node_functions={},
                state_schema=mock_state_schema,
            )

    def test_to_json_from_json_roundtrip(self, builder):
        routing_fn = MagicMock(return_value="high")
        builder.add_node("decide", MagicMock())
        builder.add_node("execute", MagicMock())
        builder.add_edge("decide", "execute")
        builder.add_conditional_edges(
            source="decide",
            routing_fn=routing_fn,
            mapping={"high": "execute"},
            default="execute",
        )
        json_str = builder.to_json()
        data = json.loads(json_str)
        assert data["name"] == "test-graph"


class TestSetEntryPoint:
    def test_set_entry_point(self, builder):
        builder.add_node("start", MagicMock())
        builder.add_node("next", MagicMock())
        builder.set_entry_point("start")
        assert builder._entry_point == "start"

    def test_set_entry_point_unknown_raises(self, builder):
        with pytest.raises(NodeNotFoundError):
            builder.set_entry_point("unknown-node")
