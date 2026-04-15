"""
Ralph Mode - Output Verifier

L2 輕量驗證：檢查 sub-agent 產出檔案是否存在且基本有效。

Author: methodology-v2
Version: 1.0.0
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any

from .task_parser import TaskOutputParser


@dataclass
class VerificationResult:
    """驗證結果"""
    passed: bool
    fr: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    verification_level: str = "L2"
    
    # 詳細資訊
    checked_files: int = 0
    missing_files: List[str] = field(default_factory=list)
    small_files: List[str] = field(default_factory=list)
    empty_files: List[str] = field(default_factory=list)


class OutputVerifier:
    """
    L2 輕量驗證器
    
    只檢查：
    - L2a: 檔案是否存在
    - L2b: 檔案大小是否 > 100 bytes
    - L2c: Python 檔案是否包含基本程式碼結構 (import/class/def)
    
    不做：lint / type check / pytest
    
    Example:
        >>> verifier = OutputVerifier(Path("/repo"))
        >>> result = verifier.verify_fr({
        ...     "fr": "FR-01",
        ...     "expected_outputs": ["src/fr01.py", "tests/test_fr01.py"]
        ... })
        >>> print(result.passed)
        True
    """
    
    MIN_FILE_SIZE = 100  # bytes
    PYTHON_KEYWORDS = ["import", "class ", "def "]
    
    def __init__(self, repo_path: Path):
        """
        初始化 OutputVerifier
        
        Args:
            repo_path: 專案根目錄
        """
        self.repo_path = Path(repo_path)
        self.parser = TaskOutputParser()
    
    def verify_fr(self, fr_task: Dict[str, Any]) -> VerificationResult:
        """
        驗證單個 FR 的產出
        
        Args:
            fr_task: {
                "fr": "FR-01",
                "expected_outputs": ["src/fr01.py", ...],
                // 或
                "task_text": "..."  # 包含 OUTPUT 段落的 task text
            }
            
        Returns:
            VerificationResult
        """
        fr_id = fr_task.get("fr", "UNKNOWN")
        
        # 解析預期輸出
        if "expected_outputs" in fr_task:
            expected_files = fr_task["expected_outputs"]
        elif "task_text" in fr_task:
            expected_files = self.parser.parse(fr_task["task_text"])
        else:
            return VerificationResult(
                passed=False,
                fr=fr_id,
                errors=["No expected_outputs or task_text provided"]
            )
        
        result = VerificationResult(
            passed=True,
            fr=fr_id,
            checked_files=len(expected_files)
        )
        
        for filepath in expected_files:
            # 轉換為絕對路徑
            if not Path(filepath).is_absolute():
                abs_path = self.repo_path / filepath
            else:
                abs_path = Path(filepath)
            
            # L2a: 檢查存在性
            if not abs_path.exists():
                result.passed = False
                result.errors.append(f"Missing: {filepath}")
                result.missing_files.append(str(abs_path))
                continue
            
            # L2b: 檢查大小
            try:
                size = abs_path.stat().st_size
                if size < self.MIN_FILE_SIZE:
                    result.passed = False
                    result.errors.append(
                        f"Too small ({size} bytes, need >={self.MIN_FILE_SIZE}): {filepath}"
                    )
                    result.small_files.append(str(abs_path))
            except Exception as e:
                result.warnings.append(f"Cannot check size: {filepath}: {e}")
            
            # L2c: 檢查 Python 檔案結構
            if filepath.endswith(".py"):
                try:
                    content = abs_path.read_text()
                    has_code = any(kw in content for kw in self.PYTHON_KEYWORDS)
                    if not has_code:
                        result.passed = False
                        result.errors.append(f"No code found (need one of {self.PYTHON_KEYWORDS}): {filepath}")
                        result.empty_files.append(str(abs_path))
                except Exception as e:
                    result.warnings.append(f"Cannot read content: {filepath}: {e}")
        
        return result
    
    def verify_batch(self, fr_tasks: List[Dict[str, Any]]) -> List[VerificationResult]:
        """
        批次驗證多個 FR
        
        Args:
            fr_tasks: FR 任務列表
            
        Returns:
            驗證結果列表
        """
        return [self.verify_fr(fr_task) for fr_task in fr_tasks]
    
    def get_summary(self, results: List[VerificationResult]) -> Dict[str, Any]:
        """
        取得批次驗證摘要
        
        Args:
            results: 驗證結果列表
            
        Returns:
            {
                "total": int,
                "passed": int,
                "failed": int,
                "pass_rate": float
            }
        """
        total = len(results)
        passed = sum(1 for r in results if r.passed)
        failed = total - passed
        
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / total if total > 0 else 0.0
        }
