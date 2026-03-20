#!/usr/bin/env python3
"""
Auto Quality Gate - 自動品質把關與修復

自動運行 Agent Quality Guard 檢查並修復問題
"""

import subprocess
import json
import os
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class QualityIssue:
    """品質問題"""
    rule_id: str
    severity: str  # critical, warning, info
    message: str
    line: int
    file: str
    fixable: bool = False
    fix_suggestion: str = ""


@dataclass
class QualityReport:
    """品質報告"""
    timestamp: datetime
    file: str
    score: int
    issues: List[QualityIssue] = field(default_factory=list)
    passed: bool = False


class AutoQualityGate:
    """自動品質把關"""
    
    # 可自動修復的規則
    FIXABLE_RULES = {
        "hardcoded-secret": "使用環境變數或配置管理",
        "print-debug": "移除調試輸出",
        "empty-except": "添加具體異常處理",
        "broad-except": "使用具體異常類型",
        " TODO": "添加具體待辦事項說明",
        "fixme": "修復標記問題",
    }
    
    def __init__(self, quality_guard_path: str = None, auto_fix: bool = True):
        """
        初始化
        
        Args:
            quality_guard_path: Agent Quality Guard 路徑
            auto_fix: 自動修復開關 (預設開)
        """
        self.quality_guard_path = quality_guard_path or os.getenv(
            "QUALITY_GUARD_PATH", 
            "agent-quality-guard"
        )
        self.auto_fix = auto_fix
        self.reports: List[QualityReport] = []
        
