# TDAD Testing Methodology - 完整手冊

> Test-Driven AI Agent Development：如何用測試驅動 AI Agent 開發

---

## 1️⃣ 概述

### 什麼是 TDAD？

TDAD (Test-Driven AI Agent Development) 是一種將傳統 TDD 概念應用於 AI Agent 開發的方法論。

**核心問題**：
- AI Agent 的輸出不穩定
- Prompt 改變會導致靜默回歸
- 工具誤用難以偵測
- 政策違規只在部署後才發現

**TDAD 解決方案**：
- 用測試定義行為規格
- 將 Agent Prompts 視為「編譯後的 Artifact」
- 持續驗證合規性

---

## 2️⃣ TDAD 四大核心概念

| 概念 | 說明 | methodology-v2 實作 |
|------|------|---------------------|
| **Compiled Prompts** | Agent prompts 作為編譯後的 artifact | `CompiledConstitution` |
| **Visible/Hidden Tests** | 開發時可見測試 vs 隱藏驗證測試 | `QualityGateTDAD` |
| **Mutation Testing** | 生成錯誤變體，測試是否能偵測 | `MutationTester` |
| **Impact Analysis** | 圖形化分析變更影響 | `ImpactAnalyzer` |

---

## 3️⃣ TDAD 工作流程

### 3.1 傳統 TDD vs TDAD

```
傳統 TDD：
Red → Green → Refactor
寫測試 → 讓程式通過 → 重構

TDAD：
Specify → Compile → Verify → Monitor
訂規格 → 編譯 Constitution → 驗證輸出 → 監控行為
```

### 3.2 TDAD 流程圖

```
┌─────────────────────────────────────────────────────────────┐
│                    TDAD 工作流程                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐                                          │
│  │   Specify   │ ← 定義行為規格                            │
│  └──────┬──────┘                                          │
│         ↓                                                  │
│  ┌─────────────┐                                          │
│  │  Compile    │ → CompiledConstitution                   │
│  └──────┬──────┘                                          │
│         ↓                                                  │
│  ┌─────────────┐    ┌─────────────┐                       │
│  │   Verify    │ ←→ │ Hidden Tests│ ← 最終驗證            │
│  └──────┬──────┘    └─────────────┘                       │
│         ↓                                                  │
│  ┌─────────────┐                                          │
│  │   Monitor   │ → Impact Analysis                        │
│  └─────────────┘                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 4️⃣ 詳細實作

### 4.1 Compiled Constitution

**概念**：將 Constitution 視為編譯後的 artifact，不可變更。

```python
from constitution import compile_constitution, verify_agent_output

# 編譯 Constitution
constitution = compile_constitution()

# 驗證 Agent 輸出
result = verify_agent_output(constitution, agent_output)

print(f"合規: {result['compliant']}")
print(f"分數: {result['score']}/100")
print(f"版本: {result['version']}")
```

**驗證項目**：
| 檢查項 | 說明 |
|--------|------|
| 關鍵詞檢查 | 禁止 bypass/skip/--no-verify |
| Task ID | 所有 commit 必須有 task_id |
| 審批流程 | 危險操作必須經過審批 |

### 4.2 Visible/Hidden Tests

**概念**：
- **Visible Tests**：開發者可見，用於引導開發
- **Hidden Tests**：僅用於最終驗證，防止 specification gaming

```python
from auto_quality_gate import QualityGateTDAD

gate = QualityGateTDAD()

# 添加可見測試（開發時使用）
gate.add_visible_test(
    test_id="vt-1",
    test_fn=lambda: check_syntax(code),
    description="語法檢查"
)

# 添加隱藏測試（最終驗證）
gate.add_hidden_test(
    test_id="ht-1",
    test_fn=lambda: check_security(code)
)

# 執行完整 Gate
result = gate.run_full_gate()

print(f"隱藏測試通過率: {result['hidden_pass_rate']}%")
print(f"TDAD 合規: {result['tdad_compliant']}")
```

**TDAD 合規標準**：
- Hidden Test Pass Rate >= 95%

### 4.3 Mutation Testing

**概念**：生成錯誤的程式碼變體，測試是否能偵測。

```python
from anti_shortcut.mutation_tester import MutationGenerator, MutationTester

# 生成變異體
generator = MutationGenerator()
mutations = generator.generate(code, num_mutations=20)

