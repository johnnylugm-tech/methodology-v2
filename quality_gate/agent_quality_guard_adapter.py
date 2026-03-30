#!/usr/bin/env python3
"""
Agent Quality Guard Adapter
=============================
隔離外部 Agent Quality Guard 依賴的適配器。

提供統一接口，即使外部依賴不可用也能維持基本功能。
包含 fallback 機制，確保 L3 檢查不會因外部依賴失敗而中斷。

使用方式：
    from quality_gate.agent_quality_guard_adapter import AgentQualityGuardAdapter
    
    adapter = AgentQualityGuardAdapter("/path/to/project")
    result = adapter.analyze()
    
    print(result.score)
    print(result.issues)
"""

import sys
import json
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple


@dataclass
class QualityGuardResult:
    """品質檢查結果"""
    score: float
    grade: str  # A, B, C, D, F
    files_scanned: int
    issues: List[Dict[str, Any]]
    passed: bool
    details: Dict[str, Any]
    external_used: bool
    fallback_used: bool
    error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)


class AgentQualityGuardAdapter:
    """
    Agent Quality Guard 適配器
    
    提供：
    - 統一接口隔離外部依賴
    - Fallback 機制（外部不可用時使用本地檢查）
    - 分數閾值配置（預設分數 ≥ 90，等級 A）
    """
    
    # 預設閾值
    DEFAULT_SCORE_THRESHOLD = 90
    DEFAULT_GRADE_THRESHOLD = "A"
    
    # 等級對應分數
    GRADE_SCORES = {
        "A": (90, 100),
        "B": (80, 89),
        "C": (70, 79),
        "D": (60, 69),
        "F": (0, 59),
    }
    
    def __init__(
        self,
        project_path: str,
        score_threshold: float = DEFAULT_SCORE_THRESHOLD,
        grade_threshold: str = DEFAULT_GRADE_THRESHOLD
    ):
        self.project_path = Path(project_path)
        self.score_threshold = score_threshold
        self.grade_threshold = grade_threshold
        
        # 檢查外部 Agent Quality Guard 是否可用
        self.external_available = self._check_external_availability()
        
        # 初始化結果緩存
        self._cached_result: Optional[QualityGuardResult] = None
    
    def _check_external_availability(self) -> bool:
        """檢查外部 Agent Quality Guard 是否可用"""
        try:
            agent_guard_path = (
                Path(__file__).parent.parent / 
                "agent-quality-guard" / "src"
            )
            if agent_guard_path.exists():
                sys.path.insert(0, str(agent_guard_path))
                from analyzer import analyze_code
                from scorer import score_from_code
                return True
        except ImportError:
            pass
        except Exception:
            pass
        return False
    
    def _calculate_grade(self, score: float) -> str:
        """根據分數計算等級"""
        for grade, (low, high) in self.GRADE_SCORES.items():
            if low <= score <= high:
                return grade
        return "F"
    
    def analyze(self, force_refresh: bool = False) -> QualityGuardResult:
        """
        執行代碼品質分析
        
        Args:
            force_refresh: 是否強制重新分析（不使用緩存）
            
        Returns:
            QualityGuardResult: 檢查結果
        """
        # 返回緩存結果（如果存在且未強制刷新）
        if self._cached_result is not None and not force_refresh:
            return self._cached_result
        
        # 嘗試使用外部 Agent Quality Guard
        if self.external_available:
            try:
                result = self._analyze_with_external()
                self._cached_result = result
                return result
            except Exception as e:
                # 外部失敗，fallback 到本地檢查
                pass
        
        # Fallback 到本地檢查
        result = self._analyze_with_fallback()
        self._cached_result = result
        return result
    
    def _analyze_with_external(self) -> QualityGuardResult:
        """使用外部 Agent Quality Guard 分析"""
        try:
            from analyzer import analyze_code
            from scorer import score_from_code
            
            # 分析代碼
            analysis = analyze_code(str(self.project_path))
            
            # 計算分數
            score = score_from_code(analysis)
            
            # 計算等級
            grade = self._calculate_grade(score)
            
            # 判斷是否通過
            passed = score >= self.score_threshold
            
            return QualityGuardResult(
                score=score,
                grade=grade,
                files_scanned=len(analysis.get("files", [])),
                issues=analysis.get("issues", []),
                passed=passed,
                details=analysis,
                external_used=True,
                fallback_used=False
            )
        except Exception as e:
            return QualityGuardResult(
                score=0,
                grade="F",
                files_scanned=0,
                issues=[],
                passed=False,
                details={},
                external_used=True,
                fallback_used=False,
                error=str(e)
            )
    
    def _analyze_with_fallback(self) -> QualityGuardResult:
        """使用本地 fallback 機制分析"""
        issues = []
        files_scanned = 0
        
        # 掃描 Python 檔案
        python_files = list(self.project_path.rglob("*.py"))
        python_files = [
            f for f in python_files
            if not any(
                p in str(f) for p in [
                    "__pycache__",
                    ".git",
                    "node_modules",
                    ".venv",
                    "venv"
                ]
            )
        ]
        
        for py_file in python_files:
            try:
                content = py_file.read_text(encoding='utf-8')
                files_scanned += 1
                
                # 基本檢查
                file_issues = []
                
                # 檢查 1: 空檔案
                if len(content.strip()) == 0:
                    file_issues.append({
                        "type": "empty_file",
                        "severity": "warning",
                        "file": str(py_file)
                    })
                
                # 檢查 2: 過長的行
                for i, line in enumerate(content.split('\n'), 1):
                    if len(line) > 120:
                        file_issues.append({
                            "type": "line_too_long",
                            "severity": "warning",
                            "file": str(py_file),
                            "line": i,
                            "length": len(line)
                        })
                
                # 檢查 3: TODO 註解
                if "TODO" in content or "FIXME" in content:
                    file_issues.append({
                        "type": "todo_comment",
                        "severity": "info",
                        "file": str(py_file)
                    })
                
                if file_issues:
                    issues.extend(file_issues)
                    
            except Exception:
                pass
        
        # 計算分數（基於問題數量）
        warning_count = len([i for i in issues if i.get("severity") == "warning"])
        info_count = len([i for i in issues if i.get("severity") == "info"])
        
        # 簡單的評分邏輯
        base_score = 100
        score = max(0, base_score - (warning_count * 2) - (info_count * 0.5))
        
        # 計算等級
        grade = self._calculate_grade(score)
        
        # 判斷是否通過
        passed = score >= self.score_threshold
        
        return QualityGuardResult(
            score=score,
            grade=grade,
            files_scanned=files_scanned,
            issues=issues,
            passed=passed,
            details={
                "warning_count": warning_count,
                "info_count": info_count,
                "python_files_found": len(python_files)
            },
            external_used=False,
            fallback_used=True
        )
    
    def check_threshold(self) -> Tuple[bool, str]:
        """
        檢查是否滿足閾值
        
        Returns:
            Tuple[bool, str]: (是否通過, 訊息)
        """
        result = self.analyze()
        
        if result.passed:
            return True, f"Passed: {result.score:.1f} ({result.grade})"
        else:
            return False, f"Failed: {result.score:.1f} (need ≥ {self.score_threshold})"
    
    def get_health_status(self) -> Dict[str, Any]:
        """
        取得健康狀態
        
        Returns:
            Dict: 健康狀態資訊
        """
        return {
            "external_available": self.external_available,
            "score_threshold": self.score_threshold,
            "grade_threshold": self.grade_threshold,
            "last_result": self._cached_result.to_dict() if self._cached_result else None
        }


