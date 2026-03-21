"""
Tests for Contract Testing Module
"""

import pytest
from framework_bridge.contract_test import (
    ContractTest,
    ContractValidator,
    ContractSchema,
    SchemaField,
    ContractType,
    Contract,
    TestCase,
    TestResult,
    VerificationResult,
    TestRunResult,
)
from framework_bridge.contract_validator import ValidationReport, ValidationSeverity


class TestContractTest:
    """Test ContractTest"""

    def setup_method(self):
        self.tester = ContractTest()

    def test_define_contract(self):
        """Test defining a contract"""
        input_schema = ContractSchema(
            name="test_input",
            fields=[
                SchemaField(name="prompt", type="string", required=True),
                SchemaField(name="temperature", type="number", required=False, default=0.7),
            ],
        )
        output_schema = ContractSchema(
            name="test_output",
            fields=[
                SchemaField(name="response", type="string", required=True),
                SchemaField(name="tokens_used", type="integer", required=False),
            ],
        )

        contract = self.tester.define_contract(
            agent_name="TestAgent",
            input_schema=input_schema,
            output_schema=output_schema,
        )

        assert contract.agent_name == "TestAgent"
        assert len(contract.input_schema.fields) == 2
        assert len(contract.output_schema.fields) == 2

    def test_get_contract(self):
        """Test getting a contract"""
        input_schema = ContractSchema(
            name="input",
            fields=[SchemaField(name="text", type="string")],
        )
        output_schema = ContractSchema(
            name="output",
            fields=[SchemaField(name="result", type="string")],
        )

        self.tester.define_contract(
            agent_name="MyAgent",
            input_schema=input_schema,
            output_schema=output_schema,
        )

        contract = self.tester.get_contract("MyAgent")
        assert contract is not None
        assert contract.agent_name == "MyAgent"

        missing = self.tester.get_contract("NonExistent")
        assert missing is None

    def test_verify_contract_valid(self):
        """Test verification with valid data"""
        input_schema = ContractSchema(
            name="input",
            fields=[SchemaField(name="prompt", type="string", required=True)],
        )
        output_schema = ContractSchema(
            name="output",
            fields=[SchemaField(name="response", type="string", required=True)],
        )

        self.tester.define_contract(
            agent_name="ChatAgent",
            input_schema=input_schema,
            output_schema=output_schema,
        )

        result = self.tester.verify_contract(
            agent_name="ChatAgent",
            actual_input={"prompt": "Hello"},
            actual_output={"response": "Hi there"},
        )

        assert result.success is True
        assert len(result.errors) == 0

    def test_verify_contract_missing_required(self):
        """Test verification with missing required field"""
        input_schema = ContractSchema(
            name="input",
            fields=[SchemaField(name="prompt", type="string", required=True)],
        )
        output_schema = ContractSchema(
            name="output",
            fields=[SchemaField(name="response", type="string", required=True)],
        )

        self.tester.define_contract(
            agent_name="ChatAgent",
            input_schema=input_schema,
            output_schema=output_schema,
        )

        result = self.tester.verify_contract(
            agent_name="ChatAgent",
            actual_input={},  # missing prompt
            actual_output={"response": "Hi"},
        )

        assert result.success is False
        assert any("Missing required field" in e for e in result.errors)

    def test_verify_contract_type_error(self):
        """Test verification with type error"""
        input_schema = ContractSchema(
            name="input",
            fields=[SchemaField(name="count", type="integer", required=True)],
        )
        output_schema = ContractSchema(
            name="output",
            fields=[SchemaField(name="result", type="string")],
        )

        self.tester.define_contract(
            agent_name="CountAgent",
            input_schema=input_schema,
            output_schema=output_schema,
        )

        result = self.tester.verify_contract(
            agent_name="CountAgent",
            actual_input={"count": "not_an_integer"},
        )

        assert result.success is False
        assert any("expected type integer" in e for e in result.errors)

    def test_verify_contract_unknown_agent(self):
        """Test verification with unknown agent"""
        result = self.tester.verify_contract(
            agent_name="UnknownAgent",
            actual_input={},
        )

        assert result.success is False
        assert any("Contract not found" in e for e in result.errors)

    def test_generate_test_cases(self):
        """Test generating test cases"""
        input_schema = ContractSchema(
            name="input",
            fields=[
                SchemaField(name="text", type="string", required=True),
                SchemaField(name="mode", type="string", required=False, enum_values=["fast", "accurate"]),
            ],
        )
        output_schema = ContractSchema(
            name="output",
            fields=[SchemaField(name="result", type="string", required=True)],
        )

        self.tester.define_contract(
            agent_name="ProcessorAgent",
            input_schema=input_schema,
            output_schema=output_schema,
        )

        test_cases = self.tester.generate_test_cases("ProcessorAgent")

        assert len(test_cases) > 0
        # Should have: required_field_text, missing_required_text, type_error_text, valid_input_all_fields, enum_mode_*, enum_invalid_mode
        names = [tc.name for tc in test_cases]
        assert "required_field_text" in names
        assert "missing_required_text" in names
        assert "valid_input_all_fields" in names

    def test_run_tests(self):
        """Test running tests"""
        input_schema = ContractSchema(
            name="input",
            fields=[SchemaField(name="value", type="integer", required=True)],
        )
        output_schema = ContractSchema(
            name="output",
            fields=[SchemaField(name="doubled", type="integer")],
        )

        self.tester.define_contract(
            agent_name="DoublerAgent",
            input_schema=input_schema,
            output_schema=output_schema,
        )

        result = self.tester.run_tests("DoublerAgent")

        assert isinstance(result, TestRunResult)
        assert result.total > 0
        assert result.passed + result.failed == result.total

    def test_export_import_contracts(self, tmp_path):
        """Test export and import of contracts"""
        input_schema = ContractSchema(
            name="input",
            fields=[SchemaField(name="text", type="string")],
        )
        output_schema = ContractSchema(
            name="output",
            fields=[SchemaField(name="result", type="string")],
        )

        self.tester.define_contract(
            agent_name="ExportTestAgent",
            input_schema=input_schema,
            output_schema=output_schema,
        )

        file_path = tmp_path / "contracts.json"
        self.tester.export_contracts(str(file_path))

        new_tester = ContractTest()
        new_tester.import_contracts(str(file_path))

        assert "ExportTestAgent" in new_tester.list_contracts()


