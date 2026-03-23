#!/usr/bin/env python3
"""
Security Scanner - methodology-v2 模組
=========================================
方案 D: 自動化安全掃描

功能:
- SAST 靜態分析
- Dependency 檢查
- 漏洞檢測
"""

import os
import re
import logging
from typing import Dict, List
from dataclasses import dataclass

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Vulnerability:
    severity: str
    type: str
    file: str
    line: int
    description: str


class SecurityScanner:
    """安全掃描器"""
    
    VULNERABILITY_PATTERNS = {
        'sql_injection': {
            'pattern': r'(execute|query|cursor)\([^)]*["\']',
            'severity': 'critical', 'cwe': 'CWE-89'
        },
        'command_injection': {
            'pattern': r'(os\.system|subprocess|eval|exec)\(',
            'severity': 'critical', 'cwe': 'CWE-78'
        },
        'hardcoded_secret': {
            'pattern': r'(password|api_key|secret|token)\s*=\s*["\'][^"\']{8,}["\']',
            'severity': 'high', 'cwe': 'CWE-798'
        },
        'weak_crypto': {
            'pattern': r'(md5|sha1|base64)\s*\(',
            'severity': 'medium', 'cwe': 'CWE-327'
        },
    }
    
    def __init__(self):
        self.score = 100
    
    def scan_file(self, filepath: str) -> List[Vulnerability]:
        vulns = []
        try:
            with open(filepath, 'r') as f:
                lines = f.read().split('\n')
            
            for vuln_type, config in self.VULNERABILITY_PATTERNS.items():
                for i, line in enumerate(lines, 1):
                    if re.search(config['pattern'], line, re.IGNORECASE):
                        vulns.append(Vulnerability(
                            severity=config['severity'],
                            type=vuln_type,
                            file=filepath,
                            line=i,
                            description=f"{vuln_type} - {config['cwe']}"
                        ))
        except Exception as e:
            logger.error(f"Error: {e}")
        return vulns
    
    def scan_directory(self, directory: str) -> Dict:
        all_vulns = []
        files_scanned = 0
        
        for root, dirs, files in os.walk(directory):
            dirs[:] = [d for d in dirs if d not in ['__pycache__', '.git']]
            for file in files:
                if file.endswith('.py'):
                    vulns = self.scan_file(os.path.join(root, file))
                    all_vulns.extend(vulns)
                    files_scanned += 1
        
        weights = {'critical': 20, 'high': 10, 'medium': 5, 'low': 2}
        total_weight = sum(weights.get(v.severity, 5) for v in all_vulns)
        self.score = max(0, 100 - total_weight)
        
        return {
            'files_scanned': files_scanned,
            'vuln_count': len(all_vulns),
            'critical': len([v for v in all_vulns if v.severity == 'critical']),
            'score': self.score,
            'pass': self.score >= 95
        }
    
    def check_dependencies(self, req_file: str = "requirements.txt") -> Dict:
        vulnerable = []
        known = {'requests': '<2.20.0', 'django': '<3.2.0', 'flask': '<1.1.0'}
        
        if os.path.exists(req_file):
            with open(req_file, 'r') as f:
                for line in f:
                    pkg = line.strip().split('>=')[0].split('==')[0]
                    if pkg in known:
                        vulnerable.append({'package': pkg, 'vulnerable': known[pkg]})
        
        return {'vulnerable': vulnerable, 'score': max(0, 100 - len(vulnerable) * 15)}


def run_security_scan(directory: str) -> Dict:
    scanner = SecurityScanner()
    static = scanner.scan_directory(directory)
    req_file = os.path.join(directory, 'requirements.txt')
    dep = scanner.check_dependencies(req_file)
    
    final_score = (static['score'] + dep['score']) / 2
    return {
        'static': static,
        'dependencies': dep,
        'score': final_score,
        'pass': final_score >= 95
    }


if __name__ == "__main__":
    import sys
    directory = sys.argv[1] if len(sys.argv) > 1 else "src"
    result = run_security_scan(directory)
    print(f"Score: {result['score']}")
