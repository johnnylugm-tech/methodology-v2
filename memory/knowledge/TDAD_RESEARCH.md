# TDAD Research Summary

## 研究來源

| 研究 | 機構 | 核心發現 |
| ------------------- | ------ | --------------------------------------------- |
| TDAD (2603.08806) | F-labs | Agent prompts as compiled artifacts，92% 編譯成功率 |
| TDAD (2603.17973) | 獨立研究 | TDD prompting alone 反而增加回歸 9.94% |
| Simon Willison | 獨立研究者 | Red/Green TDD 非常適合 coding agents |
| CloudQA 2026 Trends | 業界 | Agentic AI 帶來 40% 測試覆蓋提升 |

---

## 關鍵發現

### 1. TDD prompting alone 增加回歸 9.94%

**原因**：Smaller models 從 procedural instructions 獲益少，從 contextual information (which tests to verify) 獲益多

**啟示**：
- 不要只給流程，要給上下文
- 「要測試什麼」比「如何做 TDD」更重要

### 2. Graph-Based Impact Analysis 減少回歸 70%

**做法**：
- 建立原始碼和測試之間的依賴圖
- 預測變更會影響哪些測試
- 讓 agent 知道提交前要驗證哪些測試

**效果**：
- 回歸：6.08% → 1.82%（降低 70%）
- Issue resolution：24% → 32%

### 3. Visible/Hidden Test Splits

**目的**：防止 specification gaming

**做法**：
- Visible Tests：開發者可見，用於引導開發
- Hidden Tests：僅用於最終驗證，開發者不知道有哪些

### 4. Mutation Testing

**目的**：測試測試的有效性

**做法**：
- 生成錯誤的程式碼變體
- 測試是否能偵測這些變體
- Mutation Score = 偵測到的變體 / 總變體數

---

## 與 methodology-v2 的整合

| TDAD 概念 | methodology-v2 實作 | 狀態 |
|-----------|-------------------|------|
| Compiled Prompts | `CompiledConstitution` | ✅ 已實作 |
| Visible/Hidden Tests | `QualityGateTDAD` | ✅ 已實作 |
| Mutation Testing | `MutationTester` | ✅ 已實作 |
| Impact Analysis | `ImpactAnalyzer` | ✅ 已實作 |

---

*最後更新：2026-03-23*