# 執行測試
tester = MutationTester(test_runner=lambda c: run_tests(c))
summary = tester.run_all(mutations)

print(f"Mutation Score: {summary['mutation_score']}%")
print(f"偵測率: {summary['detected']}/{summary['total']}")
```

**變異類型**：
| 類型 | 說明 |
|------|------|
| VARIABLE_REPLACE | 變數替換 |
| CONDITION_FLIP | 條件反轉 |
| LOGIC_DELETE | 刪除邏輯 |
| CONSTANT_CHANGE | 常數改變 |

### 4.4 Impact Analysis

**概念**：建立依賴圖，分析變更會影響哪些測試。

```python
from anti_shortcut.impact_analysis import ImpactAnalyzer

# 分析變更影響
analyzer = ImpactAnalyzer()
analyzer.scan_project()

impact = analyzer.analyze_change("src/core.py")

print(f"風險分數: {impact.risk_score}")
print(f"受影響測試: {len(impact.affected_tests)}")
print(f"建議: {impact.recommendations}")
```

**風險分數**：
| 分數 | 等級 | 建議 |
|------|------|------|
| 0-30 | 🟢 Low | 正常流程 |
| 31-60 | 🟡 Medium | 增加測試 |
| 61-100 | 🔴 High | Code review |

---

## 5️⃣ CLI 命令

```bash
# Constitution 編譯和驗證
python3 cli.py constitution compile
python3 cli.py constitution verify "<output>"

# Quality Gate
python3 cli.py quality gate --tdad

# Impact Analysis
python3 cli.py trace impact --file <file>
python3 cli.py trace graphviz
python3 cli.py trace risk-report

# Mutation Testing
python3 -m anti_shortcut.mutation_tester
```

---

## 6️⃣ TDAD 指標

| 指標 | 目標 | 說明 |
|------|------|------|
| **Hidden Pass Rate** | >= 95% | 隱藏測試通過率 |
| **Mutation Score** | >= 80% | 變異偵測率 |
| **Regression Safety** | >= 90% | 回歸安全分數 |
| **Compilation Success** | >= 90% | Constitution 編譯成功率 |

---

## 7️⃣ 與 methodology-v2 整合

### 7.1 在開發流程中啟用 TDAD

```bash
#!/bin/bash

# 1. 編譯 Constitution
python3 cli.py constitution compile || exit 1

# 2. 開始任務
export CONSTITUTION_VERSION=$(python3 cli.py constitution version)

# 3. 開發（每次 commit 前）
python3 cli.py constitution verify "$(git log -1 --format=%s)" || exit 1

# 4. Quality Gate
python3 cli.py quality gate --tdad || exit 1

# 5. 提交前 Impact Analysis
python3 cli.py trace impact --file $CHANGED_FILE || exit 1
```

### 7.2 與 Anti-Shortcut Framework 整合

```
TDAD + Anti-Shortcut：
     ↓
TDAD 確保：正確的行為被定義
Anti-Shortcut 確保：無法走捷徑
     ↓
雙重保障：行為定義 + 執行驗證
```

---

## 8️⃣ 常見問題

**Q: 為什麼 Hidden Test Pass Rate 重要？**

A: Hidden Tests 是用來防止「針對可見測試優化」的問題。如果開發者只通過 Visible Tests 但破壞了 Hidden Tests，說明 specification gaming 正在發生。

**Q: Mutation Score 低說明什麼？**

A: Mutation Score 低表示測試無法有效偵測錯誤。可能的原因：
- 測試覆蓋不足
- 測試太寬鬆
- 程式碼結構不易變異

**Q: Impact Analysis 的風險分數如何計算？**

A: 風險分數基於：
- 變更的檔案類型（core/base 高風險）
- 受影響的測試數量
- 依賴圖深度

---

## 9️⃣ 參考資源

| 資源 | 連結 |
|------|------|
| TDAD Paper 1 | arxiv.org/abs/2603.08806 |
| TDAD Paper 2 | arxiv.org/abs/2603.17973 |
| methodology-v2 | github.com/johnnylugm-tech/methodology-v2 |

---

## 📊 TDAD 檢查清單

在每次發布前檢查：

- [ ] Constitution 已編譯
- [ ] Hidden Pass Rate >= 95%
- [ ] Mutation Score >= 80%
- [ ] Impact Analysis 已執行
- [ ] 所有危險操作已審批

---

*最後更新：2026-03-23*