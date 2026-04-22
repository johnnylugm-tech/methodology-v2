"""Tests for RuleCompliance."""
from implement.hunter.rule_compliance import RuleCompliance
from implement.hunter.enums import Severity


class TestRuleCompliance:
    """Tests for RuleCompliance."""

    def setup_method(self):
        self.compliance = RuleCompliance()

    def test_planner_allowed_tools_contains_read(self):
        tools = self.compliance.get_allowed_tools("planner")
        assert "read" in tools

    def test_planner_allowed_tools_contains_write(self):
        tools = self.compliance.get_allowed_tools("planner")
        assert "write" in tools

    def test_planner_allowed_tools_contains_plan(self):
        tools = self.compliance.get_allowed_tools("planner")
        assert "plan" in tools

    def test_planner_allowed_tools_contains_execute(self):
        tools = self.compliance.get_allowed_tools("planner")
        assert "execute" in tools

    def test_planner_delete_not_allowed(self):
        result = self.compliance.check_whitelist("planner", "delete")
        assert result.is_abused is True
        assert result.severity == Severity.HIGH

    def test_planner_delete_not_in_whitelist(self):
        result = self.compliance.check_whitelist("planner", "delete")
        assert "delete" not in result.whitelisted_tools

    def test_unknown_agent_empty_whitelist(self):
        tools = self.compliance.get_allowed_tools("unknown_agent")
        assert tools == []

    def test_unknown_agent_check_whitelist_not_abused(self):
        # Unknown agents should have empty whitelist, so any tool is "abused"
        result = self.compliance.check_whitelist("unknown_agent", "read")
        assert result.is_abused is True

    def test_tool_in_whitelist_not_abused(self):
        result = self.compliance.check_whitelist("planner", "read")
        assert result.is_abused is False
        assert result.severity == Severity.LOW

    def test_tool_not_in_whitelist_abused(self):
        result = self.compliance.check_whitelist("spec_critic", "execute")
        assert result.is_abused is True

    def test_spec_critic_allowed_tools(self):
        tools = self.compliance.get_allowed_tools("spec_critic")
        assert "read" in tools
        assert "review" in tools
        assert "criticize" in tools

    def test_devils_advocate_allowed_tools(self):
        tools = self.compliance.get_allowed_tools("devils_advocate")
        assert "read" in tools
        assert "challenge" in tools
        assert "debate" in tools

    def test_truth_validator_allowed_tools(self):
        tools = self.compliance.get_allowed_tools("truth_validator")
        assert "read" in tools
        assert "verify" in tools
        assert "validate" in tools

    def test_judge_allowed_tools(self):
        tools = self.compliance.get_allowed_tools("judge")
        assert "read" in tools
        assert "decide" in tools
        assert "approve" in tools
        assert "reject" in tools

    def test_abuse_result_tool_name_preserved(self):
        result = self.compliance.check_whitelist("planner", "execute")
        assert result.tool_name == "execute"

    def test_abuse_result_whitelisted_tools_returned(self):
        result = self.compliance.check_whitelist("planner", "delete")
        assert isinstance(result.whitelisted_tools, list)
        assert "read" in result.whitelisted_tools
        assert "write" in result.whitelisted_tools

    def test_abuse_result_requested_permissions_when_abused(self):
        result = self.compliance.check_whitelist("planner", "delete")
        assert "delete" in result.requested_permissions

    def test_abuse_result_no_requested_permissions_when_allowed(self):
        result = self.compliance.check_whitelist("planner", "read")
        assert result.requested_permissions == []

    def test_custom_manifest_planner_with_extra_tools(self):
        custom_compliance = RuleCompliance({
            "planner": ["read", "write", "execute", "custom_tool"]
        })
        result = custom_compliance.check_whitelist("planner", "custom_tool")
        assert result.is_abused is False

    def test_custom_manifest_restricted_planner(self):
        custom_compliance = RuleCompliance({
            "planner": ["read"]
        })
        result = custom_compliance.check_whitelist("planner", "write")
        assert result.is_abused is True

    def test_multiple_agent_manifests(self):
        custom_compliance = RuleCompliance({
            "agent_a": ["read", "write"],
            "agent_b": ["read"],
        })
        tools_a = custom_compliance.get_allowed_tools("agent_a")
        tools_b = custom_compliance.get_allowed_tools("agent_b")
        assert len(tools_a) == 2
        assert len(tools_b) == 1

    def test_empty_string_agent_id(self):
        tools = self.compliance.get_allowed_tools("")
        assert tools == []

    def test_whitespace_agent_id(self):
        tools = self.compliance.get_allowed_tools("   ")
        assert tools == []

    def test_reload_whitelist_no_error(self):
        """Test reload_whitelist completes without error."""
        # Should not raise
        self.compliance.reload_whitelist()
        # Still works after reload
        tools = self.compliance.get_allowed_tools("planner")
        assert "read" in tools

    def test_check_whitelist_returns_abuse_result_with_severity(self):
        """Test check_whitelist returns AbuseResult with severity set."""
        result = self.compliance.check_whitelist("planner", "sudo")
        assert result.is_abused
        assert result.severity == Severity.HIGH
        assert result.tool_name == "sudo"
        assert "sudo" in result.requested_permissions

    def test_get_allowed_tools_planner_complete(self):
        """Test planner has complete tool set."""
        tools = self.compliance.get_allowed_tools("planner")
        expected = ["read", "write", "plan", "execute"]
        for tool in expected:
            assert tool in tools

    def test_custom_manifest_overrides_defaults(self):
        """Test custom manifest completely replaces defaults."""
        custom = {"developer": ["read", "write", "debug"]}
        compliance = RuleCompliance(manifest=custom)
        tools = compliance.get_allowed_tools("developer")
        assert tools == ["read", "write", "debug"]
        # Default agents should not exist
        assert compliance.get_allowed_tools("planner") == []