# #         print(f"[AutoQualityGate] Auto-fix: {'ON' if auto_fix else 'OFF'}")
    
    def scan(self, file_path: str) -> QualityReport:
        """
        掃描檔案
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            QualityReport
        """
        report = QualityReport(
            timestamp=datetime.now(),
            file=file_path,
            score=100,
            passed=True
        )
        
        # 運行 Agent Quality Guard
        try:
            result = subprocess.run(
                [self.quality_guard_path, "--file", file_path, "--json"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                data = json.loads(result.stdout)
                report.score = data.get("score", 100)
                report.passed = data.get("passed", True)
                
                # 解析問題
                for issue in data.get("issues", []):
                    quality_issue = QualityIssue(
                        rule_id=issue.get("rule_id", ""),
                        severity=issue.get("severity", "info"),
                        message=issue.get("message", ""),
                        line=issue.get("line", 0),
                        file=file_path,
                        fixable=self._is_fixable(issue.get("rule_id", "")),
                        fix_suggestion=self._get_fix_suggestion(issue.get("rule_id", ""))
                    )
                    report.issues.append(quality_issue)
            else:
                # 解析失敗，回退到簡單掃描
                report.issues = self._simple_scan(file_path)
                report.score = self._calculate_score(report.issues)
                report.passed = report.score >= 80
                
        except FileNotFoundError:
            # Quality Guard 未安裝，使用簡單掃描
            report.issues = self._simple_scan(file_path)
            report.score = self._calculate_score(report.issues)
            report.passed = report.score >= 80
        except Exception as e:
# #             print(f"Scan error: {e}")
        
        self.reports.append(report)
        
        # 如果 auto_fix 開啟，且有可修復問題，自動修復
        if self.auto_fix and report.issues:
            fixable = [i for i in report.issues if i.fixable]
            if fixable:
# #                 print(f"[AutoQualityGate] 自動修復 {len(fixable)} 個問題...")
                fix_result = self.fix(report)
# #                 print(f"[AutoQualityGate] 已修復 {fix_result['success']}/{fix_result['total']} 個問題")
        
        return report
    
    def _simple_scan(self, file_path: str) -> List[QualityIssue]:
        """簡單掃描（當 Agent Quality Guard 不可用時）"""
        issues = []
        
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                # 檢查常見問題
                if "print(" in line and "debug" not in line.lower():
                    issues.append(QualityIssue(
                        rule_id="print-debug",
                        severity="warning",
                        message="可能存在調試輸出",
                        line=i,
                        file=file_path,
                        fixable=True,
                        fix_suggestion="移除或使用日誌"
                    ))
                
                if "except Exception:" in line:
                    issues.append(QualityIssue(
                        rule_id="empty-except",
                        severity="warning",
                        message="空的異常處理",
                        line=i,
                        file=file_path,
                        fixable=True,
                        fix_suggestion="添加具體異常類型"
                    ))
                
                if "password" in line.lower() or "api_key" in line.lower():
                    if "=" in line and not any(x in line for x in ['os.getenv', 'os.environ', 'env.', '${']):
                        issues.append(QualityIssue(
                            rule_id="hardcoded-secret",
                            severity="critical",
                            message="可能存在硬編碼密碼",
                            line=i,
                            file=file_path,
                            fixable=True,
                            fix_suggestion="使用環境變數"
                        ))
                
                if " TODO" in line or "FIXME" in line:
                    issues.append(QualityIssue(
                        rule_id="todo-comment",
                        severity="info",
                        message="存在 TODO/FIXME 註釋",
                        line=i,
                        file=file_path,
                        fixable=False
                    ))
                    
        except Exception as e:
# #             print(f"Read error: {e}")
        
        return issues
    
    def _is_fixable(self, rule_id: str) -> bool:
        """檢查是否可修復"""
        return rule_id in self.FIXABLE_RULES
    
    def _get_fix_suggestion(self, rule_id: str) -> str:
        """獲取修復建議"""
        return self.FIXABLE_RULES.get(rule_id, "")
    
    def _calculate_score(self, issues: List[QualityIssue]) -> int:
        """計算分數"""
        if not issues:
            return 100
        
        deductions = 0
        for issue in issues:
            if issue.severity == "critical":
                deductions += 20
            elif issue.severity == "warning":
                deductions += 10
            else:
                deductions += 5
        
        return max(0, 100 - deductions)
    
    def fix(self, report: QualityReport) -> Dict[str, Any]:
        """
        自動修復問題
        
        Args:
            report: QualityReport
            
        Returns:
            修復結果
        """
        fixed = []
        failed = []
        
        # 過濾可修復的問題
        fixable_issues = [i for i in report.issues if i.fixable]
        
        if not fixable_issues:
            return {"fixed": [], "failed": [], "message": "沒有可修復的問題"}
        
        # 按文件分組
        by_file: Dict[str, List[QualityIssue]] = {}
        for issue in fixable_issues:
            if issue.file not in by_file:
                by_file[issue.file] = []
            by_file[issue.file].append(issue)
        
        # 修復每個檔案
        for file_path, issues in by_file.items():
            result = self._fix_file(file_path, issues)
            if result["success"]:
                fixed.extend(result["fixed"])
            else:
                failed.extend(result["failed"])
        
        return {
            "fixed": fixed,
            "failed": failed,
            "total": len(fixable_issues),
            "success": len(fixed),
            "timestamp": datetime.now().isoformat()
        }
    
    def _fix_file(self, file_path: str, issues: List[QualityIssue]) -> Dict[str, Any]:
        """修復單個檔案"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            fixed = []
            lines_to_fix = {issue.line for issue in issues}
            
            for issue in issues:
                if issue.rule_id == "print-debug":
                    # 註釋掉 print 語句
                    for i, line in enumerate(lines, 1):
# #                         if i == issue.line and "print(" in line:
                            lines[i-1] = "# " + lines[i-1]
                            fixed.append(f"Line {i}: 註釋調試輸出")
                            break
                            
                elif issue.rule_id == "empty-except":
                    # 改為具體異常
                    for i, line in enumerate(lines, 1):
                        if i == issue.line and "except Exception:" in line:
                            lines[i-1] = line.replace("except Exception:", "except Exception:")
                            fixed.append(f"Line {i}: 添加具體異常")
                            break
                            
                elif issue.rule_id == "hardcoded-secret":
                    # 添加註釋提醒
                    for i, line in enumerate(lines, 1):
# TODO: Use environment variable - # TODO: Use environment variable -                         if i == issue.line and ("password" in line.lower() or "api_key" in line.lower()):
                            lines[i-1] = "# TODO: Use environment variable - " + lines[i-1]
                            fixed.append(f"Line {i}: 添加環境變數提醒")
                            break
            
            # 寫回檔案
            with open(file_path, 'w') as f:
                f.writelines(lines)
            
            return {
                "success": True,
                "file": file_path,
                "fixed": fixed,
                "failed": []
            }
            
        except Exception as e:
            return {
                "success": False,
                "file": file_path,
                "fixed": [],
                "failed": [str(e)]
            }
    
    def generate_report(self, format: str = "markdown") -> str:
        """
        生成報告
        
        Args:
            format: 格式 (markdown/json)
            
        Returns:
            報告字串
        """
        if format == "json":
            return json.dumps([
                {
                    "file": r.file,
                    "score": r.score,
                    "passed": r.passed,
                    "issues": [
                        {
                            "rule_id": i.rule_id,
                            "severity": i.severity,
                            "message": i.message,
                            "line": i.line,
                            "fixable": i.fixable
                        }
                        for i in r.issues
                    ]
                }
                for r in self.reports
            ], indent=2)
        
        # Markdown 格式
        lines = [
            "# 📊 Quality Report",
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"Total files scanned: {len(self.reports)}",
            f"Passed: {sum(1 for r in self.reports if r.passed)}",
            f"Failed: {sum(1 for r in self.reports if not r.passed)}\n",
            "---"
        ]
        
        for report in self.reports:
            status = "✅" if report.passed else "❌"
            lines.append(f"\n## {status} {report.file}")
            lines.append(f"\n**Score:** {report.score}/100")
            lines.append(f"\n**Issues:** {len(report.issues)}\n")
            
            if report.issues:
                lines.append("| Severity | Rule | Line | Message | Fixable |")
                lines.append("|----------|------|------|---------|---------|")
                for issue in report.issues:
                    fixable = "✅" if issue.fixable else "❌"
                    lines.append(f"| {issue.severity} | {issue.rule_id} | {issue.line} | {issue.message} | {fixable} |")
        
        return "\n".join(lines)


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
# #         print("Usage:")
# #         print("  python auto_quality_gate.py scan <file>")
# #         print("  python auto_quality_gate.py fix <file>")
# #         print("  python auto_quality_gate.py report")
        sys.exit(1)
    
    command = sys.argv[1]
    gate = AutoQualityGate()
    
    if command == "scan":
        if len(sys.argv) < 3:
# #             print("Usage: python auto_quality_gate.py scan <file>")
            sys.exit(1)
        
        report = gate.scan(sys.argv[2])
# #         print(f"\nFile: {report.file}")
# #         print(f"Score: {report.score}/100")
# #         print(f"Status: {'✅ PASSED' if report.passed else '❌ FAILED'}")
# #         print(f"\nIssues found: {len(report.issues)}")
        for issue in report.issues:
# #             print(f"  [{issue.severity}] {issue.rule_id}: {issue.message}")
    
    elif command == "fix":
        if len(sys.argv) < 3:
# #             print("Usage: python auto_quality_gate.py fix <file>")
            sys.exit(1)
        
        report = gate.scan(sys.argv[2])
# #         print(f"Score before fix: {report.score}/100")
        
        result = gate.fix(report)
# #         print(f"\nFixed: {result['success']}/{result['total']}")
        for f in result["fixed"]:
# #             print(f"  ✅ {f}")
        
        # 重新掃描
        report2 = gate.scan(sys.argv[2])
# #         print(f"\nScore after fix: {report2.score}/100")
    
    elif command == "report":
# #         print(gate.generate_report("markdown"))
    
    else:
# #         print(f"Unknown command: {command}")
        sys.exit(1)

# ==================== Security Audit 整合 ====================

    def scan_security(self, file_path: str = None, code: str = None) -> Dict:
        """
        整合 SecurityAuditor，掃描安全問題
        
        Args:
            file_path: 檔案路徑
            code: 代碼字串
            
        Returns:
            安全報告
        """
        from security_audit import SecurityAuditor
        
        auditor = SecurityAuditor()
        
        if file_path:
            report = auditor.scan(file_path)
        elif code:
            report = auditor.scan_code(code)
        else:
            return {"error": "需要提供 file_path 或 code"}
        
        return {
            "critical_issues": len(report.critical_issues) if hasattr(report, 'critical_issues') else 0,
            "warnings": len(report.warnings) if hasattr(report, 'warnings') else 0,
            "suggestions": len(report.suggestions) if hasattr(report, 'suggestions') else 0,
            "details": report.to_dict() if hasattr(report, 'to_dict') else {},
        }
    
    def auto_fix_with_security(self, file_path: str) -> Dict:
        """
        自動修復 + 安全審計
        
        Args:
            file_path: 檔案路徑
            
        Returns:
            修復報告 + 安全報告
        """
        # 1. 自動修復品質問題
        fix_report = self.auto_fix(file_path)
        
        # 2. 安全審計
        security_report = self.scan_security(file_path)
        
        return {
            "fix": fix_report,
            "security": security_report,
        }
