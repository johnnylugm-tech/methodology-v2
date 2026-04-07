#!/usr/bin/env python3
"""
Agent Output Validator

提供：
- JSON Schema 驗證
- Pydantic 模型驗證
- 自訂規則驗證
- 自動修復常見問題
"""

import re
import json
import copy
from typing import Dict, List, Optional, Any, Callable, Union, Type
from dataclasses import dataclass, field
from datetime import datetime

try:
    from pydantic import BaseModel, ValidationError, create_model
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False


@dataclass
class ValidationError_:
    """驗證錯誤"""
    field: str
    message: str
    severity: str = "error"  # error, warning, info
    fixable: bool = False
    auto_fix_value: Any = None


@dataclass
class ValidationReport:
    """驗證報告"""
    valid: bool = True
    errors: List[ValidationError_] = field(default_factory=list)
    warnings: List[ValidationError_] = field(default_factory=list)
    fix_applied: List[str] = field(default_factory=list)
    schema_type: str = "unknown"  # json_schema, pydantic, custom
    timestamp: datetime = field(default_factory=datetime.now)

    def add_error(self, field: str, message: str, fixable: bool = False, auto_fix_value: Any = None):
        err = ValidationError_(
            field=field,
            message=message,
            severity="error",
            fixable=fixable,
            auto_fix_value=auto_fix_value
        )
        self.errors.append(err)
        self.valid = False

    def add_warning(self, field: str, message: str, fixable: bool = False, auto_fix_value: Any = None):
        warn = ValidationError_(
            field=field,
            message=message,
            severity="warning",
            fixable=fixable,
            auto_fix_value=auto_fix_value
        )
        self.warnings.append(warn)

    def to_dict(self) -> Dict:
        return {
            "valid": self.valid,
            "errors": [
                {"field": e.field, "message": e.message, "severity": e.severity}
                for e in self.errors
            ],
            "warnings": [
                {"field": w.field, "message": w.message, "severity": w.severity}
                for w in self.warnings
            ],
            "fix_applied": self.fix_applied,
            "schema_type": self.schema_type,
            "timestamp": self.timestamp.isoformat()
        }


