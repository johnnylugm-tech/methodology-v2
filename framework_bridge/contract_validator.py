"""
Contract Validator Module

契約驗證器 - 深度驗證契約與實際資料的差異
"""

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Tuple, Set
from enum import Enum


class ValidationSeverity(Enum):
    """驗證嚴重程度"""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """驗證問題"""
    severity: ValidationSeverity
    field_path: str
    message: str
    expected: Any = None
    actual: Any = None

    def __str__(self) -> str:
        icon = {
            ValidationSeverity.ERROR: "❌",
            ValidationSeverity.WARNING: "⚠️",
            ValidationSeverity.INFO: "ℹ️",
        }[self.severity]
        return f"{icon} [{self.severity.value}] {self.field_path}: {self.message}"


@dataclass
class ValidationReport:
    """驗證報告"""
    contract_name: str
    is_valid: bool
    issues: List[ValidationIssue] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)

    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)

    @property
    def info_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.INFO)

    def summary(self) -> str:
        lines = [
            f"Validation Report: {self.contract_name}",
            f"Status: {'✅ VALID' if self.is_valid else '❌ INVALID'}",
            f"Issues: {self.error_count} errors, {self.warning_count} warnings, {self.info_count} info",
            "",
        ]
        if self.issues:
            lines.append("Details:")
            for issue in self.issues:
                lines.append(f"  {str(issue)}")
                if issue.expected is not None or issue.actual is not None:
                    lines.append(
                        f"      Expected: {issue.expected!r} | Actual: {issue.actual!r}"
                    )
        return "\n".join(lines)


