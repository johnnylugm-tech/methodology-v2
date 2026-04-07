"""
Fitness Functions — 架構健康度量
衡量 Coupling / Cohesion / Stability / Reusability

公式依據：
- Coupling: Martin 的 OO Metric (I = Ce / (Ca + Ce))
- Cohesion: LCOM2 (Lack of Cohesion of Methods v2)
- Stability: Instability-based 分類
- Reusability: 作為 Coupling + Cohesion 的衍生指標
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Any, Optional, Set
import ast
import json

# ─── Data Classes ───────────────────────────────────────────────────────────────

@dataclass
class ModuleMetrics:
    """單一模組的度量"""
    name: str
    afferent_coupling: int   # Ca: 有多少模組依賴我
    efferent_coupling: int   # Ce: 我依賴多少模組
    instability: float       # I = Ce / (Ca + Ce), 0=完全穩定, 1=完全不穩定
    coupling_score: float    # 0-100, 100=完全解耦
    cohesion: float           # 0-100, 100=完全內聚
    is_stable: bool          # Ca > 0 and Ce == 0
    is_unstable: bool        # Ce > 0 and Ca == 0
    is_zone_of_pain: bool    # I接近1且被大量依賴 = 危險
    is_zone_of_exclusion: bool  # I接近0且大量依賴他人 = 沒意義

@dataclass
class FitnessResult:
    """完整 fitness 評估結果"""
    overall_score: float           # 0-100
    coupling_score: float          # 0-100
    cohesion_score: float           # 0-100
    stability_score: float          # 0-100
    reusability_score: float       # 0-100
    modules: List[ModuleMetrics]
    violations: List[Dict[str, Any]]  # 架構違規
    cycle_groups: List[List[str]]     # 循環依賴群組
    critical_modules: List[str]     # Zone of Pain 模組

# ─── Main Class ────────────────────────────────────────────────────────────────

class FitnessFunctions:
    """
    Architecture Fitness Functions

    核心度量：
    1. Coupling (Afferent/Efferent) — 模組間依賴程度
    2. Cohesion (LCOM2) — 類別內方法的內聚程度
    3. Stability — 模組的穩定性分類
    4. Reusability — 可重用性（耦合+內聚的衍生）
    """

    def __init__(self, project_path: str):
        self.project_path = Path(project_path)
        self.modules: Dict[str, ModuleMetrics] = {}
        self.dependencies: Dict[str, List[str]] = {}  # {module: [dep1, dep2]}
        self.violations: List[Dict[str, Any]] = []
        self.cycle_groups: List[List[str]] = []

        # Threshold
        self.instability_threshold = 0.3   # I > 0.3 = unstable
        self.cohesion_threshold = 50.0     # < 50 = 低內聚
        self.max_efferent = 10              # Ce > 10 = 過度耦合

    def evaluate(self) -> FitnessResult:
        """
        執行完整 fitness 評估

        流程：
        1. 提取模組依賴關係
        2. 計算 Coupling (Ca, Ce, I)
        3. 計算 Cohesion (LCOM2)
        4. 分類 Stability
        5. 偵測循環依賴
        6. 識別 Zone of Pain / Exclusion
        7. 計算 overall score
        """
        # Step 1: Extract dependencies
        self._extract_dependencies()

        # Step 2: Calculate Coupling
        self._calculate_coupling()

        # Step 3: Calculate Cohesion (LCOM2)
        self._calculate_cohesion()

        # Step 4: Identify violations
        self._identify_violations()

        # Step 5: Detect cycles
        self._detect_cycles()

        # Step 6: Calculate overall score
        overall = self._calc_overall_score()

        # Step 7: Critical modules
        critical = [m.name for m in self.modules.values() if m.is_zone_of_pain]

        return FitnessResult(
            overall_score=overall,
            coupling_score=self._avg_coupling_score(),
            cohesion_score=self._avg_cohesion_score(),
            stability_score=self._calc_stability_score(),
            reusability_score=self._calc_reusability_score(),
            modules=list(self.modules.values()),
            violations=self.violations,
            cycle_groups=self.cycle_groups,
            critical_modules=critical
        )

    def _extract_dependencies(self):
        """從 imports 提取模組依賴關係"""
        self.dependencies = {}

        # 找出所有 Python 模組
        py_files = list(self.project_path.rglob("*.py"))
        py_files = [f for f in py_files if "__pycache__" not in str(f) and "test" not in f.name]

        for py_file in py_files:
            module_name = self._get_module_name(py_file)
            if not module_name:
                continue

            try:
                content = py_file.read_text()
                tree = ast.parse(content)

                imports = set()
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imports.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imports.add(node.module.split('.')[0])

                self.dependencies[module_name] = sorted(imports)
            except Exception:
                self.dependencies[module_name] = []

    def _get_module_name(self, py_file: Path) -> Optional[str]:
        """從檔案路徑取得模組名"""
        try:
            rel = py_file.relative_to(self.project_path)
            parts = list(rel.parts)
            if parts[-1] == "__init__.py":
                parts = parts[:-1]
            elif parts[-1].endswith(".py"):
                parts[-1] = parts[-1][:-3]
            return ".".join(parts)
        except Exception:
            return None

    def _calculate_coupling(self):
        """計算 Coupling 度量 (Ca, Ce, I)"""
        # 建立反向索引：Afferent
        afferent: Dict[str, Set[str]] = {m: set() for m in self.dependencies}

        for module, deps in self.dependencies.items():
            for dep in deps:
                # 嘗試匹配 dep 到已知模組
                for known in self.dependencies:
                    if dep == known or dep in known.split('.'):
                        afferent[known].add(module)
                        break

        # 計算每個模組的 Coupling
        for module in self.dependencies:
            ca = len(afferent[module])  # Afferent Coupling
            ce = len(self.dependencies[module])  # Efferent Coupling
            instability = ce / (ca + ce + 0.001)

            coupling_score = max(0, 100 - instability * 100)

            is_stable = ca > 0 and ce == 0
            is_unstable = ce > 0 and ca == 0
            is_zone_of_pain = instability > 0.7 and ca > 2  # 高I且被多模組依賴
            is_zone_of_exclusion = instability < 0.3 and ce > 5  # 低I且高度依賴他人

            self.modules[module] = ModuleMetrics(
                name=module,
                afferent_coupling=ca,
                efferent_coupling=ce,
                instability=instability,
                coupling_score=coupling_score,
                cohesion=50.0,  # 待 _calculate_cohesion 更新
                is_stable=is_stable,
                is_unstable=is_unstable,
                is_zone_of_pain=is_zone_of_pain,
                is_zone_of_exclusion=is_zone_of_exclusion
            )

    def _calculate_cohesion(self):
        """計算 Cohesion (LCOM2)"""
        for py_file in self.project_path.rglob("*.py"):
            if "__pycache__" in str(py_file) or "test" in py_file.name:
                continue

            module_name = self._get_module_name(py_file)
            if not module_name or module_name not in self.modules:
                continue

            try:
                content = py_file.read_text()
                tree = ast.parse(content)

                # 對每個類別計算 LCOM2
                for node in ast.walk(tree):
                    if isinstance(node, ast.ClassDef):
                        lcom2 = self._calc_lcom2(node)
                        # 更新 module 的 cohesion（取平均）
                        existing = self.modules[module_name].cohesion
                        # 用簡單平均
                        if existing == 50.0:  # 初始值
                            self.modules[module_name].cohesion = lcom2
                        else:
                            self.modules[module_name].cohesion = (existing + lcom2) / 2
            except Exception:
                pass

    def _calc_lcom2(self, cls_node: ast.ClassDef) -> float:
        """
        計算 LCOM2 (Lack of Cohesion of Methods v2)

        LCOM2 = 1 - (sum(shared_attrs_per_pair) / (n * (n-1)/2 * avg_attrs_per_method))

        但這裡用簡化版：
        - 計算類別方法共享的 instance attributes
        - 共享越多，內聚越高
        """
        methods = [n for n in cls_node.body if isinstance(n, ast.FunctionDef)]
        if len(methods) < 2:
            return 100.0

        # 找出所有 instance attribute 引用
        attr_sets = []
        for method in methods:
            attrs = set()
            for node in ast.walk(method):
                if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name):
                    if node.value.id == 'self':
                        attrs.add(node.attr)
            attr_sets.append(attrs)

        if not any(attr_sets):
            return 50.0

        # 計算每對方法共享的 attributes
        n = len(attr_sets)
        total_pairs = n * (n - 1) / 2
        shared_sum = 0

        for i in range(n):
            for j in range(i + 1, n):
                shared_sum += len(attr_sets[i] & attr_sets[j])

        total_unique = len(set().union(*attr_sets))
        if total_unique == 0:
            return 50.0

        avg_shared_per_pair = shared_sum / total_pairs if total_pairs > 0 else 0
        lcom2 = 1 - (avg_shared_per_pair / total_unique)

        return max(0, min(100, (1 - lcom2) * 100))

    def _identify_violations(self):
        """識別架構違規"""
        self.violations = []

        for module, metrics in self.modules.items():
            # Stable Dependency Principle 違反
            if metrics.is_zone_of_pain:
                self.violations.append({
                    "type": "zone_of_pain",
                    "module": module,
                    "instability": metrics.instability,
                    "afferent_coupling": metrics.afferent_coupling,
                    "message": f"Zone of Pain: {module} is unstable (I={metrics.instability:.2f}) but highly depended upon"
                })

            # Stable Abstractions Principle 違反
            if metrics.is_zone_of_exclusion:
                self.violations.append({
                    "type": "zone_of_exclusion",
                    "module": module,
                    "instability": metrics.instability,
                    "efferent_coupling": metrics.efferent_coupling,
                    "message": f"Zone of Exclusion: {module} is stable but depends on too many (I={metrics.instability:.2f})"
                })

            # 過度耦合
            if metrics.efferent_coupling > self.max_efferent:
                self.violations.append({
                    "type": "high_coupling",
                    "module": module,
                    "efferent_coupling": metrics.efferent_coupling,
                    "message": f"High Coupling: {module} depends on {metrics.efferent_coupling} modules (> {self.max_efferent})"
                })

            # 低內聚
            if metrics.cohesion < self.cohesion_threshold:
                self.violations.append({
                    "type": "low_cohesion",
                    "module": module,
                    "cohesion": metrics.cohesion,
                    "message": f"Low Cohesion: {module} cohesion={metrics.cohesion:.1f}% (< {self.cohesion_threshold})"
                })

    def _detect_cycles(self):
        """偵測循環依賴（使用 DFS）"""
        self.cycle_groups = []

        WHITE, GREY, BLACK = 0, 1, 2
        color = {m: WHITE for m in self.dependencies}
        # parent = {m: None for m in self.dependencies}  # unused, kept for clarity

        def dfs(node: str, path: List[str]) -> Optional[List[str]]:
            color[node] = GREY
            path.append(node)

            for dep in self.dependencies.get(node, []):
                if dep in color:
                    if color[dep] == GREY:
                        # 找到循環
                        cycle_start = path.index(dep)
                        return path[cycle_start:]
                    elif color[dep] == WHITE:
                        result = dfs(dep, path)
                        if result:
                            return result

            path.pop()
            color[node] = BLACK
            return None

        for module in self.dependencies:
            if color[module] == WHITE:
                cycle = dfs(module, [])
                if cycle:
                    self.cycle_groups.append(cycle)
                    # 重新標記這些模組為已處理
                    for m in cycle:
                        color[m] = BLACK

    def _avg_coupling_score(self) -> float:
        """計算平均 Coupling Score"""
        if not self.modules:
            return 100.0
        return sum(m.coupling_score for m in self.modules.values()) / len(self.modules)

    def _avg_cohesion_score(self) -> float:
        """計算平均 Cohesion Score"""
        if not self.modules:
            return 100.0
        return sum(m.cohesion for m in self.modules.values()) / len(self.modules)

    def _calc_stability_score(self) -> float:
        """計算 Stability Score"""
        if not self.modules:
            return 100.0

        stable_count = sum(1 for m in self.modules.values() if m.is_stable)
        unstable_count = sum(1 for m in self.modules.values() if m.is_unstable)
        total = len(self.modules)

        # 目標：穩定模組應該多於不穩定模組
        if total == 0:
            return 100.0

        # 根據 stable vs unstable 比例評分
        ratio = stable_count / (stable_count + unstable_count + 0.001)
        return ratio * 100

    def _calc_reusability_score(self) -> float:
        """計算 Reusability Score（Coupling + Cohesion 的衍生）"""
        coupling = self._avg_coupling_score()
        cohesion = self._avg_cohesion_score()

        # 低耦合(40%) + 高內聚(40%) + 低循環依賴(20%)
        cycle_penalty = max(0, 20 - len(self.cycle_groups) * 5)

        return (coupling * 0.4 + cohesion * 0.4 + cycle_penalty)

    def _calc_overall_score(self) -> float:
        """計算 Overall Fitness Score"""
        weights = {
            "coupling": 0.30,
            "cohesion": 0.30,
            "stability": 0.20,
            "reusability": 0.20
        }

        return (
            self._avg_coupling_score() * weights["coupling"] +
            self._avg_cohesion_score() * weights["cohesion"] +
            self._calc_stability_score() * weights["stability"] +
            self._calc_reusability_score() * weights["reusability"]
        )

    def get_report(self, result: FitnessResult) -> str:
        """產生人類可讀的 fitness report"""
        lines = []
        lines.append("## Architecture Fitness Report")
        lines.append("")
        lines.append(f"**Overall Score**: {result.overall_score:.1f} / 100")
        lines.append("")
        lines.append("| Metric | Score |")
        lines.append("|--------|-------|")
        lines.append(f"| Coupling | {result.coupling_score:.1f} |")
        lines.append(f"| Cohesion | {result.cohesion_score:.1f} |")
        lines.append(f"| Stability | {result.stability_score:.1f} |")
        lines.append(f"| Reusability | {result.reusability_score:.1f} |")
        lines.append("")

        if result.critical_modules:
            lines.append(f"**⚠️ Zone of Pain Modules**: {', '.join(result.critical_modules)}")
            lines.append("")

        if result.cycle_groups:
            lines.append("**🔴 Circular Dependencies**:")
            for cycle in result.cycle_groups:
                lines.append(f"  - {' → '.join(cycle)} → {cycle[0]}")
            lines.append("")

        if result.violations:
            lines.append(f"**⚠️ Violations** ({len(result.violations)}):")
            for v in result.violations[:10]:
                lines.append(f"  - [{v['type']}] {v['module']}: {v['message']}")
            lines.append("")

        if result.overall_score >= 80:
            lines.append("✅ **Status**: Healthy — Architecture is well-structured")
        elif result.overall_score >= 60:
            lines.append("⚠️ **Status**: Warning — Minor violations detected")
        else:
            lines.append("❌ **Status**: Critical — Major architecture issues need attention")

        return "\n".join(lines)


# ─── CLI ───────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Architecture Fitness Functions")
    parser.add_argument("--path", required=True, help="Project path")
    parser.add_argument("--json", action="store_true", help="JSON output")
    args = parser.parse_args()

    ff = FitnessFunctions(args.path)
    result = ff.evaluate()

    if args.json:
        import dataclasses
        data = {
            "overall_score": result.overall_score,
            "coupling_score": result.coupling_score,
            "cohesion_score": result.cohesion_score,
            "stability_score": result.stability_score,
            "reusability_score": result.reusability_score,
            "modules": [dataclasses.asdict(m) for m in result.modules],
            "violations": result.violations,
            "cycle_groups": result.cycle_groups,
            "critical_modules": result.critical_modules
        }
        print(json.dumps(data, indent=2))
    else:
        print(ff.get_report(result))

if __name__ == "__main__":
    main()
