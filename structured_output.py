#!/usr/bin/env python3
"""
Structured Output Engine

提供：
- 結構化輸出驗證 (JSON Schema)
- 自動重試 + fallback
- 輸出穩定性追蹤
- 多格式支援 (JSON/YAML/Markdown)
- Agent Output Validator 整合
"""

import re
import json
import time
import hashlib
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable, Union
from enum import Enum
from datetime import datetime

# Agent Output Validator 整合
try:
    from agent_output_validator import AgentOutputValidator, ValidationReport as AOVReport
    VALIDATOR_AVAILABLE = True
except ImportError:
    VALIDATOR_AVAILABLE = False


class OutputFormat(Enum):
    """輸出格式"""
    JSON = "json"
    YAML = "yaml"
    MARKDOWN = "markdown"
    TEXT = "text"
    AUTO = "auto"


class ParseStrategy(Enum):
    """解析策略"""
    DIRECT = "direct"           # 直接解析
    REGEX_EXTRACT = "regex"    # 正則提取
    REPAIR = "repair"          # 修復後解析
    RETRY = "retry"            # 重試
    FALLBACK = "fallback"      # 回退


@dataclass
class OutputSchema:
    """輸出結構定義"""
    name: str
    description: str = ""
    
    # 欄位定義
    fields: Dict[str, "FieldDefinition"] = field(default_factory=dict)
    
    # 驗證規則
    required_fields: List[str] = field(default_factory=list)
    custom_validators: List[Callable] = field(default_factory=list)
    
    def validate(self, data: Dict) -> "ValidationResult":
        """驗證資料"""
        result = ValidationResult()
        
        for field_name, field_def in self.fields.items():
            value = data.get(field_name)
            
            # Required check
            if field_name in self.required_fields and value is None:
                result.add_error(field_name, "Required field is missing")
                continue
            
            # Type check
            if value is not None and field_def.field_type:
                if not isinstance(value, field_def.field_type):
                    result.add_error(
                        field_name, 
                        f"Expected {field_def.field_type.__name__}, got {type(value).__name__}"
                    )
                    continue
            
            # Pattern check
            if value and field_def.pattern:
                if not re.match(field_def.pattern, str(value)):
                    result.add_error(
                        field_name,
                        f"Does not match pattern: {field_def.pattern}"
                    )
            
            # Enum check
            if value and field_def.enum_values:
                if value not in field_def.enum_values:
                    result.add_error(
                        field_name,
                        f"Value must be one of: {field_def.enum_values}"
                    )
            
            # Range check
            if value is not None:
                if field_def.min_value is not None and value < field_def.min_value:
                    result.add_error(field_name, f"Value must be >= {field_def.min_value}")
                if field_def.max_value is not None and value > field_def.max_value:
                    result.add_error(field_name, f"Value must be <= {field_def.max_value}")
        
        result.valid = len(result.errors) == 0
        return result


@dataclass
class FieldDefinition:
    """欄位定義"""
    name: str
    field_type: type = None
    
    # 驗證
    pattern: str = None
    enum_values: List[Any] = None
    min_value: float = None
    max_value: float = None
    
    # 描述
    description: str = ""
    example: Any = None


@dataclass
class ValidationResult:
    """驗證結果"""
    valid: bool = True
    errors: Dict[str, List[str]] = field(default_factory=dict)
    warnings: Dict[str, List[str]] = field(default_factory=dict)
    
    def add_error(self, field: str, message: str):
        self.valid = False
        if field not in self.errors:
            self.errors[field] = []
        self.errors[field].append(message)
    
    def add_warning(self, field: str, message: str):
        if field not in self.warnings:
            self.warnings[field] = []
        self.warnings[field].append(message)
    
    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "errors": self.errors,
            "warnings": self.warnings
        }


@dataclass
class ParseResult:
    """解析結果"""
    success: bool
    data: Any = None
    raw_output: str = ""
    
    # 解析過程
    strategy_used: ParseStrategy = None
    attempts: int = 0
    parse_time_ms: float = 0.0
    
    # 錯誤
    error: str = None
    error_type: str = None
    fallback_used: bool = False
    
    # 驗證
    validation: ValidationResult = None
    
    # 指標
    timestamp: datetime = field(default_factory=datetime.now)
    
    @property
    def is_valid(self) -> bool:
        return self.success and (self.validation is None or self.validation.valid)


