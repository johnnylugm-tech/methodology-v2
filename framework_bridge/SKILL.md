---
name: framework-bridge
description: CrewAI ↔ LangGraph migration with contract testing. Define agent contracts, verify outputs, and auto-generate test cases.
---

# FrameworkBridge Contract Testing

CrewAI ↔ LangGraph 遷移 + 契約測試模組

## Quick Start

```python
from framework_bridge import ContractTest, ContractValidator
from framework_bridge.contract_test import ContractSchema, SchemaField, ContractType

# 1. 建立契約測試器
tester = ContractTest()

# 2. 定義輸入/輸出 Schema
input_schema = ContractSchema(
    name="chat_input",
    fields=[
        SchemaField(name="prompt", type="string", required=True, description="User prompt"),
        SchemaField(name="temperature", type="number", required=False, default=0.7),
        SchemaField(name="mode", type="string", enum_values=["fast", "accurate"]),
    ],
)

output_schema = ContractSchema(
    name="chat_output",
    fields=[
        SchemaField(name="response", type="string", required=True),
        SchemaField(name="tokens_used", type="integer"),
    ],
)

# 3. 定義 Agent 契約
tester.define_contract(
    agent_name="ChatAgent",
    input_schema=input_schema,
    output_schema=output_schema,
)

# 4. 驗證輸出
result = tester.verify_contract(
    agent_name="ChatAgent",
    actual_input={"prompt": "Hello", "mode": "fast"},
    actual_output={"response": "Hi there!", "tokens_used": 42},
)
print(result.summary())

# 5. 自動生成測試案例
test_cases = tester.generate_test_cases("ChatAgent")
print(f"Generated {len(test_cases)} test cases")

# 6. 執行測試
run_result = tester.run_tests("ChatAgent")
print(run_result.summary())
```

## Features

### 契約定義 (Contract Definition)

```python
# 基本用法
tester.define_contract(
    agent_name="MyAgent",
    input_schema=input_schema,
    output_schema=output_schema,
    contract_type=ContractType.BIDIRECTIONAL,
    version="1.0.0",
)
```

### Schema 欄位類型

| Type | Python Type |
|------|-------------|
| `string` / `str` | `str` |
| `integer` / `int` | `int` |
| `number` / `float` | `int`, `float` |
| `boolean` / `bool` | `bool` |
| `array` / `list` | `list` |
| `object` / `dict` | `dict` |

### 欄位驗證選項

```python
SchemaField(
    name="field_name",
    type="string",
    required=True,           # 必填欄位
    default="value",         # 預設值
    enum_values=["a", "b"],  # 列舉值
    pattern=r"^[a-z]+$",     # Regex 模式
)
```

### 契約驗證器 (ContractValidator)

深度驗證，提供詳細差異報告：

```python
validator = ContractValidator()

# 單一驗證
report = validator.validate(contract, actual_data, strict=False)
print(report.summary())

# 批量驗證
reports = validator.validate_batch(contract, dataset)
print(validator.batch_summary(reports))

# 比較兩個契約
issues = validator.compare_contracts(contract_a, contract_b)
```

## CLI 使用

```bash
# 執行契約測試
python -m framework_bridge.cli contract-test --agent ChatAgent

# 驗證資料
python -m framework_bridge.cli verify --agent ChatAgent --data '{"prompt": "hi"}'

# 生成測試案例
python -m framework_bridge.cli generate --agent ChatAgent --output test_cases.json

# 深度驗證
python -m framework_bridge.cli validate --contract contract.json --data data.json --strict

# 比較契約
python -m framework_bridge.cli compare --a contract_a.json --b contract_b.json

# 批量驗證
python -m framework_bridge.cli batch --contract contract.json --dataset dataset.json

# 列出所有契約
python -m framework_bridge.cli list --contract-file contracts.json
```

## 匯出/匯入

```python
# 匯出契約到 JSON
tester.export_contracts("contracts.json")

# 匯入契約
new_tester = ContractTest()
new_tester.import_contracts("contracts.json")
```

## Contract Types

- `INPUT` - 只驗證輸入
- `OUTPUT` - 只驗證輸出
- `BIDIRECTIONAL` - 雙向驗證（預設）

## Example: 完整工作流

```python
from framework_bridge import ContractTest, ContractValidator
from framework_bridge.contract_test import ContractSchema, SchemaField

# 建立並定義契約
tester = ContractTest()

tester.define_contract(
    agent_name="TranslatorAgent",
    input_schema=ContractSchema(
        name="translator_input",
        fields=[
            SchemaField(name="text", type="string", required=True),
            SchemaField(name="target_lang", type="string", enum_values=["en", "zh", "ja"]),
        ],
    ),
    output_schema=ContractSchema(
        name="translator_output",
        fields=[
            SchemaField(name="translated_text", type="string", required=True),
            SchemaField(name="confidence", type="number"),
        ],
    ),
)

# 生成並執行測試
test_cases = tester.generate_test_cases("TranslatorAgent")
result = tester.run_tests("TranslatorAgent")

print(result.summary())
```
