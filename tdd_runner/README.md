# TDD Runner Module

## 功能
- 自動化測試生成
- 測試覆蓋率計算
- Shift-Left Testing

## 使用方法

```python
from tdd_runner import TDDRunner

runner = TDDRunner()
runner.generate_test_cases('src')
result = runner.run_tests()
print(f"Coverage: {result['coverage']}%")
```

## Quality Gate

- 覆蓋率 >= 80% 通過
