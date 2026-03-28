#!/usr/bin/env python3
"""
Spec Logic Checker - 邏輯正確性自動化檢查
==========================================
自動檢查程式碼的「邏輯正確性」，彌補 Quality Gate 盲點

功能：
1. 檢查輸出是否多於輸入（字串操作）
2. 檢查分支是否一致（單一 vs 多）
3. 檢查是否 lazy check（外部依賴初始化）
4. 語意驗證（對照 SRS）

使用方法：
    python scripts/spec_logic_checker.py /path/to/project
    python scripts/spec_logic_checker.py /path/to/project --srs /path/to/SRS.md
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
            except Exception:
                pass
        
        # 計算分數
        score = self._calculate_score(len(self.issues), functions_checked)
        
        return SpecLogicCheckResult(
            passed=score >= 80,
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
            if line.strip().startswith('#'):
                continue
            
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
        for i in range(current_line - 1, -1, -1):
            match = re.match(r'def\s+(\w+)', lines[i])
            if match:
                return match.group(1)
        return "unknown"
    
    def _calculate_score(self, issue_count: int, function_count: int) -> float:
        if function_count == 0:
            return 100
        
        high_issues = sum(1 for i in self.issues if i.severity == "HIGH")
        medium_issues = sum(1 for i in self.issues if i.severity == "MEDIUM")
        
        deduction = high_issues * 10 + medium_issues * 5
        score = max(0, 100 - deduction)
        
        return score
    
    def print_report(self, result: SpecLogicCheckResult):
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


class SemanticValidator:
    """語意驗證器 - 對照 SRS 驗證邏輯正確性"""
    
    def __init__(self, srs_path: str):
        self.srs_path = srs_path
        self.requirements = self._parse_srs()
    
    def _parse_srs(self) -> Dict[str, str]:
        requirements = {}
        
        try:
            content = Path(self.srs_path).read_text(encoding="utf-8")
            
            for match in re.finditer(r'\|\s*FR-(\d+)\s*\|([^\n|]+)', content):
                fr_id = f"FR-{match.group(1)}"
                description = match.group(2).strip()
                
                verification = self._infer_verification(description)
                requirements[fr_id] = {
                    "description": description,
                    "verification": verification
                }
        except Exception as e:
            print(f"警告：無法解析 SRS: {e}")
        
        return requirements
    
    def _infer_verification(self, description: str) -> str:
        desc = description.lower()
        
        if "分段" in desc and "字" in desc:
            return "輸出長度 <= 輸入長度"
        elif "合併" in desc:
            return "單一檔案格式 = 多檔案格式"
        elif "保留" in desc or "標點" in desc:
            return "輸出不插入額外字符"
        elif "重試" in desc:
            return "L1-L2 可重試，L3-L4 不可重試"
        elif "熔斷" in desc:
            return "連續失敗觸發熔斷"
        elif "timeout" in desc:
            return "超時拋出 TimeoutError"
        else:
            return "需人工驗證"
    
    def verify(self, code: str, fr_id: str) -> Tuple[bool, str]:
        if fr_id not in self.requirements:
            return True, f"未找到 {fr_id} 需求"
        
        requirement = self.requirements[fr_id]
        verification = requirement["verification"]
        
        if verification == "輸出長度 <= 輸入長度":
            if re.search(r'\+\s*["\'][\。？！\s]', code):
                return False, f"{fr_id} 可能插入額外字符"
        
        elif verification == "單一檔案格式 = 多檔案格式":
            if re.search(r'if\s+len\([^)]+\)\s*==\s*1\s*:', code):
                return True, f"{fr_id} 有特殊處理，需確認一致性"
        
        return True, "邏輯符合 SRS"


def main():
    parser = argparse.ArgumentParser(description="Spec Logic Checker")
    parser.add_argument("project_path", help="專案路徑")
    parser.add_argument("--srs", help="SRS.md 路徑，用於語意驗證")
    args = parser.parse_args()
    
    if not os.path.exists(args.project_path):
        print(f"錯誤：路徑不存在: {args.project_path}")
        sys.exit(1)
    
    checker = SpecLogicChecker(args.project_path)
    result = checker.scan_python_files()
    checker.print_report(result)
    
    # 語意驗證（可選）
    if args.srs and os.path.exists(args.srs):
        print("\n" + "="*60)
        print("語意驗證報告")
        print("="*60)
        validator = SemanticValidator(args.srs)
        print(f"\n📋 SRS 需求對照")
        print(f"   總需求數: {len(validator.requirements)}")
        
        for fr_id, req in list(validator.requirements.items())[:5]:
            print(f"\n   {fr_id}: {req['description'][:40]}...")
            print(f"   驗證方法: {req['verification']}")
        
        if len(validator.requirements) > 5:
            print(f"\n   ... 還有 {len(validator.requirements) - 5} 個需求")
    
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()