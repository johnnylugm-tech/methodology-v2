# Quality Gate Module

## ASPICE Documentation Quality Gate

提供自動化文檔檢查功能。

### 使用方式

```bash
# 檢查當前目錄
python quality_gate/doc_checker.py

# 檢查指定目錄
python quality_gate/doc_checker.py --path /path/to/project

# JSON 輸出
python quality_gate/doc_checker.py --format json
```

### Python API

```python
from quality_gate.doc_checker import DocumentChecker

checker = DocumentChecker("/path/to/project")
report = checker.check_all()
print(report)
```

