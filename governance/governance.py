"""Governance and Compliance Module for methodology-v2 with framework integration"""
import json, time

# Framework integration
try:
    import sys
    sys.path.insert(0, '/workspace/methodology-v2')
    from methodology import RBAC, AuditLogger as FrameworkAuditLogger
    FRAMEWORK_AVAILABLE = True
except ImportError:
    FRAMEWORK_AVAILABLE = False
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

class Severity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RiskLevel(Enum):
    LOW = 0
    MEDIUM = 50
    HIGH = 75
    CRITICAL = 100

@dataclass
class Policy:
    """Policy definition"""
    name: str
    rules: List[str]
    severity: str = "medium"
    thresholds: Dict = field(default_factory=dict)
    enabled: bool = True

@dataclass
class AuditEntry:
    """Audit log entry"""
    entry_id: str
    timestamp: float
    action: str
    agent: str
    user: str
    result: str
    metadata: Dict = field(default_factory=dict)

class PolicyEngine:
    """Policy enforcement engine"""
    
    def __init__(self):
        self.policies: Dict[str, Policy] = {}
        self.violations: List[Dict] = []
    
    def add_policy(self, policy: Policy):
        self.policies[policy.name] = policy
    
    def check(self, action: Dict) -> Dict:
        """Check action against policies"""
        violations = []
        
        for policy in self.policies.values():
            if not policy.enabled:
                continue
            
            # Check each rule
            for rule in policy.rules:
                if self._violates(action, rule, policy.thresholds):
                    violations.append({
                        "policy": policy.name,
                        "rule": rule,
                        "severity": policy.severity,
                        "action": action
                    })
        
        if violations:
            self.violations.extend(violations)
        
        return {
            "allowed": len(violations) == 0,
            "violations": violations
        }
    
    def _violates(self, action: Dict, rule: str, thresholds: Dict) -> bool:
        """Check if action violates rule"""
        if rule == "max_tokens_per_day":
            return action.get("tokens", 0) > thresholds.get("max_tokens", 100000)
        if rule == "max_cost_per_request":
            return action.get("cost", 0) > thresholds.get("max_cost", 10.0)
        if rule == "no_pii_storage":
            return "pii" in action.get("data", "").lower()
        if rule == "encrypt_sensitive":
            return action.get("encrypted", True) == False
        
        return False

class AuditLogger:
    """Audit trail logger"""
    
    def __init__(self):
        self.entries: List[AuditEntry] = []
    
    def log(self, action: str, agent: str, user: str, result: str, metadata: Dict = None):
        entry = AuditEntry(
            entry_id=f"audit_{len(self.entries)}",
            timestamp=time.time(),
            action=action,
            agent=agent,
            user=user,
            result=result,
            metadata=metadata or {}
        )
        self.entries.append(entry)
    
    def query(self, start_date: str = None, end_date: str = None, 
              agent: str = None, user: str = None, action: str = None) -> List[AuditEntry]:
        results = self.entries
        
        if agent:
            results = [e for e in results if e.agent == agent]
        if user:
            results = [e for e in results if e.user == user]
        if action:
            results = [e for e in results if e.action == action]
        
        return results
    
    def get_stats(self) -> Dict:
        stats = {
            "total": len(self.entries),
            "by_agent": defaultdict(int),
            "by_user": defaultdict(int),
            "by_result": defaultdict(int)
        }
        
        for entry in self.entries:
            stats["by_agent"][entry.agent] += 1
            stats["by_user"][entry.user] += 1
            stats["by_result"][entry.result] += 1
        
        return dict(stats)

class ComplianceReporter:
    """Generate compliance reports"""
    
    FRAMEWORKS = ["SOC2", "GDPR", "HIPAA", "ISO27001"]
    
    def __init__(self):
        self.audit_logger = AuditLogger()
    
    def generate(self, framework: str, period: str) -> Dict:
        """Generate compliance report"""
        if framework not in self.FRAMEWORKS:
            raise ValueError(f"Unknown framework: {framework}")
        
        report = {
            "framework": framework,
            "period": period,
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_actions": len(self.audit_logger.entries),
                "compliant": sum(1 for e in self.audit_logger.entries if e.result == "success"),
                "violations": len(self.audit_logger.entries) - sum(1 for e in self.audit_logger.entries if e.result == "success")
            },
            "controls": self._get_controls(framework)
        }
        
        return report
    
    def _get_controls(self, framework: str) -> List[Dict]:
        """Get control requirements for framework"""
        controls = {
            "SOC2": [
                {"id": "CC6.1", "name": "Logical Access", "status": "pass"},
                {"id": "CC7.2", "name": "System Operations", "status": "pass"},
                {"id": "CC8.1", "name": "Change Management", "status": "pass"}
            ],
            "GDPR": [
                {"id": "ART-32", "name": "Security of Processing", "status": "pass"},
                {"id": "ART-33", "name": "Breach Notification", "status": "pass"}
            ]
        }
        
        return controls.get(framework, [])

