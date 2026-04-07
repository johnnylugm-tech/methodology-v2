#!/usr/bin/env python3
"""
Mutation Tester - 變異測試系統

對標 TDAD 的 Semantic Mutation Testing：
- 生成錯誤的程式碼變體
- 測試是否能偵測這些變體
- 量化 mutation score

核心概念：
- 變異操作：替換變數、刪除邏輯、改變條件
- Mutation Score = 偵測到的變體 / 總變體數
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional, Callable
from datetime import datetime
import re
import random

class MutationType(Enum):
    """變異類型"""
    VARIABLE_REPLACE = "variable_replace"    # 變數替換
    CONDITION_FLIP = "condition_flip"        # 條件反轉
    LOGIC_DELETE = "logic_delete"           # 刪除邏輯
    CONSTANT_CHANGE = "constant_change"     # 常數改變
    OPERATOR_SWAP = "operator_swap"         # 操作符交換
    DEAD_CODE = "dead_code"               # 無用程式碼

@dataclass
class Mutation:
    """單一變異"""
    mutation_id: str
    original_code: str
    mutated_code: str
    mutation_type: MutationType
    line_number: int
    description: str

@dataclass
class MutationResult:
    """變異測試結果"""
    mutation: Mutation
    detected: bool
    test_name: str = ""
    execution_time: float = 0.0

class MutationGenerator:
    """
    變異生成器
    
    功能：
    - 讀取原始程式碼
    - 套用變異操作
    - 生成變異體
    """
    
    def __init__(self):
        self.mutations: List[Mutation] = []
    
    def generate(self, code: str, num_mutations: int = 10) -> List[Mutation]:
        """
        生成變異體
        
        Args:
            code: 原始程式碼
            num_mutations: 生成數量
        
        Returns:
            List[Mutation]: 變異體列表
        """
        mutations = []
        lines = code.split('\n')
        
        for i, line in enumerate(lines):
            if len(mutations) >= num_mutations:
                break
            
            # 嘗試各種變異
            mutated = self._try_mutate(line)
            if mutated:
                mutations.append(Mutation(
                    mutation_id=f"mut-{len(mutations)}",
                    original_code=line,
                    mutated_code=mutated,
                    mutation_type=self._detect_type(line),
                    line_number=i + 1,
                    description=self._describe(line, mutated)
                ))
        
        self.mutations.extend(mutations)
        return mutations
    
    def _try_mutate(self, line: str) -> Optional[str]:
        """嘗試變異一行程式碼"""
        mutations = [
            # 條件反轉
            lambda: re.sub(r'if\s+(.+)', lambda m: f'if not ({m.group(1)})', line),
            # 常數改變
            lambda: re.sub(r'\b(\d+)\b', lambda m: str(int(m.group(1)) + 1), line),
            # 布爾反轉
            lambda: line.replace('==', '!=').replace('True', 'False') if '==' in line or 'True' in line else None,
        ]
        
        for mut_fn in mutations:
            try:
                result = mut_fn()
                if result and result != line:
                    return result
            except:
                pass
        return None
    
    def _detect_type(self, line: str) -> MutationType:
        """偵測變異類型"""
        if 'if' in line and any(op in line for op in ['==', '!=', '<', '>']):
            return MutationType.CONDITION_FLIP
        if any(op in line for op in ['+', '-', '*', '/']):
            return MutationType.OPERATOR_SWAP
        if re.search(r'\b\d+\b', line):
            return MutationType.CONSTANT_CHANGE
        return MutationType.LOGIC_DELETE
    
    def _describe(self, original: str, mutated: str) -> str:
        """描述變異"""
        return f"Line {self._detect_type(original).value}: '{original[:30]}...' -> '{mutated[:30]}...'"

class MutationTester:
    """
    變異測試器
    
    功能：
    - 執行變異體
    - 判斷是否被偵測
    - 計算 mutation score
    """
    
    def __init__(self, test_runner: Callable = None):
        """
        初始化
        
        Args:
            test_runner: 測試執行函數 (code -> bool)
        """
        self.test_runner = test_runner or self._default_runner
        self.results: List[MutationResult] = []
    
    def _default_runner(self, code: str) -> bool:
        """預設測試執行：總是通過"""
        return True
    
    def run(self, mutation: Mutation) -> MutationResult:
        """
        執行單一變異測試
        
        Args:
            mutation: 變異體
        
        Returns:
            MutationResult: 測試結果
        """
        start = datetime.now()
        
        # 執行測試
        detected = not self.test_runner(mutation.mutated_code)
        
        execution_time = (datetime.now() - start).total_seconds()
        
        result = MutationResult(
            mutation=mutation,
            detected=detected,
            execution_time=execution_time
        )
        
        self.results.append(result)
        return result
    
    def run_all(self, mutations: List[Mutation]) -> dict:
        """
        執行所有變異測試
        
        Returns:
            dict: 測試摘要
        """
        for mutation in mutations:
            self.run(mutation)
        
        return self.get_summary()
    
    def get_summary(self) -> dict:
        """
        取得測試摘要
        
        Returns:
            dict: {
                total: int,
                detected: int,
                not_detected: int,
                mutation_score: float,  # 0-100%
                by_type: dict,
            }
        """
        total = len(self.results)
        if total == 0:
            return {"total": 0, "mutation_score": 0}
        
        detected = sum(1 for r in self.results if r.detected)
        not_detected = total - detected
        
        by_type = {}
        for result in self.results:
            mt = result.mutation.mutation_type.value
            if mt not in by_type:
                by_type[mt] = {"total": 0, "detected": 0}
            by_type[mt]["total"] += 1
            if result.detected:
                by_type[mt]["detected"] += 1
        
        return {
            "total": total,
            "detected": detected,
            "not_detected": not_detected,
            "mutation_score": round(detected / total * 100, 2),
            "by_type": by_type,
            "results": [
                {
                    "id": r.mutation.mutation_id,
                    "type": r.mutation.mutation_type.value,
                    "detected": r.detected,
                    "line": r.mutation.line_number,
                }
                for r in self.results
            ]
        }

def run_mutation_testing(code: str, test_runner: Callable = None) -> dict:
    """
    便捷函數：執行完整的變異測試
    
    Args:
        code: 原始程式碼
        test_runner: 測試執行函數
    
    Returns:
        dict: 測試報告
    """
    generator = MutationGenerator()
    mutations = generator.generate(code, num_mutations=20)
    
    tester = MutationTester(test_runner)
    summary = tester.run_all(mutations)
    
    return summary
