# 軟體品質提升 AutoResearch Prompt 模板

> 基於 `https://github.com/karpathy/autoresearch`
> 版本: v1.1.0
> 更新: 2026-04-11

---

## 📋 軟體品質提升 AutoResearch 模板

---

### 第一階段：定義品質基線與瓶頸分析 (Quality Baseline Setup)

> **指令**：
> 請充當 AI 軟體品質工程師 (Senior Quality Engineer)。
> 
> **目標專案**：`/path/to/project`
> 
> **研究任務**：
> 1. 首先執行 `python3 quality_dashboard/dashboard.py --project /path/to/project` 取得初始分數
> 2. 分析 9 個維度的分數：
>    - D1 Linting (10%) - 目標 ≥85%
>    - D2 Type Safety (15%) - 目標 ≥90%
>    - D3 Test Coverage (20%) - 目標 ≥70%
>    - D4 Security (15%) - 目標 ≥90%
>    - D5 Complexity (10%) - 目標 ≥80%
>    - D6 Architecture (10%) - 目標 ≥70%
>    - D7 Readability (10%) - 目標 ≥70%
>    - D8 Error Handling (5%) - 目標 ≥60%
>    - D9 Documentation (5%) - 目標 ≥70%
> 
> **產出**：
> - 熱點問題列表（分數最低的維度）
> - 瓶頸分析（為何這些維度分數低）
> - 優先修復順序建議

---

### 第二階段：設定品質評分量表 (Quality Evaluation Metrics)

> **指令**：
> 請根據以下 9 個維度對品質改進結果進行評分（0-10 分）：
> 
> | 維度 | 權重 | 評估標準 |
> |------|------|---------|
> | **D1 Linting** | 10% | ruff/flake8 錯誤數量，代碼風格一致性 |
> | **D2 TypeSafety** | 15% | mypy 錯誤數量，類型註解完整度 |
> | **D3 Coverage** | 20% | pytest-cov 覆蓋率，關鍵函數是否被測試 |
> | **D4 Security** | 15% | bandit 安全問題數量，是否有已知漏洞 |
> | **D5 Complexity** | 10% | lizard CCN 複雜度，函數是否過於複雜 |
> | **D6 Architecture** | 10% | radon 架構評分，模組耦合度 |
> | **D7 Readability** | 10% | 代碼可讀性，是否符合 PEP8 |
> | **D8 ErrorHandling** | 5% | 錯誤處理覆蓋率，是否有 try-except |
> | **D9 Documentation** | 5% | docstring 完整度，是否有使用範例 |
> 
> **評估維度**：
> - [改進幅度]：相比上一輪，分數提升了多少？
> - [改進品質]：修復是否實質提升了品質，而非只是繞過問題？
> - [副作用風險]：修復是否可能引入新的問題？
> - [可維護性]：修復後的代碼是否容易維護？

---

### 第三階段：啟動「上帝模式」品質改進迭代 (The Quality Evolution Loop)

> **指令**：
> 依據 AutoResearch 手法，執行 **5 輪**品質改進：
> 
> ```
> 每輪迭代流程：
> 
> Round 1: 基於初始評估結果
> ├─ 識別最低分維度（D2/D3/D4 通常最關鍵）
> ├─ Agent 修復（使用 sessions_spawn 或手動）
> ├─ 重新評估 9 維度
> └─ 記錄改進幅度
> 
> Round 2-5: 持續優化
> ├─ 分析上一輪修復效果
> ├─ 針對仍然低分的維度深入修復
> ├─ 避免重複修復已達標維度
> └─ 目標：9 維度全部 ≥8 分（加權後總分 ≥85%）
> ```
> 
> **迭代策略**：
> 1. **初稿修復**：針對最緊急的維度（D3 Coverage 通常優先）
> 2. **批判性審查 (Self-Criticism)**：模擬「資深工程師」視角，提出質疑：
>    - 「這個修復是否真正解決了問題？」
>    - 「是否引入了新的技術債？」
>    - 「這個修復是否可持續？」
> 3. **提示詞進化 (Prompt Refinement)**：
>    - 自動修改下一輪的指令
>    - 加入「反直覺發現」的權重
>    - 強制 AI 尋找非共識的深刻洞察
> 4. **終稿優化**：整合所有反饋，產出最終品質報告

---

### 第四階段：研究成果落地儀表板 (Quality Dashboard)

> **指令**：
> 利用 artifacts 或 markdown 建立一個 **Quality Improvement Dashboard**：
> 
> ```markdown
> ## 品質提升儀表板
> 
> ### 關鍵指標摘要
> | 維度 | 基線分數 | Round 1 | Round 2 | Round 3 | Round 4 | Round 5 | 最終 |
> |------|---------|---------|---------|---------|---------|---------|------|
> | D1 Linting | X% | | | | | | |
> | D2 TypeSafety | X% | | | | | | |
> | D3 Coverage | X% | | | | | | |
> | D4 Security | X% | | | | | | |
> | D5 Complexity | X% | | | | | | |
> | D6 Architecture | X% | | | | | | |
> | D7 Readability | X% | | | | | | |
> | D8 ErrorHandling | X% | | | | | | |
> | D9 Documentation | X% | | | | | | |
> | **總分** | **X%** | | | | | | **X%** |
> 
> ### 落地路徑圖 (Roadmap)
> - **短期 (1-2輪)**：修復最緊急的維度（D3/D4）
> - **中期 (3-4輪)**：深化修復，提升穩定性
> - **長期 (5輪)**：全面達標，建立品質監控
> 
> ### 風險評估矩陣
> | 風險 | 影響 | 機率 | 應對策略 |
> |------|------|------|---------|
> | 修復引入新問題 | 高 | 低 | 回滾機制 |
> | 時間超出預期 | 中 | 中 | 優先修復關鍵維度 |
> | 工具限制 | 低 | 高 | 人工介入 |
> ```
> 
> **成功標準**：
> - ✅ 9 維度全部 ≥8 分
> - ✅ 加權總分 ≥85%
> - ✅ 無重大風險

---

### 🚀 執行範例

```bash
# 執行 5 輪，每輪 30 分鐘超時
python3 quality_dashboard/agent_auto_research.py \
    --project /path/to/project \
    --iterations 5 \
    --timeout 1800 \
    --target 85
```

---

## 與 Topic Research 模板差異

| 項目 | Topic Research | 軟體品質 |
|------|---------------|----------|
| 目標 | 洞察研究 | 維度分數 |
| 維度 | 8 維度 | 9 維度（軟體特定）|
| 產出 | 研究報告 | 品質儀表板 |
| 成功標準 | 深度洞察 | 全部維度 ≥8 分 |

---

## 已知限制

1. **D2 TypeSafety (0%)**: 需要為模組添加完整類型註解，機械式修復只能添加基本 `-> None:`
2. **D3 Coverage (0%)**: 需要建立完整的測試框架，這是架構級別的工作
3. **建議**: Phase 4 (Testing) 完成後再執行此模板效果最佳
