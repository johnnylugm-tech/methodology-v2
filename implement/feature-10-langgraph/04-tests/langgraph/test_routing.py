"""
Tests for routing.py (Router and pre-built routing functions).

No langgraph dependency required.
"""

from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from ml_langgraph.routing import (
    Router,
    RouteResult,
    confidence_router,
    count_router,
    error_router,
    bool_router,
    regex_router,
    chain_routers,
    fallback_router,
)


# ─────────────────────────────────────────────────────────────────────────────
# RouteResult dataclass
# ─────────────────────────────────────────────────────────────────────────────

class TestRouteResult:
    def test_route_result_frozen(self):
        """RouteResult should be frozen (immutable)."""
        result = RouteResult(route_key="test", target_nodes=["a"], metadata={})
        assert result.route_key == "test"

    def test_route_result_target_nodes_copy(self):
        """target_nodes should be a copy to prevent mutation."""
        original = ["a", "b"]
        result = RouteResult(route_key="k", target_nodes=original)
        result.target_nodes.append("c")
        assert result.target_nodes == ["a", "b"]
        assert original == ["a", "b"]

    def test_route_result_metadata(self):
        """metadata dict should be stored."""
        meta = {"source": "router"}
        result = RouteResult(route_key="k", target_nodes=[], metadata=meta)
        assert result.metadata["source"] == "router"


# ─────────────────────────────────────────────────────────────────────────────
# Router Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestRouter:
    def test_router_valid_route(self):
        """Router.route() should return RouteResult for valid route key."""
        router = Router({"draft": ["write"], "revise": ["review"]})

        routing_fn = MagicMock(return_value="draft")
        result = router.route({}, routing_fn)

        assert result.route_key == "draft"
        assert result.target_nodes == ["write"]

    def test_router_unknown_key_raises(self):
        """Router.route() should raise ValueError for unknown key."""
        router = Router({"known": ["node"]})
        routing_fn = MagicMock(return_value="unknown-key")

        with pytest.raises(ValueError, match="unknown"):
            router.route({}, routing_fn)

    def test_router_get_targets(self):
        """get_targets() should return node list for a key."""
        router = Router({"k1": ["a", "b"], "k2": ["c"]})
        assert router.get_targets("k1") == ["a", "b"]
        assert router.get_targets("missing") == []

    def test_router_rejects_non_list_nodes(self):
        """Router should reject routes mapping to non-list values."""
        with pytest.raises(TypeError, match="list"):
            Router({"key": "not-a-list"})

    def test_router_rejects_non_string_nodes(self):
        """Router should reject routes with non-string node names."""
        with pytest.raises(TypeError, match="string"):
            Router({"key": [1, 2, 3]})


# ─────────────────────────────────────────────────────────────────────────────
# Pre-built Routing Functions
# ─────────────────────────────────────────────────────────────────────────────

class TestConfidenceRouter:
    def test_confidence_router_high(self):
        """confidence_router should return high key when confidence >= threshold."""
        router_fn = confidence_router({"high": 0.8, "medium": 0.5, "low": 0.0})
        assert router_fn({"confidence": 0.9}) == "high"
        assert router_fn({"confidence": 0.8}) == "high"

    def test_confidence_router_medium(self):
        router_fn = confidence_router({"high": 0.8, "medium": 0.5, "low": 0.0})
        assert router_fn({"confidence": 0.6}) == "medium"
        assert router_fn({"confidence": 0.5}) == "medium"

    def test_confidence_router_low(self):
        router_fn = confidence_router({"high": 0.8, "medium": 0.5, "low": 0.0})
        assert router_fn({"confidence": 0.3}) == "low"
        assert router_fn({"confidence": 0.0}) == "low"

    def test_confidence_router_defaults_to_lowest(self):
        """When no threshold matches, should return the lowest threshold key."""
        router_fn = confidence_router({"high": 0.8, "medium": 0.5, "low": 0.0})
        assert router_fn({"confidence": -0.5}) == "low"

    def test_confidence_router_non_numeric_raises(self):
        """Non-numeric confidence should raise TypeError."""
        router_fn = confidence_router({"high": 0.8})
        with pytest.raises(TypeError, match="confidence"):
            router_fn({"confidence": "very high"})

    def test_confidence_router_missing_key_uses_zero(self):
        """Missing confidence key should default to 0.0."""
        router_fn = confidence_router({"high": 0.8, "low": 0.0})
        assert router_fn({}) == "low"


