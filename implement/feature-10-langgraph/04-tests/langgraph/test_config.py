"""
Tests for config.py (GraphConfig + load/validate/merge).

No langgraph dependency required.
"""

from __future__ import annotations

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

from ml_langgraph.config import (
    GraphConfig,
    DEFAULT_CONFIG,
    GraphConfig as GC,
    validate_config,
    merge_configs,
    load_config,
    load_config_or_default,
    config_to_dict,
    save_config,
)


# ─────────────────────────────────────────────────────────────────────────────
# GraphConfig dataclass
# ─────────────────────────────────────────────────────────────────────────────

class TestGraphConfigDefaults:
    def test_default_values(self):
        """GraphConfig should have sensible defaults."""
        config = GraphConfig()
        assert config.name == "langgraph_workflow"
        assert config.max_cycle_count == 100
        assert config.enable_state_persistence is True
        assert config.checkpoint_interval == 10
        assert config.debug is False
        assert config.timeout_ms == 300_000

    def test_custom_values(self):
        """GraphConfig should accept custom parameter values."""
        config = GraphConfig(
            name="my-workflow",
            max_cycle_count=50,
            enable_state_persistence=False,
            checkpoint_interval=5,
            debug=True,
            timeout_ms=60_000,
        )
        assert config.name == "my-workflow"
        assert config.max_cycle_count == 50
        assert config.enable_state_persistence is False
        assert config.checkpoint_interval == 5
        assert config.debug is True
        assert config.timeout_ms == 60_000


# ─────────────────────────────────────────────────────────────────────────────
# validate_config
# ─────────────────────────────────────────────────────────────────────────────

class TestValidateConfig:
    def test_validate_config_valid(self):
        """validate_config should return True for a valid config."""
        config = GraphConfig(name="valid", checkpoint_interval=5)
        assert validate_config(config) is True

    def test_validate_empty_name_raises(self):
        """Empty name string should raise ValueError."""
        config = GraphConfig(name="")
        with pytest.raises(ValueError, match="non-empty"):
            validate_config(config)

    def test_validate_whitespace_name_raises(self):
        """Whitespace-only name should raise ValueError."""
        config = GraphConfig(name="   ")
        with pytest.raises(ValueError, match="non-empty"):
            validate_config(config)

    def test_validate_negative_max_cycle_count_raises(self):
        """Negative max_cycle_count should raise ValueError."""
        config = GraphConfig(max_cycle_count=-1)
        with pytest.raises(ValueError, match="positive"):
            validate_config(config)

    def test_validate_zero_max_cycle_count_allowed(self):
        """max_cycle_count=None (unlimited) should be allowed (not positive int)."""
        config = GraphConfig(max_cycle_count=None)
        assert validate_config(config) is True

    def test_validate_zero_checkpoint_interval_raises(self):
        """checkpoint_interval=0 should raise ValueError."""
        config = GraphConfig(checkpoint_interval=0)
        with pytest.raises(ValueError, match="positive"):
            validate_config(config)

    def test_validate_negative_timeout_raises(self):
        """Negative timeout_ms should raise ValueError."""
        config = GraphConfig(timeout_ms=-1)
        with pytest.raises(ValueError, match="positive"):
            validate_config(config)

    def test_validate_timeout_none_allowed(self):
        """timeout_ms=None should be allowed."""
        config = GraphConfig(timeout_ms=None)
        assert validate_config(config) is True

    def test_validate_non_bool_debug_raises(self):
        """Non-bool debug value should raise TypeError."""
        config = GraphConfig(debug="true")
        with pytest.raises(TypeError, match="bool"):
            validate_config(config)


# ─────────────────────────────────────────────────────────────────────────────
# merge_configs
# ─────────────────────────────────────────────────────────────────────────────

class TestMergeConfigs:
    def test_merge_configs_overrides_name(self):
        """merge_configs should replace name when present in override dict."""
        base = GraphConfig(name="base-name")
        merged = merge_configs(base, {"name": "new-name"})
        assert merged.name == "new-name"

    def test_merge_configs_keeps_base_for_missing_keys(self):
        """merge_configs should keep base values for keys not in override."""
        base = GraphConfig(name="base", max_cycle_count=50, debug=True)
        merged = merge_configs(base, {"name": "override"})
        assert merged.max_cycle_count == 50
        assert merged.debug is True

    def test_merge_configs_ignores_unknown_keys(self):
        """Unknown keys in override should be silently ignored."""
        base = GraphConfig(name="base", checkpoint_interval=10)
        merged = merge_configs(base, {"unknown_key": "value", "debug": True})
        assert not hasattr(merged, "unknown_key")
        assert merged.debug is True

    def test_merge_configs_returns_new_instance(self):
        """merge_configs should not mutate the base config."""
        base = GraphConfig(name="base")
        merged = merge_configs(base, {"name": "new"})
        assert base.name == "base"
        assert merged.name == "new"
        assert merged is not base


