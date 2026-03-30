#!/usr/bin/env python3
"""
Root Cause Checker - 根本原因分析檢查器
=================================
檢查失敗案例是否有具體代碼行數分析

使用方式：
    python3 quality_gate/root_cause_checker.py --project-dir /path/to/project

Pass 條件：
    - P4-11: 失敗案例根本原因分析 = 必需
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List


class RootCauseChecker:
    """根本原因分析檢查器"""
    
    def __init__(self, project_path: str, verbose: bool = False):
        self.project_path = Path(project_path)
        self.verbose = verbose
    
    def run(self, project_path: str = None) -> Dict:
        if project_path:
            self.project_path = Path(project_path)
        return self.check()
    
    def check(self) -> Dict:
        issues = self._extract_issues()
        root_cause_analysis = self._check_root_cause_analysis(issues)
        
        return {
            'passed': root_cause_analysis['has_rca'],
            'total_issues': len(issues),
            'issues_with_rca': root_cause_analysis['issues_with_rca'],
            'issues_without_rca': root_cause_analysis['issues_without_rca'],
            'details': root_cause_analysis['details'],
            'threshold': 'has_line_number',
            'phase_conditions': ['P4-11']
        }
    
    def _extract_issues(self) -> List[Dict]:
        issues = []
        
        issue_paths = [
            self.project_path / 'docs' / 'ISSUES.md',
            self.project_path / 'ISSUES.md',
            self.project_path / 'issues.md',
            self.project_path / 'docs' / 'issue_tracker.md',
            self.project_path / '.github' / 'ISSUES.md'
        ]
        
        for issue_path in issue_paths:
            if not issue_path.exists():
                continue
            
            content = issue_path.read_text(encoding='utf-8')
            
            issue_patterns = [
                r'###\s+(\d+)\s+[:\-](.+?)(?=###|\Z)',
                r'##\s+(?:Issue|Bug|Failure)\s+(\d+)',
                r'^\s*-\s+\[ \]\s+(.+?)(?:\n|$)',
                r'#\s+(?:Failure|Case)\s+(\d+)'
            ]
            
            for pattern in issue_patterns:
                matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
                for match in matches:
                    issues.append({'source': str(issue_path), 'title': match[0] if isinstance(match, tuple) else match})
            
            if issues:
                break
        
        if self.verbose:
            print(f"Found {len(issues)} issues")
        
        return issues
    
    def _check_root_cause_analysis(self, issues: List[Dict]) -> Dict:
        details = []
        issues_with_rca = []
        issues_without_rca = []
        
        for issue in issues:
            title = issue.get('title', '')
            source = issue.get('source', '')
            
            has_rca = False
            has_line_number = False
            has_code_context = False
            
            if source:
                content = Path(source).read_text(encoding='utf-8') if Path(source).exists() else ''
            else:
                content = ''
            
            rca_keywords = ['root cause', '根本原因', 'rca', 'cause', 'reason', 'because', '由於']
            has_rca = any(kw in title.lower() for kw in rca_keywords) or any(kw in content.lower() for kw in rca_keywords)
            
            line_patterns = [r'line\s+(\d+)', r':(\d+):', r'L(\d+)', r'行(\d+)']
            has_line_number = any(re.search(p, title) or re.search(p, content) for p in line_patterns)
            
            code_patterns = [r'```[\s\S]*?```', r'`[^`]+`', r'def\s+\w+\(', r'class\s+\w+']
            has_code_context = any(re.search(p, content) for p in code_patterns)
            
            if has_rca and has_line_number:
                issues_with_rca.append(title)
            else:
                issues_without_rca.append(title)
            
            details.append({
                'issue': title,
                'has_rca': has_rca,
                'has_line_number': has_line_number,
                'has_code_context': has_code_context
            })
        
        has_rca = len(issues) == 0 or (len(issues_with_rca) == len(issues) and len(issues) > 0)
        
        return {
            'has_rca': has_rca,
            'issues_with_rca': issues_with_rca,
            'issues_without_rca': issues_without_rca,
            'details': details
        }


def main():
    parser = argparse.ArgumentParser(description='根本原因分析檢查器')
    parser.add_argument('--project-dir', type=str, default='.', help='專案目錄路徑')
    parser.add_argument('--output', type=str, default=None, help='輸出 JSON 檔案路徑')
    parser.add_argument('--verbose', action='store_true', help='顯示詳細輸出')
    args = parser.parse_args()
    
    checker = RootCauseChecker(args.project_path, args.verbose)
    result = checker.check()
    
    json_output = json.dumps(result, indent=2, ensure_ascii=False)
    
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json_output, encoding='utf-8')
        print(f"Report saved to: {args.output}")
    else:
        print(json_output)
    
    sys.exit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()
