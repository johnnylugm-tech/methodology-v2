"""
LLM Test Generator - AI 驅動的測試生成器

使用 LLM 分析代碼結構、提取不變量、生成有意義的測試套件。

HR-17 合規：所有 AI 生成測試必須標記 `# AI-GENERATED - REVIEW REQUIRED`
"""

import json
import re
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field

# 嘗試從 parent directory 引入 provider_abstraction
# 如果失敗則使用本地 mock
try:
    import sys
    from pathlib import Path
    skill_root = Path(__file__).parent.parent.parent.parent
    if str(skill_root) not in sys.path:
        sys.path.insert(0, str(skill_root))
    from provider_abstraction import BaseProvider
except ImportError:
    # Fallback: 建立 mock BaseProvider
    from abc import ABC, abstractmethod
    class BaseProvider(ABC):
        @abstractmethod
        def chat(self, messages: List[Dict], **kwargs) -> str:
            pass


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class EdgeCaseHypothesis:
    """Edge case 假設"""
    input_repr: str          # 輸入的程式碼表示
    reason: str              # 為什麼這個是 edge case
    expected_behavior: str   # 預期行為
    severity: str = "medium" # low / medium / high


@dataclass
class Invariant:
    """不變量（Invariant）"""
    property_name: str       # 屬性描述
    test_strategy: str       # 如何測試這個屬性
    examples: List[str]      # 具體例子
    code_snippet: str = ""   # 測試用的程式碼片段


@dataclass
class ErrorHandling:
    """錯誤處理假設"""
    condition: str           # 觸發條件
    expected_exception: str  # 預期異常類型
    description: str = ""


@dataclass
class CodeAnalysis:
    """LLM 代碼分析結果"""
    modules: List[str] = field(default_factory=list)
    apis: List[Dict] = field(default_factory=list)
    models: List[Dict] = field(default_factory=list)
    edge_case_hypotheses: List[EdgeCaseHypothesis] = field(default_factory=list)
    invariants: List[Invariant] = field(default_factory=list)
    error_handling: List[ErrorHandling] = field(default_factory=list)
    raw_json: str = ""  # 保留原始 JSON 供審查


@dataclass
class GeneratedTestCase:
    """產生的測試用例"""
    name: str
    description: str
    code: str  # 完整的測試程式碼
    tags: List[str] = field(default_factory=list)
    is_ai_generated: bool = True  # HR-17 標記
    llm_model: str = ""


# ============================================================================
# Prompts
# ============================================================================

INVARIANT_EXTRACTION_PROMPT = """你是測試工程師。分析以下代碼，找出：
1. 所有可能的 edge cases（input validation, boundary conditions）
2. 所有保持不變的 properties（e.g., "排序後的元素數量不變"）
3. 所有錯誤處理的假設（什麼情況會拋異常）

{context_block}

程式碼：
```{language}
{code}
```

輸出 JSON（嚴格 JSON，無 markdown 包裝）：
{{
  "edge_cases": [
    {{
      "input": "代碼表示，如 x=0, s=\\"\\"",
      "reason": "為什麼這是 edge case",
      "expected": "預期行為描述",
      "severity": "low|medium|high"
    }}
  ],
  "invariants": [
    {{
      "property": "不變的屬性描述",
      "test_strategy": "如何測試（e.g., compare len before and after）",
      "examples": ["具體例子1", "例子2"]
    }}
  ],
  "error_handling": [
    {{
      "condition": "觸發條件",
      "expected_exception": "預期異常類型（如 ValueError）"
    }}
  ]
}}
"""


CODE_STRUCTURE_PROMPT = """你是架構分析師。分析以下代碼，輸出結構化描述：

程式碼：
```{language}
{code}
```

輸出 JSON（嚴格 JSON，無 markdown 包裝）：
{{
  "modules": ["module1", "module2"],
  "apis": [
    {{
      "name": "function_name",
      "params": ["param1:type", "param2:type"],
      "return_type": "ReturnType",
      "description": "功能描述"
    }}
  ],
  "models": [
    {{
      "name": "ClassName",
      "fields": ["field1:type", "field2:type"],
      "description": "模型描述"
    }}
  ]
}}
"""


