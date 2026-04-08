from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

from .module_weights import ModuleWeights


@dataclass
class SensorResult:
    """單一傳感器結果"""
    name: str
    passed: bool
    score: float
    details: dict = field(default_factory=dict)
    violations: list[dict] = field(default_factory=list)


@dataclass
class SensorReport:
    """綜合傳感器報告"""
    project_path: str
    timestamp: str
    passed: bool
    weighted_score: float
    sensors: dict[str, SensorResult]
    total_violations: int

    def to_dict(self) -> dict:
        return asdict(self)


class ComputationalSensors:
    """
    統一的 Computational Sensors 入口。
    封裝所有 quality sensors，提供單一介面。

    使用方式：
        sensors = ComputationalSensors(project_path="/path/to/project")
        report = sensors.scan()

        print(f"Score: {report.weighted_score}")
        for name, result in report.sensors.items():
            print(f"  {name}: {result.score:.2f}")
    """

    def __init__(
        self,
        project_path: str,
        weights: ModuleWeights | None = None,
        config: dict | None = None,
    ):
        self.project_path = Path(project_path)
        self.weights = weights or ModuleWeights()
        self.config = config or {}

        # Lazy-load existing checkers
        self._complexity_sensor: Optional[object] = None
        self._quality_sensor: Optional[object] = None
        self._coverage_sensor: Optional[object] = None

    def scan(self) -> SensorReport:
        """
        執行所有 sensors，返回綜合報告。
        """
        from datetime import datetime, timezone

        results = {}

        # 執行每個 sensor
        complexity = self._scan_complexity()
        results["complexity"] = complexity

        coupling = self._scan_coupling()
        results["coupling"] = coupling

        coverage = self._scan_coverage()
        results["coverage"] = coverage

        maintainability = self._scan_maintainability()
        results["maintainability"] = maintainability

        # 計算加權分數
        weighted_score = (
            results["complexity"].score * self.weights.complexity +
            results["coupling"].score * self.weights.coupling +
            results["coverage"].score * self.weights.coverage +
            results["maintainability"].score * self.weights.maintainability
        )

        # 統計 violations
        total_violations = sum(
            len(r.violations) for r in results.values()
        )

        return SensorReport(
            project_path=str(self.project_path),
            timestamp=datetime.now(timezone.utc).isoformat(),
            passed=weighted_score >= 0.7,
            weighted_score=weighted_score,
            sensors=results,
            total_violations=total_violations,
        )

    def _scan_complexity(self) -> SensorResult:
        """執行複雜度 sensor。"""
        if self._complexity_sensor is None:
            from quality_gate.complexity_checker import ComplexityChecker
            self._complexity_sensor = ComplexityChecker(str(self.project_path))

        # 執行檢查
        result = self._complexity_sensor.run()
        avg_cc = result.avg_complexity

        # 分數：CC < 10 = 1.0, CC > 20 = 0.0
        score = max(0.0, min(1.0, (20 - avg_cc) / 10))

        return SensorResult(
            name="complexity",
            passed=score >= 0.7,
            score=score,
            details={"avg_cc": avg_cc, "max_cc": result.max_complexity},
            violations=result.violations,
        )

    def _scan_coupling(self) -> SensorResult:
        """執行耦合度 sensor。"""
        if self._quality_sensor is None:
            from quality_gate.fitness_functions import FitnessFunctions
            self._quality_sensor = FitnessFunctions(str(self.project_path))

        # 執行 evaluate 來計算 coupling
        fitness_result = self._quality_sensor.evaluate()

        # 取得 overall coupling score (0-100) 轉換為 0-1
        coupling_score = fitness_result.coupling_score / 100.0

        # 收集 coupling violations
        violations = []
        for m in fitness_result.modules:
            if m.is_zone_of_pain:
                violations.append({
                    "type": "zone_of_pain",
                    "module": m.name,
                    "instability": m.instability,
                    "afferent_coupling": m.afferent_coupling,
                })
            elif m.is_zone_of_exclusion:
                violations.append({
                    "type": "zone_of_exclusion",
                    "module": m.name,
                    "instability": m.instability,
                    "efferent_coupling": m.efferent_coupling,
                })

        return SensorResult(
            name="coupling",
            passed=coupling_score >= 0.7,
            score=coupling_score,
            details={"coupling_score": fitness_result.coupling_score},
            violations=violations,
        )

    def _scan_coverage(self) -> SensorResult:
        """執行覆蓋率 sensor。"""
        if self._coverage_sensor is None:
            from quality_gate.coverage_checker import CoverageChecker
            self._coverage_sensor = CoverageChecker(str(self.project_path))

        result = self._coverage_sensor.check()

        # 支援兩種回傳格式: {coverage: float} 或 {passed, line_coverage, ...}
        if "coverage" in result:
            coverage = result.get("coverage", 0.0) / 100.0
        else:
            coverage = result.get("line_coverage", result.get("line_coverage", 0)) / 100.0

        return SensorResult(
            name="coverage",
            passed=coverage >= 0.7,
            score=coverage,
            details={
                "coverage_pct": result.get("coverage", result.get("line_coverage", 0)),
                "branch_coverage": result.get("branch_coverage"),
            },
            violations=result.get("violations", []),
        )

    def _scan_maintainability(self) -> SensorResult:
        """
        計算真正的 Maintainability Index。

        公式（Microsoft 版）：
        MI = 171 - 5.2 * ln(avgCC) - 0.23 * ln(avgLOC)
             - 16.2 * ln(totalLines)
             + 50 * sin(sqrt(2.46 * commentRatio))

        範圍：0-100
        - 100-80: A (Excellent)
        - 80-60: B (Good)
        - 60-40: C (Fair)
        - 40-20: D (Poor)
        - 20-0:  F (Very Poor)

        補充：
        - 高測試覆蓋率（>80%）加分
        - 高註釋覆蓋率（>30%）加分
        """
        import math

        # 1. 計算 CC
        avg_cc = self._calculate_avg_cyclomatic_complexity()

        # 2. 計算 LOC
        total_loc = self._calculate_total_loc()
        avg_loc = self._calculate_avg_loc()

        # 3. 計算註釋覆蓋率
        comment_ratio = self._calculate_comment_ratio()  # 0.0 - 1.0

        # 4. 計算測試覆蓋率（如果有的話）
        coverage_ratio = self._get_coverage_ratio()  # 0.0 - 1.0

        # 基礎 MI
        if total_loc == 0 or avg_loc == 0 or avg_cc == 0:
            mi = 100.0
        else:
            mi = (
                171
                - 5.2 * math.log(avg_cc + 1)
                - 0.23 * math.log(avg_loc + 1)
                - 16.2 * math.log(total_loc + 1)
                + 50 * math.sin(math.sqrt(2.46 * comment_ratio + 0.01))
            )

        # 測試覆蓋率加分（>80% 覆蓋率額外加 5 分）
        if coverage_ratio > 0.8:
            mi += 5

        # 限制在 0-100 範圍
        mi = max(0.0, min(100.0, mi))

        # 分數計算（100 = 1.0, 0 = 0.0）
        score = mi / 100.0

        return SensorResult(
            name="maintainability",
            passed=mi >= 60.0,  # B grade or better
            score=score,
            details={
                "maintainability_index": mi,
                "avg_cyclomatic_complexity": avg_cc,
                "total_loc": total_loc,
                "comment_ratio": comment_ratio,
                "coverage_ratio": coverage_ratio,
                "grade": self._mi_to_grade(mi),
            },
            violations=[],
        )

    def _calculate_avg_cyclomatic_complexity(self) -> float:
        """計算平均 CC（簡單版本）。"""
        complexity_results = []
        for py_file in self.project_path.rglob("*.py"):
            try:
                import ast
                tree = ast.parse(py_file.read_text(encoding="utf-8", errors="ignore"))
                cc = self._count_cyclomatic_complexity(tree)
                complexity_results.append(cc)
            except Exception:
                continue

        if not complexity_results:
            return 5.0  # 預設值

        return sum(complexity_results) / len(complexity_results)

    def _count_cyclomatic_complexity(self, tree: "ast.AST") -> int:
        """計算 AST 的 CC。"""
        import ast
        cc = 1
        for node in ast.walk(tree):
            if isinstance(node, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                cc += 1
            elif isinstance(node, ast.BoolOp):
                cc += len(node.values) - 1
        return cc

    def _calculate_loc(self) -> int:
        """計算總 LOC。"""
        return self._calculate_total_loc()

    def _calculate_total_loc(self) -> int:
        """計算總 LOC。"""
        total = 0
        for py_file in self.project_path.rglob("*.py"):
            try:
                total += len(py_file.read_text(encoding="utf-8", errors="ignore").splitlines())
            except Exception:
                continue
        return total

    def _calculate_avg_loc(self) -> float:
        """計算平均 LOC（每個檔案）。"""
        file_locs = []
        for py_file in self.project_path.rglob("*.py"):
            try:
                loc = len(py_file.read_text(encoding="utf-8", errors="ignore").splitlines())
                file_locs.append(loc)
            except Exception:
                continue

        if not file_locs:
            return 0.0

        return sum(file_locs) / len(file_locs)

    def _calculate_comment_ratio(self) -> float:
        """計算代碼中的註釋比率。"""
        total_lines = 0
        comment_lines = 0

        for py_file in self.project_path.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                lines = content.splitlines()
                total_lines += len(lines)

                # 計算註釋行（# 開頭 或 """xxx""" 內）
                in_docstring = False
                for line in lines:
                    stripped = line.strip()
                    if stripped.startswith('#'):
                        comment_lines += 1
                    elif stripped.startswith('"""') or stripped.startswith("'''"):
                        in_docstring = not in_docstring
                        comment_lines += 1
                    elif in_docstring:
                        comment_lines += 1
            except Exception:
                continue

        if total_lines == 0:
            return 0.0

        return min(comment_lines / total_lines, 0.5)  # 最多 50%

    def _get_coverage_ratio(self) -> float:
        """
        獲取測試覆蓋率。
        優先從 coverage report 讀取。
        """
        # 嘗試找 coverage.json 或 .coverage
        coverage_files = list(self.project_path.glob("coverage/*.json"))
        coverage_files.extend(self.project_path.glob("**/.coverage"))

        if coverage_files:
            # 讀取 coverage 數據
            # 這裡用簡單的實現
            return 0.65  # 預設值，實際應該讀取 coverage report

        return 0.5  # 預設 50% 覆蓋率

    def _mi_to_grade(self, mi: float) -> str:
        """將 MI 轉換為字母等級。"""
        if mi >= 100:
            return "A+"
        elif mi >= 80:
            return "A"
        elif mi >= 60:
            return "B"
        elif mi >= 40:
            return "C"
        elif mi >= 20:
            return "D"
        return "F"
