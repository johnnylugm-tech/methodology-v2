#!/usr/bin/env python3
"""
Quality Gate 輸出解析模組
功能：解析 doc_checker.py、constitution runner.py 的輸出，提取關鍵指標
"""

import re
import json
from typing import Dict, Any, Optional, List
from pathlib import Path


class QualityGateParser:
    """Quality Gate 輸出解析器"""
    
    def __init__(self):
        self.last_parse_result = None
        
    def parse_doc_checker(self, output: str) -> Dict[str, Any]:
        """
        解析 doc_checker.py 輸出
        
        Args:
            output: 命令輸出文字
            
        Returns:
            {"compliance_rate": 87.5, "passed_phases": 7, "total_phases": 8, "details": [...]}
        """
        result = {
            "tool": "doc_checker",
            "raw_output": output[:500],
            "compliance_rate": 0,
            "passed": False,
            "details": []
        }
        
        # 解析合規率
        match = re.search(r'Compliance Rate[:\s]+(\d+\.?\d*)%?', output, re.IGNORECASE)
        if match:
            result["compliance_rate"] = float(match.group(1))
        
        # 解析通過的 Phase 數量
        match = re.search(r'(\d+)/(\d+)\s*(phases?|steps?|items?)', output, re.IGNORECASE)
        if match:
            result["passed_phases"] = int(match.group(1))
            result["total_phases"] = int(match.group(2))
        
        # 解析 PASSED/FAILED
        if "passed" in output.lower() or "100%" in output:
            result["passed"] = True
        elif "failed" in output.lower():
            result["passed"] = False
            
        # 解析詳細項目
        lines = output.split('\n')
        for line in lines:
            if '✅' in line or '❌' in line or 'PASS' in line or 'FAIL' in line:
                result["details"].append(line.strip())
        
        self.last_parse_result = result
        return result
    
    def parse_constitution(self, output: str) -> Dict[str, Any]:
        """
        解析 constitution runner.py 輸出
        
        Args:
            output: 命令輸出文字
            
        Returns:
            {"score": 85, "dimensions": {"正確性": 100, "安全性": 100, "可維護性": 75, "測試覆蓋率": 80}}
        """
        result = {
            "tool": "constitution",
            "raw_output": output[:500],
            "score": 0,
            "passed": False,
            "dimensions": {}
        }
        
        # 解析總分
        match = re.search(r'(\d+)/100', output)
        if match:
            result["score"] = int(match.group(1))
        
        # 如果沒有 /100 格式，嘗試其他方式
        if result["score"] == 0:
            match = re.search(r'score[:\s]+(\d+)', output, re.IGNORECASE)
            if match:
                result["score"] = int(match.group(1))
        
        # 解析維度分數
        dimension_patterns = [
            (r'正確性[:\s]+(\d+)%?', '正確性'),
            (r'安全性[:\s]+(\d+)%?', '安全性'),
            (r'可維護性[:\s]+(\d+)%?', '可維護性'),
            (r'測試覆蓋率[:\s]+(\d+)%?', '測試覆蓋率'),
            (r'correctness[:\s]+(\d+)%?', 'Correctness'),
            (r'security[:\s]+(\d+)%?', 'Security'),
            (r'maintainability[:\s]+(\d+)%?', 'Maintainability'),
            (r'coverage[:\s]+(\d+)%?', 'Coverage'),
        ]
        
        for pattern, name in dimension_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                result["dimensions"][name] = int(match.group(1))
        
        # 判斷是否通過（默認 70 分）
        if result["score"] >= 70:
            result["passed"] = True
        elif result["score"] > 0:
            result["passed"] = False
            
        self.last_parse_result = result
        return result
    
    def parse_spec_track(self, output: str) -> Dict[str, Any]:
        """
        解析 spec-track check 輸出
        
        Args:
            output: 命令輸出文字
            
        Returns:
            {"completeness": 90, "missing": [...], "passed": True}
        """
        result = {
            "tool": "spec_track",
            "raw_output": output[:500],
            "completeness": 0,
            "passed": False,
            "missing": []
        }
        
        # 解析完整性
        match = re.search(r'(\d+\.?\d*)%', output)
        if match:
            result["completeness"] = float(match.group(1))
        
        # 解析缺失的項目
        missing_patterns = [
            r'missing[:\s]+\[([^\]]+)\]',
            r'not found[:\s]+(.+)',
            r'缺失[:\s]+(.+)'
        ]
        
        for pattern in missing_patterns:
            match = re.search(pattern, output, re.IGNORECASE)
            if match:
                result["missing"] = [item.strip() for item in match.group(1).split(',')]
        
        # 判斷是否通過（默認 90%）
        if result["completeness"] >= 90:
            result["passed"] = True
        elif result["completeness"] > 0:
            result["passed"] = False
            
        self.last_parse_result = result
        return result
    
    def parse_enforcement(self, output: str) -> Dict[str, Any]:
        """
        解析 enforcement 輸出
        
        Args:
            output: 命令輸出文字
            
        Returns:
            {"has_block": False, "has_warn": False, "items": [...]}
        """
        result = {
            "tool": "enforcement",
            "raw_output": output[:500],
            "has_block": False,
            "has_warn": False,
            "passed": True,
            "items": []
        }
        
        # 解析 BLOCK 項目
        if "BLOCK" in output:
            result["has_block"] = True
            result["passed"] = False
            
            block_matches = re.findall(r'\[BLOCK\]([^\n]+)', output)
            for item in block_matches:
                result["items"].append({"type": "BLOCK", "message": item.strip()})
        
        # 解析 WARN 項目
        if "WARN" in output:
            result["has_warn"] = True
            
            warn_matches = re.findall(r'\[WARN\]([^\n]+)', output)
            for item in warn_matches:
                result["items"].append({"type": "WARN", "message": item.strip()})
        
        # 如果有 PASSED 或無 BLOCK/WARN，則通過
        if "passed" in output.lower() or "✅" in output:
            result["passed"] = True
            
        self.last_parse_result = result
        return result
    
    def parse(self, output: str, tool_type: str) -> Dict[str, Any]:
        """
        通用解析接口
        
        Args:
            output: 命令輸出文字
            tool_type: "doc_checker" / "constitution" / "spec_track" / "enforcement"
            
        Returns:
            解析後的結果
        """
        if tool_type == "doc_checker":
            return self.parse_doc_checker(output)
        elif tool_type == "constitution":
            return self.parse_constitution(output)
        elif tool_type == "spec_track":
            return self.parse_spec_track(output)
        elif tool_type == "enforcement":
            return self.parse_enforcement(output)
        else:
            return {"error": f"Unknown tool_type: {tool_type}"}
    
    def to_json(self, result: Dict[str, Any]) -> str:
        """轉換為 JSON"""
        return json.dumps(result, indent=2, ensure_ascii=False)


# 全域實例
parser = QualityGateParser()


# 便捷函數
def parse_qg_output(output: str, tool_type: str) -> Dict[str, Any]:
    """快速解析 Quality Gate 輸出"""
    return parser.parse(output, tool_type)


# 測試
if __name__ == "__main__":
    print("=== QualityGateParser 測試 ===")
    
    # 測試 Constitution 解析
    test_output = """
    ===== Constitution Check Results =====
    正確性: 100%
    安全性: 100%
    可維護性: 75%
    測試覆蓋率: 80%
    總分: 88/100
    PASSED
    """
    
    result = parse_qg_output(test_output, "constitution")
    print(f"\nConstitution 解析結果:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    # 測試 DOC Checker 解析
    test_output2 = """
    ASPICE Compliance Check
    Compliance Rate: 87.5%
    Passed: 7/8 phases
    PASSED
    """
    
    result2 = parse_qg_output(test_output2, "doc_checker")
    print(f"\nDoc Checker 解析結果:")
    print(json.dumps(result2, indent=2, ensure_ascii=False))
    
    print("\n✅ QualityGateParser 測試完成")