#!/usr/bin/env python3
"""
Spec Logic Checker - 邏輯正確性自動化檢查
==========================================
自動檢查程式碼的「邏輯正確性」，彌補 Quality Gate 盲點

功能：
1. 檢查輸出是否多於輸入（字串操作）
2. 檢查分支是否一致（單一 vs 多）
3. 檢查是否 lazy check（外部依賴初始化）

使用方法：
    python scripts/spec_logic_checker.py /path/to/project
    python scripts/spec_logic_checker.py /path/to/project --fix
"""

import os
import re
import sys
import argparse
from pathlib import Path
from typing import List, Dict, Tuple
from dataclasses import dataclass, field


@dataclass
class LogicIssue:
    """邏輯問題"""
    file_path: str
    function_name: str
    line_number: int
    issue_type: str
    description: str
    severity: str = "HIGH"  # HIGH, MEDIUM, LOW


@dataclass
class SpecLogicCheckResult:
    """檢查結果"""
    passed: bool
    score: float
    issues: List[LogicIssue] = field(default_factory=list)
    files_checked: int = 0
    functions_checked: int = 0


class SpecLogicChecker:
    """邏輯正確性檢查器"""
    
    # 檢測模式
    PATTERNS = {
        "string_insertion": [
            (r'\+\s*["\'][\。？！\s]', "可能插入額外字符（標點/空格）"),
            (r'\+\s*"\.join\(', "可能插入多餘字符"),
        ],
        "branch_inconsistency": [
            (r'if\s+len\([^)]+\)\s*==\s*1\s*:', "單一情况特殊處理，需確認與多情况一致"),
            (r'if\s+len\([^)]+\)\s*==\s*0\s*:', "空情況特殊處理"),
        ],
        "non_lazy_init": [
            (r'def\s+__init__.*ffmpeg\.', "__init__ 直接呼叫 ffmpeg，應用 lazy check"),
            (r'def\s+__init__.*requests\.', "__init__ 直接呼叫 requests，應用 lazy check"),
            (r'def\s+__init__.*import\s+ffmpeg', "__init__ 直接 import ffmpeg，應用 lazy check"),
        ],
    }
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.issues: List[LogicIssue] = []
    
    def scan_python_files(self) -> SpecLogicCheckResult:
        """掃描所有 Python 檔案"""
        python_files = list(self.project_path.rglob("*.py"))
        
        # 排除測試和虛擬環境
        python_files = [
            f for f in python_files
            if "test" not in f.name.lower()
            and "venv" not in str(f)
            and "__pycache__" not in str(f)
        ]
        
        files_checked = 0
        functions_checked = 0
        
        for py_file in python_files:
            files_checked += 1
            try:
                content = py_file.read_text(encoding="utf-8")
                file_issues = self._check_file(content, str(py_file))
                self.issues.extend(file_issues)
                functions_checked += len(re.findall(r'def\s+\w+', content))
            except Exception as e:
                # 跳過無法讀取的檔案
                pass
        
        # 計算分數
        score = self._calculate_score(len(self.issues), functions_checked)
        
        return SpecLogicCheckResult(
            passed=score >= 80,  # 80 分及格
            score=score,
            issues=self.issues,
            files_checked=files_checked,
            functions_checked=functions_checked
        )
    
    def _check_file(self, content: str, file_path: str) -> List[LogicIssue]:
        """檢查單一檔案"""
        issues = []
        lines = content.split('\n')
        
        for i, line in enumerate(lines, 1):
            # 跳过注释
            if line.strip().startswith('#'):
                continue
            
            # 檢查字串插入
            for pattern, desc in self.PATTERNS["string_insertion"]:
                if re.search(pattern, line):
                    issues.append(LogicIssue(
                        file_path=file_path,
                        function_name=self._get_function_name(lines, i),
                        line_number=i,
                        issue_type="string_insertion",
                        description=desc,
                        severity="HIGH"
                    ))
            
            # 檢查分支不一致
            for pattern, desc in self.PATTERNS["branch_inconsistency"]:
                if re.search(pattern, line):
                    issues.append(LogicIssue(
                        file_path=file_path,
                        function_name=self._get_function_name(lines, i),
                        line_number=i,
                        issue_type="branch_inconsistency",
                        description=desc,
                        severity="MEDIUM"
                    ))
            
            # 檢查非 lazy init
            for pattern, desc in self.PATTERNS["non_lazy_init"]:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(LogicIssue(
                        file_path=file_path,
                        function_name=self._get_function_name(lines, i),
                        line_number=i,
                        issue_type="non_lazy_init",
                        description=desc,
                        severity="HIGH"
                    ))
        
        return issues
    
    def _get_function_name(self, lines: List[str], current_line: int) -> str:
        """取得當前函數名稱"""
        for i in range(current_line - 1, -1, -1):
            match = re.match(r'def\s+(\w+)', lines[i])
            if match:
                return match.group(1)
        return "unknown"
    
    def _calculate_score(self, issue_count: int, function_count: int) -> float:
        """計算分數"""
        if function_count == 0:
            return 100
        
        # 每個嚴重問題扣 10 分，中等扣 5 分
        high_issues = sum(1 for i in self.issues if i.severity == "HIGH")
        medium_issues = sum(1 for i in self.issues if i.severity == "MEDIUM")
        
        deduction = high_issues * 10 + medium_issues * 5
        score = max(0, 100 - deduction)
        
        return score
    
    def print_report(self, result: SpecLogicCheckResult):
        """印出報告"""
        print("\n" + "="*60)
        print("Spec Logic Checker 報告")
        print("="*60)
        
        print(f"\n📊 統計")
        print(f"   檔案數: {result.files_checked}")
        print(f"   函數數: {result.functions_checked}")
        print(f"   問題數: {len(result.issues)}")
        print(f"   分數: {result.score}/100")
        
        print(f"\n✅ 結果: {'PASS' if result.passed else 'FAIL'}")
        
        if result.issues:
            print(f"\n🚨 問題清單")
            for issue in result.issues:
                print(f"\n   [{issue.severity}] {issue.file_path}:{issue.line_number}")
                print(f"   函數: {issue.function_name}")
                print(f"   類型: {issue.issue_type}")
                print(f"   說明: {issue.description}")
        
        print("\n" + "="*60)


def main():
    parser = argparse.ArgumentParser(description="Spec Logic Checker")
    parser.add_argument("project_path", help="專案路徑")
    parser.add_argument("--fix", action="store_true", help="自動修復（尚未實作）")
    args = parser.parse_args()
    
    if not os.path.exists(args.project_path):
        print(f"錯誤：路徑不存在: {args.project_path}")
        sys.exit(1)
    
    checker = SpecLogicChecker(args.project_path)
    result = checker.scan_python_files()
    checker.print_report(result)
    
    # 退出碼
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()