#!/usr/bin/env python3
"""
Issue Tracker - 問題追蹤自動化工具
=============================
自動追蹤測試失敗、風險識別的問題

使用方式：
    python3 quality_gate/issue_tracker.py --project-dir /path/to/project
    python3 quality_gate/issue_tracker.py --project-dir . --output issues.json

輸出：
    JSON 問題狀態報告
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime


class IssueTracker:
    """問題追蹤器"""
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.issues: List[Dict] = []
    
    def track(self) -> Dict:
        """執行問題追蹤"""
        # 1. 追蹤測試失敗
        self._track_test_failures()
        
        # 2. 追蹤 linter 問題
        self._track_linter_issues()
        
        # 3. 追蹤静态分析問題
        self._track_static_issues()
        
        # 4. 追蹤未關閉的 TODO
        self._track_todos()
        
        # 5. 計算統計
        open_issues = len([i for i in self.issues if i.get('status') == 'open'])
        critical = len([i for i in self.issues if i.get('severity') == 'CRITICAL'])
        
        return {
            'passed': critical == 0 and open_issues == 0,
            'total_issues': len(self.issues),
            'open_issues': open_issues,
            'closed_issues': len(self.issues) - open_issues,
            'critical': critical,
            'details': self.issues,
            'timestamp': datetime.now().isoformat()
        }
    
    def _track_test_failures(self):
        """追蹤測試失敗"""
        try:
            result = subprocess.run(
                ['pytest', '-v', '--tb=short'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                output = result.stdout + result.stderr
                lines = output.split('\n')
                
                for i, line in enumerate(lines):
                    if 'FAILED' in line or 'ERROR' in line:
                        self.issues.append({
                            'id': f'TEST-{len(self.issues) + 1}',
                            'type': 'test_failure',
                            'severity': 'HIGH',
                            'status': 'open',
                            'source': 'pytest',
                            'description': line.strip(),
                            'line': i + 1
                        })
        except Exception:
            pass
    
    def _track_linter_issues(self):
        """追蹤 linter 問題"""
        # 嘗試使用 flake8
        try:
            result = subprocess.run(
                ['flake8', '--select=E9,F63,F7,F82', '--show-source', '--statistics'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                output = result.stdout
                lines = output.split('\n')
                
                for line in lines:
                    if line.strip():
                        parts = line.split(':')
                        if len(parts) >= 3:
                            self.issues.append({
                                'id': f'LINT-{len(self.issues) + 1}',
                                'type': 'linter',
                                'severity': 'MEDIUM',
                                'status': 'open',
                                'source': 'flake8',
                                'file': parts[0],
                                'line': parts[1] if len(parts) > 1 else '',
                                'description': ':'.join(parts[2:]).strip()
                            })
        except Exception:
            pass
    
    def _track_static_issues(self):
        """追蹤靜態分析問題"""
        src_dir = self.project_path / 'src'
        if not src_dir.exists():
            src_dir = self.project_path
        
        # 掃描所有 Python 文件
        for py_file in src_dir.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')
            except Exception:
                continue
            
            # 檢查常見問題
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                # 檢查 bare except
                if 'except:' in line and 'except ' not in line:
                    self.issues.append({
                        'id': f'STATIC-{len(self.issues) + 1}',
                        'type': 'static_analysis',
                        'severity': 'MEDIUM',
                        'status': 'open',
                        'source': 'code_review',
                        'file': str(py_file.relative_to(self.project_path)),
                        'line': i + 1,
                        'description': 'Bare except clause (使用 Exception 具體類型)'
                    })
                
                # 檢查 hardcoded credentials
                if 'password' in line.lower() and '=' in line:
                    if 'os.getenv' not in line and 'os.environ' not in line:
                        if not line.strip().startswith('#'):
                            self.issues.append({
                                'id': f'STATIC-{len(self.issues) + 1}',
                                'type': 'security',
                                'severity': 'HIGH',
                                'status': 'open',
                                'source': 'code_review',
                                'file': str(py_file.relative_to(self.project_path)),
                                'line': i + 1,
                                'description': '可能包含硬編碼密碼'
                            })
    
    def _track_todos(self):
        """追蹤未關閉的 TODO"""
        src_dir = self.project_path / 'src'
        if not src_dir.exists():
            src_dir = self.project_path
        
        for py_file in src_dir.rglob('*.py'):
            try:
                content = py_file.read_text(encoding='utf-8')
            except Exception:
                continue
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines):
                if 'TODO' in line.upper() or 'FIXME' in line.upper() or 'XXX' in line.upper():
                    self.issues.append({
                        'id': f'TODO-{len(self.issues) + 1}',
                        'type': 'todo',
                        'severity': 'LOW',
                        'status': 'open',
                        'source': 'code_review',
                        'file': str(py_file.relative_to(self.project_path)),
                        'line': i + 1,
                        'description': line.strip()
                    })


def main():
    """主函數"""
    parser = argparse.ArgumentParser(
        description='問題追蹤自動化工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
範例：
  python3 quality_gate/issue_tracker.py
  python3 quality_gate/issue_tracker.py --project-dir /path/to/project
  python3 quality_gate/issue_tracker.py --project-dir . --output issues.json
        '''
    )
    
    parser.add_argument(
        '--project-dir',
        type=str,
        default='.',
        help='專案目錄路徑（預設：當前目錄）'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='輸出 JSON 檔案路徑（可選）'
    )
    
    parser.add_argument(
        '--phase',
        type=str,
        default=None,
        help='Phase 編號（用於 unified_gate 整合）'
    )
    
    args = parser.parse_args()
    
    # 執行問題追蹤
    tracker = IssueTracker(args.project_dir)
    result = tracker.track()
    
    # 輸出結果
    json_output = json.dumps(result, indent=2, ensure_ascii=False)
    
    if args.output:
        # 寫入檔案
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_output, encoding='utf-8')
        print(f'Report saved to: {args.output}')
    else:
        # 輸出到 stdout
        print(json_output)
    
    # 返回狀態碼
    sys.exit(0 if result['passed'] else 1)


if __name__ == '__main__':
    main()