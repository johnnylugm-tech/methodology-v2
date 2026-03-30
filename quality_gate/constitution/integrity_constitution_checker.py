#!/usr/bin/env python3
"""
Integrity Constitution Checker
================================

為 Constitution 增加「誠信維度」檢查。

功能：
1. 檢查 .integrity_tracker.json 是否存在
2. 檢查誠信分數是否低於閾值
3. 檢查是否有重大違規記錄
4. 輸出帶有 Integrity 維度的 Constitution 結果

Usage:
    python integrity_constitution_checker.py /path/to/project
    python integrity_constitution_checker.py /path/to/project --threshold 60
"""

import sys
import json
from pathlib import Path
from typing import Dict, Optional

# 確保可以匯入
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from quality_gate.integrity_tracker import IntegrityTracker


class IntegrityConstitutionChecker:
    """Constitution Integrity 維度檢查器"""
    
    DEFAULT_THRESHOLD = 60  # 預設誠信分數閾值
    
    def __init__(self, project_path: str, threshold: int = None):
        """
        初始化檢查器
        
        Args:
            project_path: 專案路徑
            threshold: 誠信分數閾值（預設 60）
        """
        self.project_path = Path(project_path)
        self.threshold = threshold or self.DEFAULT_THRESHOLD
        self.tracker = None
    
    def check(self) -> Dict:
        """
        執行 Integrity Constitution 檢查
        
        Returns:
            Dict: 檢查結果
        """
        integrity_file = self.project_path / ".integrity_tracker.json"
        
        # 1. 檢查是否存在 Integrity Tracker 記錄
        if not integrity_file.exists():
            return {
                "passed": True,  # 沒有記錄 = 無違規 = 通過
                "score": 100,
                "violations": [],
                "integrity_score": 100,
                "trust_level": "FULL_TRUST",
                "message": "無 Integrity Tracker 記錄，視為誠信"
            }
        
        # 2. 載入並檢查
        try:
            self.tracker = IntegrityTracker(str(self.project_path))
            report = self.tracker.get_integrity_report()
            
            score = report["integrity_score"]
            trust_level = report["trust_level"]
            violations = report["violations"]
            
            # 3. 判斷是否通過
            passed = score >= self.threshold
            
            # 4. 找出嚴重違規
            critical_violations = []
            for v in violations:
                if v["deduction"] >= 20:  # 重大違規扣 20 分以上
                    critical_violations.append({
                        "type": v["type"],
                        "phase": v["phase"],
                        "details": v["details"],
                        "deduction": v["deduction"]
                    })
            
            return {
                "passed": passed,
                "score": score,
                "violations": critical_violations,
                "integrity_score": score,
                "trust_level": trust_level,
                "message": f"Integrity Score: {score}, Trust: {trust_level}"
            }
            
        except Exception as e:
            return {
                "passed": False,
                "score": 0,
                "violations": [{
                    "type": "integrity_check_failed",
                    "details": str(e)
                }],
                "integrity_score": 0,
                "trust_level": "UNKNOWN",
                "message": f"Integrity Check Failed: {e}"
            }
    
    def get_exit_conditions(self) -> Dict:
        """
        取得 Integrity 相關的 Phase 退出條件
        
        Returns:
            Dict: 退出條件
        """
        if not self.tracker:
            self.tracker = IntegrityTracker(str(self.project_path))
        
        can_proceed = self.tracker.can_proceed_to_next_phase()
        
        return {
            "integrity_score": self.tracker.integrity_score,
            "trust_level": self.tracker.get_trust_level(),
            "allowed": can_proceed["allowed"],
            "reason": can_proceed["reason"],
            "restrictions": can_proceed["restrictions"]
        }


def main():
    """CLI 入口"""
    if len(sys.argv) < 2:
        print("Usage: integrity_constitution_checker.py <project_path> [threshold]")
        sys.exit(1)
    
    project_path = sys.argv[1]
    threshold = int(sys.argv[2]) if len(sys.argv) > 2 else None
    
    checker = IntegrityConstitutionChecker(project_path, threshold)
    result = checker.check()
    
    # 輸出結果
    print("\n" + "=" * 50)
    print("🛡️  Integrity Constitution Check")
    print("=" * 50)
    print(f"\nPassed: {'✅ YES' if result['passed'] else '❌ NO'}")
    print(f"Score: {result['score']}/100")
    print(f"Trust Level: {result['trust_level']}")
    print(f"Message: {result['message']}")
    
    if result['violations']:
        print(f"\n⚠️  Critical Violations ({len(result['violations'])}):")
        for v in result['violations']:
            print(f"   - [{v['type']}] {v['details']} (Phase: {v['phase']}, -{v['deduction']} points)")
    
    # 退出條件
    exit_conditions = checker.get_exit_conditions()
    print(f"\n📋 Phase Exit Conditions:")
    print(f"   Allowed: {'✅ YES' if exit_conditions['allowed'] else '❌ NO'}")
    print(f"   Reason: {exit_conditions['reason']}")
    if exit_conditions['restrictions']:
        print(f"   Restrictions:")
        for r in exit_conditions['restrictions']:
            print(f"      - {r}")
    
    # JSON 輸出（如果需要）
    if "--json" in sys.argv:
        print("\n" + json.dumps(result, indent=2, ensure_ascii=False))
    
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()