"""
Data Sources for Scenario Model.

Provides historical data from FeedbackStore and Git history.
Each function returns (value, source_tag) tuple - value may be None if data unavailable.
"""

from __future__ import annotations

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, TypedDict

# Optional: FeedbackStore integration
try:
    from core.feedback.feedback import FeedbackStore, FeedbackCategory

    HAS_FEEDBACK = True
except ImportError:
    HAS_FEEDBACK = False
    FeedbackStore = None
    FeedbackCategory = None


class SourceTag(TypedDict):
    """Source tag with value and origin."""

    value: float | None
    source: str  # historical_data | user_input | assumption
    detail: str


def get_historical_defects(
    feedback_store: FeedbackStore | None,
    project_path: str | Path | None = None,
) -> SourceTag:
    """
    Get historical defect count from FeedbackStore.

    Returns source-tagged defect statistics.
    Falls back to None if no data available, tagged as 'assumption'.
    """
    if feedback_store is None:
        return SourceTag(value=None, source="assumption", detail="No feedback store provided")

    try:
        all_feedback = feedback_store.list_all()
        bugs = [
            fb
            for fb in all_feedback
            if hasattr(fb, "category") and fb.category == FeedbackCategory.BUG
        ]

        if not bugs:
            return SourceTag(
                value=None,
                source="assumption",
                detail="No bug-category feedback found in store",
            )

        # Count by severity
        severity_counts: dict[str, int] = {}
        for fb in bugs:
            sev = getattr(fb, "severity", "unknown")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

        total = len(bugs)

        return SourceTag(
            value=float(total),
            source="historical_data",
            detail=f"Bug feedback count from store: {severity_counts}",
        )
    except Exception as e:
        return SourceTag(value=None, source="assumption", detail=f"Error reading feedback store: {e}")


def get_phase_completion_times(
    project_path: str | Path,
    phase: int | None = None,
) -> SourceTag:
    """
    Get phase completion times from Git history.

    Analyzes commit messages to find phase transitions and calculate durations.
    Returns average time per phase or specific phase if requested.
    Falls back to None if insufficient data.
    """
    if project_path is None:
        return SourceTag(value=None, source="assumption", detail="No project path provided")

    project_path = Path(project_path)
    if not project_path.exists():
        return SourceTag(value=None, source="assumption", detail="Project path does not exist")

    try:
        # Get commits with phase markers
        result = subprocess.run(
            [
                "git",
                "log",
                "--all",
                "--pretty=format:%H|%ad|%s",
                "--date=iso",
            ],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            return SourceTag(
                value=None,
                source="assumption",
                detail="Git log failed - may not be a git repo",
            )

        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        if len(lines) < 2:
            return SourceTag(
                value=None,
                source="assumption",
                detail="Insufficient git history for phase timing",
            )

        # Parse phase markers
        phase_times: dict[int, list[float]] = {}
        current_phase: int | None = None
        phase_start: datetime | None = None

        for line in lines:
            if "|" not in line:
                continue
            commit_hash, date_str, message = line.split("|", 2)
            try:
                commit_time = datetime.fromisoformat(date_str.strip()).timestamp()
            except (ValueError, OSError):
                continue

            # Detect phase change
            msg_lower = message.lower()
            if "phase" in msg_lower or "p" in msg_lower[:3]:
                # Look for phase number
                import re

                m = re.search(r"[Pp]h?a?s?e?\s*(\d)", message)
                if m:
                    detected_phase = int(m.group(1))
                    if current_phase is not None and phase_start is not None:
                        duration = commit_time - phase_start
                        if duration > 0:
                            if current_phase not in phase_times:
                                phase_times[current_phase] = []
                            phase_times[current_phase].append(duration)

                    current_phase = detected_phase
                    phase_start = commit_time

        if not phase_times:
            return SourceTag(
                value=None,
                source="assumption",
                detail="No phase markers found in git history",
            )

        # Calculate average duration per phase (in hours)
        all_durations = [d for durations in phase_times.values() for d in durations]
        if not all_durations:
            return SourceTag(
                value=None,
                source="assumption",
                detail="Phase durations could not be calculated",
            )

        avg_hours = sum(all_durations) / len(all_durations) / 3600

        if phase is not None and phase in phase_times:
            phase_durations = [d / 3600 for d in phase_times[phase]]
            avg_hours = sum(phase_durations) / len(phase_durations)
            return SourceTag(
                value=avg_hours,
                source="historical_data",
                detail=f"Phase {phase} average from {len(phase_durations)} commits",
            )

        return SourceTag(
            value=avg_hours,
            source="historical_data",
            detail=f"Average from {len(phase_times)} phases, {len(all_durations)} transitions",
        )

    except subprocess.TimeoutExpired:
        return SourceTag(value=None, source="assumption", detail="Git log timed out")
    except Exception as e:
        return SourceTag(value=None, source="assumption", detail=f"Git analysis error: {e}")


def get_team_velocity(
    feedback_store: FeedbackStore | None = None,
    project_path: str | Path | None = None,
) -> SourceTag:
    """
    Get team velocity metric - closed feedback per week.

    Returns None if insufficient data, tagged appropriately.
    """
    if feedback_store is None:
        return SourceTag(value=None, source="assumption", detail="No feedback store provided")

    try:
        all_feedback = feedback_store.list_all()
        if not all_feedback:
            return SourceTag(
                value=None,
                source="assumption",
                detail="No feedback data available for velocity calculation",
            )

        # Find date range
        timestamps = []
        for fb in all_feedback:
            ts = getattr(fb, "timestamp", None)
            if ts:
                try:
                    dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    timestamps.append(dt)
                except (ValueError, OSError):
                    continue

        if len(timestamps) < 2:
            return SourceTag(
                value=None,
                source="assumption",
                detail="Insufficient timestamp data for velocity",
            )

        min_dt = min(timestamps)
        max_dt = max(timestamps)
        weeks = max((max_dt - min_dt).days / 7, 1)

        closed = len([fb for fb in all_feedback if getattr(fb, "status", None) in ("closed", "verified")])

        velocity = closed / weeks

        return SourceTag(
            value=velocity,
            source="historical_data",
            detail=f"Closed {closed} items over {weeks:.1f} weeks",
        )
    except Exception as e:
        return SourceTag(value=None, source="assumption", detail=f"Velocity calculation error: {e}")
