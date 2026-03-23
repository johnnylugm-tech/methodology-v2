# methodology-v2 v5.26 範例

> **版本**: v5.26

---

## 範例 1: AI Quality Gate

```python
from ai_quality_gate import AIQualityGate

gate = AIQualityGate()
result = gate.scan_directory('src')
print(f"Score: {result['score']}")
```

## 範例 2: TDD Runner

```python
from tdd_runner import TDDRunner

tdd = TDDRunner()
tdd.generate_test_cases('src')
result = tdd.run_tests()
print(f"Coverage: {result['coverage']}%")
```

## 範例 3: Multi-Agent Team

```python
from multi_agent_team import MultiAgentTeam

team = MultiAgentTeam()
result = team.run_workflow('src')
print(f"Steps: {result['steps']}")
```

## 範例 4: Security Scanner

```python
from security_scanner import SecurityScanner

scanner = SecurityScanner()
result = scanner.scan_directory('src')
print(f"Score: {result['score']}")
```

---

*最後更新：2026-03-23*