class TestContractValidator:
    """Test ContractValidator"""

    def setup_method(self):
        self.validator = ContractValidator()

    def test_validate_valid_data(self):
        """Test validation with valid data"""
        contract = {
            "agent_name": "TestAgent",
            "contract_type": "bidirectional",
            "input_schema": {
                "name": "input",
                "fields": [
                    {"name": "text", "type": "string", "required": True},
                ],
            },
            "output_schema": {
                "name": "output",
                "fields": [
                    {"name": "result", "type": "string", "required": True},
                ],
            },
        }

        actual = {
            "input": {"text": "hello"},
            "output": {"result": "world"},
        }

        report = self.validator.validate(contract, actual)

        assert report.is_valid is True
        assert report.error_count == 0

    def test_validate_type_error(self):
        """Test validation with type error"""
        contract = {
            "agent_name": "TestAgent",
            "contract_type": "bidirectional",
            "input_schema": {
                "name": "input",
                "fields": [
                    {"name": "count", "type": "integer", "required": True},
                ],
            },
            "output_schema": {
                "name": "output",
                "fields": [],
            },
        }

        actual = {"input": {"count": "not_int"}}

        report = self.validator.validate(contract, actual)

        assert report.is_valid is False
        assert any(
            "Type mismatch" in str(i) for i in report.issues
        )

    def test_validate_enum_error(self):
        """Test validation with enum error"""
        contract = {
            "agent_name": "TestAgent",
            "contract_type": "bidirectional",
            "input_schema": {
                "name": "input",
                "fields": [
                    {
                        "name": "mode",
                        "type": "string",
                        "required": True,
                        "enum_values": ["fast", "slow"],
                    },
                ],
            },
            "output_schema": {"name": "output", "fields": []},
        }

        actual = {"input": {"mode": "invalid"}}

        report = self.validator.validate(contract, actual)

        assert report.is_valid is False
        assert any("enum" in str(i).lower() for i in report.issues)

    def test_validate_strict_extra_fields(self):
        """Test strict mode with extra fields"""
        contract = {
            "agent_name": "TestAgent",
            "contract_type": "bidirectional",
            "input_schema": {"name": "input", "fields": []},
            "output_schema": {"name": "output", "fields": []},
        }

        actual = {"extra_field": "value"}

        # Non-strict: should pass
        report = self.validator.validate(contract, actual, strict=False)
        assert report.warning_count == 0

        # Strict: should warn
        report = self.validator.validate(contract, actual, strict=True)
        assert report.warning_count > 0

    def test_compare_contracts(self):
        """Test comparing two contracts"""
        contract_a = {
            "agent_name": "AgentA",
            "input_schema": {
                "fields": [
                    {"name": "field1", "type": "string"},
                    {"name": "field2", "type": "integer"},
                ],
            },
            "output_schema": {"fields": []},
        }

        contract_b = {
            "agent_name": "AgentB",
            "input_schema": {
                "fields": [
                    {"name": "field1", "type": "string"},
                    {"name": "field3", "type": "boolean"},
                ],
            },
            "output_schema": {"fields": []},
        }

        issues = self.validator.compare_contracts(contract_a, contract_b)

        assert len(issues) > 0
        field_names = {i.field_path for i in issues}
        assert "input.field2" in field_names
        assert "input.field3" in field_names

    def test_batch_validation(self):
        """Test batch validation"""
        contract = {
            "agent_name": "TestAgent",
            "contract_type": "bidirectional",
            "input_schema": {
                "fields": [
                    {"name": "text", "type": "string", "required": True},
                ],
            },
            "output_schema": {"fields": []},
        }

        dataset = [
            {"input": {"text": "first"}},
            {"input": {"text": "second"}},
            {"input": {}},  # invalid - missing required
        ]

        reports = self.validator.validate_batch(contract, dataset)

        assert len(reports) == 3
        assert reports[0].is_valid is True
        assert reports[1].is_valid is True
        assert reports[2].is_valid is False