# ============================================================================
# LLM Test Generator
# ============================================================================

class LLMTestGenerator:
    """
    AI-powered 測試生成器
    
    使用 LLM 分析代碼結構、提取不變量、生成有意義的測試套件。
    """
    
    def __init__(self, provider: BaseProvider, model: str = None):
        """
        Args:
            provider: BaseProvider 實例（Anthropic/OpenAI/GLM）
            model: 可選，指定模型
        """
        self.provider = provider
        self.model = model
    
    def analyze_code_structure(self, source_code: str,
                                 context: Dict[str, str] = None) -> CodeAnalysis:
        """
        用 LLM 分析代碼結構
        
        Args:
            source_code: Python 原始碼
            context: 可選上下文（如 {"file_path": "...", "language": "python"}）
            
        Returns:
            CodeAnalysis: 結構化分析結果
        """
        language = context.get("language", "python") if context else "python"
        file_path = context.get("file_path", "unknown") if context else "unknown"
        
        messages = [
            {
                "role": "user",
                "content": CODE_STRUCTURE_PROMPT.format(
                    language=language,
                    code=source_code
                )
            }
        ]
        
        try:
            response = self.provider.chat(messages, model=self.model)
            analysis = self._parse_structure_response(response)
            return analysis
        except Exception as e:
            # Fallback: 回傳空分析
            return CodeAnalysis(raw_json=str(e))
    
    def extract_invariants(self, source_code: str,
                           context: Dict[str, str] = None) -> List[Invariant]:
        """
        用 LLM 提取不變量（Invariant）
        
        Args:
            source_code: Python 原始碼
            context: 可選上下文
            
        Returns:
            List[Invariant]: 不變量列表
        """
        language = context.get("language", "python") if context else "python"
        context_block = ""
        if context:
            context_block = "\\n".join(f"# {k}: {v}" for k, v in context.items())
        
        messages = [
            {
                "role": "user",
                "content": INVARIANT_EXTRACTION_PROMPT.format(
                    language=language,
                    code=source_code,
                    context_block=context_block
                )
            }
        ]
        
        try:
            response = self.provider.chat(messages, model=self.model)
            invariants = self._parse_invariants_response(response)
            return invariants
        except Exception as e:
            return []
    
    def generate_test_suite(self, source_code: str,
                            artifacts: Dict[str, Any] = None) -> List[GeneratedTestCase]:
        """
        生成完整測試套件
        
        結合 code structure 分析 + invariant extraction + edge cases
        
        Args:
            source_code: Python 原始碼
            artifacts: 可選，前期分析結果（如已呼叫過 analyze_code_structure）
            
        Returns:
            List[GeneratedTestCase]: 測試用例列表
        """
        artifacts = artifacts or {}
        
        # 1. 分析代碼結構（若未提供）
        if "structure" not in artifacts:
            structure = self.analyze_code_structure(source_code)
        else:
            structure = artifacts["structure"]
        
        # 2. 提取不變量（若未提供）
        if "invariants" not in artifacts:
            invariants = self.extract_invariants(source_code)
        else:
            invariants = artifacts["invariants"]
        
        # 3. 產生測試用例
        test_cases = []
        
        # 3a. 基於結構的測試
        for api in structure.apis:
            tc = self._generate_api_test(api, invariants)
            if tc:
                test_cases.append(tc)
        
        # 3b. 基於不變量的測試
        for invariant in invariants:
            tc = self._generate_invariant_test(invariant)
            if tc:
                test_cases.append(tc)
        
        # 3c. Edge case 測試（從 LLM 建議的 edge cases）
        for ec in structure.edge_case_hypotheses:
            tc = self._generate_edge_case_test(ec)
            if tc:
                test_cases.append(tc)
        
        # 3d. 錯誤處理測試
        for eh in structure.error_handling:
            tc = self._generate_error_handling_test(eh)
            if tc:
                test_cases.append(tc)
        
        return test_cases
    
    def _generate_api_test(self, api: Dict, invariants: List[Invariant]) -> GeneratedTestCase:
        """為一個 API 產生測試"""
        name = api.get("name", "unknown")
        params = api.get("params", [])
        return_type = api.get("return_type", "Any")
        
        # 建構參數代碼
        param_lines = []
        param_names = []
        for p in params:
            if ":" in p:
                pname, ptype = p.rsplit(":", 1)
                pname = pname.strip()
                ptype = ptype.strip()
                default_val = self._type_to_default_value(ptype)
                param_lines.append(f"    {pname} = {default_val}  # type: {ptype}")
                param_names.append(pname)
            else:
                pname = p.strip()
                param_lines.append(f"    {pname} = None")
                param_names.append(pname)
        
        param_str = ", ".join(param_names)
        description = api.get("description", f"API: {name}")
        
        code = f'''\"\"\"
AI-GENERATED - REVIEW REQUIRED
Test for API: {name}
\"\"\"

import pytest

def test_{name}():
    \"\"\"
    Description: {description}
    \"\"\"
    # 參數準備
{chr(10).join(param_lines)}

    # 呼叫 API
    result = {name}({param_str})

    # HR-17: AI 生成測試，人工審查後啟用
    # 基本斷言 - 根據 return_type 調整
    # assert result is not None
'''

        return GeneratedTestCase(
            name=f"test_{name}",
            description=description,
            code=code,
            tags=["api", "ai-generated"],
            is_ai_generated=True,
            llm_model=self.model or "unknown"
        )
    
    def _generate_invariant_test(self, invariant: Invariant) -> GeneratedTestCase:
        """為一個不變量產生測試"""
        property_name = invariant.property_name
        test_strategy = invariant.test_strategy
        
        code = f'''\"\"\"
AI-GENERATED - REVIEW REQUIRED
Test for Invariant: {property_name}
Test Strategy: {test_strategy}
\"\"\"

import pytest

def test_invariant_{self._sanitize_name(property_name)}():
    \"\"\"
    Property: {property_name}
    Strategy: {test_strategy}
    
    Examples:
{chr(10).join(f"    - {ex}" for ex in invariant.examples)}
    \"\"\"
    # TODO: 根據 test_strategy 實作
    # HR-17: AI 生成測試，人工審查後啟用
    pass
'''

        return GeneratedTestCase(
            name=f"test_invariant_{self._sanitize_name(property_name)}",
            description=f"Invariant: {property_name}",
            code=code,
            tags=["invariant", "ai-generated"],
            is_ai_generated=True,
            llm_model=self.model or "unknown"
        )
    
    def _generate_edge_case_test(self, ec: EdgeCaseHypothesis) -> GeneratedTestCase:
        """為一個 edge case 產生測試"""
        code = f'''\"\"\"
AI-GENERATED - REVIEW REQUIRED
Edge Case: {ec.input_repr}
Reason: {ec.reason}
Expected: {ec.expected_behavior}
Severity: {ec.severity}
\"\"\"

import pytest

def test_edge_{self._sanitize_name(ec.input_repr)}():
    \"\"\"
    Input: {ec.input_repr}
    Reason: {ec.reason}
    Expected Behavior: {ec.expected_behavior}
    Severity: {ec.severity}
    \"\"\"
    # TODO: 實作 edge case 測試
    # HR-17: AI 生成測試，人工審查後啟用
    pass
'''

        return GeneratedTestCase(
            name=f"test_edge_{self._sanitize_name(ec.input_repr)}",
            description=f"Edge case: {ec.reason}",
            code=code,
            tags=["edge-case", "ai-generated"],
            is_ai_generated=True,
            llm_model=self.model or "unknown"
        )
    
    def _generate_error_handling_test(self, eh: ErrorHandling) -> GeneratedTestCase:
        """為錯誤處理產生測試"""
        code = f'''\"\"\"
AI-GENERATED - REVIEW REQUIRED
Error Handling Test
Condition: {eh.condition}
Expected Exception: {eh.expected_exception}
Description: {eh.description}
\"\"\"

import pytest

def test_error_{self._sanitize_name(eh.condition)}():
    \"\"\"
    Condition: {eh.condition}
    Expected: {eh.expected_exception}
    Description: {eh.description}
    \"\"\"
    # HR-17: AI 生成測試，人工審查後啟用
    with pytest.raises({eh.expected_exception}):
        # TODO: 觸發錯誤條件
        pass
'''

        return GeneratedTestCase(
            name=f"test_error_{self._sanitize_name(eh.condition)}",
            description=f"Error: {eh.condition}",
            code=code,
            tags=["error-handling", "ai-generated"],
            is_ai_generated=True,
            llm_model=self.model or "unknown"
        )
    
    def _type_to_default_value(self, type_hint: str) -> str:
        """將類型提示轉換為預設值"""
        type_hint = type_hint.lower().strip()
        if "int" in type_hint:
            return "0"
        elif "float" in type_hint:
            return "0.0"
        elif "str" in type_hint:
            return "''"
        elif "bool" in type_hint:
            return "False"
        elif "list" in type_hint or "array" in type_hint:
            return "[]"
        elif "dict" in type_hint or "map" in type_hint:
            return "{}"
        elif "optional" in type_hint:
            return "None"
        else:
            return "None"
    
    def _sanitize_name(self, name: str) -> str:
        """將字串轉為合法的 Python 識別符"""
        # 移除不合法的字元
        s = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        # 確保不是數字開頭
        if s and s[0].isdigit():
            s = '_' + s
        # 限制長度
        return s[:50]
    
    def _parse_structure_response(self, response: str) -> CodeAnalysis:
        """解析 LLM 回應（結構分析）"""
        # 嘗試從 response 中提取 JSON
        json_str = self._extract_json(response)
        
        try:
            data = json.loads(json_str) if json_str else {}
        except json.JSONDecodeError:
            data = {}
        
        # 建構 CodeAnalysis
        modules = data.get("modules", [])
        apis = data.get("apis", [])
        models = data.get("models", [])
        
        # 從 apis 提取 edge_case_hypotheses（如果 LLM 有提供）
        edge_cases = []
        for api in apis:
            # 如果 API 文件中有提到 edge cases，加入
            desc = api.get("description", "")
            if "edge" in desc.lower() or "boundary" in desc.lower():
                edge_cases.append(EdgeCaseHypothesis(
                    input_repr=f"API: {api['name']}",
                    reason=desc,
                    expected_behavior="see description",
                    severity="medium"
                ))
        
        return CodeAnalysis(
            modules=modules,
            apis=apis,
            models=models,
            edge_case_hypotheses=edge_cases,
            raw_json=json_str
        )
    
    def _parse_invariants_response(self, response: str) -> List[Invariant]:
        """解析 LLM 回應（不變量提取）"""
        json_str = self._extract_json(response)
        
        try:
            data = json.loads(json_str) if json_str else {}
        except json.JSONDecodeError:
            return []
        
        invariants = []
        for item in data.get("invariants", []):
            invariants.append(Invariant(
                property_name=item.get("property", "unknown"),
                test_strategy=item.get("test_strategy", ""),
                examples=item.get("examples", [])
            ))
        
        return invariants
    
    def _extract_json(self, text: str) -> str:
        """
        從 LLM 回應中提取 JSON 區塊
        
        嘗試多種策略：
        1. 找 ```json ... ``` 區塊
        2. 找 ``` ... ``` 區塊
        3. 直接返回原文字（讓 json.loads 處理）
        """
        # 移除 markdown code block
        patterns = [
            r'```json\s*(.*?)\s*```',
            r'```\s*(.*?)\s*```',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return text.strip()
