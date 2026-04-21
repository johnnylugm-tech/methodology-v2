"""
Configuration management for LangGraph workflows.

Supports loading from YAML, JSON, dict, or using defaults.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------

@dataclass
class GraphConfig:
    """Configuration for a LangGraph workflow.

    Attributes:
        name: Workflow name identifier.
        max_cycle_count: Maximum number of execution cycles before
            raising CyclicExecutionError. None means unlimited.
        enable_state_persistence: Whether to persist checkpoint state.
        checkpoint_interval: Number of steps between automatic checkpoints.
        debug: Enable debug logging and verbose output.
        timeout_ms: Global execution timeout in milliseconds.
            None means no timeout.
    """

    name: str = "langgraph_workflow"
    max_cycle_count: int | None = 100
    enable_state_persistence: bool = True
    checkpoint_interval: int = 10
    debug: bool = False
    timeout_ms: int | None = 300_000  # 5 minutes default


# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULT_CONFIG = GraphConfig()


# ---------------------------------------------------------------------------
# Serialization helpers
# ---------------------------------------------------------------------------

def config_to_dict(config: GraphConfig) -> dict[str, Any]:
    """Convert a GraphConfig into a plain dictionary.

    This is the inverse of passing a dict to load_config().

    Args:
        config: GraphConfig instance to serialize.

    Returns:
        Plain dict suitable for JSON/YAML serialization.
    """
    return asdict(config)


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_config(config: GraphConfig) -> bool:
    """Validate a GraphConfig instance.

    Checks:
        - name is non-empty string
        - max_cycle_count is None or positive integer
        - checkpoint_interval is positive integer
        - timeout_ms is None or positive integer
        - enable_state_persistence is bool
        - debug is bool

    Args:
        config: GraphConfig instance to validate.

    Returns:
        True if valid, raises ValueError if invalid.
    """
    if not isinstance(config.name, str) or not config.name.strip():
        raise ValueError("GraphConfig.name must be a non-empty string")

    if config.max_cycle_count is not None:
        if not isinstance(config.max_cycle_count, int):
            raise TypeError("GraphConfig.max_cycle_count must be an int or None")
        if config.max_cycle_count <= 0:
            raise ValueError("GraphConfig.max_cycle_count must be positive or None")

    if not isinstance(config.checkpoint_interval, int):
        raise TypeError("GraphConfig.checkpoint_interval must be an int")
    if config.checkpoint_interval <= 0:
        raise ValueError("GraphConfig.checkpoint_interval must be positive")

    if config.timeout_ms is not None:
        if not isinstance(config.timeout_ms, int):
            raise TypeError("GraphConfig.timeout_ms must be an int or None")
        if config.timeout_ms <= 0:
            raise ValueError("GraphConfig.timeout_ms must be positive or None")

    if not isinstance(config.enable_state_persistence, bool):
        raise TypeError("GraphConfig.enable_state_persistence must be a bool")

    if not isinstance(config.debug, bool):
        raise TypeError("GraphConfig.debug must be a bool")

    return True


# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------

def merge_configs(base: GraphConfig, override: dict[str, Any]) -> GraphConfig:
    """Merge override dict into a base GraphConfig.

    Only fields present in ``override`` replace base values.
    Unknown keys in ``override`` are silently ignored.

    Args:
        base: Base GraphConfig to start from.
        override: Dict of field names → new values.

    Returns:
        New GraphConfig with merged values.
    """
    base_dict = asdict(base)

    # Apply overrides, ignoring unknown keys
    for key in base_dict:
        if key in override:
            base_dict[key] = override[key]

    return GraphConfig(**base_dict)


# ---------------------------------------------------------------------------
# Loading
# ---------------------------------------------------------------------------

def load_config(config_path: str | dict[str, Any] | None = None) -> GraphConfig:
    """Load GraphConfig from a file path or dict.

    File formats are detected by extension:
        .yaml / .yml → YAML
        .json        → JSON

    If ``config_path`` is None, returns a default GraphConfig.

    Args:
        config_path:
            - Path to YAML/JSON config file (str).
            - Already-parsed config dict (dict).
            - None to use all defaults.

    Returns:
        Loaded GraphConfig instance.

    Raises:
        FileNotFoundError: Config file does not exist.
        ValueError: Config file is invalid or fails validation.
        NotImplementedError: Unsupported file extension.
    """
    # None → defaults
    if config_path is None:
        return GraphConfig()

    # dict path → use directly
    if isinstance(config_path, dict):
        return _config_from_dict(config_path)

    # Resolve string path
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    suffix = path.suffix.lower()

    if suffix in (".yaml", ".yml"):
        return _config_from_yaml(path)
    elif suffix == ".json":
        return _config_from_json(path)
    else:
        raise NotImplementedError(
            f"Unsupported config file extension '{suffix}'. "
            "Use .yaml, .yml, or .json"
        )


def _config_from_dict(raw: dict[str, Any]) -> GraphConfig:
    """Build GraphConfig from a plain dict, applying defaults for missing keys."""
    defaults = asdict(DEFAULT_CONFIG)
    defaults.update(raw)
    config = GraphConfig(**defaults)
    validate_config(config)
    return config


def _config_from_json(path: Path) -> GraphConfig:
    """Load and parse a JSON config file."""
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError(f"JSON config must be a JSON object, got {type(raw).__name__}")

    return _config_from_dict(raw)


def _config_from_yaml(path: Path) -> GraphConfig:
    """Load and parse a YAML config file.

    Attempts to import ``ruamel.yaml`` with fall-back to ``yaml``.
    If neither is available, raises ImportError.
    """
    yaml = _get_yaml_parser()
    try:
        raw = yaml.load(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise ValueError(f"Invalid YAML in {path}: {exc}") from exc

    if not isinstance(raw, dict):
        raise ValueError(f"YAML config must be a YAML mapping, got {type(raw).__name__}")

    return _config_from_dict(raw)


def _get_yaml_parser():
    """Return a YAML parser, trying ruamel.yaml then yaml."""
    try:
        from ruamel.yaml import YAML as _YAML
        yaml = _YAML()
        yaml.preserve_quotes = True
        return yaml
    except ImportError:
        pass

    try:
        import yaml
        return yaml
    except ImportError as exc:
        raise ImportError(
            "YAML support requires 'ruamel.yaml' or 'pyyaml'. "
            "Install with: pip install ruamel.yaml"
        ) from exc


# ---------------------------------------------------------------------------
# Convenience utilities
# ---------------------------------------------------------------------------

def save_config(config: GraphConfig, path: str, *, overwrite: bool = True) -> None:
    """Write a GraphConfig to a JSON file.

    Args:
        config: GraphConfig to serialize.
        path: Output file path (extension .json).
        overwrite: Allow overwriting existing file.

    Raises:
        FileExistsError: Path exists and overwrite=False.
        ValueError: Unknown / unsupported extension.
    """
    out_path = Path(path)

    if out_path.exists() and not overwrite:
        raise FileExistsError(f"File already exists: {out_path}")

    suffix = out_path.suffix.lower()
    if suffix == ".json":
        out_path.write_text(
            json.dumps(config_to_dict(config), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
    elif suffix in (".yaml", ".yml"):
        yaml = _get_yaml_parser()
        yaml.dump(config_to_dict(config), out_path)
    else:
        raise ValueError(f"Unsupported output extension '{suffix}'")


# ---------------------------------------------------------------------------
# CLI-friendly helpers (for testing / scripting)
# ---------------------------------------------------------------------------

def load_config_or_default(config_path: str | None) -> GraphConfig:
    """Load config if path is non-None and non-empty, else return default."""
    if config_path:
        return load_config(config_path)
    return GraphConfig()