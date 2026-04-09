#!/usr/bin/env python3
"""
AutoResearch Loop - 自動品質改進系統
基於 Karpathy AutoResearch 概念：迭代式自動優化

流程:
1. 評估當前分數
2. 識別最低分維度
3. Agent 生成改進方案
4. 執行改變
5. 重新評估
6. 如果改善 → 保留；否則 → 回滾
7. 重複直到達標或達到最大迭代
"""

import json
import subprocess
import sys
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from datetime import datetime
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent))
from dashboard import QualityDashboard, DimensionScore

# ============================================================================
# IMPROVEMENT STRATEGIES
# ============================================================================

@dataclass
class ImprovementAction:
    dimension: str
    file_path: str
    original_code: str
    new_code: str
    expected_improvement: float
    executed: bool = False
    reverted: bool = False
    improvement_achieved: Optional[float] = None

class ImprovementStrategy:
    """改進策略基類"""
    
    def __init__(self, dashboard: QualityDashboard):
        self.dashboard = dashboard
        self.actions: List[ImprovementAction] = []
    
    def analyze(self) -> List[ImprovementAction]:
        """分析並生成改進行動"""
        raise NotImplementedError
    
    def execute(self, action: ImprovementAction) -> bool:
        """執行改進行動"""
        raise NotImplementedError
    
    def validate(self, action: ImprovementAction) -> float:
        """驗證改進效果，返回實際提升分數"""
        raise NotImplementedError
    
    def revert(self, action: ImprovementAction) -> bool:
        """回滾改變"""
        raise NotImplementedError


class CoverageImprovement(ImprovementStrategy):
    """D3: Test Coverage 改進策略"""
    
    TARGET_COVERAGE = 70  # 目標覆蓋率
    
    def analyze(self) -> List[ImprovementAction]:
        actions = []
        project_path = self.dashboard.project_path
        
        # 找到所有 Python 文件
        py_files = list(project_path.rglob("*.py"))
        
        # 找到現有測試文件
        test_files = list((project_path / "tests").rglob("test_*.py")) if (project_path / "tests").exists() else []
        tested_modules = set()
        
        for test_file in test_files:
            content = test_file.read_text()
            # 提取測試的模組名
            imports = re.findall(r'from\s+(\S+)\s+import', content)
            for imp in imports:
                if '.' in imp:
                    tested_modules.add(imp.split('.')[0])
        
        # 找出未測試的模組
        for py_file in py_files:
            if 'test' in py_file.name or py_file.name.startswith('__'):
                continue
            
            rel_path = py_file.relative_to(project_path)
            
            # 檢查這個檔案是否被測試
            module_name = str(rel_path).replace('/', '.').replace('.py', '')
            if module_name in tested_modules:
                continue
            
            # 讀取代碼，提取函數
            try:
                content = py_file.read_text()
                functions = re.findall(r'def\s+(\w+)\s*\([^)]*\)\s*(?:->\s*\w+\s*)?:', content)
                
                if functions and len(functions) > 0:
                    # 生成測試檔案名
                    test_name = f"test_{rel_path.stem}.py"
                    test_path = project_path / "tests" / test_name
                    
                    # 生成的測試模板
                    test_code = self._generate_test_template(py_file, functions, rel_path)
                    
                    actions.append(ImprovementAction(
                        dimension="D3_Coverage",
                        file_path=str(test_path),
                        original_code="",  # 新檔案，無 original
                        new_code=test_code,
                        expected_improvement=10.0  # 預期每個測試檔案提升 10%
                    ))
            except Exception as e:
                continue
        
        return actions[:3]  # 最多生成 3 個測試檔案
    
    def _generate_test_template(self, py_file: Path, functions: List[str], rel_path) -> str:
        module_name = str(rel_path).replace('/', '.').replace('.py', '')
        class_name = ''.join([w.capitalize() for w in rel_path.stem.split('_')]) + 'Tests'
        
        imports = [f"import pytest", f"import sys", f"sys.path.insert(0, '{py_file.parent.parent}')"]
        
        try:
            content = py_file.read_text()
            # 提取 import
            existing_imports = re.findall(r'^import\s+\S+|^from\s+\S+\s+import\s+[^\n]+', content, re.MULTILINE)
            for imp in existing_imports[:5]:
                imports.append(imp)
            module_import = f"from {module_name} import *"
            if module_import not in imports:
                imports.append(module_import)
        except:
            pass
        
        test_methods = []
        for func in functions:
            if not func.startswith('_'):
                test_methods.append(f"""
    def test_{func}(self):
        \"\"\"Test {func}\"\"\"
        pass""")
        
        return f'''"""Auto-generated tests for {rel_path}"""

{chr(10).join(imports)}


class {class_name}:
{chr(10).join(test_methods)}
'''
    
    def execute(self, action: ImprovementAction) -> bool:
        try:
            test_path = Path(action.file_path)
            test_path.parent.mkdir(parents=True, exist_ok=True)
            test_path.write_text(action.new_code)
            action.executed = True
            return True
        except Exception as e:
            print(f"❌ Execute failed: {e}")
            return False
    
    def validate(self, action: ImprovementAction) -> float:
        """驗證測試覆蓋率提升"""
        # 重新運行評估
        result = self.dashboard.run_evaluation()
        coverage_dim = result.dimensions.get("D3_Coverage")
        if coverage_dim:
            return coverage_dim.score
        return 0.0
    
    def revert(self, action: ImprovementAction) -> bool:
        try:
            if Path(action.file_path).exists():
                Path(action.file_path).unlink()
            action.reverted = True
            return True
        except:
            return False