class AgentOutputValidator:
    """標準化 Agent 輸出格式驗證器"""

    # 常見類型映射
    TYPE_MAP = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None),
    }

    # 可自動修復的模式
    AUTO_FIX_RULES: List[Dict[str, Any]] = [
        {
            "pattern": r'^[\'\"](.+)[\'\"]$',
            "description": "去除多餘的引號包裝",
            "fields": ["*"],
        },
        {
            "pattern": r'\s+$',
            "description": "去除末尾空白",
            "fields": ["*"],
        },
        {
            "pattern": r'^\s+',
            "description": "去除開頭空白",
            "fields": ["*"],
        },
    ]

    def __init__(self):
        self.validation_history: List[ValidationReport] = []

    # ==================== JSON Schema 驗證 ====================

    def validate_json_schema(self, output: Any, schema: Dict) -> ValidationReport:
        """
        JSON Schema 驗證

        Args:
            output: 待驗證的輸出
            schema: JSON Schema 定義

        Returns:
            ValidationReport
        """
        report = ValidationReport(schema_type="json_schema")
        self._validate_with_schema(output, schema, "", report)
        self.validation_history.append(report)
        return report

    def _validate_with_schema(self, value: Any, schema: Dict, path: str, report: ValidationReport):
        """遞迴驗證"""
        if value is None:
            if schema.get("type") == "null":
                return
            if schema.get("required") and path.split(".")[-1] in schema.get("required", []):
                report.add_error(path or "root", "Required field is missing")
            return

        # Type 檢查
        expected_type = schema.get("type")
        if expected_type:
            python_type = self.TYPE_MAP.get(expected_type)
            if python_type and not isinstance(value, python_type):
                # 嘗試轉換
                converted = self._try_convert(value, expected_type)
                if converted is None:
                    report.add_error(
                        path or "root",
                        f"Expected {expected_type}, got {type(value).__name__}"
                    )
                    return
                value = converted

        # Enum 檢查
        if "enum" in schema:
            if value not in schema["enum"]:
                report.add_error(
                    path or "root",
                    f"Value must be one of: {schema['enum']}, got {value}"
                )

        # Pattern 檢查
        if "pattern" in schema and isinstance(value, str):
            if not re.match(schema["pattern"], value):
                report.add_error(
                    path,
                    f"Does not match pattern: {schema['pattern']}"
                )

        # Min/Max length
        if isinstance(value, (str, list)):
            if "minLength" in schema and len(value) < schema["minLength"]:
                report.add_error(path, f"Min length: {schema['minLength']}")
            if "maxLength" in schema and len(value) > schema["maxLength"]:
                report.add_error(path, f"Max length: {schema['maxLength']}")

        # Min/Max value
        if isinstance(value, (int, float)):
            if "minimum" in schema and value < schema["minimum"]:
                report.add_error(path, f"Min value: {schema['minimum']}")
            if "maximum" in schema and value > schema["maximum"]:
                report.add_error(path, f"Max value: {schema['maximum']}")

        # Array items
        if isinstance(value, list) and "items" in schema:
            for i, item in enumerate(value):
                self._validate_with_schema(item, schema["items"], f"{path}[{i}]", report)

        # Object properties
        if isinstance(value, dict) and "properties" in schema:
            required = schema.get("required", [])
            for prop_name, prop_schema in schema["properties"].items():
                prop_value = value.get(prop_name)
                prop_path = f"{path}.{prop_name}" if path else prop_name
                if prop_name in required and prop_value is None:
                    report.add_error(prop_path, "Required field is missing")
                if prop_value is not None:
                    self._validate_with_schema(prop_value, prop_schema, prop_path, report)

    def _try_convert(self, value: Any, target_type: str) -> Any:
        """嘗試類型轉換"""
        try:
            if target_type == "integer":
                return int(value)
            elif target_type == "number":
                return float(value)
            elif target_type == "boolean":
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes")
                return bool(value)
            elif target_type == "string":
                return str(value)
        except (ValueError, TypeError):
            pass
        return None

    # ==================== Pydantic 模型驗證 ====================

    def validate_pydantic(self, output: Any, model: Type) -> ValidationReport:
        """
        Pydantic 模型驗證

        Args:
            output: 待驗證的輸出 (dict)
            model: Pydantic BaseModel 子類

        Returns:
            ValidationReport
        """
        report = ValidationReport(schema_type="pydantic")

        if not PYDANTIC_AVAILABLE:
            report.add_error("root", "Pydantic is not installed")
            self.validation_history.append(report)
            return report

        if not isinstance(output, dict):
            report.add_error("root", f"Expected dict, got {type(output).__name__}")
            self.validation_history.append(report)
            return report

        try:
            model.model_validate(output)
        except ValidationError as e:
            for err in e.errors():
                loc = ".".join(str(l) for l in err["loc"])
                msg = err["msg"]
                report.add_error(loc, f"{err['type']}: {msg}")

        self.validation_history.append(report)
        return report

    # ==================== 自訂規則驗證 ====================

    def validate_custom(
        self,
        output: Any,
        rules: List[Dict[str, Any]]
    ) -> ValidationReport:
        """
        自訂規則驗證

        Args:
            output: 待驗證的輸出
            rules: 規則列表
                - {"field": "path.to.field", "check": "required"}
                - {"field": "path.to.field", "check": "type", "expected": str}
                - {"field": "path.to.field", "check": "range", "min": 0, "max": 100}
                - {"field": "path.to.field", "check": "pattern", "pattern": r"..."}
                - {"field": "path.to.field", "check": "enum", "values": [...]}
                - {"field": "path.to.field", "check": "custom", "fn": callable}

        Returns:
            ValidationReport
        """
        report = ValidationReport(schema_type="custom")

        for rule in rules:
            field_path = rule.get("field", "root")
            check_type = rule.get("check", "")

            value = self._get_nested_value(output, field_path)

            if check_type == "required":
                if value is None:
                    report.add_error(field_path, "Required field is missing")

            elif check_type == "type":
                expected = rule.get("expected")
                if value is not None and not isinstance(value, expected):
                    report.add_error(
                        field_path,
                        f"Expected {expected.__name__}, got {type(value).__name__}"
                    )

            elif check_type == "range":
                if value is not None:
                    if "min" in rule and value < rule["min"]:
                        report.add_error(field_path, f"Value must be >= {rule['min']}")
                    if "max" in rule and value > rule["max"]:
                        report.add_error(field_path, f"Value must be <= {rule['max']}")

            elif check_type == "pattern":
                if value is not None and isinstance(value, str):
                    pattern = rule.get("pattern", "")
                    if not re.match(pattern, value):
                        report.add_error(field_path, f"Does not match pattern: {pattern}")

            elif check_type == "enum":
                if value is not None and value not in rule.get("values", []):
                    report.add_error(field_path, f"Value must be one of: {rule['values']}")

            elif check_type == "custom":
                fn = rule.get("fn")
                if fn and value is not None:
                    try:
                        if not fn(value):
                            report.add_error(field_path, "Custom validation failed")
                    except Exception as e:
                        report.add_error(field_path, f"Custom validation error: {e}")

            elif check_type == "forbidden":
                if value is not None:
                    report.add_error(field_path, "Forbidden field must not be present")

        self.validation_history.append(report)
        return report

    def _get_nested_value(self, data: Any, path: str) -> Any:
        """獲取巢狀欄位的值"""
        if path == "root" or path == "":
            return data

        parts = path.replace("[", ".").replace("]", "").split(".")
        current = data

        for part in parts:
            if part.isdigit():
                idx = int(part)
                if isinstance(current, (list, tuple)) and idx < len(current):
                    current = current[idx]
                else:
                    return None
            elif isinstance(current, dict):
                current = current.get(part)
            else:
                return None

        return current

    # ==================== 統一驗證入口 ====================

    def validate(
        self,
        output: Any,
        schema: Union[Dict, Type, List[Dict], str, None] = None
    ) -> ValidationReport:
        """
        統一驗證入口

        Args:
            output: 待驗證的輸出
            schema: Schema 定義
                - Dict: 視為 JSON Schema
                - Type (Pydantic): Pydantic 模型驗證
                - List[Dict]: 自訂規則列表
                - str: schema 名稱（需預先註冊）
                - None: 嘗試自動推斷

        Returns:
            ValidationReport
        """
        if schema is None:
            # 嘗試自動推斷
            if isinstance(output, dict):
                return self._auto_validate(output)
            else:
                report = ValidationReport()
                report.add_error("root", "Unable to validate non-dict output without schema")
                return report

        if isinstance(schema, dict):
            return self.validate_json_schema(output, schema)
        elif isinstance(schema, list):
            return self.validate_custom(output, schema)
        elif PYDANTIC_AVAILABLE and isinstance(schema, type) and issubclass(schema, BaseModel):
            return self.validate_pydantic(output, schema)
        elif isinstance(schema, str):
            # 嘗試從已註冊的 schema 獲取
            return self._validate_with_registered_schema(output, schema)
        else:
            report = ValidationReport()
            report.add_error("root", f"Unknown schema type: {type(schema)}")
            return report

    def _auto_validate(self, output: Dict) -> ValidationReport:
        """自動推斷驗證"""
        report = ValidationReport(schema_type="auto")

        # 基本結構檢查
        if not isinstance(output, dict):
            report.add_error("root", f"Expected dict, got {type(output).__name__}")
            return report

        # 常見欄位類型推斷
        type_inferences = {
            "id": (int, str),
            "name": str,
            "email": str,
            "status": str,
            "count": (int, float),
            "score": (int, float),
            "tags": list,
            "items": list,
            "data": (dict, list),
        }

        for key, expected_type in type_inferences.items():
            if key in output:
                value = output[key]
                if not isinstance(value, expected_type):
                    report.add_warning(
                        key,
                        f"Type mismatch: expected {expected_type}, got {type(value).__name__}"
                    )

        self.validation_history.append(report)
        return report

    def _validate_with_registered_schema(self, output: Any, schema_name: str) -> ValidationReport:
        """使用已註冊的 schema 驗證"""
        report = ValidationReport()
        report.add_error("root", f"Schema '{schema_name}' not registered")
        return report

    # ==================== 自動修復 ====================

    def auto_fix(
        self,
        output: Any,
        schema: Union[Dict, Type, List[Dict], None] = None,
        dry_run: bool = False
    ) -> tuple[Any, ValidationReport]:
        """
        自動修復常見問題

        Args:
            output: 待修復的輸出
            schema: Schema 定義（用於驗證修復後結果）
            dry_run: True = 只報告不實際修改

        Returns:
            (修復後的輸出, ValidationReport)
        """
        report = ValidationReport()
        fixed_output = copy.deepcopy(output)

        # 1. 修復類型問題
        fixed_output = self._fix_type_issues(fixed_output, schema, report)

        # 2. 修復常見格式問題
        fixed_output = self._fix_common_issues(fixed_output, report)

        # 3. 修剪多餘結構
        fixed_output = self._fix_extra_wrappers(fixed_output, report)

        # 如果有 schema，驗證修復後結果
        if schema and not dry_run:
            validation = self.validate(fixed_output, schema)
            report.valid = validation.valid
            if not validation.valid:
                report.errors.extend(validation.errors)
            report.warnings.extend(validation.warnings)

        return fixed_output, report

    def _fix_type_issues(
        self,
        data: Any,
        schema: Optional[Dict],
        report: ValidationReport
    ) -> Any:
        """修復類型問題"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                result[key] = self._fix_type_issues(value, schema, report)

                # 嘗試從 string 轉 int/float
                if schema and isinstance(schema, dict):
                    prop_schema = schema.get("properties", {}).get(key, {})
                    expected_type = prop_schema.get("type")

                    if expected_type == "integer" and isinstance(value, str):
                        try:
                            result[key] = int(value)
                            report.fix_applied.append(f"{key}: string → int")
                        except ValueError:
                            pass

                    elif expected_type == "number" and isinstance(value, str):
                        try:
                            result[key] = float(value)
                            report.fix_applied.append(f"{key}: string → float")
                        except ValueError:
                            pass

            return result

        elif isinstance(data, list):
            return [self._fix_type_issues(item, schema, report) for item in data]

        else:
            return data

    def _fix_common_issues(self, data: Any, report: ValidationReport) -> Any:
        """修復常見格式問題"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                result[key] = self._fix_common_issues(value, report)

                # 去除多餘引號
                if isinstance(value, str):
                    stripped = value.strip()
                    match = re.match(r'^[\'"](.+)[\'\"]$', stripped)
                    if match and len(stripped) > 2:
                        result[key] = match.group(1)
                        report.fix_applied.append(f"{key}: removed extra quotes")

            return result

        elif isinstance(data, list):
            return [self._fix_common_issues(item, report) for item in data]

        elif isinstance(data, str):
            # 去除多餘空白
            stripped = data.strip()
            if stripped != data:
                return stripped
            return data

        return data

    def _fix_extra_wrappers(self, data: Any, report: ValidationReport) -> Any:
        """修復多餘的包裝（如 {"data": {"actual": ...}} → {"actual": ...}）"""
        if isinstance(data, dict):
            # 常見的 wrapper key
            wrapper_keys = ["data", "result", "output", "response", "content"]

            for wrapper in wrapper_keys:
                if wrapper in data and len(data) == 1:
                    inner = data[wrapper]
                    if isinstance(inner, dict):
                        report.fix_applied.append(f"Removed wrapper: {wrapper}")
                        return self._fix_extra_wrappers(inner, report)

            # 遞迴處理
            return {k: self._fix_extra_wrappers(v, report) for k, v in data.items()}

        elif isinstance(data, list):
            return [self._fix_extra_wrappers(item, report) for item in data]

        return data

    # ==================== 報告 ====================

    def generate_report(self, format: str = "markdown") -> str:
        """生成驗證報告"""
        if not self.validation_history:
            return "No validation history."

        if format == "json":
            return json.dumps([r.to_dict() for r in self.validation_history], indent=2, default=str)

        lines = [
            "# 🔍 Agent Output Validator Report",
            f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
            f"Total validations: {len(self.validation_history)}",
            f"Passed: {sum(1 for r in self.validation_history if r.valid)}",
            f"Failed: {sum(1 for r in self.validation_history if not r.valid)}\n",
            "---"
        ]

        for i, report in enumerate(self.validation_history[-10:], 1):
            status = "✅" if report.valid else "❌"
            lines.append(f"\n## {status} Validation #{i} ({report.schema_type})")

            if report.errors:
                lines.append("\n**Errors:**")
                for err in report.errors:
                    lines.append(f"- [{err.field}] {err.message}")

            if report.warnings:
                lines.append("\n**Warnings:**")
                for warn in report.warnings:
                    lines.append(f"- [{warn.field}] {warn.message}")

            if report.fix_applied:
                lines.append("\n**Fixes Applied:**")
                for fix in report.fix_applied:
                    lines.append(f"- {fix}")

        return "\n".join(lines)