def main():
    """命令列入口點"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Agent Quality Guard Adapter"
    )
    parser.add_argument(
        "project_path",
        nargs="?",
        default=".",
        help="Project root path"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=90,
        help="Score threshold (default: 90)"
    )
    parser.add_argument(
        "--quiet", "-q",
        action="store_true",
        help="Quiet mode (no verbose output)"
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--health",
        action="store_true",
        help="Show health status"
    )
    
    args = parser.parse_args()
    
    adapter = AgentQualityGuardAdapter(
        args.project_path,
        score_threshold=args.threshold
    )
    
    if args.health:
        status = adapter.get_health_status()
        print(json.dumps(status, indent=2))
        sys.exit(0)
    
    result = adapter.analyze()
    
    if not args.quiet:
        status = "✅ PASS" if result.passed else "❌ FAIL"
        print(f"Status: {status}")
        print(f"Score: {result.score:.1f} ({result.grade})")
        print(f"Files Scanned: {result.files_scanned}")
        print(f"Issues Found: {len(result.issues)}")
        print(f"External Used: {result.external_used}")
        print(f"Fallback Used: {result.fallback_used}")
        
        if result.error:
            print(f"Error: {result.error}")
    
    if args.json:
        print(result.to_json())
    
    sys.exit(0 if result.passed else 1)


if __name__ == "__main__":
    main()