class ContractValidator:
    """
    契約驗證器

    深度驗證契約與實際資料的差異，提供詳細的差異報告。
    """

    def __init__(self):
        self.validation_history: List[ValidationReport] = []

    def validate(
        self,
        contract: Any,
        actual: Dict[str, Any],
        strict: bool = False,
    ) -> ValidationReport:
        """
        驗證並報告差異

        Args:
            contract: Contract 物件或 contract dict
            actual: 實際資料
            strict: 是否嚴格模式 (strict=True 時，額外欄位也會警告)

        Returns:
            ValidationReport
        """
        # 取得 contract 名稱
        contract_name = getattr(contract, "agent_name", "unknown")

        # 統一轉換為 dict
        if hasattr(contract, "to_dict"):
            contract_dict = contract.to_dict()
        else:
            contract_dict = contract

        issues: List[ValidationIssue] = []

        # 根據 contract 類型驗證
        contract_type = contract_dict.get("contract_type", "bidirectional")

        if contract_type in ("input", "bidirectional"):
            input_schema = contract_dict.get("input_schema", {})
            input_data = actual.get("input", actual)  # 支援 input 包裝或直接數據
            input_issues = self._validate_schema_fields(
                input_schema, input_data, strict
            )
            issues.extend(input_issues)

        if contract_type in ("output", "bidirectional"):
            output_schema = contract_dict.get("output_schema", {})
            output_data = actual.get("output", actual)
            output_issues = self._validate_schema_fields(
                output_schema, output_data, strict
            )
            issues.extend(output_issues)

        # 額外欄位檢查 (strict mode)
        if strict:
            extra_issues = self._check_extra_fields(
                contract_dict, actual, contract_type
            )
            issues.extend(extra_issues)

        is_valid = all(i.severity != ValidationSeverity.ERROR for i in issues)

        report = ValidationReport(
            contract_name=contract_name,
            is_valid=is_valid,
            issues=issues,
        )
        self.validation_history.append(report)

        return report

    def _validate_schema_fields(
        self,
        schema: Dict[str, Any],
        data: Dict[str, Any],
        strict: bool = False,
    ) -> List[ValidationIssue]:
        """驗證 Schema 欄位"""
        issues: List[ValidationIssue] = []
        schema_fields = schema.get("fields", [])

        # 建立欄位名稱集合
        schema_field_names: Set[str] = {f["name"] for f in schema_fields}
        data_field_names: Set[str] = set(data.keys())

        # 檢查必填欄位
        for field_def in schema_fields:
            field_name = field_def["name"]
            if field_def.get("required", True) and field_name not in data:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field_path=f"{field_name}",
                        message="Required field is missing",
                        expected=field_def.get("type"),
                        actual=None,
                    )
                )

        # 驗證每個資料欄位
        for field_name, field_value in data.items():
            field_def = next((f for f in schema_fields if f["name"] == field_name), None)

            if not field_def:
                # 未知欄位
                if strict:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            field_path=f"{field_name}",
                            message="Extra field not defined in contract",
                            actual=field_value,
                        )
                    )
                continue

            # 類型驗證
            type_issues = self._validate_field_type(
                field_name, field_value, field_def
            )
            issues.extend(type_issues)

            # Enum 驗證
            enum_values = field_def.get("enum_values", [])
            if enum_values and field_value not in enum_values:
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        field_path=f"{field_name}",
                        message=f"Value not in allowed enum values",
                        expected=enum_values,
                        actual=field_value,
                    )
                )

            # Pattern 驗證
            pattern = field_def.get("pattern", "")
            if pattern and isinstance(field_value, str):
                if not re.match(pattern, field_value):
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            field_path=f"{field_name}",
                            message=f"Value does not match pattern: {pattern}",
                            expected=pattern,
                            actual=field_value,
                        )
                    )

            # 範圍驗證 (如果有)
            min_val = field_def.get("min")
            max_val = field_def.get("max")
            if min_val is not None and isinstance(field_value, (int, float)):
                if field_value < min_val:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            field_path=f"{field_name}",
                            message=f"Value below minimum: {min_val}",
                            expected=min_val,
                            actual=field_value,
                        )
                    )
            if max_val is not None and isinstance(field_value, (int, float)):
                if field_value > max_val:
                    issues.append(
                        ValidationIssue(
                            severity=ValidationSeverity.ERROR,
                            field_path=f"{field_name}",
                            message=f"Value above maximum: {max_val}",
                            expected=max_val,
                            actual=field_value,
                        )
                    )

        return issues

    def _validate_field_type(
        self, field_name: str, value: Any, field_def: Dict[str, Any]
    ) -> List[ValidationIssue]:
        """驗證單一欄位類型"""
        issues: List[ValidationIssue] = []
        expected_type = field_def.get("type", "string").lower()

        type_map = {
            "string": str, "str": str,
            "integer": int, "int": int,
            "number": (int, float), "float": float, "double": float,
            "boolean": bool, "bool": bool,
            "array": list, "list": list,
            "object": dict, "dict": dict,
        }

        python_type = type_map.get(expected_type)
        if python_type and not isinstance(value, python_type):
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    field_path=f"{field_name}",
                    message=f"Type mismatch: expected {expected_type}",
                    expected=expected_type,
                    actual=type(value).__name__,
                )
            )

        # 額外的巢狀驗證
        if expected_type == "array" and isinstance(value, list):
            item_type = field_def.get("items", {}).get("type", "").lower()
            if item_type:
                for i, item in enumerate(value[:5]):  # 只檢查前5個
                    item_issues = self._validate_field_type(
                        f"{field_name}[{i}]", item, {"type": item_type}
                    )
                    issues.extend(item_issues)

        return issues

    def _check_extra_fields(
        self,
        contract: Dict[str, Any],
        actual: Dict[str, Any],
        contract_type: str,
    ) -> List[ValidationIssue]:
        """檢查額外未定義的欄位"""
        issues: List[ValidationIssue] = []

        schema = contract.get(
            f"{contract_type}_schema",
            contract.get("input_schema", {}),
        )
        schema_field_names = {f["name"] for f in schema.get("fields", [])}

        for key in actual.keys():
            if key not in schema_field_names and key not in ("input", "output"):
                issues.append(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        field_path=key,
                        message="Field not defined in contract schema",
                        actual=actual[key],
                    )
                )

        return issues

    # ==================== Comparative Validation ====================

    def compare_contracts(
        self, contract_a: Any, contract_b: Any
    ) -> List[ValidationIssue]:
        """
        比較兩個契約的差異

        Args:
            contract_a: 第一個契約
            contract_b: 第二個契約

        Returns:
            List[ValidationIssue]
        """
        issues: List[ValidationIssue] = []

        a_dict = contract_a.to_dict() if hasattr(contract_a, "to_dict") else contract_a
        b_dict = contract_b.to_dict() if hasattr(contract_b, "to_dict") else contract_b

        # 比較 input schema
        a_input_fields = {f["name"] for f in a_dict.get("input_schema", {}).get("fields", [])}
        b_input_fields = {f["name"] for f in b_dict.get("input_schema", {}).get("fields", [])}

        for field_name in a_input_fields - b_input_fields:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field_path=f"input.{field_name}",
                    message="Field only in contract A",
                    expected=field_name,
                    actual=None,
                )
            )

        for field_name in b_input_fields - a_input_fields:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field_path=f"input.{field_name}",
                    message="Field only in contract B",
                    expected=field_name,
                    actual=None,
                )
            )

        # 比較 output schema
        a_output_fields = {f["name"] for f in a_dict.get("output_schema", {}).get("fields", [])}
        b_output_fields = {f["name"] for f in b_dict.get("output_schema", {}).get("fields", [])}

        for field_name in a_output_fields - b_output_fields:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field_path=f"output.{field_name}",
                    message="Field only in contract A",
                    expected=field_name,
                    actual=None,
                )
            )

        for field_name in b_output_fields - a_output_fields:
            issues.append(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    field_path=f"output.{field_name}",
                    message="Field only in contract B",
                    expected=field_name,
                    actual=None,
                )
            )

        return issues

    # ==================== Batch Validation ====================

    def validate_batch(
        self,
        contract: Any,
        dataset: List[Dict[str, Any]],
        strict: bool = False,
    ) -> List[ValidationReport]:
        """
        批量驗證多筆資料

        Args:
            contract: Contract 物件
            dataset: 資料集
            strict: 是否嚴格模式

        Returns:
            List[ValidationReport]
        """
        reports = []
        for i, data in enumerate(dataset):
            report = self.validate(contract, data, strict=strict)
            report.metadata["batch_index"] = i
            reports.append(report)
        return reports

    def batch_summary(self, reports: List[ValidationReport]) -> str:
        """產生批量驗證摘要"""
        total_errors = sum(r.error_count for r in reports)
        total_warnings = sum(r.warning_count for r in reports)
        valid_count = sum(1 for r in reports if r.is_valid)

        lines = [
            f"Batch Validation Summary",
            f"{'=' * 40}",
            f"Total: {len(reports)} | Valid: {valid_count} | Invalid: {len(reports) - valid_count}",
            f"Errors: {total_errors} | Warnings: {total_warnings}",
            f"",
            f"Per-item breakdown:",
        ]

        for i, report in enumerate(reports):
            icon = "✅" if report.is_valid else "❌"
            lines.append(
                f"  [{i}] {icon} {report.contract_name} - "
                f"{report.error_count} errors, {report.warning_count} warnings"
            )

        return "\n".join(lines)

    # ==================== Schema Compatibility ====================

    def check_compatibility(
        self,
        contract: Any,
        target_schema: Dict[str, Any],
    ) -> Tuple[bool, List[str]]:
        """
        檢查契約是否與目標 Schema 相容

        Args:
            contract: Contract 物件
            target_schema: 目標 Schema dict

        Returns:
            (is_compatible, messages)
        """
        messages = []
        is_compatible = True

        contract_dict = contract.to_dict() if hasattr(contract, "to_dict") else contract

        # 檢查 input schema 相容性
        input_fields = {
            f["name"]: f for f in contract_dict.get("input_schema", {}).get("fields", [])
        }
        target_fields = {
            f["name"]: f for f in target_schema.get("fields", [])
        }

        for name, field_def in target_fields.items():
            if name not in input_fields:
                messages.append(f"⚠️ Missing input field: {name}")
                is_compatible = False
            else:
                # 類型相容性檢查
                source_type = input_fields[name].get("type", "").lower()
                target_type = field_def.get("type", "").lower()
                if source_type != target_type:
                    messages.append(
                        f"⚠️ Type mismatch for '{name}': "
                        f"contract has {source_type}, target expects {target_type}"
                    )
                    is_compatible = False

        return is_compatible, messages
