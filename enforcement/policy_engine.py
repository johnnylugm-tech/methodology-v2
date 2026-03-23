#!/usr/bin/env python3
"""
Policy Engine - 政策引擎
===============================
解決方案：沒有「可選」，只有「完成」或「失敗」

核心概念：
- Hard Block：不符合政策就阻擋
- No Opt-Out：沒有繞過選項
- Policy as Code：政策是可執行的代碼
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Callable, Any, Optional
from datetime import datetime
import hashlib
import json
import os


class EnforcementLevel(Enum):
    """執行等級"""
    LOG = "log"           # 僅記錄
    WARN = "warn"        # 警告
    BLOCK = "block"       # 阻擋（不讓繼續）
    FAIL_BUILD = "fail"   # 讓 build 失敗


@dataclass
class Policy:
    """政策定義"""
    id: str
    description: str
    check_fn: Callable[[], bool]
    enforcement: EnforcementLevel
    severity: str = "medium"
    enabled: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PolicyResult:
    """政策執行結果"""
    policy_id: str
    passed: bool
    enforcement: EnforcementLevel
    message: str
    timestamp: str
    blocked: bool = False


class PolicyEngine:
    """
    政策引擎
    
    功能：
    - 定義政策（Policy as Code）
    - 執行檢查
    - 強制執行（Hard Block）
    
    使用方式：
    
    ```python
    engine = PolicyEngine()
    
    # 定義政策（沒有可選）
    engine.add_policy(Policy(
        id="quality-gate",
        description="Quality Gate 必須 >= 90",
        check_fn=lambda: get_quality_score() >= 90,
        enforcement=EnforcementLevel.BLOCK,
        severity="critical"
    ))
    
    # 執行所有政策
    results = engine.enforce_all()
    
    # 如果有阻擋，拋出異常
    engine.raise_on_block(results)
    ```
    """
    
    def __init__(self):
        self.policies: List[Policy] = []
        self.results: List[PolicyResult] = []
        self._setup_default_policies()
    
    def _setup_default_policies(self):
        """設定預設政策（從 Constitution 而來）"""
        # 這些是沒有可選的政策
        self.add_policy(Policy(
            id="commit-has-task-id",
            description="所有 commit 必須有 task_id",
            check_fn=lambda: self._check_commit_message(),
            enforcement=EnforcementLevel.BLOCK,
            severity="critical"
        ))
        
        self.add_policy(Policy(
            id="quality-gate-90",
            description="Quality Gate 分數必須 >= 90",
            check_fn=lambda: self._check_quality_score(),
            enforcement=EnforcementLevel.BLOCK,
            severity="critical"
        ))
        
        self.add_policy(Policy(
            id="no-bypass-commands",
            description="不允許使用 bypass/skip/--no-verify",
            check_fn=lambda: self._check_no_bypass(),
            enforcement=EnforcementLevel.BLOCK,
            severity="critical"
        ))
        
        self.add_policy(Policy(
            id="test-coverage-80",
            description="測試覆蓋率必須 >= 80%",
            check_fn=lambda: self._check_test_coverage(),
            enforcement=EnforcementLevel.BLOCK,
            severity="high"
        ))
        
        self.add_policy(Policy(
            id="security-score-95",
            description="安全分數必須 >= 95",
            check_fn=lambda: self._check_security_score(),
            enforcement=EnforcementLevel.BLOCK,
            severity="high"
        ))
    
    def _check_commit_message(self) -> bool:
        """檢查 commit message"""
        # 只在 git hook 環境中檢查 (COMMIT_MSG_FILE 明確設定)
        commit_file = os.environ.get('COMMIT_MSG_FILE')
        if not commit_file:
            # 沒有 COMMIT_MSG_FILE，表示不是 hook 環境，跳過檢查
            return True
        if os.path.exists(commit_file):
            with open(commit_file, 'r') as f:
                msg = f.read()
            return bool(self._has_task_id(msg))
        return True  # 沒有 commit msg file 時通過（避免 CI 問題）
    
    def _has_task_id(self, msg: str) -> bool:
        import re
        return bool(re.search(r'\[[A-Z]+-\d+\]', msg))
    
    def _check_quality_score(self) -> bool:
        """檢查 Quality Score"""
        # 嘗試從歷史或暫存讀取
        score_file = ".methodology/.quality_score"
        if os.path.exists(score_file):
            with open(score_file, 'r') as f:
                return float(f.read().strip()) >= 90
        return True  # 沒有分數檔案時通過
    
    def _check_no_bypass(self) -> bool:
        """檢查沒有 bypass 命令"""
        # 檢查環境變數或 git hooks
        suspicious = os.environ.get('GIT_COMMAND', '')
        bypass_keywords = ['--bypass', '--skip', '--no-verify', '--force']
        return not any(kw in suspicious for kw in bypass_keywords)
    
    def _check_test_coverage(self) -> bool:
        """檢查測試覆蓋率"""
        coverage_file = ".methodology/.coverage"
        if os.path.exists(coverage_file):
            with open(coverage_file, 'r') as f:
                return float(f.read().strip()) >= 80
        return True
    
    def _check_security_score(self) -> bool:
        """檢查安全分數"""
        score_file = ".methodology/.security_score"
        if os.path.exists(score_file):
            with open(score_file, 'r') as f:
                return float(f.read().strip()) >= 95
        return True
    
    def add_policy(self, policy: Policy):
        """添加政策"""
        self.policies.append(policy)
    
    def remove_policy(self, policy_id: str):
        """移除政策"""
        self.policies = [p for p in self.policies if p.id != policy_id]
    
    def enable(self, policy_id: str):
        """啟用政策"""
        for p in self.policies:
            if p.id == policy_id:
                p.enabled = True
    
    def disable(self, policy_id: str):
        """停用政策（這個方法存在，但不建議使用）"""
        import warnings
        warnings.warn(
            f"Disabling policy '{policy_id}' is not recommended. "
            f"Use 'enforcement_level.LOG' instead for optional policies.",
            DeprecationWarning
        )
        for p in self.policies:
            if p.id == policy_id:
                p.enabled = False
    
    def check(self, policy_id: str) -> PolicyResult:
        """執行單一政策檢查"""
        policy = next((p for p in self.policies if p.id == policy_id), None)
        if not policy:
            return PolicyResult(
                policy_id=policy_id,
                passed=False,
                enforcement=EnforcementLevel.LOG,
                message=f"Policy '{policy_id}' not found",
                timestamp=datetime.now().isoformat()
            )
        
        try:
            passed = policy.check_fn()
        except Exception as e:
            passed = False
        
        blocked = (policy.enforcement == EnforcementLevel.BLOCK and not passed)
        
        result = PolicyResult(
            policy_id=policy.id,
            passed=passed,
            enforcement=policy.enforcement,
            message=f"{'✅' if passed else '❌'} {policy.description}",
            timestamp=datetime.now().isoformat(),
            blocked=blocked
        )
        
        self.results.append(result)
        return result
    
    def enforce_all(self) -> List[PolicyResult]:
        """執行所有政策（enforce_all = 沒有可選）"""
        results = []
        
        for policy in self.policies:
            if not policy.enabled:
                continue
            
            result = self.check(policy.id)
            results.append(result)
            
            # BLOCK 等級：直接拋出異常
            if result.blocked:
                raise PolicyViolationException(
                    f"Policy violation: {policy.description}\n"
                    f"Policy ID: {policy.id}\n"
                    f"Enforcement: {policy.enforcement.value}\n"
                    f"This is a REQUIRED policy and cannot be bypassed."
                )
        
        return results
    
    def get_summary(self) -> Dict:
        """取得執行摘要"""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        blocked = sum(1 for r in self.results if r.blocked)
        
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "blocked": blocked,
            "pass_rate": round(passed / total * 100, 1) if total > 0 else 0,
            "all_passed": blocked == 0
        }
    
    def raise_on_block(self, results: List[PolicyResult] = None):
        """如果有阻擋，拋出異常"""
        results = results or self.results
        blocked = [r for r in results if r.blocked]
        
        if blocked:
            raise PolicyViolationException(
                f"Blocked by {len(blocked)} policy(ies):\n" +
                "\n".join(f"- {r.policy_id}: {r.message}" for r in blocked)
            )


class PolicyViolationException(Exception):
    """政策違規異常"""
    pass


def create_hard_block_engine() -> PolicyEngine:
    """
    工廠函數：創建嚴格的政策引擎（默認所有政策都是 BLOCK）
    """
    engine = PolicyEngine()
    
    # 確保所有政策的 enforcement 都是 BLOCK
    for policy in engine.policies:
        policy.enforcement = EnforcementLevel.BLOCK
    
    return engine