# ─────────────────────────────────────────────────────────────────────────────
# config_to_dict
# ─────────────────────────────────────────────────────────────────────────────

class TestConfigToDict:
    def test_config_to_dict(self):
        """config_to_dict should return a flat dict of all fields."""
        config = GraphConfig(name="dict-test", checkpoint_interval=7)
        d = config_to_dict(config)
        assert isinstance(d, dict)
        assert d["name"] == "dict-test"
        assert d["checkpoint_interval"] == 7


# ─────────────────────────────────────────────────────────────────────────────
# load_config
# ─────────────────────────────────────────────────────────────────────────────

class TestLoadConfig:
    def test_load_config_none_returns_defaults(self):
        """load_config(None) should return a default GraphConfig."""
        config = load_config(None)
        assert config.name == "langgraph_workflow"
        assert config.checkpoint_interval == 10

    def test_load_config_from_dict(self):
        """load_config(dict) should parse dict and validate."""
        raw = {
            "name": "from-dict",
            "checkpoint_interval": 3,
            "debug": True,
        }
        config = load_config(raw)
        assert config.name == "from-dict"
        assert config.checkpoint_interval == 3
        assert config.debug is True

    def test_load_config_missing_required_fields_uses_defaults(self):
        """Missing fields in dict should use defaults."""
        raw = {"debug": True}
        config = load_config(raw)
        assert config.name == "langgraph_workflow"  # default
        assert config.debug is True

    def test_load_config_file_not_found(self):
        """load_config(path) with non-existent path should raise FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.json")

    def test_load_config_invalid_json_raises(self):
        """load_config(json_path) with invalid JSON should raise ValueError."""
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            f.write("{ invalid json }")
            path = f.name
        try:
            with pytest.raises(ValueError, match="Invalid JSON"):
                load_config(path)
        finally:
            Path(path).unlink()

    def test_load_config_valid_json(self):
        """load_config(json_path) with valid JSON should load and validate."""
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"name": "from-file", "checkpoint_interval": 4}, f)
            path = f.name
        try:
            config = load_config(path)
            assert config.name == "from-file"
            assert config.checkpoint_interval == 4
        finally:
            Path(path).unlink()

    def test_load_config_unsupported_extension_raises(self):
        """load_config(path) with unsupported extension should raise NotImplementedError."""
        with tempfile.NamedTemporaryFile(suffix=".toml", mode="w", delete=False) as f:
            f.write("[config]")
            path = f.name
        try:
            with pytest.raises(NotImplementedError, match="Unsupported"):
                load_config(path)
        finally:
            Path(path).unlink()


# ─────────────────────────────────────────────────────────────────────────────
# save_config
# ─────────────────────────────────────────────────────────────────────────────

class TestSaveConfig:
    def test_save_config_json(self):
        """save_config should write GraphConfig to JSON file."""
        config = GraphConfig(name="saved", checkpoint_interval=2)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            save_config(config, path, overwrite=True)
            loaded = json.loads(Path(path).read_text())
            assert loaded["name"] == "saved"
            assert loaded["checkpoint_interval"] == 2
        finally:
            Path(path).unlink()

    def test_save_config_overwrite_false_raises(self):
        """save_config with overwrite=False should raise FileExistsError if file exists."""
        config = GraphConfig()
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            with pytest.raises(FileExistsError):
                save_config(config, path, overwrite=False)
        finally:
            Path(path).unlink()


# ─────────────────────────────────────────────────────────────────────────────
# load_config_or_default
# ─────────────────────────────────────────────────────────────────────────────

class TestLoadConfigOrDefault:
    def test_returns_default_for_none(self):
        """load_config_or_default(None) should return default GraphConfig."""
        config = load_config_or_default(None)
        assert config.name == "langgraph_workflow"

    def test_loads_file_when_path_provided(self):
        """load_config_or_default(path) should load the config file."""
        with tempfile.NamedTemporaryFile(suffix=".json", mode="w", delete=False) as f:
            json.dump({"name": "from-or-default"}, f)
            path = f.name
        try:
            config = load_config_or_default(path)
            assert config.name == "from-or-default"
        finally:
            Path(path).unlink()


# ─────────────────────────────────────────────────────────────────────────────
# DEFAULT_CONFIG
# ─────────────────────────────────────────────────────────────────────────────

class TestDefaultConfig:
    def test_default_config_is_valid(self):
        """DEFAULT_CONFIG should pass validate_config."""
        assert validate_config(DEFAULT_CONFIG) is True

    def test_default_config_unchanged_by_load_config_none(self):
        """Loading None should not mutate DEFAULT_CONFIG."""
        load_config(None)
        assert DEFAULT_CONFIG.name == "langgraph_workflow"
        assert DEFAULT_CONFIG.checkpoint_interval == 10