class StructuredOutputEngine:
    """結構化輸出引擎"""
    
    def __init__(self):
        self.schemas: Dict[str, OutputSchema] = {}
        self.parse_history: List[ParseResult] = []
        self.stats: Dict[str, int] = {
            "total": 0,
            "success": 0,
            "fallback": 0,
            "failed": 0
        }
        
        # 預設 schema
        self._register_defaults()
    
    def _register_defaults(self):
        """註冊預設 schema"""
        # User Info Schema
        user_schema = OutputSchema(
            name="user_info",
            description="User information extraction",
            fields={
                "id": FieldDefinition("id", int, description="User ID"),
                "name": FieldDefinition("name", str, description="Full name"),
                "email": FieldDefinition("email", str, pattern=r"^[\w.-]+@[\w.-]+\.\w+$", description="Email address"),
                "role": FieldDefinition("role", str, enum_values=["admin", "user", "guest"], description="User role"),
            },
            required_fields=["id", "email"]
        )
        self.schemas["user_info"] = user_schema
        
        # Task Schema
        task_schema = OutputSchema(
            name="task",
            description="Task information",
            fields={
                "id": FieldDefinition("id", str, description="Task ID"),
                "title": FieldDefinition("title", str, description="Task title"),
                "status": FieldDefinition("status", str, enum_values=["todo", "in_progress", "done"], description="Task status"),
                "priority": FieldDefinition("priority", int, min_value=1, max_value=5, description="Priority (1-5)"),
                "assignee": FieldDefinition("assignee", str, description="Assignee name"),
                "tags": FieldDefinition("tags", list, description="Task tags"),
            },
            required_fields=["id", "title"]
        )
        self.schemas["task"] = task_schema
        
        # Analysis Schema
        analysis_schema = OutputSchema(
            name="analysis",
            description="Analysis result",
            fields={
                "summary": FieldDefinition("summary", str, description="Summary text"),
                "sentiment": FieldDefinition("sentiment", str, enum_values=["positive", "neutral", "negative"], description="Sentiment"),
                "confidence": FieldDefinition("confidence", float, min_value=0.0, max_value=1.0, description="Confidence score"),
                "entities": FieldDefinition("entities", list, description="Extracted entities"),
                "categories": FieldDefinition("categories", list, description="Categories"),
            },
            required_fields=["summary", "sentiment"]
        )
        self.schemas["analysis"] = analysis_schema
    
    def register_schema(self, schema: OutputSchema):
        """註冊自訂 schema"""
        self.schemas[schema.name] = schema
    
    def parse(
        self,
        prompt: str,
        llm_call: Callable,
        schema_name: str = None,
        output_format: OutputFormat = OutputFormat.JSON,
        max_retries: int = 3,
        timeout: float = 30.0,
        **llm_kwargs
    ) -> ParseResult:
        """
        解析 LLM 輸出為結構化資料
        
        Args:
            prompt: 輸入提示
            llm_call: LLM 呼叫函數 (prompt) -> str
            schema_name: Schema 名稱
            output_format: 預期格式
            max_retries: 最大重試次數
            timeout: 超時時間
            
        Returns:
            ParseResult
        """
        start_time = time.time()
        result = ParseResult(success=False, raw_output="", strategy_used=ParseStrategy.DIRECT)
        
        self.stats["total"] += 1
        
        # 嘗試解析
        for attempt in range(max_retries):
            result.attempts = attempt + 1
            
            try:
                # 呼叫 LLM
                if attempt == 0:
                    raw_output = llm_call(prompt, **llm_kwargs)
                else:
                    # 加入格式提示
                    format_prompt = f"{prompt}\n\nIMPORTANT: Respond in valid JSON format only."
                    raw_output = llm_call(format_prompt, **llm_kwargs)
                
                result.raw_output = raw_output
                
                # 嘗試不同解析策略
                parsed = self._parse_with_fallback(raw_output, result)
                
                if parsed is not None:
                    result.data = parsed
                    result.success = True
                    
                    # 驗證
                    if schema_name and schema_name in self.schemas:
                        schema = self.schemas[schema_name]
                        result.validation = schema.validate(parsed)
                    
                    break
                    
            except Exception as e:
                result.error = str(e)
                result.error_type = type(e).__name__
        
        # 解析失敗
        if not result.success:
            self.stats["failed"] += 1
            result.error = result.error or "Failed to parse output"
        
        # Fallback
        if result.attempts > 1:
            self.stats["fallback"] += 1
            result.fallback_used = True
        
        result.parse_time_ms = (time.time() - start_time) * 1000
        self.parse_history.append(result)
        
        return result
    
    def _parse_with_fallback(self, raw_output: str, result: ParseResult) -> Optional[Dict]:
        """使用 fallback 策略解析"""
        
        # Strategy 1: Direct JSON parse
        result.strategy_used = ParseStrategy.DIRECT
        try:
            # 嘗試提取 JSON
            json_str = self._extract_json(raw_output)
            return json.loads(json_str)
        except Exception:
            pass
        
        # Strategy 2: Regex extraction
        result.strategy_used = ParseStrategy.REGEX_EXTRACT
        try:
            # 嘗試從 Markdown code block 提取
            match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', raw_output)
            if match:
                return json.loads(match.group(1))
            
            # 嘗試從 {...} 提取
            match = re.search(r'\{[\s\S]*\}', raw_output)
            if match:
                return json.loads(match.group(0))
        except Exception:
            pass
        
        # Strategy 3: Key-value extraction
        result.strategy_used = ParseStrategy.REPAIR
        try:
            data = self._extract_kv(raw_output)
            if data:
                return data
        except Exception:
            pass
        
        return None
    
    def _extract_json(self, text: str) -> str:
        """提取 JSON 字串"""
        # 移除 markdown code block
        text = re.sub(r'```(?:json)?\s*', '', text)
        text = re.sub(r'```\s*$', '', text)
        
        # 移除 BOM
        text = text.lstrip('\ufeff')
        
        return text.strip()
    
    def _extract_kv(self, text: str) -> Optional[Dict]:
        """從 key-value 格式提取"""
        result = {}
        
        # 嘗試 "key": "value" 格式
        pattern = r'"(\w+)":\s*(?:"([^"]*)"|(\d+\.?\d*)|(\[\])|(\{\})|null|true|false)'
        matches = re.findall(pattern, text)
        
        for match in matches:
            key = match[0]
            value = match[1] or match[2] or (match[3] if match[3] == '[]' else None)
            
            if value:
                # 嘗試轉換類型
                if value.isdigit():
                    value = int(value)
                elif re.match(r'^\d+\.\d+$', value):
                    value = float(value)
                
                result[key] = value
        
        return result if result else None

    # ==================== Agent Output Validator 整合 ====================

    def validate_output(
        self,
        output: Any,
        schema: Any = None,
        auto_fix: bool = True,
        quality_gate=None
    ) -> AOVReport:
        """
        使用 AgentOutputValidator 驗證輸出並可選自動修復

        Args:
            output: 待驗證的輸出
            schema: Schema 定義（Dict/Pydantic/List[Dict]/str）
            auto_fix: 是否自動修復可修復的問題
            quality_gate: 可選的 AutoQualityGate 實例用於整合

        Returns:
            ValidationReport（整合了 AOV 結果）
        """
        if not VALIDATOR_AVAILABLE:
            # Fallback: 使用內建的簡單驗證
            return self._fallback_validate(output, schema)

        validator = AgentOutputValidator()

        # 驗證
        if auto_fix:
            fixed_output, fix_report = validator.auto_fix(output, schema, dry_run=False)
            # 合併報告
            combined = ValidationResult()
            combined.valid = fix_report.valid and (output is not None)
            for err in fix_report.errors:
                combined.add_error(err.field, err.message)
            for warn in fix_report.warnings:
                combined.add_warning(warn.field, warn.message)
            combined._auto_fix_report = fix_report  # 附加元數據
            return combined
        else:
            aov_report = validator.validate(output, schema)
            # 轉換為內建格式
            combined = ValidationResult()
            combined.valid = aov_report.valid
            for err in aov_report.errors:
                combined.add_error(err.field, err.message)
            for warn in aov_report.warnings:
                combined.add_warning(warn.field, warn.message)
            combined._auto_fix_report = aov_report  # 附加元數據
            return combined

    def _fallback_validate(self, output: Any, schema: Any) -> ValidationResult:
        """當 AgentOutputValidator 不可用時的 fallback"""
        result = ValidationResult()

        if schema is None:
            return result

        # 如果有 registered schema，使用它
        if isinstance(schema, str) and schema in self.schemas:
            return self.schemas[schema].validate(output)

        # 如果是 dict 且有 properties，當作簡單 schema
        if isinstance(schema, dict) and "properties" in schema:
            result.valid = True
            return result

        return result

    def validate_and_fix_with_quality_gate(
        self,
        output: Any,
        schema: Any = None,
        quality_gate=None,
        file_path: str = None
    ) -> ValidationResult:
        """
        完整驗證流程：Validator + AutoFix + QualityGate

        Args:
            output: 待驗證的輸出
            schema: Schema 定義
            quality_gate: AutoQualityGate 實例
            file_path: 當提供時，也會用 QualityGate 掃描

        Returns:
            ValidationResult（含 extra 數據）
        """
        # Step 1: Validator 驗證 + 自動修復
        validation_result = self.validate_output(output, schema, auto_fix=True)

        # Step 2: QualityGate 額外檢查（如果提供）
        extra_issues = []
        if quality_gate and file_path:
            try:
                qg_report = quality_gate.scan(file_path)
                for issue in qg_report.issues:
                    extra_issues.append({
                        "source": "quality_gate",
                        "rule_id": issue.rule_id,
                        "severity": issue.severity,
                        "message": issue.message,
                        "line": issue.line,
                        "fixable": issue.fixable
                    })
                    if issue.severity == "critical":
                        validation_result.add_error(
                            f"quality_gate:{issue.rule_id}",
                            f"[QG] {issue.message}"
                        )
            except Exception:
                pass  # QualityGate 失敗不影響主流程

        # 附加額外資訊
        validation_result._extra_issues = extra_issues
        return validation_result

    def generate_report(self) -> str:
        """產生穩定性報告"""
        lines = []
        lines.append("╔" + "═" * 70 + "╗")
        lines.append("║" + " 📊 Structured Output Stability Report ".center(70) + "║")
        lines.append("╚" + "═" * 70 + "╝")
        lines.append("")
        
        # 統計
        total = self.stats["total"]
        success = self.stats["success"]
        fallback = self.stats["fallback"]
        failed = self.stats["failed"]
        
        lines.append("## 📈 Statistics")
        lines.append(f"- **Total Parses**: {total}")
        lines.append(f"- **Success**: {success} ({success/total*100:.1f}%)" if total > 0 else "- Success: 0")
        lines.append(f"- **Fallback Used**: {fallback} ({fallback/total*100:.1f}%)" if total > 0 else "- Fallback: 0")
        lines.append(f"- **Failed**: {failed} ({failed/total*100:.1f}%)" if total > 0 else "- Failed: 0")
        lines.append("")
        
        # 最近解析
        if self.parse_history:
            lines.append("## 📋 Recent Parses")
            for i, r in enumerate(self.parse_history[-5:]):
                status = "✅" if r.success else "❌"
                lines.append(
                    f"{status} [{r.strategy_used.value}] "
                    f"Score={r.parse_time_ms:.0f}ms | "
                    f"Attempts={r.attempts}"
                )
            lines.append("")
        
        # Registered schemas
        lines.append("## 📦 Registered Schemas")
        for name in self.schemas:
            lines.append(f"- {name}")
        lines.append("")
        
        return "\n".join(lines)


