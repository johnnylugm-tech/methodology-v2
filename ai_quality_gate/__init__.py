#!/usr/bin/env python3
"""
AI Quality Gate - methodology-v2 模組
=====================================
方案 A: AI Quality Gate Sub-agent

功能:
- 自動 Code Review
- 檢測 debug statements
- 檢測 hardcoded secrets
- AI 審查
"""

import os
import re
import logging
from typing import Dict, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AIQualityGate:
    """AI Quality Gate - Claude Code sub-agent 審查"""
    
    def __init__(self):
        self.issues = []
        self.score = 0
        logger.info("AIQualityGate initialized")
    
    def scan_file(self, filepath: str) -> Dict:
        """掃描單一檔案"""
        issues = []
        
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                lines = content.split('\n')
            
            # 檢測 debug statements
            debug_patterns = [r'print\(', r'console\.log', r'debugger', r'# TODO', r'# FIXME']
            
            for i, line in enumerate(lines, 1):
                for pattern in debug_patterns:
                    if re.search(pattern, line):
                        issues.append({'file': filepath, 'line': i, 'type': 'debug', 'content': line.strip()[:50]})
            
            # 檢測 hardcoded secrets
            secret_patterns = [
                r'password\s*=\s*["\'][^"\']+["\']',
                r'api[_-]?key\s*=\s*["\'][^"\']+["\']',
                r'secret\s*=\s*["\'][^"\']+["\']',
                r'token\s*=\s*["\'][^"\']+["\']',
            ]
            
            for i, line in enumerate(lines, 1):
                for pattern in secret_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        issues.append({'file': filepath, 'line': i, 'type': 'security', 'content': line.strip()[:50]})
                        
        except Exception as e:
            logger.error(f"Error scanning {filepath}: {e}")
        
        return {'file': filepath, 'issues': issues, 'issue_count': len(issues)}
    
    def scan_directory(self, directory: str, extensions: List[str] = ['.py']) -> Dict:
        """掃描目錄"""
        total_issues = []
        files_scanned = 0
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git', 'node_modules']]
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    filepath = os.path.join(root, file)
                    result = self.scan_file(filepath)
                    total_issues.extend(result['issues'])
                    files_scanned += 1
        
        total_weight = sum(
            {'debug': 1, 'security': 5, 'todo': 2}.get(i['type'], 1) 
            for i in total_issues
        )
        
        self.score = max(0, 100 - total_weight)
        
        return {
            'files_scanned': files_scanned,
            'total_issues': len(total_issues),
            'issues': total_issues,
            'score': self.score,
            'pass': self.score >= 90
        }


def run_quality_gate(directory: str) -> bool:
    """運行 Quality Gate"""
    gate = AIQualityGate()
    result = gate.scan_directory(directory)
    logger.info(f"Quality Score: {result['score']}")
    return result['pass']


if __name__ == "__main__":
    import sys
    directory = sys.argv[1] if len(sys.argv) > 1 else "src"
    success = run_quality_gate(directory)
    sys.exit(0 if success else 1)
