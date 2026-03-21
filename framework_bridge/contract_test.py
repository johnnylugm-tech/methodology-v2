"""
Contract Testing Module for FrameworkBridge

提供 Agent 契約測試能力：
- 定義 Agent 的輸入/輸出契約 (Schema)
- 驗證實際輸出是否符合契約
- 自動生成測試案例
"""

import json
import re
import ast
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Callable
from enum import Enum


class ContractType(Enum):
    """契約類型"""
    INPUT = "input"
    OUTPUT = "output"
    BIDIRECTIONAL = "bidirectional"


@dataclass
class SchemaField:
    """Schema 欄位定義"""
    name: str
    type: str
    required: bool = True
    description: str = ""
    default: Any = None
    enum_values: List[Any] = field(default_factory=list)
    pattern: str = ""  # regex pattern for string validation


@dataclass
class ContractSchema:
    """契約 Schema 定義"""
    name: str
    fields: List[SchemaField] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "fields": [
                {
                    "name": f.name,
                    "type": f.type,
                    "required": f.required,
                    "description": f.description,
                    "default": f.default,
                    "enum_values": f.enum_values,
                    "pattern": f.pattern,
                }
                for f in self.fields
            ],
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ContractSchema":
        fields = [
            SchemaField(
                name=f["name"],
                type=f["type"],
                required=f.get("required", True),
                description=f.get("description", ""),
                default=f.get("default"),
                enum_values=f.get("enum_values", []),
                pattern=f.get("pattern", ""),
            )
            for f in data.get("fields", [])
        ]
        return cls(
            name=data.get("name", ""),
            fields=fields,
            description=data.get("description", ""),
        )