# ==================== 預設 Schema 工廠 ====================

def create_output_schema(
    name: str,
    fields: Dict[str, Dict],
    required: List[str] = None
) -> Dict:
    """
    快速建立 JSON Schema

    Args:
        name: Schema 名稱
        fields: 欄位定義 {"field_name": {"type": "string", "enum": [...]}}
        required: 必填欄位列表

    Returns:
        JSON Schema Dict
    """
    properties = {}
    for field_name, field_def in fields.items():
        prop = {"type": field_def.get("type", "string")}
        if "enum" in field_def:
            prop["enum"] = field_def["enum"]
        if "pattern" in field_def:
            prop["pattern"] = field_def["pattern"]
        if "min" in field_def:
            prop["minimum"] = field_def["min"]
        if "max" in field_def:
            prop["maximum"] = field_def["max"]
        properties[field_name] = prop

    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": name,
        "type": "object",
        "properties": properties,
    }

    if required:
        schema["required"] = required

    return schema


# ==================== Main ====================

if __name__ == "__main__":
    validator = AgentOutputValidator()

    # 測試 JSON Schema 驗證
    schema = create_output_schema(
        "user_info",
        {
            "id": {"type": "integer"},
            "name": {"type": "string"},
            "email": {"type": "string", "pattern": r"^[\w.-]+@[\w.-]+\.\w+$"},
            "role": {"type": "string", "enum": ["admin", "user", "guest"]},
        },
        required=["id", "email"]
    )

    valid_data = {
        "id": 123,
        "name": "John Doe",
        "email": "john@example.com",
        "role": "admin"
    }

    invalid_data = {
        "id": "not_an_int",
        "name": "John",
        "email": "invalid_email"
    }

    # 測試驗證
    report1 = validator.validate(valid_data, schema)
    report2 = validator.validate(invalid_data, schema)

    # 測試自動修復
    fixed_data, fix_report = validator.auto_fix(invalid_data, schema)

    # 生成報告
    print(validator.generate_report())
