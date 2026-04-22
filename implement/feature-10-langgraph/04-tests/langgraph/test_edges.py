"""
Tests for edges.py (EdgeItem, ConditionalEdgeItem, EdgeValidator, helper routers).

No langgraph dependency required.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from ml_langgraph.edges import (
    EdgeItem,
    ConditionalEdgeItem,
    EdgeValidator,
    EdgeValidationError,
    EdgeBuilder,
    route_by_confidence,
    route_by_result_count,
    route_by_error_count,
    merge_edges,
    get_all_nodes,
)


# ─────────────────────────────────────────────────────────────────────────────
# EdgeItem Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeItem:
    def test_edge_item_creation(self):
        edge = EdgeItem(source="a", target="b")
        assert edge.source == "a"
        assert edge.target == "b"

    def test_edge_item_repr(self):
        edge = EdgeItem(source="x", target="y")
        assert "x" in repr(edge)
        assert "y" in repr(edge)

    def test_edge_item_hashable(self):
        """EdgeItem should be usable in sets and as dict keys."""
        a = EdgeItem("n1", "n2")
        b = EdgeItem("n1", "n2")
        assert a == b
        assert hash(a) == hash(b)

    def test_edge_item_inequality(self):
        a = EdgeItem("n1", "n2")
        c = EdgeItem("n1", "n3")
        assert a != c


# ─────────────────────────────────────────────────────────────────────────────
# ConditionalEdgeItem Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestConditionalEdgeItem:
    def test_route_returns_target_from_mapping(self):
        routing_fn = MagicMock(return_value="high")
        cond = ConditionalEdgeItem(
            source="decide",
            routing_fn=routing_fn,
            mapping={"high": "execute", "low": "retry"},
            default="retry",
        )
        state = {"confidence": 0.9}
        result = cond.route(state)
        assert result == "execute"
        routing_fn.assert_called_once_with(state)

    def test_route_returns_default_when_key_not_in_mapping(self):
        routing_fn = MagicMock(return_value="unknown")
        cond = ConditionalEdgeItem(
            source="decide",
            routing_fn=routing_fn,
            mapping={"high": "execute"},
            default="fallback",
        )
        result = cond.route({})
        assert result == "fallback"

    def test_route_returns_none_when_no_default(self):
        routing_fn = MagicMock(return_value="unmapped")
        cond = ConditionalEdgeItem(
            source="decide",
            routing_fn=routing_fn,
            mapping={},
        )
        result = cond.route({})
        assert result is None


# ─────────────────────────────────────────────────────────────────────────────
# Route Helper Functions
# ─────────────────────────────────────────────────────────────────────────────

class TestRouteByConfidence:
    def test_route_by_confidence_high(self):
        state = {"confidence": 0.9}
        result = route_by_confidence(state, threshold=0.5)
        assert result == "high_confidence"

    def test_route_by_confidence_low(self):
        state = {"confidence": 0.3}
        result = route_by_confidence(state, threshold=0.5)
        assert result == "low_confidence"

    def test_route_by_confidence_missing_key(self):
        state = {}
        with pytest.raises(KeyError):
            route_by_confidence(state, threshold=0.5)


class TestRouteByResultCount:
    def test_route_by_result_count_sufficient(self):
        state = {"results": [1, 2, 3, 4, 5]}
        result = route_by_result_count(state, min_count=3)
        assert result == "sufficient"

    def test_route_by_result_count_insufficient(self):
        state = {"results": [1]}
        result = route_by_result_count(state, min_count=3)
        assert result == "insufficient"

    def test_route_by_result_count_empty(self):
        state = {"results": []}
        result = route_by_result_count(state, min_count=1)
        assert result == "insufficient"

    def test_route_by_result_count_non_list(self):
        """Non-list results should be treated as empty."""
        state = {"results": "not a list"}
        result = route_by_result_count(state, min_count=1)
        assert result == "insufficient"


# ─────────────────────────────────────────────────────────────────────────────
# EdgeValidator Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeValidator:
    def test_validate_edge_valid(self):
        edges = [EdgeItem("a", "b"), EdgeItem("b", "c")]
        nodes = {"a", "b", "c"}
        errors = EdgeValidator.validate_edge(edges, nodes)
        assert errors == []

    def test_validate_edge_unknown_source(self):
        edges = [EdgeItem("x", "b")]
        nodes = {"a", "b", "c"}
        errors = EdgeValidator.validate_edge(edges, nodes)
        assert any("x" in e and "source" in e for e in errors)

    def test_validate_edge_unknown_target(self):
        edges = [EdgeItem("a", "z")]
        nodes = {"a", "b", "c"}
        errors = EdgeValidator.validate_edge(edges, nodes)
        assert any("z" in e and "target" in e for e in errors)

    def test_validate_edge_detect_duplicate(self):
        edges = [EdgeItem("a", "b"), EdgeItem("a", "b")]
        nodes = {"a", "b"}
        errors = EdgeValidator.validate_edge(edges, nodes)
        assert any("Duplicate" in e for e in errors)

    def test_edge_validator_detect_orphaned(self):
        """detect_orphaned_nodes should return unreachable and no-outgoing nodes."""
        edges = [EdgeItem("a", "b")]
        nodes = {"a", "b", "c"}  # c is unreachable from entry point
        result = EdgeValidator.detect_orphaned_nodes(
            edges, nodes, entry_point="a"
        )
        assert "c" in result["unreachable"]
        assert "c" in result["no_incoming"]

    def test_detect_orphaned_with_entry_point(self):
        """Node with no incoming edges but is entry point should not be orphaned."""
        edges = [EdgeItem("start", "next")]
        nodes = {"start", "next", "orphan"}
        result = EdgeValidator.detect_orphaned_nodes(
            edges, nodes, entry_point="start"
        )
        # "start" is the entry point so should not appear in no_incoming
        assert "start" not in result["no_incoming"]

    def test_detect_orphaned_no_outgoing(self):
        """A node with no outgoing edges should appear in no_outgoing."""
        edges = [EdgeItem("a", "b")]
        nodes = {"a", "b"}
        result = EdgeValidator.detect_orphaned_nodes(edges, nodes, entry_point="a")
        assert "b" in result["no_outgoing"]


# ─────────────────────────────────────────────────────────────────────────────
# EdgeBuilder Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestEdgeBuilder:
    def test_builder_add(self):
        builder = EdgeBuilder()
        result = builder.add("a", "b").add("b", "c")
        assert result is builder
        edges = builder.build()
        assert len(edges) == 2
        assert edges[0].source == "a"

    def test_builder_chained_add(self):
        edges = EdgeBuilder().add("x", "y").add("y", "z").build()
        assert len(edges) == 2


# ─────────────────────────────────────────────────────────────────────────────
# Composite Edge Helpers
# ─────────────────────────────────────────────────────────────────────────────

class TestMergeEdges:
    def test_merge_edges_deduplicates(self):
        list_a = [EdgeItem("a", "b")]
        list_b = [EdgeItem("a", "b"), EdgeItem("b", "c")]
        merged = merge_edges([list_a, list_b])
        assert len(merged) == 2

    def test_merge_edges_empty_lists(self):
        merged = merge_edges([])
        assert merged == []


class TestGetAllNodes:
    def test_get_all_nodes_extracts_sources_and_targets(self):
        edges = [EdgeItem("a", "b"), EdgeItem("b", "c")]
        nodes = get_all_nodes(edges)
        assert nodes == {"a", "b", "c"}