class TestSchemaField:
    """Test SchemaField"""

    def test_schema_field_creation(self):
        """Test creating a schema field"""
        field = SchemaField(
            name="test_field",
            type="string",
            required=True,
            description="A test field",
            default="default_value",
            enum_values=["a", "b", "c"],
            pattern=r"^[a-z]+$",
        )

        assert field.name == "test_field"
        assert field.type == "string"
        assert field.required is True
        assert field.default == "default_value"
        assert field.enum_values == ["a", "b", "c"]
        assert field.pattern == r"^[a-z]+$"


class TestContractSchema:
    """Test ContractSchema"""

    def test_to_dict_from_dict(self):
        """Test serialization roundtrip"""
        schema = ContractSchema(
            name="test_schema",
            description="A test schema",
            fields=[
                SchemaField(name="field1", type="string", required=True),
                SchemaField(name="field2", type="integer", required=False, default=0),
            ],
        )

        data = schema.to_dict()
        restored = ContractSchema.from_dict(data)

        assert restored.name == schema.name
        assert restored.description == schema.description
        assert len(restored.fields) == len(schema.fields)
        assert restored.fields[0].name == "field1"
        assert restored.fields[1].default == 0


class TestContract:
    """Test Contract"""

    def test_to_dict_from_dict(self):
        """Test contract serialization"""
        input_schema = ContractSchema(
            name="input",
            fields=[SchemaField(name="text", type="string")],
        )
        output_schema = ContractSchema(
            name="output",
            fields=[SchemaField(name="result", type="string")],
        )

        contract = Contract(
            agent_name="TestAgent",
            input_schema=input_schema,
            output_schema=output_schema,
            contract_type=ContractType.BIDIRECTIONAL,
            version="2.0.0",
            metadata={"author": "test"},
        )

        data = contract.to_dict()
        restored = Contract.from_dict(data)

        assert restored.agent_name == "TestAgent"
        assert restored.version == "2.0.0"
        assert restored.contract_type == ContractType.BIDIRECTIONAL
        assert restored.metadata["author"] == "test"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