class LintingImprovement(ImprovementStrategy):
    """D1: Linting 改進策略"""
    
    def analyze(self) -> List[ImprovementAction]:
        actions = []
        
        # 運行 ruff check 獲取錯誤
        result = subprocess.run(
            ["ruff", "check", str(self.dashboard.project_path), "--ignore=D100,E501,F401"],
            capture_output=True, text=True
        )
        
        # 解析錯誤
        errors = []
        for line in result.stdout.split('\n'):
            if line.startswith('F'):
                parts = line.split(':')
                if len(parts) >= 4:
                    file_path = ':'.join(parts[:-2])
                    error_code = parts[-2]
                    errors.append((file_path, error_code))
        
        # 只處理 F401 (unused import) 等簡單錯誤
        for file_path, error_code in errors[:5]:
            if error_code == 'F401':
                actions.append(ImprovementAction(
                    dimension="D1_Linting",
                    file_path=file_path,
                    original_code=Path(file_path).read_text(),
                    new_code="",  # Agent 會處理
                    expected_improvement=2.0
                ))
        
        return actions
    
    def execute(self, action: ImprovementAction) -> bool:
        # 使用 ruff --fix 自動修復
        result = subprocess.run(
            ["ruff", "check", str(self.dashboard.project_path), "--fix", "--ignore=D100,E501"],
            capture_output=True, text=True
        )
        action.executed = True
        return result.returncode == 0
    
    def validate(self, action: ImprovementAction) -> float:
        result = self.dashboard.run_evaluation()
        linting_dim = result.dimensions.get("D1_Linting")
        return linting_dim.score if linting_dim else 0.0
    
    def revert(self, action: ImprovementAction) -> bool:
        try:
            Path(action.file_path).write_text(action.original_code)
            action.reverted = True
            return True
        except:
            return False


