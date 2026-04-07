#!/usr/bin/env python3
"""
Metrics Tracker
===============
統一代碼品質指標追蹤器
"""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict
from .complexity import ComplexityChecker
from .coupling import CouplingAnalyzer

class MetricsTracker:
    """
    統一代碼品質指標追蹤
    
    使用方式：
    
    ```python
    tracker = MetricsTracker()
    report = tracker.generate_report("src/")
    
    print(f"Coverage: {report['coverage']}%")
    print(f"Complexity violations: {report['complexity_violations']}")
    ```
    """
    
    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path)
        self.metrics_file = self.project_path / ".methodology" / "metrics.json"
        self.metrics_file.parent.mkdir(parents=True, exist_ok=True)
    
    def generate_report(self, src_path: str = "src") -> Dict:
        """生成代碼品質報告"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "complexity_violations": [],
            "coupling": {},
            "summary": {}
        }
        
        # 複雜度檢查
        checker = ComplexityChecker()
        src_dir = self.project_path / src_path
        
        if src_dir.exists():
            for py_file in src_dir.rglob("*.py"):
                try:
                    result = checker.check_file(str(py_file))
                    if not result.passed:
                        for v in result.violations:
                            report["complexity_violations"].append({
                                "file": v.file,
                                "function": v.name,
                                "line": v.line,
                                "complexity": v.complexity,
                                "threshold": v.threshold
                            })
                except:
                    pass
        
        # 耦合度分析
        analyzer = CouplingAnalyzer()
        try:
            coupling_result = analyzer.analyze_directory(str(src_dir))
            report["coupling"] = {
                "afferent": coupling_result.afferent,
                "efferent": coupling_result.efferent,
                "instability": round(coupling_result.instability, 3)
            }
        except:
            pass
        
        # 總結
        report["summary"] = {
            "total_violations": len(report["complexity_violations"]),
            "passed": len(report["complexity_violations"]) == 0
        }
        
        # 儲存
        self._save(report)
        
        return report
    
    def _save(self, report: Dict):
        """儲存報告"""
        self.metrics_file.write_text(json.dumps(report, indent=2))
    
    def get_latest(self) -> Dict:
        """取得最新報告"""
        if self.metrics_file.exists():
            return json.loads(self.metrics_file.read_text())
        return None