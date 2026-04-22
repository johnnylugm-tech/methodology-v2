"""
ml_langfuse.client — Langfuse client singleton with OTel SDK registration.

This module provides the singleton Langfuse client and handles all
OpenTelemetry SDK setup (TracerProvider, OTLP exporter, BatchSpanProcessor).
"""

from __future__ import annotations

import atexit
import logging
from typing import Optional

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_export import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from ml_langfuse.config import LangfuseConfig, get_config, ConfigurationError

__all__ = ["get_langfuse_client", "LangfuseClient", "ConfigurationError"]

logger = logging.getLogger("ml_langfuse")

DEFAULT_LANGFUSE_OTLP_ENDPOINT = "https://cloud.langfuse.com/api/public/ingestion/otlp"


# ---------------------------------------------------------------------------
# Singleton management
# ---------------------------------------------------------------------------

_client: Optional[LangfuseClient] = None
_initialized = False


def get_langfuse_client() -> LangfuseClient:
    """
    Return the singleton LangfuseClient instance.

    On first call, the client is created, OTel is set up, and an atexit
    handler is registered to flush pending spans on process exit.

    Returns:
        The singleton LangfuseClient.

    Raises:
        ConfigurationError: If required configuration is missing or invalid.
    """
    global _client, _initialized
    if _initialized:
        return _client

    config = get_config()

    # Fail-fast on invalid config
    try:
        config.validate_config()
    except ConfigurationError:
        logger.error("ml_langfuse configuration invalid — see prior logs for details")
        raise

    _client = LangfuseClient(config)
    _client._setup_otel()
    _initialized = True

    # Ensure pending spans are flushed on normal process exit
    atexit.register(_flush_and_shutdown)

    return _client


def reset_client() -> None:
    """
    Reset the global client singleton.

    Used in tests to ensure each test starts with a fresh client.
    """
    global _client, _initialized
    _client = None
    _initialized = False


def _flush_and_shutdown() -> None:
    """atexit handler to flush pending spans before process exits."""
    global _client
    if _client is not None:
        try:
            _client.flush()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Error flushing spans on shutdown: %s", exc)


# ---------------------------------------------------------------------------
# Client class
# ---------------------------------------------------------------------------

class LangfuseClient:
    """
    Langfuse observability client backed by OpenTelemetry SDK.

    This client:
        - Owns the global TracerProvider
        - Provides tracer instances for span creation
        - Exposes a ``flush()`` method to synchronously export pending spans
    """

    def __init__(self, config: LangfuseConfig) -> None:
        self._config = config
        self._tracer_provider: Optional[TracerProvider] = None
        self._tracer: Optional[trace.Tracer] = None

    # ------------------------------------------------------------------
    # OTel setup
    # ------------------------------------------------------------------

    def _setup_otel(self) -> None:
        """
        Initialize the OpenTelemetry SDK and register it globally.

        Steps:
            1. Build a Resource with service name
            2. Determine OTLP endpoint (cloud or self-hosted / custom)
            3. Create OTLP exporter
            4. Wrap in BatchSpanProcessor (flush every 100 spans or 5s)
            5. Create TracerProvider and set as global default
            6. Get a Tracer for ml_langfuse internals
        """
        # --- Resource ---
        resource = Resource.create({
            "service.name": self._config.otel_service_name,
            "service.version": "0.1.0",
        })

        # --- OTLP endpoint ---
        endpoint = self._get_otlp_endpoint()

        # --- Exporter ---
        try:
            otlp_exporter = OTLPSpanExporter(
                endpoint=endpoint,
                # langfuse cloud expects no auth header from OTLP exporter
                # auth is handled via LANGFUSE_PUBLIC_KEY in the Langfuse SDK
                compression=None,
                timeout=10,
            )
        except Exception as exc:
            logger.warning(
                "Failed to create OTLP exporter (endpoint=%s): %s. "
                "Traces will be dropped.",
                endpoint,
                exc,
            )
            otlp_exporter = None

        # --- Span processor ---
        if otlp_exporter is not None:
            span_processor: SpanProcessor = BatchSpanProcessor(
                otlp_exporter,
                max_queue_size=10_000,
                schedule_delay_millis=5_000,   # flush every 5s
                max_export_batch_size=100,
            )
        else:
            # No-op processor — drop all spans gracefully
            from opentelemetry.sdk.trace.export import SimpleSpanProcessor, SpanExporter
            span_processor = SimpleSpanProcessor(
                SpanExporter()  # type: ignore[arg-type]
            )

        # --- TracerProvider ---
        self._tracer_provider = TracerProvider(
            resource=resource,
            span_processors=[span_processor],
            # Active span limit (prevent runaway spans)
            max_span_attrs_count=100,
        )

        # Register as global default
        trace.set_tracer_provider(self._tracer_provider, log_warning=True)

        # --- Tracer for ml_langfuse own use ---
        self._tracer = self._tracer_provider.get_tracer("ml_langfuse")

    def _get_otlp_endpoint(self) -> str:
        """Resolve the OTLP endpoint URL."""
        # 1. Explicit config / env var
        if self._config.otel_exporter_endpoint:
            return self._config.otel_exporter_endpoint
        if self._config.otels_exporter_endpoint:  # typo-tolerant alias in config
            return self._config.otels_exporter_endpoint

        # 2. Self-hosted host
        if self._config.mode == "self_hosted":
            host = self._config.host.rstrip("/")
            return f"{host}/api/public/ingestion/otlp"

        # 3. Default: Langfuse cloud
        return DEFAULT_LANGFUSE_OTLP_ENDPOINT

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_tracer(self, name: str) -> trace.Tracer:
        """
        Return an OpenTelemetry Tracer for the given scope name.

        The returned Tracer creates spans in the same TracerProvider owned
        by this client.

        Args:
            name: The logical name of the tracer (e.g. "phase6.risk_evaluation").
                  Convention: use dot-separated hierarchical names.

        Returns:
            An OTel Tracer instance.
        """
        if self._tracer_provider is None:
            # Return a no-op tracer to avoid crashes
            return trace.get_tracer(name)
        return self._tracer_provider.get_tracer(name)

    def flush(self) -> None:
        """
        Force-flush all pending spans through the export pipeline.

        This is called automatically on process exit via atexit.
        Can also be called manually during long-running processes.
        """
        if self._tracer_provider is None:
            return
        for processor in self._tracer_provider._span_processors:  # type: ignore[attr-defined]
            try:
                processor.force_flush()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Error force-flushing span processor: %s", exc)

    @property
    def config(self) -> LangfuseConfig:
        """Return the config used to initialize this client."""
        return self._config


# ---------------------------------------------------------------------------
# No-op SpanExporter for graceful degradation
# ---------------------------------------------------------------------------

class _NoOpSpanExporter:
    """A SpanExporter that drops all spans (used when OTLP endpoint is unreachable)."""

    name = "ml_langfuse.noop"

    def export(self, spans):  # type: ignore[no-untyped-def]
        """Drop all spans."""
        return None

    def shutdown(self) -> None:
        """No-op shutdown."""
        pass


class SpanExporter:  # type: ignore[no-redef]
    """Alias used to avoid import errors when constructing SimpleSpanProcessor."""
    ...
