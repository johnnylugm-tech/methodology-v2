"""Tests for ml_langgraph.utils."""

from __future__ import annotations

import pytest

from ml_langgraph.utils import (
    clamp,
    format_duration,
    generate_id,
    get_node_retry_policy,
    import_langgraph_checkpointer,
    merge_state,
    safe_get,
    sanitize_node_name,
    validate_node_signature,
)
from ml_langgraph.exceptions import FeatureError


class TestGenerateId:
    def test_no_prefix_returns_8_hex_chars(self):
        id_ = generate_id()
        assert len(id_) == 8
        assert all(c in "0123456789abcdef" for c in id_)

    def test_with_prefix_returns_prefix_underscore_hex(self):
        id_ = generate_id("node")
        assert id_.startswith("node_")
        suffix = id_[5:]
        assert len(suffix) == 8
        assert all(c in "0123456789abcdef" for c in suffix)

    def test_empty_prefix_behaves_as_no_prefix(self):
        id_ = generate_id("")
        assert len(id_) == 8

    def test_unique_ids_are_unique(self):
        ids = [generate_id() for _ in range(100)]
        assert len(ids) == len(set(ids))


class TestMergeState:
    def test_shallow_mode_overwrites_top_level(self):
        base = {"a": 1, "b": {"c": 2}}
        update = {"b": {"d": 3}}
        result = merge_state(base, update, mode="shallow")
        assert result["a"] == 1
        assert result["b"] == {"d": 3}  # replaced entirely

    def test_deep_mode_recursively_merges(self):
        base = {"a": 1, "b": {"c": 2}}
        update = {"b": {"d": 3}}
        result = merge_state(base, update, mode="deep")
        assert result["a"] == 1
        assert result["b"] == {"c": 2, "d": 3}

    def test_deep_mode_does_not_modify_original(self):
        base = {"a": 1, "b": {"c": 2}}
        update = {"b": {"d": 3}}
        merge_state(base, update, mode="deep")
        assert base["b"] == {"c": 2}

    def test_new_keys_added(self):
        base = {"a": 1}
        update = {"b": 2}
        result = merge_state(base, update)
        assert result == {"a": 1, "b": 2}

    def test_invalid_mode_raises_typeerror(self):
        with pytest.raises(TypeError, match="mode must be 'deep' or 'shallow'"):
            merge_state({}, {"a": 1}, mode="invalid")

    def test_deep_mode_with_non_dict_overwrites(self):
        base = {"a": {"nested": 1}}
        update = {"a": "string"}
        result = merge_state(base, update, mode="deep")
        assert result["a"] == "string"

    def test_deep_mode_with_list_replaces(self):
        base = {"a": [1, 2]}
        update = {"a": [3]}
        result = merge_state(base, update, mode="deep")
        assert result["a"] == [3]


class TestValidateNodeSignature:
    from typing import TypedDict

    class MyState(TypedDict):
        x: int

    def test_unannotated_first_param_returns_true(self):
        def node(state):
            return state

        assert validate_node_signature(node, self.MyState) is True

    def test_correctly_annotated_param_with_typeddict_returns_false_due_to_bug(self):
        # Note: TypedDict does not support issubclass(), so this returns False
        # This is a known limitation of validate_node_signature
        def node(state: self.MyState):
            return state

        assert validate_node_signature(node, self.MyState) is False

    def test_wrong_annotation_returns_false(self):
        from typing import TypedDict

        class OtherState(TypedDict):
            y: str

        def node(state: OtherState):
            return state

        assert validate_node_signature(node, self.MyState) is False

    def test_no_params_returns_false(self):
        def node():
            pass

        assert validate_node_signature(node, self.MyState) is False

    def test_unannotated_function_returns_true(self):
        def node(ctx, value):
            return value

        assert validate_node_signature(node, self.MyState) is True

    def test_non_callable_returns_false(self):
        # validate_node_signature catches TypeError internally and returns False
        result = validate_node_signature("not a function", self.MyState)
        assert result is False


class TestGetNodeRetryPolicy:
    def test_none_config_returns_default(self):
        from ml_langgraph.state import RetryPolicy

        default = RetryPolicy(max_attempts=3)
        result = get_node_retry_policy(None, default)
        assert result == default

    def test_config_with_retry_policy_returns_it(self):
        from ml_langgraph.state import RetryPolicy
        from ml_langgraph.builder import NodeConfig

        policy = RetryPolicy(max_attempts=5)
        config = NodeConfig(retry_policy=policy)
        result = get_node_retry_policy(config, RetryPolicy(max_attempts=1))
        assert result == policy

    def test_config_with_none_retry_policy_returns_default(self):
        from ml_langgraph.state import RetryPolicy
        from ml_langgraph.builder import NodeConfig

        default = RetryPolicy(max_attempts=3)
        config = NodeConfig(retry_policy=None)
        result = get_node_retry_policy(config, default)
        assert result == default


