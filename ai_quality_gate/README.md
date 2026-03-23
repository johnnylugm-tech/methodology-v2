# AI Quality Gate Module

## 功能
- 自動 Code Review
- 檢測 debug statements
- 檢測 hardcoded secrets
- AI 審查

## 使用方法

```python
from ai_quality_gate import AIQualityGate

gate = AIQualityGate()
result = gate.scan_directory('src')
print(f"Score: {result['score']}")
```

## Quality Gate

- 分數 >= 90 通過
- Debug: -1 分
- Security: -5 分
- TODO: -2 分