@dataclass
class Contract:
    """Agent 契約"""
    agent_name: str
    input_schema: ContractSchema
    output_schema: ContractSchema
    contract_type: ContractType = ContractType.BIDIRECTIONAL
    version: str = "1.0.0"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "agent_name": self.agent_name,
            "contract_type": self.contract_type.value,
            "version": self.version,
            "input_schema": self.input_schema.to_dict(),
            "output_schema": self.output_schema.to_dict(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Contract":
        return cls(
            agent_name=data["agent_name"],
            input_schema=ContractSchema.from_dict(data["input_schema"]),
            output_schema=ContractSchema.from_dict(data["output_schema"]),
            contract_type=ContractType(data.get("contract_type", "bidirectional")),
            version=data.get("version", "1.0.0"),
            metadata=data.get("metadata", {}),
        )


class ContractTest:
    """
    契約測試類

    用於定義、驗證和管理 Agent 契約測試。
    """

    def __init__(self):
        self.contracts: Dict[str, Contract] = {}
        self.test_results: Dict[str, List["TestResult"]] = {}

    # ==================== Contract Management ====================

    def define_contract(
        self,
        agent_name: str,
        input_schema: ContractSchema,
        output_schema: ContractSchema,
        contract_type: ContractType = ContractType.BIDIRECTIONAL,
        version: str = "1.0.0",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Contract:
        """
        定義 Agent 契約

        Args:
            agent_name: Agent 名稱
            input_schema: 輸入 Schema
            output_schema: 輸出 Schema
            contract_type: 契約類型
            version: 版本號
            metadata: 額外元數據

        Returns:
            Contract 物件
        """
        contract = Contract(
            agent_name=agent_name,
            input_schema=input_schema,
            output_schema=output_schema,
            contract_type=contract_type,
            version=version,
            metadata=metadata or {},
        )
        self.contracts[agent_name] = contract
        return contract

    def get_contract(self, agent_name: str) -> Optional[Contract]:
        """取得契約"""
        return self.contracts.get(agent_name)

    def list_contracts(self) -> List[str]:
        """列出所有已定義的契約"""
        return list(self.contracts.keys())

    # ==================== Schema Builders ====================

    def create_input_schema(
        self,
        name: str,
        fields: List[SchemaField],
        description: str = "",
    ) -> ContractSchema:
        """建立輸入 Schema"""
        return ContractSchema(name=name, fields=fields, description=description)

    def create_output_schema(
        self,
        name: str,
        fields: List[SchemaField],
        description: str = "",
    ) -> ContractSchema:
        """建立輸出 Schema"""
        return ContractSchema(name=name, fields=fields, description=description)

    def schema_field(
        self,
        name: str,
        type: str,
        required: bool = True,
        description: str = "",
        default: Any = None,
        enum_values: Optional[List[Any]] = None,
        pattern: str = "",
    ) -> SchemaField:
        """建立 Schema 欄位"""
        return SchemaField(
            name=name,
            type=type,
            required=required,
            description=description,
            default=default,
            enum_values=enum_values or [],
            pattern=pattern,
        )

    # ==================== Contract Verification ====================

    def verify_contract(
        self,
        agent_name: str,
        actual_input: Optional[Dict[str, Any]] = None,
        actual_output: Optional[Dict[str, Any]] = None,
    ) -> "VerificationResult":
        """
        驗證輸出是否符合契約

        Args:
            agent_name: Agent 名稱
            actual_input: 實際輸入 (可選)
            actual_output: 實際輸出 (可選)

        Returns:
            VerificationResult
        """
        contract = self.contracts.get(agent_name)
        if not contract:
            return VerificationResult(
                agent_name=agent_name,
                success=False,
                errors=[f"Contract not found for agent: {agent_name}"],
            )

        errors = []

        # 驗證輸入
        if actual_input is not None and contract.contract_type in (
            ContractType.INPUT,
            ContractType.BIDIRECTIONAL,
        ):
            input_errors = self._validate_schema(
                actual_input, contract.input_schema, "input"
            )
            errors.extend(input_errors)

        # 驗證輸出
        if actual_output is not None and contract.contract_type in (
            ContractType.OUTPUT,
            ContractType.BIDIRECTIONAL,
        ):
            output_errors = self._validate_schema(
                actual_output, contract.output_schema, "output"
            )
            errors.extend(output_errors)

        return VerificationResult(
            agent_name=agent_name,
            success=len(errors) == 0,
            errors=errors,
            contract_version=contract.version,
        )

    def _validate_schema(
        self, data: Dict[str, Any], schema: ContractSchema, direction: str
    ) -> List[str]:
        """驗證資料是否符合 Schema"""
        errors = []
        schema_name = schema.name or f"{direction}_schema"

        for field in schema.fields:
            value = data.get(field.name)

            # Required check
            if field.required and value is None:
                errors.append(
                    f"[{schema_name}] Missing required field: {field.name}"
                )
                continue

            if value is None:
                continue

            # Type check
            type_errors = self._validate_type(
                field.name, value, field.type, schema_name
            )
            errors.extend(type_errors)

            # Enum check
            if field.enum_values and value not in field.enum_values:
                errors.append(
                    f"[{schema_name}] Field '{field.name}' value '{value}' "
                    f"not in allowed values: {field.enum_values}"
                )

            # Pattern check
            if field.pattern and isinstance(value, str):
                if not re.match(field.pattern, value):
                    errors.append(
                        f"[{schema_name}] Field '{field.name}' value '{value}' "
                        f"does not match pattern: {field.pattern}"
                    )

        return errors

    def _validate_type(
        self, field_name: str, value: Any, expected_type: str, schema_name: str
    ) -> List[str]:
        """驗證類型"""
        errors = []
        type_map = {
            "string": str,
            "str": str,
            "integer": int,
            "int": int,
            "number": (int, float),
            "float": float,
            "boolean": bool,
            "bool": bool,
            "array": list,
            "list": list,
            "object": dict,
            "dict": dict,
        }

        python_type = type_map.get(expected_type.lower())
        if python_type and not isinstance(value, python_type):
            errors.append(
                f"[{schema_name}] Field '{field_name}' expected type {expected_type}, "
                f"got {type(value).__name__} (value: {repr(value)[:50]})"
            )

        return errors

    # ==================== Test Case Generation ====================

    def generate_test_cases(self, agent_name: str) -> List["TestCase"]:
        """
        根據契約自動生成測試案例

        Args:
            agent_name: Agent 名稱

        Returns:
            List[TestCase]
        """
        contract = self.contracts.get(agent_name)
        if not contract:
            return []

        test_cases = []

        # 生成必填欄位測試案例
        for field in contract.input_schema.fields:
            if field.required:
                test_cases.append(
                    TestCase(
                        name=f"required_field_{field.name}",
                        description=f"Test required field: {field.name}",
                        input_data={field.name: self._generate_test_value(field)},
                        expected_valid=True,
                    )
                )

        # 生成缺失必填欄位測試案例
        for field in contract.input_schema.fields:
            if field.required:
                test_cases.append(
                    TestCase(
                        name=f"missing_required_{field.name}",
                        description=f"Test missing required field: {field.name}",
                        input_data={},
                        expected_valid=False,
                    )
                )

        # 生成類型錯誤測試案例
        for field in contract.input_schema.fields:
            test_cases.append(
                TestCase(
                    name=f"type_error_{field.name}",
                    description=f"Test type error for field: {field.name}",
                    input_data={field.name: "invalid_type_123"},
                    expected_valid=False,
                )
            )

        # 生成有效輸入測試案例
        valid_input = {
            f.name: self._generate_test_value(f)
            for f in contract.input_schema.fields
        }
        test_cases.append(
            TestCase(
                name="valid_input_all_fields",
                description="Test valid input with all fields",
                input_data=valid_input,
                expected_valid=True,
            )
        )

        # 生成 enum 測試案例
        for field in contract.input_schema.fields:
            if field.enum_values:
                for enum_val in field.enum_values:
                    test_cases.append(
                        TestCase(
                            name=f"enum_{field.name}_{enum_val}",
                            description=f"Test enum value {enum_val} for {field.name}",
                            input_data={field.name: enum_val},
                            expected_valid=True,
                        )
                    )
                # Invalid enum
                test_cases.append(
                    TestCase(
                        name=f"enum_invalid_{field.name}",
                        description=f"Test invalid enum for {field.name}",
                        input_data={field.name: "__invalid_enum__"},
                        expected_valid=False,
                    )
                )

        return test_cases

    def _generate_test_value(self, field: SchemaField) -> Any:
        """為欄位生成測試值"""
        if field.default is not None:
            return field.default
        if field.enum_values:
            return field.enum_values[0]

        type_defaults = {
            "string": "test_string",
            "str": "test_string",
            "integer": 42,
            "int": 42,
            "number": 3.14,
            "float": 3.14,
            "boolean": True,
            "bool": True,
            "array": [],
            "list": [],
            "object": {},
            "dict": {},
        }
        return type_defaults.get(field.type.lower(), "default_value")

    # ==================== Run Tests ====================

    def run_tests(
        self,
        agent_name: str,
        test_cases: Optional[List["TestCase"]] = None,
        validator_fn: Optional[Callable] = None,
    ) -> "TestRunResult":
        """
        執行測試

        Args:
            agent_name: Agent 名稱
            test_cases: 測試案例列表 (若為 None，自動生成)
            validator_fn: 自訂驗證函數 (receives TestCase, returns bool)

        Returns:
            TestRunResult
        """
        if test_cases is None:
            test_cases = self.generate_test_cases(agent_name)

        results = []
        passed = 0
        failed = 0

        for tc in test_cases:
            # 使用自訂驗證函數或預設驗證
            if validator_fn:
                is_valid = validator_fn(tc)
            else:
                result = self.verify_contract(agent_name, actual_input=tc.input_data)
                is_valid = result.success

            tc_result = TestResult(
                test_case=tc,
                passed=(is_valid == tc.expected_valid),
                actual_valid=is_valid,
                expected_valid=tc.expected_valid,
            )
            results.append(tc_result)

            if tc_result.passed:
                passed += 1
            else:
                failed += 1

        self.test_results[agent_name] = results

        return TestRunResult(
            agent_name=agent_name,
            total=len(test_cases),
            passed=passed,
            failed=failed,
            results=results,
        )

    # ==================== Export / Import ====================

    def export_contracts(self, file_path: str) -> None:
        """匯出契約到 JSON 檔案"""
        data = {
            agent_name: contract.to_dict()
            for agent_name, contract in self.contracts.items()
        }
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

    def import_contracts(self, file_path: str) -> None:
        """從 JSON 檔案匯入契約"""
        with open(file_path, "r") as f:
            data = json.load(f)
        for agent_name, contract_data in data.items():
            self.contracts[agent_name] = Contract.from_dict(contract_data)


# ==================== Data Classes ====================


@dataclass
class TestCase:
    """測試案例"""
    name: str
    description: str
    input_data: Dict[str, Any]
    expected_valid: bool
    output_data: Optional[Dict[str, Any]] = None


@dataclass
class TestResult:
    """單一測試結果"""
    test_case: TestCase
    passed: bool
    actual_valid: bool
    expected_valid: bool
    error_message: str = ""

    def __post_init__(self):
        if not self.passed:
            self.error_message = (
                f"Expected valid={self.expected_valid}, "
                f"got valid={self.actual_valid}"
            )


@dataclass
class TestRunResult:
    """測試執行結果"""
    agent_name: str
    total: int
    passed: int
    failed: int
    results: List[TestResult]

    @property
    def success_rate(self) -> float:
        if self.total == 0:
            return 0.0
        return self.passed / self.total

    def summary(self) -> str:
        lines = [
            f"Test Run: {self.agent_name}",
            f"Total: {self.total} | Passed: {self.passed} | Failed: {self.failed}",
            f"Success Rate: {self.success_rate:.1%}",
            "",
        ]
        for r in self.results:
            icon = "✅" if r.passed else "❌"
            lines.append(f"  {icon} {r.test_case.name}: {r.error_message or 'OK'}")

        return "\n".join(lines)


@dataclass
class VerificationResult:
    """契約驗證結果"""
    agent_name: str
    success: bool
    errors: List[str]
    contract_version: str = ""

    def summary(self) -> str:
        icon = "✅" if self.success else "❌"
        lines = [f"{icon} Verification: {self.agent_name} (v{self.contract_version})"]
        if self.errors:
            for err in self.errors:
                lines.append(f"   - {err}")
        else:
            lines.append("   All checks passed")
        return "\n".join(lines)