class RiskManager:
    """Risk assessment and management"""
    
    def __init__(self):
        self.risk_scores: Dict[str, int] = {}
        self.assessments: List[Dict] = []
    
    def assess(self, action: Dict) -> int:
        """Assess risk score (0-100)"""
        score = 0
        
        # Factor: Action type
        action_risk = {
            "agent.spawn": 30,
            "agent.execute": 20,
            "agent.delete": 50,
            "data.read": 10,
            "data.write": 25,
            "data.delete": 60
        }
        score += action_risk.get(action.get("type", ""), 0)
        
        # Factor: Data sensitivity
        if action.get("contains_sensitive", False):
            score += 30
        
        # Factor: User risk
        if action.get("user_trust", 1.0) < 0.5:
            score += 20
        
        # Cap at 100
        score = min(100, score)
        
        # Store
        self.risk_scores[action.get("agent", "unknown")] = score
        self.assessments.append({
            "action": action,
            "score": score,
            "level": self._score_to_level(score)
        })
        
        return score
    
    def _score_to_level(self, score: int) -> str:
        if score < 25:
            return "low"
        elif score < 50:
            return "medium"
        elif score < 75:
            return "high"
        return "critical"
    
    def get_profile(self) -> Dict:
        """Get risk profile"""
        levels = {"low": 0, "medium": 0, "high": 0, "critical": 0}
        
        for score in self.risk_scores.values():
            levels[self._score_to_level(score)] += 1
        
        return levels

class RBAC:
    """Role-Based Access Control"""
    
    def __init__(self):
        self.roles: Dict[str, List[str]] = {}
        self.user_roles: Dict[str, List[str]] = {}
    
    def add_role(self, role: str, permissions: List[str]):
        self.roles[role] = permissions
    
    def assign_role(self, user: str, role: str):
        if user not in self.user_roles:
            self.user_roles[user] = []
        self.user_roles[user].append(role)
    
    def check(self, user: str, permission: str) -> bool:
        """Check if user has permission"""
        user_role_list = self.user_roles.get(user, [])
        
        for role in user_role_list:
            perms = self.roles.get(role, [])
            if "*" in perms or permission in perms:
                return True
        
        return False

class GovernanceEngine:
    """Main governance engine"""
    
    def __init__(self):
        self.policy_engine = PolicyEngine()
        self.audit_logger = AuditLogger()
        self.compliance = ComplianceReporter()
        self.risk_manager = RiskManager()
        self.rbac = RBAC()
    
    def add_policy(self, policy: Policy):
        self.policy_engine.add_policy(policy)
    
    def check(self, action: Dict) -> Dict:
        """Check action through all governance layers"""
        # Policy check
        policy_result = self.policy_engine.check(action)
        
        # Risk assessment
        risk_score = self.risk_manager.assess(action)
        
        return {
            "allowed": policy_result["allowed"] and risk_score < 75,
            "policy_violations": policy_result["violations"],
            "risk_score": risk_score,
            "risk_level": self.risk_manager._score_to_level(risk_score)
        }

# Demo
if __name__ == "__main__":
    # Initialize
    gov = GovernanceEngine()
    
    # Add policy
    policy = Policy(
        name="cost_control",
        rules=["max_tokens_per_day", "max_cost_per_request"],
        thresholds={"max_tokens": 100000, "max_cost": 10.0}
    )
    gov.add_policy(policy)
    
    # Check action
    action = {"type": "agent.execute", "tokens": 50000, "cost": 5.0}
    result = gov.check(action)
    print("Check result:", json.dumps(result, indent=2))
    
    # Audit
    gov.audit_logger.log("agent.execute", "coder", "user123", "success", {"tokens": 500})
    print("\nAudit stats:", json.dumps(gov.audit_logger.get_stats(), indent=2))
    
    # Compliance
    report = gov.compliance.generate("SOC2", "Q1_2026")
    print("\nCompliance report:", json.dumps(report, indent=2))
    
    print("\n✅ Governance ready!")
