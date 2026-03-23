# Security Scanner Module

## 功能
- SAST 靜態分析
- Dependency 檢查
- CWE Top 25 漏洞檢測

## 使用方法

```python
from security_scanner import SecurityScanner

scanner = SecurityScanner()
result = scanner.scan_directory('src')
print(f"Score: {result['score']}")
```

## Quality Gate

- 安全分數 >= 95% 通過
- Critical: -20 分
- High: -10 分
- Medium: -5 分
