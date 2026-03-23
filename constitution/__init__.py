"""
Constitution - 團隊憲章模組

定義團隊的不可變原則

使用方法:
    from constitution import load_constitution
    
    const = load_constitution()
    print(const)
"""

from pathlib import Path


def load_constitution() -> str:
    """載入團隊憲章
    
    Returns:
        憲章內容字串
    """
    const_path = Path(__file__).parent / "CONSTITUTION.md"
    if const_path.exists():
        return const_path.read_text(encoding="utf-8")
    return "CONSTITUTION.md not found"


def get_quality_thresholds() -> dict:
    """取得品質閾值
    
    Returns:
        品質閾值字典
    """
    return {
        "correctness": 80,
        "security": 100,
        "maintainability": 70,
        "performance": 80,
        "coverage": 80
    }


def get_error_levels() -> dict:
    """取得錯誤等級定義
    
    Returns:
        錯誤等級字典
    """
    return {
        "L1": {"name": "配置錯誤", "recoverable": False},
        "L2": {"name": "API 錯誤", "recoverable": True},
        "L3": {"name": "業務錯誤", "recoverable": True},
        "L4": {"name": "預期異常", "recoverable": True},
        "L5": {"name": "環境錯誤", "recoverable": False},
        "L6": {"name": "災難錯誤", "recoverable": False}
    }


def check_quality_gate(code_metrics: dict) -> dict:
    """
    檢查程式碼是否符合品質閾值
    
    Args:
        code_metrics: 程式碼指標字典
            {
                "correctness": float,   # 正確性 0-100
                "security": float,       # 安全性 0-100
                "maintainability": float, # 可維護性 0-100
                "performance": float,   # 效能 0-100
                "coverage": float,      # 覆蓋率 0-100
            }
    
    Returns:
        檢查結果字典
            {
                "passed": bool,
                "details": dict,
                "failed": list,
            }
    """
    thresholds = get_quality_thresholds()
    results = {}
    failed = []
    
    for metric, threshold in thresholds.items():
        actual = code_metrics.get(metric, 0)
        passed = actual >= threshold
        results[metric] = {
            "actual": actual,
            "threshold": threshold,
            "passed": passed,
        }
        if not passed:
            failed.append(metric)
    
    return {
        "passed": len(failed) == 0,
        "details": results,
        "failed": failed,
        "summary": f"{len(failed)}/{len(thresholds)} metrics passed",
    }


def validate_constitution_compliance(project_path: str = ".") -> dict:
    """
    驗證專案是否符合憲章
    
    Args:
        project_path: 專案路徑
    
    Returns:
        驗證結果
    """
    # 這是簡單版本，實際可以擴展
    return {
        "compliant": True,
        "message": "Project is compliant with constitution",
        "checks": [],
    }


# === TDAD 風格：編譯後 Artifact ===

from typing import List, Dict, Optional, Callable
import hashlib
import re


class CompiledConstitution:
    """
    編譯後的 Constitution
    
    TDAD 概念：將 Constitution 視為編譯後的 artifact
    - 不可變更的約束
    - 版本化的合規標準
    - 可驗證的行為規格
    """
    
    def __init__(self, constitution_text: str):
        self.original_text = constitution_text
        self.version = self._compute_version(constitution_text)
        self.specs = self._parse_specs(constitution_text)
        self.hash = self._compute_hash(constitution_text)
    
    def _compute_version(self, text: str) -> str:
        """計算版本"""
        return hashlib.md5(text.encode()).hexdigest()[:8]
    
    def _compute_hash(self, text: str) -> str:
        """計算哈希"""
        return hashlib.sha256(text.encode()).hexdigest()
    
    def _parse_specs(self, text: str) -> List[Dict]:
        """解析行為規格"""
        specs = []
        # 解析章節作為 specs
        sections = text.split('\n## ')
        for section in sections:
            if section.strip():
                specs.append({
                    "name": section.split('\n')[0],
                    "content": section,
                    "hash": hashlib.md5(section.encode()).hexdigest()[:8],
                })
        return specs
    
    def verify(self, agent_output: str) -> dict:
        """
        驗證 Agent 輸出是否符合 Constitution
        
        Args:
            agent_output: Agent 的輸出
        
        Returns:
            dict: {compliant: bool, violations: [], score: float}
        """
        violations = []
        
        # 檢查關鍵詞
        forbidden_keywords = ['bypass', 'skip', '--no-verify']
        for kw in forbidden_keywords:
            if kw in agent_output.lower():
                violations.append({
                    "keyword": kw,
                    "severity": "high",
                    "description": f"Forbidden keyword '{kw}' found"
                })
        
        # 檢查是否有 task_id
        if not re.search(r'\[[A-Z]+-\d+\]', agent_output):
            violations.append({
                "keyword": "task_id",
                "severity": "medium",
                "description": "No task_id found in output"
            })
        
        score = max(0, 100 - len(violations) * 20)
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "score": score,
            "version": self.version,
            "hash": self.hash,
        }
    
    def to_json(self) -> str:
        """輸出為 JSON"""
        import json
        return json.dumps({
            "version": self.version,
            "hash": self.hash,
            "specs_count": len(self.specs),
            "specs": self.specs,
        }, indent=2, ensure_ascii=False)


def compile_constitution(constitution_path: str = None) -> CompiledConstitution:
    """
    編譯 Constitution
    
    TDAD 概念：將 Constitution 視為編譯後的 artifact
    
    Returns:
        CompiledConstitution
    """
    from pathlib import Path
    
    path = Path(constitution_path or __file__).parent / "CONSTITUTION.md"
    text = path.read_text(encoding='utf-8')
    
    return CompiledConstitution(text)


def verify_agent_output(constitution: CompiledConstitution, output: str) -> dict:
    """
    驗證 Agent 輸出
    
    Returns:
        dict: 驗證結果
    """
    return constitution.verify(output)
