"""
Complexity Checker — Cyclomatic Complexity 分析
================================================
使用 radon 進行 Python 分析，或 lizard 進行多語言分析

使用方式：
    python complexity_checker.py --path /path/to/project
    python complexity_checker.py --path /path/to/project --threshold 15
    from complexity_checker import ComplexityChecker
    checker = ComplexityChecker("/path/to/project", threshold=10)
    result = checker.run()
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Dict, Any, Optional


@dataclass
class ComplexityResult:
    """複雜度分析結果"""
    language: str
    tool: str
    avg_complexity: float
    max_complexity: int
    score: float  # 0-100
    violations: List[Dict[str, Any]]  # [{file, function, complexity, rank}]
    raw_output: str


class ComplexityChecker:
    """Cyclomatic complexity 分析"""
    
    # Complexity ranks: A (1-5), B (6-10), C (11-15), D (16-20), E (21+), F (uncomputable)
    RANK_THRESHOLDS = {
        "A": 5,   # 1-5: Simple, low risk
        "B": 10,  # 6-10: Moderate, acceptable
        "C": 15,  # 11-15: Complex, should be refactored
        "D": 20,  # 16-20: High risk, must refactor
        "E": 25,  # 21+: Very high risk
    }
    
    def __init__(self, project_path: str, threshold: int = 10):
        self.project_path = Path(project_path)
        self.threshold = threshold
    
    def detect_language(self) -> Optional[str]:
        """偵測專案語言"""
        extensions = {".py": "python", ".js": "javascript", ".ts": "typescript", ".go": "go", ".java": "java"}
        for ext, lang in extensions.items():
            if list(self.project_path.rglob(f"*{ext}")):
                return lang
        return None
    
    def run(self) -> ComplexityResult:
        """執行複雜度分析"""
        lang = self.detect_language()
        if not lang:
            return ComplexityResult(
                language="unknown", tool="none", avg_complexity=0,
                max_complexity=0, score=100, violations=[], raw_output=""
            )
        
        if lang == "python":
            return self._run_radon()
        else:
            return self._run_lizard()
    
    def _run_radon(self) -> ComplexityResult:
        """使用 radon 分析 Python"""
        try:
            result = subprocess.run(
                ["radon", "cc", "-a", "-j", str(self.project_path)],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            raw = result.stdout
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = self._parse_radon_text(raw)
            
            violations = self._extract_violations(data)
            return self._build_result("python", "radon", violations, raw)
        except FileNotFoundError:
            return ComplexityResult(
                language="python", tool="radon", avg_complexity=0,
                max_complexity=0, score=100, violations=[],
                raw_output="radon not installed"
            )
        except Exception as e:
            return ComplexityResult(
                language="python", tool="radon", avg_complexity=0,
                max_complexity=0, score=100, violations=[], raw_output=str(e)
            )
    
    def _parse_radon_text(self, raw: str) -> List[Dict]:
        """解析 radon text 輸出"""
        data = []
        for line in raw.split("\n"):
            # 格式: filename:lineno:function_name:complexity (rank)
            # 例如: src/module.py:42:my_function:5 (A)
            match = re.match(r"(.+?):(\d+):(.+?):(\d+)\s+\(([A-F])\)", line)
            if match:
                data.append({
                    "filename": match.group(1),
                    "lineno": int(match.group(2)),
                    "name": match.group(3),
                    "complexity": int(match.group(4)),
                    "rank": match.group(5)
                })
        return data
    
    def _run_lizard(self) -> ComplexityResult:
        """使用 lizard 分析多語言"""
        try:
            result = subprocess.run(
                ["lizard", "-o", "json", str(self.project_path)],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            raw = result.stdout or result.stderr
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = self._parse_lizard_text(raw)
            
            violations = self._extract_lizard_violations(data)
            return self._build_result(self.detect_language(), "lizard", violations, raw)
        except FileNotFoundError:
            return ComplexityResult(
                language=self.detect_language() or "unknown", tool="lizard",
                avg_complexity=0, max_complexity=0, score=100, violations=[],
                raw_output="lizard not installed"
            )
        except Exception as e:
            return ComplexityResult(
                language=self.detect_language() or "unknown", tool="lizard",
                avg_complexity=0, max_complexity=0, score=100, violations=[], raw_output=str(e)
            )
    
    def _parse_lizard_text(self, raw: str) -> List[Dict]:
        """解析 lizard text 輸出"""
        data = []
        for line in raw.split("\n"):
            # 格式类似: filename:lineno: function_name(complexity)
            match = re.match(r"(.+?):(\d+):\s+(.+?)\s*\((\d+)\)", line)
            if match:
                data.append({
                    "filename": match.group(1),
                    "lineno": int(match.group(2)),
                    "name": match.group(3).strip(),
                    "complexity": int(match.group(4))
                })
        return data
    
    def _extract_violations(self, data: Any) -> List[Dict[str, Any]]:
        """從 radon 輸出提取違規"""
        violations = []
        complexities = []
        
        # Radon JSON format: {"filename": {"function_name": {"lineno": X, "complexity": Y}}}
        if isinstance(data, dict):
            for filename, functions in data.items():
                if isinstance(functions, dict):
                    for func_name, func_data in functions.items():
                        if isinstance(func_data, dict):
                            complexity = func_data.get("complexity", 0)
                            lineno = func_data.get("lineno", 0)
                        else:
                            complexity = func_data
                            lineno = 0
                        
                        complexities.append(complexity)
                        
                        if complexity > self.threshold:
                            violations.append({
                                "file": filename,
                                "function": func_name,
                                "complexity": complexity,
                                "rank": self._get_rank(complexity),
                                "line": lineno
                            })
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    complexity = item.get("complexity", 0)
                    complexities.append(complexity)
                    
                    if complexity > self.threshold:
                        violations.append({
                            "file": item.get("filename", ""),
                            "function": item.get("name", ""),
                            "complexity": complexity,
                            "rank": self._get_rank(complexity),
                            "line": item.get("lineno", 0)
                        })
        
        return violations
    
    def _extract_lizard_violations(self, data: Any) -> List[Dict[str, Any]]:
        """從 lizard 輸出提取違規"""
        violations = []
        complexities = []
        
        # Lizard JSON format: {"results": [{"file": X, "functions": [...]}]}
        if isinstance(data, dict):
            results = data.get("results", [])
            if isinstance(results, list):
                for result_item in results:
                    filename = result_item.get("file", "")
                    functions = result_item.get("functions", [])
                    for func in functions:
                        if isinstance(func, dict):
                            complexity = func.get("complexity", 0)
                        else:
                            complexity = func
                        complexities.append(complexity)
                        
                        if complexity > self.threshold:
                            violations.append({
                                "file": filename,
                                "function": func.get("name", ""),
                                "complexity": complexity,
                                "rank": self._get_rank(complexity),
                                "line": func.get("line_number", 0)
                            })
        elif isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    complexity = item.get("complexity", 0)
                    complexities.append(complexity)
                    
                    if complexity > self.threshold:
                        violations.append({
                            "file": item.get("filename", ""),
                            "function": item.get("name", ""),
                            "complexity": complexity,
                            "rank": self._get_rank(complexity),
                            "line": item.get("lineno", 0)
                        })
        
        return violations
    
    def _get_rank(self, complexity: int) -> str:
        """根據複雜度返回等級"""
        if complexity <= 5: return "A"
        if complexity <= 10: return "B"
        if complexity <= 15: return "C"
        if complexity <= 20: return "D"
        if complexity <= 25: return "E"
        return "F"
    
    def _build_result(self, language: str, tool: str, violations: List[Dict], raw: str) -> ComplexityResult:
        """構建結果物件"""
        complexities = [v["complexity"] for v in violations]
        avg_complexity = sum(complexities) / len(complexities) if complexities else 0
        max_complexity = max(complexities) if complexities else 0
        
        # Score: 基于平均复杂度和超阈值函数数量
        # 基础分 100，每超一个阈值 -5，每超10个复杂度 -1
        score = 100
        if violations:
            violation_count = len(violations)
            score -= violation_count * 5
            if avg_complexity > self.threshold:
                score -= int(avg_complexity - self.threshold)
        score = max(0, score)
        
        return ComplexityResult(
            language=language,
            tool=tool,
            avg_complexity=round(avg_complexity, 2),
            max_complexity=max_complexity,
            score=score,
            violations=violations,
            raw_output=raw
        )
    
    def to_json(self) -> str:
        """將結果序列化為 JSON"""
        result = self.run()
        return json.dumps(asdict(result), indent=2, ensure_ascii=False)


def main():
    """CLI 入口"""
    parser = argparse.ArgumentParser(description="Complexity Checker - Cyclomatic Complexity 分析")
    parser.add_argument("--path", required=True, help="專案路徑")
    parser.add_argument("--threshold", type=int, default=10, help="複雜度閾值 (預設: 10)")
    parser.add_argument("--json", action="store_true", help="JSON 格式輸出")
    args = parser.parse_args()
    
    checker = ComplexityChecker(args.path, threshold=args.threshold)
    result = checker.run()
    
    if args.json:
        print(json.dumps(asdict(result), indent=2, ensure_ascii=False))
    else:
        print(f"Language: {result.language}")
        print(f"Tool: {result.tool}")
        print(f"Average Complexity: {result.avg_complexity}")
        print(f"Max Complexity: {result.max_complexity}")
        print(f"Score: {result.score}/100")
        print(f"Violations (> {args.threshold}): {len(result.violations)}")
        
        if result.raw_output and "not installed" in result.raw_output:
            print(f"\n⚠️ {result.raw_output}")
        elif result.violations:
            print("\n--- Top Violations (highest complexity) ---")
            sorted_violations = sorted(result.violations, key=lambda x: x["complexity"], reverse=True)
            for v in sorted_violations[:10]:
                print(f"  [{v['rank']}] {v['file']}:{v['line']} - {v['function']} (cc={v['complexity']})")


if __name__ == "__main__":
    main()