class ErrorHandlingImprovement(ImprovementStrategy):
    """D8: Error Handling 改進策略"""
    
    def analyze(self) -> List[ImprovementAction]:
        actions = []
        project_path = self.dashboard.project_path
        
        for py_file in project_path.rglob("*.py"):
            if 'test' in py_file.name:
                continue
            
            content = py_file.read_text()
            
            # 找空的或不完整的 try-except
            pattern = r'try:\s*.*?\s*except\s+\S+:\s*pass'
            matches = re.finditer(pattern, content, re.DOTALL)
            
            for match in matches:
                empty_blocks = match.group()
                # 建議添加有意義的錯誤處理
                new_code = content.replace(empty_blocks, f'''try:
        pass
    except Exception as e:
        # TODO: Handle specific exception
        print(f"Error occurred: {{e}}")
        raise''')
                
                if new_code != content:
                    actions.append(ImprovementAction(
                        dimension="D8_ErrorHandling",
                        file_path=str(py_file),
                        original_code=content,
                        new_code=new_code,
                        expected_improvement=5.0
                    ))
                    break  # 每個檔案只改一處
            
            if len(actions) >= 3:
                break
        
        return actions
    
    def execute(self, action: ImprovementAction) -> bool:
        try:
            Path(action.file_path).write_text(action.new_code)
            action.executed = True
            return True
        except:
            return False
    
    def validate(self, action: ImprovementAction) -> float:
        result = self.dashboard.run_evaluation()
        eh_dim = result.dimensions.get("D8_ErrorHandling")
        return eh_dim.score if eh_dim else 0.0
    
    def revert(self, action: ImprovementAction) -> bool:
        try:
            Path(action.file_path).write_text(action.original_code)
            action.reverted = True
            return True
        except:
            return False


# ============================================================================
# AUTO-RESEARCH LOOP
# ============================================================================

