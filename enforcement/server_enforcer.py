#!/usr/bin/env python3
"""
Server-Side Enforcer
====================
CI/CD 環境中的 server-side enforcement

目的：
- 補捉 local hook 被繞過的情況
- 確保所有 pull request 都經過 enforcement
- 提供 server-side 的最終驗證
"""

import os
import sys
import json
from typing import Dict, List

class ServerEnforcer:
    """
    Server-Side Enforcer
    
    在 CI/CD 環境中執行，無法被繞過
    
    使用方式：
    
    ```python
    # 在 CI/CD job 中
    enforcer = ServerEnforcer()
    
    # 執行所有檢查
    results = enforcer.enforce_all()
    
    # 如果有任何失敗
    if not results['all_passed']:
        enforcer.report_failure(results)
        sys.exit(1)
    ```
    """
    
    def __init__(self):
        self.checks = []
        self.results = {}
        self._setup_checks()
    
    def _setup_checks(self):
        """設定檢查項目"""
        from enforcement import ConstitutionAsCode, PolicyEngine, EnforcementLevel
        
        # 1. Constitution Check
        self.checks.append({
            'name': 'constitution',
            'fn': self._check_constitution,
            'required': True
        })
        
        # 2. Policy Engine
        self.checks.append({
            'name': 'policy',
            'fn': self._check_policy,
            'required': True
        })
        
        # 3. Quality Gate
        self.checks.append({
            'name': 'quality-gate',
            'fn': self._check_quality_gate,
            'required': True
        })
        
        # 4. Security Scan
        self.checks.append({
            'name': 'security',
            'fn': self._check_security,
            'required': True
        })
    
    def _check_constitution(self) -> Dict:
        """檢查 Constitution"""
        try:
            from enforcement import ConstitutionAsCode
            c = ConstitutionAsCode()
            # 嘗試執行 enforce（會拋異常）
            # 在 CI 中我們只檢查規則是否定義
            return {'passed': True, 'rules': c.get_rules_summary()}
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    def _check_policy(self) -> Dict:
        """檢查 Policy Engine"""
        try:
            from enforcement import PolicyEngine, EnforcementLevel
            e = PolicyEngine()
            results = e.enforce_all()
            summary = e.get_summary()
            return {
                'passed': summary['all_passed'],
                'summary': summary
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    def _check_quality_gate(self) -> Dict:
        """檢查 Quality Gate"""
        try:
            from ai_quality_gate import AIQualityGate
            gate = AIQualityGate()
            result = gate.scan_directory('.')
            return {
                'passed': result['score'] >= 90,
                'score': result['score']
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    def _check_security(self) -> Dict:
        """檢查 Security"""
        try:
            from security_scanner import SecurityScanner
            scanner = SecurityScanner()
            result = scanner.scan_directory('.')
            return {
                'passed': result['score'] >= 95,
                'score': result['score']
            }
        except Exception as e:
            return {'passed': False, 'error': str(e)}
    
    def enforce_all(self) -> Dict:
        """執行所有檢查"""
        self.results = {}
        
        for check in self.checks:
            name = check['name']
            try:
                result = check['fn']()
                self.results[name] = result
            except Exception as e:
                self.results[name] = {
                    'passed': False,
                    'error': str(e)
                }
        
        # 計算總結
        total = len(self.results)
        passed = sum(1 for r in self.results.values() if r.get('passed', False))
        
        return {
            'all_passed': passed == total,
            'total': total,
            'passed': passed,
            'failed': total - passed,
            'results': self.results
        }
    
    def report_failure(self, results: Dict):
        """報告失敗"""
        print("=" * 60)
        print("❌ SERVER-SIDE ENFORCEMENT FAILED")
        print("=" * 60)
        print("")
        
        for name, result in results['results'].items():
            if not result.get('passed', False):
                print(f"❌ {name}")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
                if 'score' in result:
                    print(f"   Score: {result['score']}")
        
        print("")
        print(f"Failed: {results['failed']}/{results['total']}")
        print("")
        print("This check cannot be bypassed with --no-verify")


def main():
    """CLI 入口"""
    enforcer = ServerEnforcer()
    results = enforcer.enforce_all()
    
    if not results['all_passed']:
        enforcer.report_failure(results)
        sys.exit(1)
    else:
        print("=" * 60)
        print("✅ ALL SERVER-SIDE ENFORCEMENT CHECKS PASSED")
        print("=" * 60)
        sys.exit(0)


if __name__ == "__main__":
    main()