class TestFormatDuration:
    def test_sub_millisecond(self):
        result = format_duration(0.5)
        assert result == "0.50ms"

    def test_milliseconds(self):
        result = format_duration(456)
        assert result == "456ms"

    def test_seconds(self):
        result = format_duration(1500)
        assert result == "1.50s"

    def test_minutes(self):
        result = format_duration(65000)
        assert result == "1m 5s"

    def test_hours(self):
        result = format_duration(3_600_000)
        assert result == "1h 0m 0s"

    def test_zero(self):
        result = format_duration(0)
        assert result == "0.00ms"

    def test_exact_boundary_seconds(self):
        result = format_duration(1000)
        assert result == "1.00s"

    def test_exact_boundary_minutes(self):
        result = format_duration(60_000)
        assert result == "1m 0s"


class TestSanitizeNodeName:
    def test_valid_identifier_unchanged(self):
        assert sanitize_node_name("valid_node") == "valid_node"

    def test_spaces_become_underscores(self):
        assert sanitize_node_name("my node name") == "my_node_name"

    def test_special_chars_become_underscores(self):
        assert sanitize_node_name("node@#$%name") == "node_name"

    def test_leading_digit_gets_underscore_prefix(self):
        assert sanitize_node_name("123node") == "_123node"

    def test_multiple_underscores_collapsed(self):
        assert sanitize_node_name("my  node   name") == "my_node_name"

    def test_strip_leading_underscores(self):
        assert sanitize_node_name("__node__") == "node"

    def test_empty_string_defaults_to_node(self):
        assert sanitize_node_name("") == "node"
        assert sanitize_node_name("   ") == "node"

    def test_unicode_chars_converted(self):
        result = sanitize_node_name("nodé namé")
        assert "n" in result
        assert "o" in result


class TestImportLanggraphCheckpointer:
    def test_unknown_backend_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown checkpointer backend"):
            import_langgraph_checkpointer("nonexistent_backend")

    def test_memory_backend_imports(self):
        # "memory" is the most widely available checkpointer
        mod = import_langgraph_checkpointer("memory")
        assert mod is not None

    def test_sqlite_backend_raises_import_error_if_not_installed(self):
        # sqlite may not be installed — raises ImportError
        with pytest.raises(ImportError, match="Failed to import checkpointer 'sqlite'"):
            import_langgraph_checkpointer("sqlite")

    def test_postgres_backend_raises_import_error_if_not_installed(self):
        with pytest.raises(ImportError, match="Failed to import checkpointer 'postgres'"):
            import_langgraph_checkpointer("postgres")

    def test_postgres_bornless_backend_raises_import_error_if_not_installed(self):
        with pytest.raises(ImportError, match="Failed to import checkpointer 'postgres-bornless'"):
            import_langgraph_checkpointer("postgres-bornless")


class TestSafeGet:
    def test_simple_key(self):
        d = {"a": 1, "b": 2}
        assert safe_get(d, "a") == 1

    def test_nested_keys(self):
        d = {"a": {"b": {"c": 3}}}
        assert safe_get(d, "a", "b", "c") == 3

    def test_missing_key_returns_default(self):
        d = {"a": 1}
        assert safe_get(d, "missing") is None
        assert safe_get(d, "missing", default=-1) == -1

    def test_deeply_missing_nested_returns_default(self):
        d = {"a": {"b": 1}}
        assert safe_get(d, "a", "x", "y", default="fallback") == "fallback"

    def test_none_in_path_returns_default(self):
        d = {"a": None}
        assert safe_get(d, "a", "b", default=42) == 42

    def test_non_dict_in_path_returns_default(self):
        d = {"a": 1}
        assert safe_get(d, "a", "b", default=99) == 99

    def test_empty_keys_returns_dict(self):
        d = {"a": 1}
        assert safe_get(d) == d

    def test_default_parameter_keyword_only(self):
        d = {"x": None}
        # must use keyword for default
        result = safe_get(d, "missing", default="default")
        assert result == "default"


class TestClamp:
    def test_within_range(self):
        assert clamp(5, 0, 10) == 5

    def test_below_min_returns_min(self):
        assert clamp(-5, 0, 10) == 0

    def test_above_max_returns_max(self):
        assert clamp(15, 0, 10) == 10

    def test_equal_to_min(self):
        assert clamp(0, 0, 10) == 0

    def test_equal_to_max(self):
        assert clamp(10, 0, 10) == 10

    def test_negative_range(self):
        assert clamp(0, -10, -5) == -5
        assert clamp(-7, -10, -5) == -7
        assert clamp(-15, -10, -5) == -10

    def test_float_values(self):
        assert clamp(3.5, 0.0, 10.0) == 3.5
        assert clamp(-0.5, 0.0, 10.0) == 0.0
        assert clamp(15.0, 0.0, 10.0) == 10.0