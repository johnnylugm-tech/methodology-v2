"""Tests for governance module"""
from governance import Policy, PolicyEngine, AuditLogger, ComplianceReporter, RiskManager, RBAC, GovernanceEngine

def test_policy():
    policy = Policy(name="test", rules=["rule1"], severity="high")
    assert policy.name == "test"

def test_policy_engine():
    engine = PolicyEngine()
    policy = Policy(name="test", rules=["rule1"])
    engine.add_policy(policy)
    assert "test" in engine.policies

def test_audit_logger():
    logger = AuditLogger()
    logger.log("test", "agent1", "user1", "success")
    logs = logger.query(action="test")
    assert len(logs) >= 1

def test_compliance():
    reporter = ComplianceReporter()
    report = reporter.generate("SOC2", "Q1_2026")
    assert report["framework"] == "SOC2"

def test_risk():
    risk_mgr = RiskManager()
    score = risk_mgr.assess({"type": "agent.execute"})
    assert 0 <= score <= 100

def test_rbac():
    rbac = RBAC()
    rbac.add_role("admin", ["*"])
    assert "admin" in rbac.roles

def test_governance():
    gov = GovernanceEngine()
    policy = Policy(name="test", rules=[])
    gov.add_policy(policy)
    result = gov.check({"type": "agent.execute"})
    assert "allowed" in result

if __name__ == "__main__":
    test_policy()
    test_policy_engine()
    test_audit_logger()
    test_compliance()
    test_risk()
    test_rbac()
    test_governance()
    print("All tests passed!")
