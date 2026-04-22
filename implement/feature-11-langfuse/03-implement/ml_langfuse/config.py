"""
ml_langfuse.config — Centralized configuration management for Langfuse/OTel.

Sources (priority high → low):
    1. Environment variables
    2. config.yaml file (if present)
    3. Hardcoded defaults
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal, Optional

import yaml
from pydantic import BaseModel, Field, field_validator

__all__ = ["LangfuseConfig", "get_config", "ConfigurationError"]


class ConfigurationError(Exception):
    """Raised when required configuration is missing or invalid."""

    pass


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_yaml_config() -> dict:
    """Load ml_langfuse section from config.yaml if present."""
    candidates = [
        Path.cwd() / "config.yaml",
        Path(__file__).parents[3] / "config.yaml",  # project root
    ]
    for path in candidates:
        if path.exists():
            with open(path) as fh:
                data = yaml.safe_load(fh) or {}
                return data.get("ml_langfuse", {})
    return {}


def _resolve_field(
    env_var: str,
    yaml_key: str,
    default: object,
    yaml_data: dict,
) -> object:
    """Resolve a field value: env var > yaml > default."""
    if env_var in os.environ:
        return os.environ[env_var]
    if yaml_key in yaml_data:
        return yaml_data[yaml_key]
    return default


# ---------------------------------------------------------------------------
# Config model
# ---------------------------------------------------------------------------

class LangfuseConfig(BaseModel):
    """
    Centralized configuration for the ml_langfuse observability layer.

    All fields can be overridden via environment variables (highest priority)
    or a `config.yaml` file.
    """

    # Mode
    mode: Literal["cloud", "self_hosted"] = Field(
        default="cloud",
        description="Langfuse operation mode: 'cloud' (Langfuse hosted) or 'self_hosted'.",
    )

    # Cloud mode credentials
    public_key: str = Field(
        default="",
        description="LANGFUSE_PUBLIC_KEY — Langfuse cloud public key.",
    )
    secret_key: str = Field(
        default="",
        description="LANGFUSE_SECRET_KEY — Langfuse cloud secret key.",
    )

    # Self-hosted mode
    host: str = Field(
        default="",
        description="LANGFUSE_HOST — Base URL for self-hosted Langfuse (e.g. https://langfuse.example.com).",
    )

    # OpenTelemetry
    otel_exporter_endpoint: str = Field(
        default="",
        description="OTEL_EXPORTER_OTLP_ENDPOINT — OTLP collector endpoint.",
    )
    otel_service_name: str = Field(
        default="methodology-v2",
        description="OTEL_SERVICE_NAME — Service name set on every span.",
    )

    # Sampling
    trace_sampling_rate: float = Field(
        default=1.0,
        ge=0.0,
        le=1.0,
        description="LANGFUSE_TRACE_SAMPLING_RATE — Fraction of spans to sample (0.0–1.0).",
    )

    # Dashboard / Audit
    dashboard_poll_interval_seconds: int = Field(
        default=5,
        gt=0,
        description="Polling interval (seconds) for real-time dashboard updates.",
    )
    audit_retention_days: int = Field(
        default=90,
        gt=0,
        description="Audit log retention period in days.",
    )

    @field_validator("mode", mode="before")
    @classmethod
    def _resolve_mode(cls, v: str) -> str:  # noqa: N805
        # Auto-detect mode from env vars if field uses default
        if not v:
            # check env
            if os.environ.get("LANGFUSE_HOST"):
                return "self_hosted"
            return "cloud"
        return v

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate_config(self) -> None:
        """
        Validate this configuration.

        Raises:
            ConfigurationError: If required fields are missing or out of range.
        """
        if self.mode == "cloud":
            missing_public = not os.environ.get("LANGFUSE_PUBLIC_KEY") and not self.public_key
            missing_secret = not os.environ.get("LANGFUSE_SECRET_KEY") and not self.secret_key
            if missing_public or missing_secret:
                raise ConfigurationError(
                    "Cloud mode requires LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY "
                    "environment variables (or public_key / secret_key in config)."
                )
        elif self.mode == "self_hosted":
            host = os.environ.get("LANGFUSE_HOST") or self.host
            if not host:
                raise ConfigurationError(
                    "Self-hosted mode requires LANGFUSE_HOST environment variable "
                    "(or host in config.yaml)."
                )
        else:
            raise ConfigurationError(f"Unknown mode: {self.mode!r} (expected 'cloud' or 'self_hosted').")

        if not 0.0 <= self.trace_sampling_rate <= 1.0:
            raise ConfigurationError(
                f"trace_sampling_rate must be in [0.0, 1.0], got {self.trace_sampling_rate}"
            )

        # Validate otel_exporter_endpoint is a valid URL if provided
        endpoint = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT") or self.otel_exporter_endpoint
        if endpoint:
            if not endpoint.startswith(("http://", "https://")):
                raise ConfigurationError(
                    f"otel_exporter_endpoint must be a valid HTTP/HTTPS URL, got {endpoint!r}"
                )

    # ------------------------------------------------------------------
    # Internal dict used for env-override resolution
    # ------------------------------------------------------------------
    model_config = {
        "extra": "ignore",  # Allow extra fields from yaml without error
    }


# ---------------------------------------------------------------------------
# Config singleton
# ---------------------------------------------------------------------------

_config: Optional[LangfuseConfig] = None


def get_config() -> LangfuseConfig:
    """
    Return the global LangfuseConfig singleton.

    Resolution order (high → low):
        1. Environment variables
        2. config.yaml (ml_langfuse section)
        3. Hardcoded defaults
    """
    global _config
    if _config is None:
        yaml_data = _load_yaml_config()

        public_key_env = os.environ.get("LANGFUSE_PUBLIC_KEY", "")
        secret_key_env = os.environ.get("LANGFUSE_SECRET_KEY", "")
        host_env = os.environ.get("LANGFUSE_HOST", "")
        otel_endpoint_env = os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "")
        service_name_env = os.environ.get("OTEL_SERVICE_NAME", "methodology-v2")
        sampling_rate_raw = os.environ.get("LANGFUSE_TRACE_SAMPLING_RATE", "")
        poll_interval_raw = os.environ.get("LANGFUSE_DASHBOARD_POLL_INTERVAL_SECONDS", "")
        retention_raw = os.environ.get("LANGFUSE_AUDIT_RETENTION_DAYS", "")

        # Resolve mode
        if host_env:
            mode: str = "self_hosted"
        else:
            mode = "cloud"

        _config = LangfuseConfig(
            mode=mode,
            public_key=public_key_env or yaml_data.get("public_key", ""),
            secret_key=secret_key_env or yaml_data.get("secret_key", ""),
            host=host_env or yaml_data.get("host", ""),
            otel_exporter_endpoint=otel_endpoint_env or yaml_data.get("otel_exporter_endpoint", ""),
            otel_service_name=service_name_env or yaml_data.get("otel_service_name", "methodology-v2"),
            trace_sampling_rate=float(sampling_rate_raw) if sampling_rate_raw else float(yaml_data.get("trace_sampling_rate", 1.0)),
            dashboard_poll_interval_seconds=int(poll_interval_raw) if poll_interval_raw else int(yaml_data.get("dashboard_poll_interval_seconds", 5)),
            audit_retention_days=int(retention_raw) if retention_raw else int(yaml_data.get("audit_retention_days", 90)),
        )
    return _config


def reset_config() -> None:
    """Reset the global config singleton. Used in tests to ensure isolation."""
    global _config
    _config = None
