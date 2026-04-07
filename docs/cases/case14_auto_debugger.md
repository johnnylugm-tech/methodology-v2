# 案例 14：Auto Debugger (auto_debugger)

## 概述

Systematic debugging for AI agents with error classification, root cause analysis, and auto-recovery.

---

## 快速開始

```python
from auto_debugger import AutoDebugger, ErrorClassifier, RootCauseAnalyzer

# Initialize debugger
debugger = AutoDebugger()

# Analyze error
result = debugger.analyze(error, agent_state)

# Auto-recover
recovery = debugger.suggest_recovery(error_type)
debugger.auto_recover(agent, error)
```

---

## 核心功能

| 功能 | 說明 |
|------|------|
| Error Classification | L1-L4 錯誤分類 |
| Root Cause Analysis | 根因分析 |
| Auto-Recovery | 自動恢復 |
| Debug Dashboard | 調試儀表板 |

---

## 錯誤分類 (L1-L4)

```python
from auto_debugger import ErrorClassifier

classifier = ErrorClassifier()
level = classifier.classify(error)

# L1: 立即返回
# L2: 重試 3 次
# L3: 降級處理
# L4: 熔斷 + 警報
```

---

## 與現有模組整合

| 模組 | 整合點 |
|------|--------|
| agent_debugger | 共享除錯系統 |
| QualityGate | 品質把關 |
| FailoverManager | 故障轉移 |

---

## CLI 使用

```bash
# 分析錯誤
python cli.py debug analyze --error-id 123

# 查看根因
python cli.py debug root-cause --trace-id 456
```

---

## 相關模組

- agent_debugger.py
- auto_quality_gate.py
- failover_manager.py
