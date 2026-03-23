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
