"""
Coverage Analyzer — 未覆蓋程式碼的「關鍵性」分析
分析未覆蓋函式被多少其他函式引用，識別真正的關鍵缺口
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Dict, Any, Optional
import subprocess
import xml.etree.ElementTree as ET
import ast
import re
import argparse


@dataclass
class CoverageGap:
    """覆蓋缺口"""
    function: str
    file: str
    line: int
    references: int  # 被多少函式引用
    severity: str    # "critical" / "high" / "medium" / "low"
    uncovered_lines: List[int]


@dataclass
class CoverageAnalysisResult:
    """分析結果"""
    total_functions: int
    covered_functions: int
    uncovered_functions: int
    coverage_rate: float
    critical_gaps: List[CoverageGap]  # references >= 5
    high_gaps: List[CoverageGap]      # references 3-4
    medium_gaps: List[CoverageGap]     # references 1-2
    score: float  # 0-100
    raw_coverage: Dict[str, Any]


class CoverageAnalyzer:
    """
    分析未覆蓋程式碼的「關鍵性」
    
    策略：
    - 用 coverage.xml 找出未覆蓋的函式
    - 用 AST/call graph 分析每個函式被多少其他函式引用
    - 被引用數 >= 5 → critical, 3-4 → high, 1-2 → medium
    """
    
    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.coverage_xml: Optional[Path] = None
        self._find_coverage_xml()
    
    def _find_coverage_xml(self):
        """找 coverage.xml"""
        for pattern in ["coverage.xml", "**/coverage.xml", "**/cobertura.xml"]:
            matches = list(self.project_path.glob(pattern))
            if matches:
                self.coverage_xml = matches[0]
                break
    
    def run(self) -> CoverageAnalysisResult:
        """執行分析"""
        if not self.coverage_xml or not self.coverage_xml.exists():
            return CoverageAnalysisResult(
                total_functions=0, covered_functions=0, uncovered_functions=0,
                coverage_rate=0, critical_gaps=[], high_gaps=[], medium_gaps=[], score=100,
                raw_coverage={"error": "coverage.xml not found"}
            )
        
        # 1. 解析 coverage.xml
        coverage_data = self._parse_coverage_xml()
        
        # 2. 建立 call graph
        callgraph = self._build_callgraph()
        
        # 3. 找出未覆蓋的 critical 函式
        gaps = self._identify_gaps(coverage_data, callgraph)
        
        # 4. 分類
        critical = [g for g in gaps if g.severity == "critical"]
        high = [g for g in gaps if g.severity == "high"]
        medium = [g for g in gaps if g.severity == "medium"]
        
        # 5. 計算分數
        score = self._calc_score(coverage_data, gaps)
        
        total = coverage_data.get("total_functions", 0)
        covered = coverage_data.get("covered_functions", 0)
        
        return CoverageAnalysisResult(
            total_functions=total,
            covered_functions=covered,
            uncovered_functions=total - covered,
            coverage_rate=coverage_data.get("rate", 0) * 100,
            critical_gaps=critical,
            high_gaps=high,
            medium_gaps=medium,
            score=score,
            raw_coverage=coverage_data
        )
    
    def _parse_coverage_xml(self) -> Dict[str, Any]:
        """解析 coverage.xml"""
        try:
            tree = ET.parse(self.coverage_xml)
            root = tree.getroot()
            
            classes = root.findall(".//class")
            functions = []
            uncovered = []
            total_lines = 0
            covered_lines = 0
            
            for cls in classes:
                cls_name = cls.get("name", "")
                for method in cls.findall("method"):
                    name = method.get("name", "")
                    if name.startswith("__"):
                        continue  # 跳過 __init__ 等
                    lines = method.find("lines")
                    if lines is not None:
                        total_lines += int(lines.get("covered", 0)) + int(lines.get("missed", 0))
                        covered_lines += int(lines.get("covered", 0))
                        line_hits = {int(l.get("number")): int(l.get("hits")) for l in lines.findall("line")}
                        
                        if all(h == 0 for h in line_hits.values()) and line_hits:
                            uncovered.append({
                                "class": cls_name,
                                "function": name,
                                "file": cls.get("filename", ""),
                                "lines": list(line_hits.keys())
                            })
                        elif any(h > 0 for h in line_hits.values()):
                            functions.append({
                                "class": cls_name,
                                "function": name,
                                "file": cls.get("filename", "")
                            })
            
            return {
                "total_functions": len(functions) + len(uncovered),
                "covered_functions": len(functions),
                "uncovered_functions": len(uncovered),
                "uncovered": uncovered,
                "rate": covered_lines / total_lines if total_lines > 0 else 0
            }
        except Exception as e:
            return {"error": str(e), "total_functions": 0, "covered_functions": 0, "uncovered_functions": 0, "rate": 0}
    
    def _build_callgraph(self) -> Dict[str, List[str]]:
        """建立簡單的 call graph（基於 AST）"""
        callgraph = {}
        
        for py_file in self.project_path.rglob("*.py"):
            if "test" in py_file.name or "__pycache__" in str(py_file):
                continue
            
            try:
                tree = ast.parse(py_file.read_text())
                funcs = {node.name: [] for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)}
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                        for func_name in funcs:
                            if func_name != node.func.id:
                                funcs[func_name].append(node.func.id)
                
                for func, calls in funcs.items():
                    key = f"{py_file.name}:{func}"
                    callgraph[key] = list(set(calls))
            except Exception:
                pass
        
        return callgraph
    
    def _identify_gaps(self, coverage_data: Dict, callgraph: Dict) -> List[CoverageGap]:
        """識別覆蓋缺口"""
        gaps = []
        for item in coverage_data.get("uncovered", []):
            func_key = f"{Path(item['file']).name}:{item['function']}"
            refs = len(callgraph.get(func_key, []))
            
            if refs >= 5:
                severity = "critical"
            elif refs >= 3:
                severity = "high"
            else:
                severity = "medium"
            
            gaps.append(CoverageGap(
                function=item["function"],
                file=item["file"],
                line=item["lines"][0] if item["lines"] else 0,
                references=refs,
                severity=severity,
                uncovered_lines=item["lines"]
            ))
        
        return gaps
    
    def _calc_score(self, coverage_data: Dict, gaps: List[CoverageGap]) -> float:
        """計算分數"""
        total = coverage_data.get("total_functions", 0)
        if total == 0:
            return 100
        
        # 被多個函式引用的未覆蓋函式，扣分更重
        penalty = sum(
            5 if g.severity == "critical" else 3 if g.severity == "high" else 1
            for g in gaps
        )
        
        base_coverage = coverage_data.get("rate", 1) * 60  # 60% from coverage
        penalty_score = max(0, 40 - penalty)  # 40% from penalty
        
        return min(100, base_coverage + penalty_score)


def main():
    parser = argparse.ArgumentParser(description="Coverage Gap Analyzer")
    parser.add_argument("--path", required=True, help="Project path")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()
    
    analyzer = CoverageAnalyzer(args.path)
    result = analyzer.run()
    
    if args.json:
        import dataclasses
        output = {
            "coverage_rate": result.coverage_rate,
            "total_functions": result.total_functions,
            "covered_functions": result.covered_functions,
            "uncovered_functions": result.uncovered_functions,
            "score": result.score,
            "critical_gaps": [(g.function, g.file, g.references) for g in result.critical_gaps],
            "high_gaps": [(g.function, g.file, g.references) for g in result.high_gaps],
            "medium_gaps": [(g.function, g.file, g.references) for g in result.medium_gaps],
        }
        import json
        print(json.dumps(output, indent=2, ensure_ascii=False))
        return
    
    print(f"=== Coverage Analysis ===")
    print(f"Coverage Rate: {result.coverage_rate:.1f}%")
    print(f"Total Functions: {result.total_functions}")
    print(f"Covered: {result.covered_functions}, Uncovered: {result.uncovered_functions}")
    print(f"Score: {result.score:.1f}/100")
    print()
    
    if result.critical_gaps:
        print(f"🔴 Critical Gaps ({len(result.critical_gaps)}):")
        for g in result.critical_gaps:
            print(f"  - {g.function} in {g.file} (refs={g.references})")
    if result.high_gaps:
        print(f"🟠 High Gaps ({len(result.high_gaps)}):")
        for g in result.high_gaps:
            print(f"  - {g.function} in {g.file} (refs={g.references})")
    if result.medium_gaps:
        print(f"⚠️ Medium Gaps ({len(result.medium_gaps)}):")
        for g in result.medium_gaps:
            print(f"  - {g.function} in {g.file} (refs={g.references})")
    
    if "error" in result.raw_coverage:
        print(f"\nError: {result.raw_coverage['error']}")


if __name__ == "__main__":
    main()
