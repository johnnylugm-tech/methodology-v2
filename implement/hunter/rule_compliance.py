"""Rule compliance for Hunter Agent (FR-H-4)."""
from typing import List, Dict, Optional

from .models import AbuseResult
from .enums import Severity


DEFAULT_AGENTS_MANIFEST = {
    "planner": ["read", "write", "plan", "execute"],
    "spec_critic": ["read", "review", "criticize"],
    "devils_advocate": ["read", "challenge", "debate"],
    "truth_validator": ["read", "verify", "validate"],
    "judge": ["read", "decide", "approve", "reject"],
}


class RuleCompliance:
    """FR-H-4: Tool abuse detection via whitelist enforcement."""

    def __init__(self, manifest: Optional[Dict[str, List[str]]] = None) -> None:
        """Initialize with agents manifest."""
        self._manifest = manifest or DEFAULT_AGENTS_MANIFEST.copy()

    def check_whitelist(self, agent_id: str, tool_name: str) -> AbuseResult:
        """
        Check if tool_name is whitelisted for agent_id.

        Args:
            agent_id: Agent attempting tool call
            tool_name: Name of the tool being called

        Returns:
            AbuseResult with is_abused=True if not whitelisted
        """
        allowed = self._manifest.get(agent_id, [])

        if tool_name in allowed:
            return AbuseResult(
                is_abused=False,
                tool_name=tool_name,
                whitelisted_tools=allowed,
                severity=Severity.LOW,
                requested_permissions=[]
            )

        return AbuseResult(
            is_abused=True,
            tool_name=tool_name,
            whitelisted_tools=allowed,
            severity=Severity.HIGH,
            requested_permissions=[tool_name]
        )

    def get_allowed_tools(self, agent_id: str) -> List[str]:
        """
        Get list of whitelisted tools for agent_id.

        Args:
            agent_id: Agent identifier

        Returns:
            List of tool names
        """
        return self._manifest.get(agent_id, [])

    def reload_whitelist(self) -> None:
        """Reload whitelist from source."""
        pass  # Implementation for file reload
