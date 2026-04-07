# methodology-v2 v5.26 上手指南

> **版本**: v5.26
> **日期**: 2026-03-23
> **目標**: 突破 9.0 品質分數

---

## 🚀 快速開始

### 安裝

```bash
cd /app/openclaw/skills/methodology-v2
git pull origin main
```

### 使用四個新模組

```python
# 1. AI Quality Gate - Code Review
from ai_quality_gate import AIQualityGate
gate = AIQualityGate()
result = gate.scan_directory('src')
print(f"Score: {result['score']}")

# 2. TDD Runner - 自動化測試
from tdd_runner import TDDRunner
tdd = TDDRunner()
tdd.generate_test_cases('src')
result = tdd.run_tests()
print(f"Coverage: {result['coverage']}%")

# 3. Multi-Agent Team - 協作開發
from multi_agent_team import MultiAgentTeam
team = MultiAgentTeam()
result = team.run_workflow('src')
print(f"Steps: {result['steps']}")

# 4. Security Scanner - 安全掃描
from security_scanner import SecurityScanner
scanner = SecurityScanner()
result = scanner.scan_directory('src')
print(f"Score: {result['score']}")
```

---

## 📋 四個方案詳解

### 方案 A: AI Quality Gate

**功能**: 自動 Code Review
- 檢測 debug statements
- 檢測 hardcoded secrets
- AI 審查

**Quality Gate**: score >= 90

### 方案 B: TDD Runner

**功能**: 測試驅動開發
- 自動化測試生成
- 覆蓋率計算
- Shift-Left Testing

**Quality Gate**: coverage >= 80%

### 方案 C: Multi-Agent Team

**功能**: 4 Agent 協作
- DevBot: 開發
- ReviewBot: 審查
- TestBot: 測試
- DocBot: 文件

**Quality Gate**: 4 steps completed

### 方案 D: Security Scanner

**功能**: 安全掃描
- SAST 靜態分析
- Dependency 檢查
- CWE Top 25 漏洞檢測

**Quality Gate**: score >= 95

---

## 🎯 完整工作流程

```
1. Constitution CLI
   ↓
2. 外部 spec 制定
   ↓
3. 開發 + AI Quality Gate (方案 A)
   ↓
4. TDD 測試 (方案 B)
   ↓
5. Multi-Agent 審查 (方案 C)
   ↓
6. Security Scan (方案 D)
   ↓
7. Quality Gate 把關
   ↓
8. 交付 (分數 >= 9.0)
```

---

## 📊 分數計算

| 維度 | 分數 | 權重 |
|------|------|------|
| 正確性 | 90 | 25% |
| 安全性 | 95 | 25% |
| 可維護性 | 85 | 25% |
| 覆蓋率 | 85 | 25% |
| **總分** | **9.0+** | 100% |

---

## 💡 常見問題

### Q1: 四個方案都要用嗎？
**A**: 建議全部使用以達到 9.0+ 分數

### Q2: 可以只用部分嗎？
**A**: 可以，但分數會對應降低

### Q3: 與舊版相容嗎？
**A**: 完全相容，這是增量模組

---

## 📚 相關文件

- `ai_quality_gate/README.md`
- `tdd_runner/README.md`
- `multi_agent_team/README.md`
- `security_scanner/README.md`
- `SKILL.md` (完整規範)

---

*最後更新：2026-03-23*
