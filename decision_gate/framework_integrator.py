#!/usr/bin/env python3
"""
DECISION_FRAMEWORK 整合器
確保決策有記錄且符合框架

使用方法：
    from decision_gate.framework_integrator import DecisionFrameworkIntegrator
    integrator = DecisionFrameworkIntegrator("/path/to/project")
    result = integrator.check_decisions_logged()
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path


class DecisionFrameworkIntegrator:
    """決策框架整合器"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.framework_file = self.project_root / "DECISION_FRAMEWORK.md"
        self.decisions_file = self.project_root / "DECISIONS.md"
        self.spec_tracking_file = self.project_root / "SPEC_TRACKING.md"
    
    def check_decisions_logged(self) -> bool:
        """檢查決策是否有記錄"""
        # 如果有 SPEC_TRACKING.md 但沒有 DECISIONS.md，可能是問題
        if self.spec_tracking_file.exists() and not self.decisions_file.exists():
            # 檢查是否有 SHOULD 被標記為不實現
            content = self.spec_tracking_file.read_text(encoding="utf-8")
            if "⚠️" in content or "❌" in content:
                return False
        return True
    
    def validate_format(self) -> bool:
        """驗證決策格式是否符合框架"""
        if not self.decisions_file.exists():
            return True  # 沒有決策檔案視為通過
        
        content = self.decisions_file.read_text(encoding="utf-8")
        
        # 檢查是否符合框架結構
        required_sections = [
            "Q1",  # 這是「要求」還是「建議」？
            "Q2",  # 這是「缺失」還是「可選」？
            "Q3"   # 偏差理由是否充分？
        ]
        
        for section in required_sections:
            if section not in content:
                return False
        
        return True
    
    def check_intent_classification(self) -> Dict:
        """檢查意圖分類是否正確套用"""
        if not self.spec_tracking_file.exists():
            return {
                "passed": True,
                "issues": []
            }
        
        content = self.spec_tracking_file.read_text(encoding="utf-8")
        issues = []
        
        # 檢查是否有 SHOULD 被錯誤標記為 MAY
        should_keywords = ["建議", "推薦", "可加入"]
        may_keywords = ["可以", "如需"]
        
        for line in content.split("\n"):
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 4:
                    description = parts[1].lower() if len(parts) > 1 else ""
                    status = parts[-1] if parts[-1] else ""
                    
                    # 檢查是否包含 SHOULD 關鍵詞但標記為 MAY
                    has_should = any(kw in description for kw in should_keywords)
                    has_may = any(kw in description for kw in may_keywords)
                    
                    if has_should and "❌" in status:
                        issues.append(f"可能錯誤分類: {parts[1][:50]}... 包含 '建議' 但標記為不實現")
        
        return {
            "passed": len(issues) == 0,
            "issues": issues
        }
    
    def validate_all(self) -> Dict:
        """執行所有驗證"""
        return {
            "decisions_logged": self.check_decisions_logged(),
            "format_valid": self.validate_format(),
            "intent_classification": self.check_intent_classification()
        }
    
    def run(self) -> bool:
        """執行決策框架整合檢查"""
        result = self.validate_all()
        
        all_passed = (
            result["decisions_logged"] and 
            result["format_valid"] and 
            result["intent_classification"]["passed"]
        )
        
        return all_passed
    
    def print_report(self):
        """打印決策框架報告"""
        result = self.validate_all()
        
        print("=" * 50)
        print("決策框架報告")
        print("=" * 50)
        
        if result["decisions_logged"]:
            print("✅ 決策記錄檢查: 通過")
        else:
            print("❌ 決策記錄檢查: 失敗")
            print("   發現 SHOULD 項目被標記為不實現但缺少 DECISIONS.md 記錄")
        
        if result["format_valid"]:
            print("✅ 決策格式驗證: 通過")
        else:
            print("❌ 決策格式驗證: 失敗")
            print("   缺少必要的 Q1/Q2/Q3 結構")
        
        if result["intent_classification"]["passed"]:
            print("✅ 意圖分類驗證: 通過")
        else:
            print("❌ 意圖分類驗證: 失敗")
            for issue in result["intent_classification"]["issues"]:
                print(f"   • {issue}")


def main():
    """命令行入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description="決策框架整合器")
    parser.add_argument("project_root", nargs="?", default=".",
                       help="專案根目錄 (預設: 目前目錄)")
    parser.add_argument("--json", action="store_true", help="JSON 輸出")
    
    args = parser.parse_args()
    
    integrator = DecisionFrameworkIntegrator(args.project_root)
    
    if not args.json:
        result = integrator.run()
        integrator.print_report()
        return 0 if result else 1
    else:
        result = integrator.validate_all()
        print(result)
        return 0 if integrator.run() else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