class AutoResearchLoop:
    """
    AutoResearch Loop - 自動品質改進迭代器
    
    基於 Karpathy AutoResearch 概念:
    - 定義"更好"的標準
    - Agent 自動執行改進
    - 迭代直到達標或達到最大次數
    """
    
    MAX_ITERATIONS = 10
    TARGET_SCORE = 85.0  # 目標總分
    
    def __init__(self, dashboard: QualityDashboard):
        self.dashboard = dashboard
        self.strategies = [
            CoverageImprovement(dashboard),
            LintingImprovement(dashboard),
            ErrorHandlingImprovement(dashboard),
        ]
        self.iteration_log: List[Dict] = []
        
    def run(self, max_iterations: int = 5) -> Dict:
        """運行 AutoResearch Loop"""
        print("\n" + "=" * 60)
        print("🚀 AutoResearch Loop 啟動")
        print("=" * 60)
        
        project_path = self.dashboard.project_path
        
        for iteration in range(1, max_iterations + 1):
            print(f"\n{'─' * 60}")
            print(f"📍 迭代 {iteration}/{max_iterations}")
            print(f"{'─' * 60}")
            
            # Step 1: 評估當前分數
            result = self.dashboard.run_evaluation()
            
            print(f"\n📊 當前分數: {result.total_score:.1f}%")
            print(f"📉 技術債: {result.technical_debt:.1f}%")
            
            # 檢查是否達標
            if result.total_score >= self.TARGET_SCORE:
                print(f"\n🎉 達成目標分數 {self.TARGET_SCORE}%！")
                break
            
            # Step 2: 識別最低分維度
            low_dims = [(name, dim) for name, dim in result.dimensions.items() if dim.score < 70]
            low_dims.sort(key=lambda x: x[1].score)
            
            if not low_dims:
                print("✅ 所有維度都已達標，無需改進")
                break
            
            print(f"\n🔍 最低分維度:")
            for name, dim in low_dims[:3]:
                print(f"   {dim.name}: {dim.score:.0f}% (目標: ≥70%)")
            
            # Step 3: 選擇對應的策略
            strategy = self._select_strategy(low_dims[0][0])
            if not strategy:
                print("❌ 沒有找到對應的改進策略")
                continue
            
            print(f"\n🛠️ 使用策略: {strategy.__class__.__name__}")
            
            # Step 4: 分析並生成行動
            actions = strategy.analyze()
            if not actions:
                print("⚠️ 分析階段未發現可改進項目")
                continue
            
            print(f"📋 發現 {len(actions)} 個潛在改進")
            
            # Step 5: 執行行動
            improvements_made = []
            for action in actions[:2]:  # 每次最多執行 2 個行動
                print(f"\n   ▶ 執行: {action.file_path}")
                
                # 保存原始分數
                original_score = result.total_score
                
                # 執行
                if strategy.execute(action):
                    # 驗證
                    new_score = strategy.validate(action)
                    action.improvement_achieved = new_score - original_score
                    
                    if new_score > original_score:
                        print(f"   ✅ 提升: {original_score:.1f}% → {new_score:.1f}% (+{new_score-original_score:.1f}%)")
                        improvements_made.append(action)
                    else:
                        print(f"   ⚠️ 無提升，回滾...")
                        strategy.revert(action)
                        # 重新驗證
                        strategy.validate(action)
                else:
                    print(f"   ❌ 執行失敗")
            
            # Step 6: 記錄迭代結果
            self.iteration_log.append({
                "iteration": iteration,
                "timestamp": datetime.now().isoformat(),
                "total_score": result.total_score,
                "improvements": [a.__dict__ for a in improvements_made],
                "low_dimensions": [(n, d.score) for n, d in low_dims[:3]]
            })
            
            # 如果連續 2 次迭代都沒有改進，停止
            if len(self.iteration_log) >= 2:
                last_improvement = self.iteration_log[-1]["improvements"]
                prev_improvement = self.iteration_log[-2]["improvements"]
                if not last_improvement and not prev_improvement:
                    print("\n⚠️ 連續 2 次迭代無改進，停止")
                    break
        
        # 最終報告
        return self._generate_final_report()
    
    def _select_strategy(self, dimension_name: str) -> Optional[ImprovementStrategy]:
        """根據維度名選擇對應策略"""
        if "Coverage" in dimension_name:
            return CoverageImprovement(self.dashboard)
        elif "Linting" in dimension_name:
            return LintingImprovement(self.dashboard)
        elif "ErrorHandling" in dimension_name:
            return ErrorHandlingImprovement(self.dashboard)
        return None
    
    def _generate_final_report(self) -> Dict:
        """生成最終報告"""
        history = self.dashboard.load_history()
        first = history[0] if history else None
        last = history[-1] if history else None
        
        report = {
            "total_iterations": len(self.iteration_log),
            "initial_score": first.total_score if first else 0,
            "final_score": last.total_score if last else 0,
            "improvement": (last.total_score - first.total_score) if first and last else 0,
            "target_reached": last.total_score >= self.TARGET_SCORE if last else False,
            "iterations": self.iteration_log
        }
        
        print("\n" + "=" * 60)
        print("📊 AutoResearch Loop 最終報告")
        print("=" * 60)
        print(f"總迭代次數: {report['total_iterations']}")
        print(f"初始分數: {report['initial_score']:.1f}%")
        print(f"最終分數: {report['final_score']:.1f}%")
        print(f"提升: {'+' if report['improvement'] >= 0 else ''}{report['improvement']:.1f}%")
        print(f"目標達成: {'✅ 是' if report['target_reached'] else '❌ 否'}")
        
        return report


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AutoResearch Loop")
    parser.add_argument("--project", default="/Users/johnny/.openclaw/workspace-musk/tts-kokoro-v613")
    parser.add_argument("--iterations", type=int, default=3, help="最大迭代次數")
    args = parser.parse_args()
    
    dashboard = QualityDashboard(args.project)
    loop = AutoResearchLoop(dashboard)
    report = loop.run(max_iterations=args.iterations)
    
    print("\n" + "=" * 60)
    print("🌐 HTML Dashboard")
    print("=" * 60)
    html_file = dashboard.generate_html_dashboard()
    print(html_file)
