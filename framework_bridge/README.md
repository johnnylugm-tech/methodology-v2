# FrameworkBridge - Contract Testing

CrewAI ↔ LangGraph 遷移工具的契約測試模組。

提供完整的 Agent 契約定義、驗證和自動測試生成能力。

## 目錄結構

```
framework_bridge/
├── __init__.py           # 套件初始化
├── contract_test.py      # 契約測試類 (ContractTest)
├── contract_validator.py # 契約驗證器 (ContractValidator)
├── cli.py                # 命令列介面
├── test_contract.py      # 單元測試
├── SKILL.md              # 技能文件
└── README.md             # 本文件
```

## 安裝

```bash
cd framework_bridge
pip install -e .
```

或直接使用（不需安裝）：

```python
import sys
sys.path.insert(0, "/path/to/methodology-v2")
from framework_bridge.contract_test import ContractTest, ContractValidator
```

## 快速開始

```python
from framework_bridge import ContractTest, ContractValidator
from framework_bridge.contract_test import ContractSchema, SchemaField

# 建立測試器
tester = ContractTest()

# 定義契約
tester.define_contract(
    agent_name="MyAgent",
    input_schema=ContractSchema(
        name="input",
        fields=[SchemaField(name="text", type="string", required=True)],
    ),
    output_schema=ContractSchema(
        name="output",
        fields=[SchemaField(name="result", type="string", required=True)],
    ),
)

# 驗證
result = tester.verify_contract(
    agent_name="MyAgent",
    actual_input={"text": "hello"},
    actual_output={"result": "world"},
)
print(result.summary())
```

## CLI 命令

```bash
# 執行測試
python -m framework_bridge.cli contract-test --agent MyAgent

# 驗證資料
python -m framework_bridge.cli verify --agent MyAgent --data '{"text": "hi"}'

# 生成測試案例
python -m framework_bridge.cli generate --agent MyAgent --output cases.json

# 深度驗證
python -m framework_bridge.cli validate --contract contract.json --strict

# 批量驗證
python -m framework_bridge.cli batch --contract contract.json --dataset data.json
```

## 執行測試

```bash
cd /Users/johnny/.openclaw/workspace-musk/skills/methodology-v2/framework_bridge
pytest test_contract.py -v
```

## 契約類型

| 類型 | 說明 |
|------|------|
| `INPUT` | 只驗證輸入 |
| `OUTPUT` | 只驗證輸出 |
| `BIDIRECTIONAL` | 雙向驗證（預設）|

## 驗證器功能

- **單一驗證**：`validator.validate(contract, data)`
- **批量驗證**：`validator.validate_batch(contract, dataset)`
- **契約比較**：`validator.compare_contracts(contract_a, contract_b)`
- **相容性檢查**：`validator.check_compatibility(contract, target_schema)`

## 與 FrameworkBridge.py 的關係

`crewai_bridge.py`（在 parent 目錄）提供 CrewAI ↔ LangGraph 遷移功能。
本目錄的契約測試模組可獨立使用，也可用於驗證遷移後的 Agent 是否符合契約。
