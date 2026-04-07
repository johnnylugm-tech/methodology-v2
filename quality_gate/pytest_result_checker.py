#!/usr/bin/env python3
"""
Pytest Result Checker - Pytest 結果檢查器
=================================
驗證測試結果來自實際 pytest 輸出

使用方式：
    python3 quality_gate/pytest_result_checker.py --project-dir /path/to/project

Pass 條件：
    - P4-12: 測試結果有 pytest 實際輸出 = 必需
"""

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Dict, List
from pathlib import Path as PathLib


class PytestResultChecker:
    """Pytest 結果檢查器"""
    
    def __init__(self, project_path: str, verbose: bool = False):
        self.project_path = Path(project_path)
        self.verbose = verbose
    
    def run(self, project_path: str = None) -> Dict:
        if project_path:
            self.project_path = Path(project_path)
        return self.check()
    
    def check(self) -> Dict:
        pytest_output = self._find_pytest_output()
        test_results = self._parse_pytest_output(pytest_output)
        
        return {
            'passed': test_results['has_valid_output'],
            'has_pytest_output': pytest_output is not None,
            'total_tests': test_results['total'],
            'passed_tests': test_results['passed'],
            'failed_tests': test_results['failed'],
            'skipped_tests': test_results['skipped'],
            'output_source': test_results['source'],
            'details': test_results,
            'threshold': 'has_output',
            'phase_conditions': ['P4-12']
        }
    
    def _find_pytest_output(self) -> str:
        output_paths = [
            self.project_path / 'tests' / 'pytest_output.txt',
            self.project_path / 'pytest_output.txt',
            self.project_path / 'test' / 'pytest_output.txt',
            self.project_path / '.pytest_cache' / '.txt',
            self.project_path / 'pytest.log',
            self.project_path / 'test_results.json'
        ]
        
        for path in output_paths:
            if path.exists() and path.stat().st_size > 0:
                if self.verbose:
                    print(f"Found pytest output: {path}")
                return path.read_text(encoding='utf-8')
        
        test_dirs = [self.project_path / 'tests', self.project_path / 'test']
        
        for test_dir in test_dirs:
            if test_dir.exists():
                for txt_file in test_dir.rglob('*.txt'):
                    if txt_file.stat().st_size > 100:
                        content = txt_file.read_text(encoding='utf-8')
                        if 'passed' in content.lower() or 'failed' in content.lower():
                            if self.verbose:
                                print(f"Found pytest-like output: {txt_file}")
                            return content
        
        return None
    
    def _parse_pytest_output(self, content: str) -> Dict:
        if not content:
            return {'has_valid_output': False, 'total': 0, 'passed': 0, 'failed': 0, 'skipped': 0, 'source': 'none'}
        
        total = 0
        passed = 0
        failed = 0
        skipped = 0
        
        passed_match = re.search(r'(\d+)\s+passed', content, re.IGNORECASE)
        failed_match = re.search(r'(\d+)\s+failed', content, re.IGNORECASE)
        skipped_match = re.search(r'(\d+)\s+skipped', content, re.IGNORECASE)
        
        if passed_match:
            passed = int(passed_match.group(1))
            total += passed
        
        if failed_match:
            failed = int(failed_match.group(1))
            total += failed
        
        if skipped_match:
            skipped = int(skipped_match.group(1))
        
        if not total:
            total_match = re.search(r'(\d+)\s+test', content, re.IGNORECASE)
            if total_match:
                total = int(total_match.group(1))
        
        has_valid = (passed > 0 or failed > 0 or skipped > 0) and total > 0
        
        return {
            'has_valid_output': has_valid,
            'total': total,
            'passed': passed,
            'failed': failed,
            'skipped': skipped,
            'source': 'pytest' if 'pytest' in content.lower() else 'unknown'
        }

    def check_ai_generated_tests(self, test_dir: str = "tests/ai_generated") -> Dict:
        """
        檢查 AI 生成的測試檔案
        
        HR-17 合規檢查：
        1. 所有 AI 生成測試必須有 '# AI-GENERATED - REVIEW REQUIRED'
        2. 測試必須經過人工審查才能啟用（標記為 skip 或註解）
        """
        results = {"total": 0, "compliant": 0, "violations": []}
        
        test_path = PathLib(test_dir)
        if not test_path.exists():
            return results
        
        for test_file in test_path.rglob("test_*.py"):
            results["total"] += 1
            content = test_file.read_text(encoding="utf-8")
            
            if "AI-GENERATED" in content:
                # 檢查是否有 REVIEW REQUIRED 標記
                if "REVIEW REQUIRED" not in content:
                    results["violations"].append({
                        "file": str(test_file),
                        "issue": "Missing '# AI-GENERATED - REVIEW REQUIRED' marker"
                    })
                # 檢查是否被 skip 或註解（表示未審查）
                elif "# AI-GENERATED - REVIEW REQUIRED" in content and \
                     "pytest.mark.skip" not in content and \
                     "# skip" not in content.lower():
                    results["compliant"] += 1
            else:
                # 非 AI 生成，無需標記
                results["compliant"] += 1
        
        return results


def main():
    parser = argparse.ArgumentParser(description='Pytest 結果檢查器')
    parser.add_argument('--project-dir', type=str, default='.', help='專案目錄路徑')
    parser.add_argument('--output', type=str, default=None, help='輸出 JSON 檔案路徑')
    parser.add_argument('--verbose', action='store_true', help='顯示詳細輸出')
    args = parser.parse_args()
    
    checker = PytestResultChecker(args.project_dir, args.verbose)
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
