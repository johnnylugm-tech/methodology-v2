# methodology-v2 使用者手冊

> **版本**: v5.26
> **目標**: 品質分數 9.0+

---

## 誰應該使用？

- AI Agent 開發者
- 軟體工程團隊
- 追求高品質代碼的開發者

---

## 核心概念

### 品質公式

```
好的規格 + 好的方法論 + 好的驗證 + AI 輔助 = 9.0+
```

### 四個方案

| 方案 | 目標 | 分數貢獻 |
|------|------|----------|
| A: AI Quality Gate | 自動審查 | +0.3 |
| B: TDD Runner | 測試覆蓋 | +0.2 |
| C: Multi-Agent | 協作審查 | +0.2 |
| D: Security Scanner | 安全掃描 | +0.1 |

---

## 快速開始

### 步驟 1: 安裝

```bash
git clone https://github.com/johnnylugm-tech/methodology-v2.git
cd methodology-v2
```

### 步驟 2: 使用 Constitution CLI

```bash
python3 cli.py constitution view
python3 cli.py constitution thresholds
```

### 步驟 3: 開發專案

```bash
# 初始化專案
python3 cli.py init my-project

# 使用 AI Quality Gate
python3 -c "from ai_quality_gate import AIQualityGate; print(AIQualityGate().scan_directory('src'))"

# 使用 TDD Runner
python3 -c "from tdd_runner import TDDRunner; print(TDDRunner().generate_test_cases('src'))"

# 使用 Multi-Agent
python3 -c "from multi_agent_team import MultiAgentTeam; print(MultiAgentTeam().run_workflow('src'))"

# 使用 Security Scanner
python3 -c "from security_scanner import SecurityScanner; print(SecurityScanner().scan_directory('src'))"
```

---

## Quality Gate 閾值

| 檢查項 | 閾值 | 說明 |
|--------|------|------|
| AI Quality Score | >= 90 | 自動審查分數 |
| TDD Coverage | >= 80% | 測試覆蓋率 |
| Multi-Agent Steps | >= 4 | 完成的步驟數 |
| Security Score | >= 95 | 安全掃描分數 |
| Correctness | >= 80 | 正確性 |
| Security | >= 100 | 安全性 |
| Maintainability | >= 70 | 可維護性 |

---

## 最佳實踐

### 1. 每次 Commit 前

```bash
python3 -c "from ai_quality_gate import AIQualityGate; gate = AIQualityGate(); gate.scan_directory('src')"
```

### 2. 提交前測試

```bash
python3 -c "from tdd_runner import TDDRunner; tdd = TDDRunner(); tdd.generate_test_cases('src')"
```

### 3. 代碼審查

```bash
python3 -c "from multi_agent_team import MultiAgentTeam; team = MultiAgentTeam(); team.run_workflow('src')"
```

### 4. 安全檢查

```bash
python3 -c "from security_scanner import SecurityScanner; scanner = SecurityScanner(); scanner.scan_directory('src')"
```

---

## 與舊版比較

| 版本 | 分數 | 新增功能 |
|------|------|----------|
| v5.21 | 7.8 | Constitution CLI |
| v5.25 | 8.3 | TDAD |
| v5.26 | **9.0+** | 4 方案整合 |

---

## 常見問題

### Q: 需要多少時間學習？
**A**: 30 分鐘閱讀本手冊

### Q: 與現有工作流程相容嗎？
**A**: 是的，完全相容

### Q: 可以只用部分功能嗎？
**A**: 可以，但分數會對應降低

---

## 技術支援

- GitHub: https://github.com/johnnylugm-tech/methodology-v2
- Issues: https://github.com/johnnylugm-tech/methodology-v2/issues

---

*最後更新：2026-03-23*
