"""
CLI Commands for FrameworkBridge Contract Testing

提供命令列介面用於執行契約測試
"""

import argparse
import json
import sys
from typing import Optional, List

from framework_bridge.contract_test import (
    ContractTest,
    ContractSchema,
    SchemaField,
    ContractType,
    TestCase,
)
from framework_bridge.contract_validator import ContractValidator


def cmd_contract_test(args: argparse.Namespace) -> int:
    """
    執行契約測試

    Usage:
        python -m framework_bridge.cli contract-test --agent <name> --input <json>
    """
    tester = ContractTest()

    # 載入契約 (如果指定檔案)
    if args.contract_file:
        tester.import_contracts(args.contract_file)

    # 如果指定了 --define，在記憶體中建立契約
    if args.define:
        import ast
        try:
            definition = ast.literal_eval(args.define)
            agent_name = definition.get("agent_name", args.agent)
            tester.define_contract(
                agent_name=agent_name,
                input_schema=ContractSchema.from_dict(definition.get("input_schema", {})),
                output_schema=ContractSchema.from_dict(definition.get("output_schema", {})),
                contract_type=ContractType(definition.get("contract_type", "bidirectional")),
                version=definition.get("version", "1.0.0"),
            )
        except Exception as e:
            print(f"❌ Failed to parse --define: {e}", file=sys.stderr)
            return 1

    # 檢查 Agent 是否存在
    if args.agent not in tester.contracts:
        print(f"❌ Contract not found for agent: {args.agent}", file=sys.stderr)
        print(f"Available contracts: {tester.list_contracts()}", file=sys.stderr)
        return 1

    # 執行測試
    result = tester.run_tests(args.agent)

    # 輸出結果
    print(result.summary())

    return 0 if result.failed == 0 else 1


def cmd_contract_verify(args: argparse.Namespace) -> int:
    """
    驗證契約

    Usage:
        python -m framework_bridge.cli verify --agent <name> --data <json>
    """
    tester = ContractTest()

    # 載入契約
    if args.contract_file:
        tester.import_contracts(args.contract_file)

    if args.agent not in tester.contracts:
        print(f"❌ Contract not found for {args.agent}", file=sys.stderr)
        return 1

    # 解析資料
    if args.data:
        try:
            actual_data = json.loads(args.data)
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON in --data: {e}", file=sys.stderr)
            return 1
    else:
        actual_data = {}

    # 驗證
    result = tester.verify_contract(args.agent, actual_input=actual_data)
    print(result.summary())

    return 0 if result.success else 1


def cmd_contract_generate(args: argparse.Namespace) -> int:
    """
    生成測試案例

    Usage:
        python -m framework_bridge.cli generate --agent <name> [--output <file>]
    """
    tester = ContractTest()

    # 載入契約
    if args.contract_file:
        tester.import_contracts(args.contract_file)

    if args.agent not in tester.contracts:
        print(f"❌ Contract not found for {args.agent}", file=sys.stderr)
        return 1

    # 生成測試案例
    test_cases = tester.generate_test_cases(args.agent)

    # 輸出
    if args.output:
        with open(args.output, "w") as f:
            json.dump(
                [
                    {
                        "name": tc.name,
                        "description": tc.description,
                        "input_data": tc.input_data,
                        "expected_valid": tc.expected_valid,
                    }
                    for tc in test_cases
                ],
                f,
                indent=2,
            )
        print(f"✅ Generated {len(test_cases)} test cases -> {args.output}")
    else:
        print(f"Generated {len(test_cases)} test cases for {args.agent}:")
        for tc in test_cases:
            print(f"  - {tc.name}: {tc.description}")

    return 0


def cmd_contract_validate(args: argparse.Namespace) -> int:
    """
    深度驗證契約與資料差異

    Usage:
        python -m framework_bridge.cli validate --contract <file> --data <json>
    """
    validator = ContractValidator()

    # 載入契約
    with open(args.contract, "r") as f:
        contract_data = json.load(f)

    # 解析資料
    if args.data:
        actual_data = json.loads(args.data)
    else:
        actual_data = {}

    # 驗證
    report = validator.validate(contract_data, actual_data, strict=args.strict)
    print(report.summary())

    return 0 if report.is_valid else 1