class TestCountRouter:
    def test_count_router_above(self):
        """count_router should return above_key when len(results) >= min_count."""
        router_fn = count_router(3, "retry", "done")
        assert router_fn({"results": [1, 2, 3]}) == "done"
        assert router_fn({"results": [1, 2, 3, 4, 5]}) == "done"

    def test_count_router_below(self):
        router_fn = count_router(3, "retry", "done")
        assert router_fn({"results": [1, 2]}) == "retry"
        assert router_fn({"results": []}) == "retry"

    def test_count_router_missing_key(self):
        """Missing results key should be treated as empty list."""
        router_fn = count_router(1, "below", "above")
        assert router_fn({}) == "below"

    def test_count_router_non_list(self):
        """Non-list results should be treated as empty list."""
        router_fn = count_router(1, "below", "above")
        assert router_fn({"results": "not a list"}) == "below"


class TestErrorRouter:
    def test_error_router_ok(self):
        """error_router should return ok_key when len(errors) <= max_errors."""
        router_fn = error_router(2, "abort", "continue")
        assert router_fn({"errors": []}) == "continue"
        assert router_fn({"errors": ["e1"]}) == "continue"
        assert router_fn({"errors": ["e1", "e2"]}) == "continue"

    def test_error_router_exceeded(self):
        router_fn = error_router(2, "abort", "continue")
        assert router_fn({"errors": ["e1", "e2", "e3"]}) == "abort"

    def test_error_router_missing_key(self):
        """Missing errors key should be treated as empty list."""
        router_fn = error_router(0, "abort", "ok")
        assert router_fn({}) == "ok"


class TestBoolRouter:
    def test_bool_router_true_key(self):
        """bool_router should return true_key when flag is truthy."""
        router_fn = bool_router("is_valid", "process", "reject")
        assert router_fn({"is_valid": True}) == "process"
        assert router_fn({"is_valid": 1}) == "process"
        assert router_fn({"is_valid": "yes"}) == "process"

    def test_bool_router_false_key(self):
        """bool_router should return false_key when flag is falsy or missing."""
        router_fn = bool_router("is_valid", "process", "reject")
        assert router_fn({"is_valid": False}) == "reject"
        assert router_fn({"is_valid": None}) == "reject"
        assert router_fn({}) == "reject"


class TestRegexRouter:
    def test_regex_router_named_group(self):
        """regex_router should match named group and return route key."""
        router_fn = regex_router(
            r"(?P<severity>error|warn|info):\s*(?P<msg>.*)",
            {"severity": "typed_route"},
        )
        assert router_fn({"text": "error: out of memory"}) == "typed_route"
        assert router_fn({"text": "warn: low disk"}) == "typed_route"

    def test_regex_router_no_match_raises(self):
        """regex_router should raise ValueError when pattern doesn't match."""
        router_fn = regex_router(r"error: (?P<msg>.*)", {"msg": "route"})
        with pytest.raises(ValueError, match="did not match"):
            router_fn({"text": "no match here"})

    def test_regex_router_non_string_text_raises(self):
        """regex_router should raise TypeError for non-string text."""
        router_fn = regex_router(r"pattern", {"key": "route"})
        with pytest.raises(TypeError, match="string"):
            router_fn({"text": 123})


# ─────────────────────────────────────────────────────────────────────────────
# Composite Routing Helpers
# ─────────────────────────────────────────────────────────────────────────────

class TestChainRouters:
    def test_chain_routers_returns_first_non_empty(self):
        """chain_routers should return first router result that is non-empty."""
        routers = [
            MagicMock(return_value=""),
            MagicMock(return_value=""),
            MagicMock(return_value="found"),
        ]
        combined = chain_routers(*routers)
        result = combined({})
        assert result == "found"

    def test_chain_routers_raises_when_all_empty(self):
        """chain_routers should raise ValueError when all routers return empty."""
        routers = [MagicMock(return_value=""), MagicMock(return_value="")]
        combined = chain_routers(*routers)
        with pytest.raises(ValueError, match="empty string"):
            combined({})


class TestFallbackRouter:
    def test_fallback_router_primary(self):
        """fallback_router should return primary result when it succeeds."""
        primary = MagicMock(return_value="primary-result")
        combined = fallback_router(primary, "fallback-key")
        result = combined({})
        assert result == "primary-result"

    def test_fallback_router_falls_back_on_exception(self):
        """fallback_router should return fallback_key when primary raises."""
        primary = MagicMock(side_effect=RuntimeError("failed"))
        combined = fallback_router(primary, "fallback-key")
        result = combined({})
        assert result == "fallback-key"