# ==================== Quick Helpers ====================

def extract_json(text: str) -> Optional[Dict]:
    """快速提取 JSON"""
    try:
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            return json.loads(match.group(0))
    except Exception:
        pass
    return None


def extract_structured(text: str, keys: List[str]) -> Dict:
    """快速提取結構化資料"""
    result = {}
    for key in keys:
        pattern = rf'{key}:\s*([^\n]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result[key] = match.group(1).strip()
    return result


# ==================== Main ====================

if __name__ == "__main__":
    pass # Removed print-debug
    pass # Removed print-debug
    pass # Removed print-debug
    
    # 建立引擎
    engine = StructuredOutputEngine()
    
    # Mock LLM 函數
    def mock_llm(prompt: str) -> str:
        """Mock LLM 回應"""
        if "user" in prompt.lower():
            return '''
            {
                "id": 123,
                "name": "John Doe",
                "email": "john@example.com",
                "role": "admin"
            }
            '''
        elif "task" in prompt.lower():
            return '''
            Here's the task info:
            
            **ID**: task-456
            **Title**: Implement login feature
            **Status**: in_progress
            **Priority**: 3
            
            ```json
            {"id": "task-456", "title": "Implement login feature", "status": "in_progress", "priority": 3}
            ```
            '''
        else:
            return '{"summary": "Test analysis", "sentiment": "positive", "confidence": 0.95}'
    
    # 測試解析
    pass # Removed print-debug
    result = engine.parse(
        prompt="Extract user info from the text",
        llm_call=mock_llm,
        schema_name="user_info"
    )
    
    pass # Removed print-debug
    pass # Removed print-debug
    pass # Removed print-debug
    pass # Removed print-debug
    pass # Removed print-debug
    if result.validation:
        pass # Removed print-debug
        if result.validation.errors:
            pass # Removed print-debug
    pass # Removed print-debug
    
    # 測試 Task 解析
    pass # Removed print-debug
    result2 = engine.parse(
        prompt="Extract task info",
        llm_call=mock_llm,
        schema_name="task"
    )
    
    pass # Removed print-debug
    pass # Removed print-debug
    pass # Removed print-debug
    
    # 產生報告
    pass # Removed print-debug
    
    # 快速提取
    pass # Removed print-debug
    text = "User: Alice, Email: alice@test.com, ID: 999"
    quick = extract_structured(text, ["User", "Email", "ID"])
    pass # Removed print-debug