def cmd_contract_compare(args: argparse.Namespace) -> int:
    """
    比較兩個契約

    Usage:
        python -m framework_bridge.cli compare --a <file> --b <file>
    """
    validator = ContractValidator()

    with open(args.a, "r") as f:
        contract_a = json.load(f)

    with open(args.b, "r") as f:
        contract_b = json.load(f)

    issues = validator.compare_contracts(contract_a, contract_b)

    if not issues:
        print("✅ Contracts are compatible")
        return 0

    print(f"⚠️ Found {len(issues)} differences:")
    for issue in issues:
        print(f"  {issue}")

    return 1


def cmd_contract_batch(args: argparse.Namespace) -> int:
    """
    批量驗證

    Usage:
        python -m framework_bridge.cli batch --contract <file> --dataset <json>
    """
    validator = ContractValidator()

    # 載入契約
    with open(args.contract, "r") as f:
        contract_data = json.load(f)

    # 載入資料集
    with open(args.dataset, "r") as f:
        dataset = json.load(f)

    # 批量驗證
    reports = validator.validate_batch(contract_data, dataset, strict=args.strict)
    print(validator.batch_summary(reports))

    valid_count = sum(1 for r in reports if r.is_valid)
    return 0 if valid_count == len(reports) else 1


def cmd_contract_list(args: argparse.Namespace) -> int:
    """列出所有契約"""
    tester = ContractTest()

    if args.contract_file:
        tester.import_contracts(args.contract_file)

    contracts = tester.list_contracts()

    if not contracts:
        print("No contracts defined")
        return 0

    print(f"Contracts ({len(contracts)}):")
    for name in contracts:
        contract = tester.get_contract(name)
        if contract:
            print(f"  - {name} (v{contract.version}, {contract.contract_type.value})")
            print(f"      Input fields: {[f.name for f in contract.input_schema.fields]}")
            print(f"      Output fields: {[f.name for f in contract.output_schema.fields]}")

    return 0


# ==================== CLI Entry Point ====================


def main():
    parser = argparse.ArgumentParser(
        description="FrameworkBridge Contract Testing CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # contract-test
    p_test = subparsers.add_parser("contract-test", help="Run contract tests")
    p_test.add_argument("--agent", required=True, help="Agent name")
    p_test.add_argument("--contract-file", help="Contract JSON file")
    p_test.add_argument("--define", help="Contract definition (Python dict literal)")
    p_test.add_argument("--input", help="Input JSON data")
    p_test.set_defaults(func=cmd_contract_test)

    # verify
    p_verify = subparsers.add_parser("verify", help="Verify data against contract")
    p_verify.add_argument("--agent", required=True, help="Agent name")
    p_verify.add_argument("--contract-file", help="Contract JSON file")
    p_verify.add_argument("--data", help="Data JSON to verify")
    p_verify.set_defaults(func=cmd_contract_verify)

    # generate
    p_gen = subparsers.add_parser("generate", help="Generate test cases")
    p_gen.add_argument("--agent", required=True, help="Agent name")
    p_gen.add_argument("--contract-file", help="Contract JSON file")
    p_gen.add_argument("--output", help="Output file for test cases")
    p_gen.set_defaults(func=cmd_contract_generate)

    # validate
    p_val = subparsers.add_parser("validate", help="Deep validate contract")
    p_val.add_argument("--contract", required=True, help="Contract JSON file")
    p_val.add_argument("--data", help="Data JSON to validate")
    p_val.add_argument("--strict", action="store_true", help="Strict mode")
    p_val.set_defaults(func=cmd_contract_validate)

    # compare
    p_cmp = subparsers.add_parser("compare", help="Compare two contracts")
    p_cmp.add_argument("--a", required=True, help="First contract file")
    p_cmp.add_argument("--b", required=True, help="Second contract file")
    p_cmp.set_defaults(func=cmd_contract_compare)

    # batch
    p_batch = subparsers.add_parser("batch", help="Batch validation")
    p_batch.add_argument("--contract", required=True, help="Contract file")
    p_batch.add_argument("--dataset", required=True, help="Dataset JSON file")
    p_batch.add_argument("--strict", action="store_true", help="Strict mode")
    p_batch.set_defaults(func=cmd_contract_batch)

    # list
    p_list = subparsers.add_parser("list", help="List all contracts")
    p_list.add_argument("--contract-file", help="Contract JSON file")
    p_list.set_defaults(func=cmd_contract_list)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return 0

    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
