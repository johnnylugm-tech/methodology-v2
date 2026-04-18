"""
KillSwitch Facade Class.

Main Kill-Switch facade that coordinates all components for unified interface.
"""

import logging
from typing import List, Optional

from .circuit_breaker import CircuitBreaker
from .enums import CircuitState, KillReason
from .exceptions import InterruptInProgressError
from .health_monitor import HealthMonitor
from .interrupt_engine import InterruptEngine
from .models import InterruptEvent, MonitorConfig
from .state_manager import StateManager

logger = logging.getLogger(__name__)


class KillSwitch:
    """
    Main Kill-Switch facade class.

    Coordinates HealthMonitor, CircuitBreaker, InterruptEngine, and StateManager
    to provide a unified interface for Kill-Switch operations.
    """

    def __init__(
        self,
        audit_logger=None,  # Optional[AuditLogger]
        state_manager: Optional[StateManager] = None,
    ) -> None:
        self.health_monitor = HealthMonitor()
        self.circuit_breaker = CircuitBreaker()
        self.state_manager = state_manager or StateManager()
        self.interrupt_engine = InterruptEngine(
            audit_logger=audit_logger,
            state_manager=self.state_manager,
        )

    def start_monitoring(
        self,
        agent_id: str,
        config: Optional[MonitorConfig] = None,
    ) -> None:
        """
        Start monitoring an agent.

        Args:
            agent_id: ID of the agent to monitor.
            config: Monitoring configuration. If None, uses defaults.

        Raises:
            AgentNotFoundError: If agent_id is invalid.
        """
        if config is None:
            config = MonitorConfig(agent_id=agent_id)

        self.health_monitor.start_monitoring(agent_id, config)
        self.circuit_breaker.initialize_circuit(agent_id)

    def stop_monitoring(self, agent_id: str) -> None:
        """
        Stop monitoring an agent.

        Args:
            agent_id: ID of the agent to stop monitoring.
        """
        self.health_monitor.stop_monitoring(agent_id)

    def get_agent_health(self, agent_id: str):
        """
        Get current health metrics for agent.

        Args:
            agent_id: ID of the agent.

        Returns:
            HealthMetrics: Current health metrics.

        Raises:
            AgentNotFoundError: If agent not being monitored.
        """
        return self.health_monitor.get_metrics(agent_id)

    def is_agent_circuit_open(self, agent_id: str) -> bool:
        """
        Check if agent's circuit is OPEN (killed or should be killed).

        Args:
            agent_id: ID of the agent.

        Returns:
            bool: True if circuit is OPEN.
        """
        # Check state manager first (persisted state)
        if self.state_manager.is_agent_killed(agent_id):
            return True

        # Check circuit breaker (in-memory state)
        return self.circuit_breaker.is_open(agent_id)

    def get_agent_state(self, agent_id: str) -> CircuitState:
        """
        Get current circuit state for agent.

        Args:
            agent_id: ID of the agent.

        Returns:
            CircuitState: Current circuit state.
        """
        return self.circuit_breaker.get_state(agent_id)

    def manual_trigger(
        self,
        agent_id: str,
        reason: str,
        operator_id: str,
    ) -> InterruptEvent:
        """
        Manually trigger Kill-Switch on an agent.

        Args:
            agent_id: ID of the agent to kill.
            reason: Human-readable reason for the kill.
            operator_id: ID of the operator triggering the kill.

        Returns:
            InterruptEvent: Event record with latency and outcome.

        Raises:
            InterruptInProgressError: If interrupt already in progress.
        """
        logger.info(
            f"Manual Kill-Switch triggered for {agent_id} by {operator_id}: "
            f"{reason}"
        )

        return self.interrupt_engine.trigger_interrupt(
            agent_id=agent_id,
            reason=reason,
            triggered_by=operator_id,
            reason_type=KillReason.MANUAL_TRIGGER,
        )

    def re_enable(
        self,
        agent_id: str,
        operator_id: str,
        acknowledgment: str,
    ) -> bool:
        """
        Re-enable a killed agent.

        Requires operator acknowledgment of kill reason. Agent remains dead
        until explicit re-enable — no auto-restart.

        Args:
            agent_id: ID of the agent to re-enable.
            operator_id: ID of the operator re-enabling the agent.
            acknowledgment: Operator's acknowledgment of kill reason.

        Returns:
            bool: True if re-enable successful.

        Raises:
            AgentNotFoundError: If agent was not killed.
        """
        if not self.is_agent_circuit_open(agent_id):
            # Agent not killed, nothing to re-enable
            logger.info(f"Agent {agent_id} was not killed, no re-enable needed")
            return True

        logger.info(
            f"Re-enabling agent {agent_id} by {operator_id}. "
            f"Acknowledgment: {acknowledgment}"
        )

        # Clear persisted state
        self.state_manager.clear_state(agent_id)

        # Reset circuit breaker state
        self.circuit_breaker.initialize_circuit(agent_id)

        # Re-initialize health monitoring
        self.health_monitor.stop_monitoring(agent_id)

        return True

    def get_interrupt_history(
        self,
        agent_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[InterruptEvent]:
        """
        Get interrupt history.

        Args:
            agent_id: Optional filter by agent ID.
            limit: Maximum number of events to return.

        Returns:
            List[InterruptEvent]: List of interrupt events.
        """
        return self.interrupt_engine.get_interrupt_history(
            agent_id=agent_id,
            limit=limit,
        )

    def evaluate_and_trigger(
        self,
        agent_id: str,
        config: MonitorConfig,
    ) -> bool:
        """
        Evaluate current metrics and trigger Kill-Switch if needed.

        Args:
            agent_id: ID of the agent.
            config: Monitoring configuration.

        Returns:
            bool: True if Kill-Switch was triggered.
        """
        try:
            metrics = self.health_monitor.get_metrics(agent_id)
        except Exception as e:
            logger.warning(f"Could not get metrics for {agent_id}: {e}")
            return False

        # Check if should trigger
        if self.circuit_breaker.should_trigger(agent_id, metrics, config):
            # Record failure
            self.circuit_breaker.record_failure(agent_id)

            # Check if circuit should open
            if self.circuit_breaker.get_failure_count(agent_id) >= config.failure_threshold:
                self.circuit_breaker.open_circuit(
                    agent_id,
                    cooldown_seconds=config.cooldown_seconds,
                )

                # Trigger interrupt
                try:
                    self.interrupt_engine.trigger_interrupt(
                        agent_id=agent_id,
                        reason=f"Threshold exceeded: {config}",
                        triggered_by="SYSTEM",
                        reason_type=KillReason.ERROR_RATE_EXCEEDED,
                    )
                    return True
                except InterruptInProgressError:
                    # Interrupt already in progress
                    return False
        else:
            # Record success
            self.circuit_breaker.record_success(agent_id)

        return False
