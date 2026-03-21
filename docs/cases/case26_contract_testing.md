# Case 26: Contract Testing - 契約測試

## 情境

多個 Agent 協作時，介面契約需要被測試，防止一方更新導致其他 Agent 失效。

## 解決方案

```python
from framework_bridge import ContractTest, ContractValidator

# 定義契約
tester = ContractTest()
tester.define_contract(
    agent_name="order-agent",
    input_schema={"order_id": "string"},
    output_schema={"status": "string", "amount": "number"}
)

# 驗證輸出
is_valid, errors = tester.verify_contract(
    "order-agent",
    {"status": "shipped", "amount": 100.0}
)

# 生成測試案例
test_cases = tester.generate_test_cases("order-agent")
```

## 功能

| 功能 | 說明 |
|------|------|
| 契約定義 | Input/Output Schema |
| 自動驗證 | 深度驗證 + 差異報告 |
| 測試生成 | 根據契約自動生成案例 |
| CLI | 命令列測試工具 |

## CLI

```bash
python framework_bridge/cli.py contract-test order-agent
python framework_bridge/test_contract.py
```

## Related

- framework_bridge.py
- framework_bridge/contract_test.py
- framework_bridge/contract_validator.py
