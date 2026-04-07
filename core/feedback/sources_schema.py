"""
Feedback Sources Schema.

Defines all possible feedback sources, their metadata, and fetch interfaces.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Any


@dataclass
class SeverityMapping:
    """Maps source-specific severity levels to standard severity tiers."""

    critical: float = 5.0
    high: float = 4.0
    medium: float = 3.0
    low: float = 2.0
    info: float = 1.0


@dataclass
class FeedbackSource:
    """
    Represents a feedback source with its configuration.

    Attributes:
        name: Unique identifier for the source.
        description: Human-readable description of the source.
        format: Data format produced by this source (json/stdout/log/metrics/event).
        severity_mapping: Maps source-specific severity to standard 1-5 scale.
        trigger: Human-readable description of what triggers feedback.
        fetch_fn: Callable that returns raw feedback data (stubbed).
        enabled: Whether this source is currently active.
    """

    name: str
    description: str
    format: str
    severity_mapping: SeverityMapping
    trigger: str
    fetch_fn: Callable[[], list[dict[str, Any]]] = field(default_factory=lambda: lambda: [])
    enabled: bool = True


def _fetch_quality_gate() -> list[dict[str, Any]]:
    """Fetch from quality gate source (stubbed)."""
    return []


def _fetch_constitution() -> list[dict[str, Any]]:
    """Fetch from constitution compliance source (stubbed)."""
    return []


def _fetch_linter() -> list[dict[str, Any]]:
    """Fetch from linter source (stubbed)."""
    return []


def _fetch_test_failure() -> list[dict[str, Any]]:
    """Fetch from test failure source (stubbed)."""
    return []


def _fetch_complexity_alert() -> list[dict[str, Any]]:
    """Fetch from complexity alert source (stubbed)."""
    return []


def _fetch_drift_detector() -> list[dict[str, Any]]:
    """Fetch from drift detector source (stubbed)."""
    return []


def _fetch_code_review() -> list[dict[str, Any]]:
    """Fetch from code review source (stubbed)."""
    return []


def _fetch_user_report() -> list[dict[str, Any]]:
    """Fetch from user report source (stubbed)."""
    return []


def _fetch_prometheus() -> list[dict[str, Any]]:
    """Fetch from Prometheus metrics source (stubbed)."""
    return []


FEEDBACK_SOURCES: dict[str, FeedbackSource] = {
    "quality_gate": FeedbackSource(
        name="quality_gate",
        description="Automated quality gate checkpoints in CI/CD pipeline",
        format="json",
        severity_mapping=SeverityMapping(
            critical=5.0, high=4.0, medium=3.0, low=2.0, info=1.0
        ),
        trigger="Quality gate threshold breached (coverage, lint, tests)",
        fetch_fn=_fetch_quality_gate,
    ),
    "constitution": FeedbackSource(
        name="constitution",
        description="Constitutional AI compliance violations",
        format="json",
        severity_mapping=SeverityMapping(
            critical=5.0, high=4.0, medium=3.0, low=2.0, info=1.0
        ),
        trigger="Constitutional constraint violation detected",
        fetch_fn=_fetch_constitution,
    ),
    "linter": FeedbackSource(
        name="linter",
        description="Code linting violations (ruff, eslint, etc.)",
        format="stdout",
        severity_mapping=SeverityMapping(
            critical=5.0, high=4.0, medium=3.0, low=2.0, info=1.0
        ),
        trigger="Linter rule violation in codebase",
        fetch_fn=_fetch_linter,
    ),
    "test_failure": FeedbackSource(
        name="test_failure",
        description="Test suite failures and regressions",
        format="json",
        severity_mapping=SeverityMapping(
            critical=5.0, high=4.0, medium=3.0, low=2.0, info=1.0
        ),
        trigger="Test case fails or test suite regression detected",
        fetch_fn=_fetch_test_failure,
    ),
    "complexity_alert": FeedbackSource(
        name="complexity_alert",
        description="Code complexity threshold violations",
        format="log",
        severity_mapping=SeverityMapping(
            critical=5.0, high=4.0, medium=3.0, low=2.0, info=1.0
        ),
        trigger="Cyclomatic complexity or LOC threshold exceeded",
        fetch_fn=_fetch_complexity_alert,
    ),
    "drift_detector": FeedbackSource(
        name="drift_detector",
        description="Architecture/behavior drift from baseline",
        format="json",
        severity_mapping=SeverityMapping(
            critical=5.0, high=4.0, medium=3.0, low=2.0, info=1.0
        ),
        trigger="Implementation diverges from reference architecture",
        fetch_fn=_fetch_drift_detector,
    ),
    "code_review": FeedbackSource(
        name="code_review",
        description="Human code review comments and suggestions",
        format="json",
        severity_mapping=SeverityMapping(
            critical=5.0, high=4.0, medium=3.0, low=2.0, info=1.0
        ),
        trigger="Reviewer posts comment or requests changes",
        fetch_fn=_fetch_code_review,
    ),
    "user_report": FeedbackSource(
        name="user_report",
        description="End-user bug reports and feature requests",
        format="json",
        severity_mapping=SeverityMapping(
            critical=5.0, high=4.0, medium=3.0, low=2.0, info=1.0
        ),
        trigger="User submits bug report or feedback form",
        fetch_fn=_fetch_user_report,
    ),
    "prometheus": FeedbackSource(
        name="prometheus",
        description="Prometheus alerting rules and metrics",
        format="metrics",
        severity_mapping=SeverityMapping(
            critical=5.0, high=4.0, medium=3.0, low=2.0, info=1.0
        ),
        trigger="Alerting threshold breached or metric anomaly detected",
        fetch_fn=_fetch_prometheus,
    ),
}


def get_source(name: str) -> FeedbackSource | None:
    """Get a feedback source by name."""
    return FEEDBACK_SOURCES.get(name)


def get_enabled_sources() -> list[FeedbackSource]:
    """Get all enabled feedback sources."""
    return [s for s in FEEDBACK_SOURCES.values() if s.enabled]