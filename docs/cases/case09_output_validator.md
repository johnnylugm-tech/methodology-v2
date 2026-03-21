# 案例九：Agent Output Validator (方案 F)

## 概述

Agent Output Validator 是專為解決「Agent 輸出格式不一致」問題而設計的驗證框架，確保不同 Agent 間的輸出符合統一規範。

---

## 問題背景

```
CrewAI agents produce inconsistent output schemas
當 Agent 產生不良輸出時，很難追蹤哪個步驟出了問題
```

---

## 核心功能

| 功能 | 說明 |
|------|------|
| JSON Schema 驗證 | 標準 JSON Schema 格式校驗 |
| Pydantic 模型驗證 | Python 類型安全的模型驗證 |
| 自訂規則驗證 | 業務邏輯自訂規則 |
| 自動修復 | 常見問題自動修復 |

---

## 快速開始

### 基本使用

```python
from agent_output_validator import AgentOutputValidator
from pydantic import BaseModel

# 定義輸出模型
class UserInfo(BaseModel):
    name: str
    email: str
    age: int

# 創建驗證器
validator = AgentOutputValidator()

# 驗證輸出
result = validator.validate(
    output={"name": "John", "email": "john@example.com", "age": 30},
    schema=UserInfo
)

if result.is_valid:
    print("✅ 輸出有效")
else:
    print(f"❌ 錯誤: {result.errors}")
```

### 自動修復

```python
# 自動修復常見問題
fixed = validator.auto_fix(output, schema)
```

### 與 QualityGate 整合

```python
from auto_quality_gate import AutoQualityGate

gate = AutoQualityGate()
result = gate.validate_output(output, schema)
```

---

## 驗證結果

```python
@dataclass
class ValidationResult:
    is_valid: bool
    errors: List[ValidationError]
    warnings: List[str]
    fixed_output: Any = None
```

---

## 與 StructuredOutputEngine 整合

```python
from structured_output import StructuredOutputEngine

engine = StructuredOutputEngine()

# 帶驗證的輸出解析
result = engine.parse_with_validation(
    prompt="擷取用戶資訊",
    llm_call=llm_fn,
    schema=UserInfo,
    validator=validator
)
```

---

## CLI 使用

```bash
# 驗證輸出
python cli.py validate output.json --schema schema.json

# 自動修復
python cli.py validate output.json --schema schema.json --fix
```

---

## 錯誤處理

| 錯誤類型 | 說明 | 處理方式 |
|----------|------|----------|
| SCHEMA_MISMATCH | 輸出不符合 Schema | 返回錯誤列表 |
| TYPE_ERROR | 類型錯誤 | 嘗試自動轉換 |
| MISSING_FIELD | 缺少必要欄位 | 使用預設值或報錯 |
| INVALID_FORMAT | 格式錯誤 | 根據格式修復 |

---

## 最佳實踐

1. **為每個 Agent 定義明確的輸出 Schema**
2. **在接收輸出後立即驗證**
3. **使用自動修復處理常見問題**
4. **與 QualityGate 整合實現完整品質把關**

---

## 相關模組

| 模組 | 說明 |
|------|------|
| StructuredOutputEngine | 結構化輸出解析 |
| AutoQualityGate | 自動化品質把關 |
| ErrorClassifier | 錯誤分類 |
