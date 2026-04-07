"""
Edge Case Generator - 共享的邊界值與錯誤案例生成邏輯

提供類型化的 edge case 生成，供 TestGenerator 和 LLMTestGenerator 共用。
"""

from typing import Any, Dict, List, Optional


# ============================================================================
# Edge Values Pool
# ============================================================================

EDGE_VALUES: Dict[str, List[Any]] = {
    "int": [
        -1,           # 負數
        0,            # 零
        1,            # 正小整數
        42,           # 典型值
        2147483647,   # INT_MAX (32-bit signed)
        -2147483648,  # INT_MIN (32-bit signed)
        2**31,        # 剛好越界
        -2**31 - 1,   # 剛好越界
    ],
    "float": [
        0.0,
        -0.0,
        1.0,
        -1.0,
        float('inf'),
        float('-inf'),
        float('nan'),
        1e-308,       # 最小正規浮點數
        1e308,        # 最大正規浮點數附近
    ],
    "str": [
        "",           # 空字串
        "a",          # 單字元
        "hello",      # 典型英文
        "中文",        # Unicode 中文
        "hello world",# 含空格
        "⚠️ error",   # 特殊符號
        "x" * 100,    # 長字串 (100)
        "x" * 1000,   # 超長字串 (1000)
        " " * 10,     # 空白字串
        "\n\t",       # 控制字元
        "\x00",       # null byte
        "123",        # 數字字串
        "<script>",   # HTML/程式碼注入
        "' OR 1=1--", # SQL 注入
    ],
    "list": [
        [],                    # 空列表
        [None],                # 包含 None
        [1, 2, 3],             # 典型小型列表
        list(range(10)),       # 10 個元素
        list(range(100)),      # 100 個元素
        list(range(1000)),     # 1000 個元素（壓力測試）
        [{}],                  # 嵌套空 dict
        [{"a": 1}],            # 嵌套 dict
        [1, "str", None, True],# 混合類型
        [[1, 2], [3, 4]],      # 嵌套列表
    ],
    "dict": [
        {},                         # 空 dict
        {"key": None},              # None 值
        {"a": 1},                   # 單 key
        {"a": 1, "b": 2},           # 多 key
        {"nested": {"deep": None}}, # 深度嵌套
        {"list": [1, 2, 3]},        # 列表值
        {str(i): i for i in range(100)},  # 100 個 keys
    ],
    "bool": [True, False],
    "None": [None],
    "bytes": [
        b"",
        b"a",
        b"\\x00\\xff",
        b"x" * 1000,
    ],
    "tuple": [
        (),
        (1,),
        (1, 2, 3),
        ("a", "b"),
    ],
    "set": [
        set(),
        {1, 2, 3},
        set(range(100)),
    ],
}


# ============================================================================
# Error Input Templates
# ============================================================================

ERROR_VALUES: Dict[str, List[Any]] = {
    "int": [None, "string", -999999999999, 2**1000],
    "float": [None, "string", 1e1000, -1e1000],
    "str": [None, 123, [], {}],
    "list": [None, "string", {}, 123],
    "dict": [None, "string", [], 123],
    "bool": [None, "string", 1, 0],
    "Any": [None],
}


# ============================================================================
# EdgeCaseGenerator
# ============================================================================

class EdgeCaseGenerator:
    """
    邊界值與錯誤案例生成器
    
    用於根據參數類型生成有意義的測試資料。
    """
    
    def __init__(self, edge_values: Dict[str, List[Any]] = None,
                 error_values: Dict[str, List[Any]] = None):
        self.edge_values = edge_values or EDGE_VALUES
        self.error_values = error_values or ERROR_VALUES
    
    def get_edge_cases(self, param_type: str, count: int = 3) -> List[Any]:
        """
        取得某類型的邊界值案例
        
        Args:
            param_type: 參數類型名稱（如 "int", "str"）
            count: 回傳案例數量上限
            
        Returns:
            List of edge values
        """
        # 萬用型別
        if param_type in ("Any", "object", None):
            return [None, 0, "", [], {}]
        
        edges = self.edge_values.get(param_type, [None])
        
        # 根據 count 截斷，避免產生過多測試案例
        # 策略：頭、中、尾各取一個
        if len(edges) <= count:
            return edges
        
        step = len(edges) // count
        return edges[::step][:count]
    
    def get_error_cases(self, param_type: str) -> List[Any]:
        """
        取得某類型的錯誤輸入案例
        
        Args:
            param_type: 參數類型名稱
            
        Returns:
            List of invalid inputs that should trigger errors
        """
        if param_type in ("Any", "object", None):
            return self.error_values.get("Any", [None])
        return self.error_values.get(param_type, [None])
    
    def get_all_cases_for_param(self, param_type: str) -> Dict[str, List[Any]]:
        """
        取得某參數類型的完整案例集（基本 + 邊界 + 錯誤）
        
        Returns:
            Dict with keys: basic, edges, errors
        """
        # 基本案例（每類型一個代表性值）
        basic = {
            "int": 42,
            "float": 3.14,
            "str": "test",
            "list": [1, 2, 3],
            "dict": {"key": "value"},
            "bool": True,
            "None": None,
            "Any": None,
        }.get(param_type, None)
        
        return {
            "basic": [basic] if basic is not None else [],
            "edges": self.get_edge_cases(param_type, count=5),
            "errors": self.get_error_cases(param_type),
        }
    
    def generate_test_matrix(self, params: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        根據多個參數生成測試矩陣（笛卡爾積）
        
        會產生所有參數組合，但為了避免爆炸會限制數量。
        
        Args:
            params: [{"name": "x", "type": "int"}, ...]
            
        Returns:
            List of test cases {"name": "...", "params": {...}}
        """
        import itertools
        
        cases_per_param = []
        names = []
        
        for p in params:
            ptype = p.get("type", "Any")
            edges = self.get_edge_cases(ptype, count=3)
            cases_per_param.append(edges)
            names.append(p["name"])
        
        # 限制總案例數（最多 27 = 3^3，否則只取前 10 組合）
        all_combinations = list(itertools.product(*cases_per_param))
        
        if len(all_combinations) > 10:
            # 取均勻分布的樣本
            step = len(all_combinations) // 10
            all_combinations = all_combinations[::step][:10]
        
        result = []
        for i, combo in enumerate(all_combinations):
            result.append({
                "name": f"matrix_{i}",
                "params": dict(zip(names, combo))
            })
        
        return result


# ============================================================================
# Quick Access Functions
# ============================================================================

def get_edge_values_for_type(param_type: str) -> List[Any]:
    """快速取得某類型的邊界值"""
    return EdgeCaseGenerator().get_edge_cases(param_type)


def get_error_values_for_type(param_type: str) -> List[Any]:
    """快速取得某類型的錯誤輸入"""
    return EdgeCaseGenerator().get_error_cases(param_type)
