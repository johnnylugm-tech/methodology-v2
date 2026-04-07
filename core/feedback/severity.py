"""
Severity Matrix Model.

Implements a 5x5 severity matrix based on impact (1-5) and urgency (1-5).
"""

from __future__ import annotations


# 5x5 severity matrix: matrix[impact-1][urgency-1] = severity_label
# Impact: how severely does this affect the system/users?
# Urgency: how time-critical is this issue?
SEVERITY_MATRIX: list[list[str]] = [
    # Urgency 1   2       3        4         5
    ["info",      "low",   "low",   "medium", "medium"],   # Impact 1
    ["low",       "low",   "medium","medium", "high"],     # Impact 2
    ["low",       "medium","medium","high",   "high"],     # Impact 3
    ["medium",    "medium","high",  "high",   "critical"], # Impact 4
    ["medium",    "high",  "high",  "critical","critical"],# Impact 5
]

# Numeric weights for severity levels (for calculations)
SEVERITY_LEVELS: tuple[str, ...] = ("info", "low", "medium", "high", "critical")
_SEVERITY_NUMERIC: dict[str, int] = {lv: i for i, lv in enumerate(SEVERITY_LEVELS)}


def _to_level(value: float) -> int:
    """
    Clamp and convert a float to an integer level 1-5.

    Args:
        value: Numeric value (will be clamped to 1-5 range).

    Returns:
        Integer in range [1, 5].
    """
    if value < 1.0:
        return 1
    if value > 5.0:
        return 5
    return int(round(value))


def calculate_severity(impact: float, urgency: float) -> str:
    """
    Calculate severity level from impact and urgency scores.

    Uses a 5x5 matrix where:
    - Impact: 1 (negligible) to 5 (catastrophic)
    - Urgency: 1 (can wait) to 5 (immediate)

    Args:
        impact: Numeric impact score (1-5).
        urgency: Numeric urgency score (1-5).

    Returns:
        Severity label: 'critical', 'high', 'medium', 'low', or 'info'.
    """
    i = _to_level(impact) - 1   # 0-indexed row
    u = _to_level(urgency) - 1  # 0-indexed column
    return SEVERITY_MATRIX[i][u]


def severity_to_numeric(severity: str) -> int:
    """
    Convert a severity label to its numeric rank.

    Returns 0-4 where 0=info, 1=low, 2=medium, 3=high, 4=critical.
    Returns -1 for unknown severity labels.
    """
    return _SEVERITY_NUMERIC.get(severity, -1)


class SeverityMatrix:
    """
    Stateful severity calculator (useful for subclassing or extension).
    """

    @staticmethod
    def calculate(impact: float, urgency: float) -> str:
        """Calculate severity — delegates to module-level function."""
        return calculate_severity(impact, urgency)

    @staticmethod
    def matrix() -> list[list[str]]:
        """Return the 5x5 severity matrix."""
        return [row[:] for row in SEVERITY_MATRIX]

    @staticmethod
    def level(value: float) -> int:
        """Convert numeric value to level — delegates to module-level function."""
        return _to_level(value)