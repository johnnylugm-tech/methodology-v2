"""
Effort Tracker [FR-R-11]

Tracks resources consumed by agents during task execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional
import uuid


@dataclass
class EffortMetrics:
    """
    Effort metrics for a single agent task.

    [FR-R-11] Schema
    """

    # Identification
    tracking_id: str = ""
    agent_id: str = ""
    task_id: str = ""
    session_id: str = ""

    # Time Metrics
    time_spent_minutes: float = 0.0
    started_at: str = ""
    completed_at: str = ""

    # Resource Metrics
    tool_calls: int = 0
    tokens_consumed: int = 0

    # Iteration Metrics
    iteration_count: int = 0
    ab_round_triggered: bool = False

    # Quality Metrics
    output_quality_score: Optional[float] = None

    # Error Metrics
    error_count: int = 0
    retry_count: int = 0

    # Context Metrics
    context_window_usage: float = 0.0
    memory_references: int = 0

    # Tool call details
    tool_call_details: list[dict] = field(default_factory=list)

    def __post_init__(self):
        if not self.tracking_id:
            self.tracking_id = str(uuid.uuid4())[:8]
        if not self.started_at:
            self.started_at = datetime.utcnow().isoformat()

    @property
    def duration_seconds(self) -> float:
        """Calculate duration in seconds."""
        if not self.completed_at:
            return 0.0
        try:
            start = datetime.fromisoformat(self.started_at)
            end = datetime.fromisoformat(self.completed_at)
            return (end - start).total_seconds()
        except Exception:
            return 0.0

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "tracking_id": self.tracking_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "session_id": self.session_id,
            "time_spent_minutes": self.time_spent_minutes,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "tool_calls": self.tool_calls,
            "tokens_consumed": self.tokens_consumed,
            "iteration_count": self.iteration_count,
            "ab_round_triggered": self.ab_round_triggered,
            "output_quality_score": self.output_quality_score,
            "error_count": self.error_count,
            "retry_count": self.retry_count,
            "context_window_usage": self.context_window_usage,
            "memory_references": self.memory_references,
            "duration_seconds": self.duration_seconds,
        }


class EffortTracker:
    """
    Tracks and records agent effort metrics [FR-R-11].

    Collection Interface:
    - start_tracking(): Begin tracking for agent/task
    - record_tool_call(): Record individual tool invocations
    - record_token_usage(): Record token consumption
    - finish_tracking(): Finalize and compute metrics
    - get_metrics(): Retrieve collected metrics
    """

    def __init__(self, config: dict = None):
        """
        Initialize EffortTracker.

        Args:
            config: Configuration dictionary
        """
        self._config = config or {}
        self._enabled = self._config.get("enabled", True)
        self._track_detailed = self._config.get("track_detailed", True)
        self._quality_threshold = self._config.get("quality_threshold", 0.7)

        # Active tracking sessions
        self._active_tracking: dict[str, EffortMetrics] = {}
        self._completed_metrics: list[EffortMetrics] = []

    @property
    def enabled(self) -> bool:
        return self._enabled

    def start_tracking(
        self,
        agent_id: str,
        task_id: str,
        session_id: str = ""
    ) -> str:
        """
        Start tracking for an agent/task.

        Args:
            agent_id: Agent identifier (e.g., "planner", "coder")
            task_id: Associated task ID
            session_id: Optional session for correlation

        Returns:
            tracking_id: Unique ID for later reference
        """
        if not self._enabled:
            return ""

        tracking_id = str(uuid.uuid4())[:8]
        metrics = EffortMetrics(
            tracking_id=tracking_id,
            agent_id=agent_id,
            task_id=task_id,
            session_id=session_id or "",
        )

        self._active_tracking[tracking_id] = metrics
        return tracking_id

    def record_tool_call(
        self,
        tracking_id: str,
        tool_name: str,
        duration_ms: float = 0,
        success: bool = True,
        error: str = None
    ) -> None:
        """
        Record individual tool call.

        Args:
            tracking_id: Tracking session ID
            tool_name: Name of the tool called
            duration_ms: Duration in milliseconds
            success: Whether call succeeded
            error: Error message if failed
        """
        if not self._enabled or tracking_id not in self._active_tracking:
            return

        metrics = self._active_tracking[tracking_id]
        metrics.tool_calls += 1

        if self._track_detailed:
            detail = {
                "tool": tool_name,
                "duration_ms": duration_ms,
                "success": success,
                "timestamp": datetime.utcnow().isoformat(),
            }
            if error:
                detail["error"] = error
            metrics.tool_call_details.append(detail)

        if not success:
            metrics.error_count += 1

    def record_token_usage(
        self,
        tracking_id: str,
        input_tokens: int = 0,
        output_tokens: int = 0
    ) -> None:
        """
        Record token consumption.

        Args:
            tracking_id: Tracking session ID
            input_tokens: Input token count
            output_tokens: Output token count
        """
        if not self._enabled or tracking_id not in self._active_tracking:
            return

        metrics = self._active_tracking[tracking_id]
        metrics.tokens_consumed += input_tokens + output_tokens

    def record_iteration(self, tracking_id: str) -> None:
        """Record an iteration/feedback loop."""
        if tracking_id in self._active_tracking:
            self._active_tracking[tracking_id].iteration_count += 1

    def record_ab_round(self, tracking_id: str) -> None:
        """Record that AB test was triggered."""
        if tracking_id in self._active_tracking:
            self._active_tracking[tracking_id].ab_round_triggered = True

    def record_memory_reference(self, tracking_id: str, read: bool = True) -> None:
        """Record a memory read/write operation."""
        if tracking_id in self._active_tracking:
            self._active_tracking[tracking_id].memory_references += 1

    def record_retry(self, tracking_id: str) -> None:
        """Record a retry operation."""
        if tracking_id in self._active_tracking:
            self._active_tracking[tracking_id].retry_count += 1

    def update_context_usage(self, tracking_id: str, usage_percent: float) -> None:
        """Update context window usage percentage."""
        if tracking_id in self._active_tracking:
            self._active_tracking[tracking_id].context_window_usage = usage_percent

    def finish_tracking(
        self,
        tracking_id: str,
        quality_score: float = None
    ) -> Optional[EffortMetrics]:
        """
        Finalize tracking and return metrics.

        Args:
            tracking_id: Tracking session ID
            quality_score: Optional post-hoc quality assessment

        Returns:
            EffortMetrics if found, None otherwise
        """
        if tracking_id not in self._active_tracking:
            return None

        metrics = self._active_tracking.pop(tracking_id)
        metrics.completed_at = datetime.utcnow().isoformat()

        # Calculate time spent
        try:
            start = datetime.fromisoformat(metrics.started_at)
            end = datetime.fromisoformat(metrics.completed_at)
            metrics.time_spent_minutes = (end - start).total_seconds() / 60.0
        except Exception:
            pass

        # Set quality score if provided
        if quality_score is not None:
            metrics.output_quality_score = quality_score

        self._completed_metrics.append(metrics)
        return metrics

    def get_metrics(self, tracking_id: str) -> Optional[dict]:
        """
        Retrieve metrics for a tracking session.

        Args:
            tracking_id: Tracking session ID

        Returns:
            Metrics dict if found, None otherwise
        """
        # Check active tracking
        if tracking_id in self._active_tracking:
            return self._active_tracking[tracking_id].to_dict()

        # Check completed
        for metrics in reversed(self._completed_metrics):
            if metrics.tracking_id == tracking_id:
                return metrics.to_dict()

        return None

    def get_active_tracking(self) -> list[str]:
        """Get list of active tracking IDs."""
        return list(self._active_tracking.keys())

    def aggregate_task_metrics(self, task_id: str) -> dict:
        """
        Aggregate effort metrics across all agents for a task.

        Args:
            task_id: Task to aggregate

        Returns:
            Aggregated metrics dict
        """
        # Collect all metrics for this task
        task_metrics = [
            m for m in self._completed_metrics
            if m.task_id == task_id
        ]

        if not task_metrics:
            return {
                "task_id": task_id,
                "total_time_minutes": 0.0,
                "total_tool_calls": 0,
                "total_tokens": 0,
                "total_iterations": 0,
                "avg_quality_score": None,
                "agents_involved": [],
                "ab_rounds_triggered": 0,
            }

        return {
            "task_id": task_id,
            "total_time_minutes": sum(m.time_spent_minutes for m in task_metrics),
            "total_tool_calls": sum(m.tool_calls for m in task_metrics),
            "total_tokens": sum(m.tokens_consumed for m in task_metrics),
            "total_iterations": sum(m.iteration_count for m in task_metrics),
            "avg_quality_score": sum(
                m.output_quality_score for m in task_metrics if m.output_quality_score
            ) / len([
                m for m in task_metrics if m.output_quality_score is not None
            ]) if any(m.output_quality_score for m in task_metrics) else None,
            "agents_involved": list(set(m.agent_id for m in task_metrics)),
            "ab_rounds_triggered": sum(1 for m in task_metrics if m.ab_round_triggered),
            "error_count": sum(m.error_count for m in task_metrics),
            "retry_count": sum(m.retry_count for m in task_metrics),
        }

    def get_efficiency_score(self, tracking_id: str) -> Optional[float]:
        """
        Calculate efficiency score for a tracking session.

        Score = (quality * output) / (time * resources)

        Args:
            tracking_id: Tracking session ID

        Returns:
            Efficiency score if metrics available, None otherwise
        """
        metrics = self.get_metrics(tracking_id)
        if not metrics:
            return None

        quality = metrics.get("output_quality_score", 0.5) or 0.5
        time_cost = metrics.get("time_spent_minutes", 1) or 1
        tokens = metrics.get("tokens_consumed", 1) or 1

        # Higher quality, lower time/tokens = higher efficiency
        efficiency = (quality * 10) / (time_cost * (tokens / 1000))

        # Normalize to 0-1 range (rough approximation)
        return min(1.0, efficiency / 100)

    def get_agent_summary(self, agent_id: str, limit: int = 100) -> dict:
        """
        Get summary statistics for an agent.

        Args:
            agent_id: Agent to summarize
            limit: Number of recent sessions to consider

        Returns:
            Summary dict
        """
        agent_metrics = [
            m for m in self._completed_metrics
            if m.agent_id == agent_id
        ][-limit:]

        if not agent_metrics:
            return {
                "agent_id": agent_id,
                "session_count": 0,
                "total_time_minutes": 0.0,
                "total_tool_calls": 0,
                "total_tokens": 0,
                "avg_quality_score": None,
                "avg_efficiency": None,
            }

        quality_scores = [m.output_quality_score for m in agent_metrics if m.output_quality_score]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else None

        return {
            "agent_id": agent_id,
            "session_count": len(agent_metrics),
            "total_time_minutes": sum(m.time_spent_minutes for m in agent_metrics),
            "total_tool_calls": sum(m.tool_calls for m in agent_metrics),
            "total_tokens": sum(m.tokens_consumed for m in agent_metrics),
            "avg_quality_score": avg_quality,
            "avg_iterations_per_session": sum(m.iteration_count for m in agent_metrics) / len(agent_metrics),
            "error_rate": sum(m.error_count for m in agent_metrics) / len(agent_metrics),
        }

    def export_metrics(self, limit: int = 1000) -> list[dict]:
        """Export completed metrics for analysis."""
        return [m.to_dict() for m in self._completed_metrics[-limit:]]

    def get_statistics(self) -> dict:
        """Get effort tracking statistics."""
        return {
            "enabled": self._enabled,
            "active_sessions": len(self._active_tracking),
            "total_completed": len(self._completed_metrics),
            "total_time_minutes": sum(m.time_spent_minutes for m in self._completed_metrics),
            "total_tool_calls": sum(m.tool_calls for m in self._completed_metrics),
            "total_tokens": sum(m.tokens_consumed for m in self._completed_metrics),
        }