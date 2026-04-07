# Phase Prompt Templates

> **版本**: v6.09.0  
> **用途**: Agent 執行每個 Phase 的標準 Prompt

---

## Phase 1: 需求規格

### Agent Prompt

```markdown
# Phase 1: 需求規格

## 角色
- Agent A: architect persona
- Agent B: reviewer persona

## 任務
為 {專案名稱} 建立完整的軟體需求規格。

## 5W1H

### WHO - 角色分工
- Agent A (architect): 撰寫 SRS.md、建立 SPEC_TRACKING.md、更新 TRACEABILITY_MATRIX.md
- Agent B (reviewer): 審查 FR 完整性、A/B 評估、給出 APPROVE/REJECT
- A/B 必須是不同 Agent，禁止自寫自審

### WHAT - 交付物
- `01-requirements/SRS.md` - 軟體需求規格
- `01-requirements/SPEC_TRACKING.md` - 規格追蹤表
- `01-requirements/TRACEABILITY_MATRIX.md` - 追溯矩陣
- `DEVELOPMENT_LOG.md` - 開發日誌（含 QG 輸出）

### WHEN - 時序門檻
- ASPICE 文檔合規率 > 80%
- Constitution SRS 正確性 = 100%
- 規格完整性 ≥ 90%
- Agent B APPROVE

### WHERE - 路徑工具
- 產出位於 `01-requirements/` 目錄
- 使用 `quality_gate/doc_checker.py`
- 使用 `constitution/runner.py --type srs`
- 使用 `python3 cli.py spec-track check`

### WHY - 設計理由
- Phase 1 缺陷到 Phase 3 才發現，修復成本 ×10
- 建立需求基線，防止規格漂移

### HOW - SOP + A/B 審查清單
1. Agent A 撰寫 SRS.md（FR-01 ~ FR-XX）
2. Agent A 初始化 SPEC_TRACKING.md
3. Agent A 初始化 TRACEABILITY_MATRIX.md（四欄空表）
4. Agent A 自檢：每條 FR 都有邏輯驗證方法
5. Agent B A/B 審查（7 項清單全部確認）
6. 執行 Quality Gate（ASPICE + Constitution）
7. Agent B 給出 APPROVE/REJECT
8. DEVELOPMENT_LOG.md 有實際命令輸出

## 驗證 Checkpoint
完成後執行：
```bash
python cli.py phase-verify --phase 1
```

## A/B 對話記錄
在 DEVELOPMENT_LOG.md 中記錄：
- Agent A session_id
- Agent B session_id
- 對話摘要
- Agent B 結論（APPROVE/REJECT + 理由）
```

---

## Phase 2: 架構設計

### Agent Prompt

```markdown
# Phase 2: 架構設計

## 角色
- Agent A: architect persona
- Agent B: reviewer persona

## 前置條件
- Phase 1 STAGE_PASS.md 已發布到 GitHub
- SPEC_TRACKING.md 存在

## 任務
為 Phase 1 的需求設計系統架構。

## 5W1H

### WHO - 角色分工
- Agent A (architect): 設計 SAD.md、定義模組邊界、決定技術選型、記錄 ADR
- Agent B (reviewer): 從實作可行性角度審查架構設計
- 禁止 Agent A 引入第三方框架
- 禁止 Agent A 偷偷妥協衝突

### WHAT - SAD.md 最低內容要求
- 架構概覽（系統邊界圖、核心模組清單）
- 模組設計（模組名稱、職責、對應 FR、依賴）
- 介面定義（模組間 API 合約、資料流向圖）
- 錯誤處理機制（L1-L6 對應、Retry/Fallback/Circuit Breaker）
- 技術選型決策 ADR
- 架構合規矩陣
- 所有外部依賴有 Lazy Init 設計

### WHEN - 進入/退出條件
- 進入確認：Phase 1 phase_artifact_enforcer 通過
- ASPICE 文檔合規率 > 80%
- Constitution SAD 正確性 = 100%
- Constitution SAD 可維護性 > 70%
- AgentEvaluator Score ≥ 80/100
- TRACEABILITY_MATRIX 已從 FR → 模組 更新
- A/B 審查結論 APPROVE

### WHERE - 路徑工具
- 產出位於 `02-architecture/` 目錄
- 使用 `quality_gate/doc_checker.py`
- 使用 `constitution/runner.py --type sad`
- 使用 `python3 cli.py spec-track check`

### WHY - 設計理由
- 架構設計比需求更需要對抗性審查
- Conflict Log 記錄任何衝突點及決策

### HOW - A/B 架構審查 5 維度
1. 審查維度 1：需求覆蓋完整性（所有 FR 有對應模組）
2. 審查維度 2：模組設計品質（邊界清晰、無循環依賴、可獨立測試）
3. 審查維度 3：錯誤處理完整性（L1-L6 對應、CB 觸發條件）
4. 審查維度 4：技術選型合理性（ADR 記錄、無幻覺框架、Lazy Init）
5. 審查維度 5：實作可行性（Phase 3 開發者可直接開始）
6. Conflict Log 已填寫（如有衝突）
7. Agent B Session ID 已記錄

## 驗證 Checkpoint
完成後執行：
```bash
python cli.py phase-verify --phase 2
```

## A/B 對話記錄
在 DEVELOPMENT_LOG.md 中記錄：
- Agent A session_id
- Agent B session_id
- 5 維度審查結果
- Agent B 結論（APPROVE/REJECT + 理由）
```

---

## Phase 3: 代碼實現

### Agent Prompt

```markdown
# Phase 3: 代碼實現

## 角色
- Agent A: developer persona
- Agent B: reviewer persona

## 前置條件
- Phase 2 STAGE_PASS.md 已發布
- SAD.md 存在

## 任務
根據 SAD.md 實作系統代碼。

## 5W1H

### WHO - 角色分工
- Agent A (developer): 代碼實作、單元測試、填寫邏輯審查對話 Developer 部分
- Agent B (reviewer): 同行邏輯審查、填寫 Architect 確認部分、測試完整性確認
- 禁止自寫自審
- 每個模組完成即觸發 A/B 審查（非全部完成後才審）
- Agent A 禁止引入 SAD.md 外的第三方框架

### WHAT - 代碼規範 + 測試三類 + 合規矩陣
- 每個模組有規範標注（對應 methodology-v2 條文 + FR 編號）
- 所有外部依賴使用 Lazy Init
- 每個模組有正向測試（Happy Path）
- 每個模組有邊界測試（空輸入、超長輸入、單一元素）
- 每個模組有負面測試（輸出≤輸入、格式一致性、錯誤路徑）
- 集成測試包含跨模組邏輯
- 合規矩陣已填寫

### WHEN - 進入/退出條件
- 進入確認：Phase 2 STAGE_PASS.md 已發布
- ASPICE 文檔合規率 > 80%
- Constitution 正確性 = 100%、覆蓋率 > 80%
- 代碼覆蓋率 ≥ 70%（pytest-cov 實際輸出）
- 單元測試全部通過
- 集成測試全部通過
- 每個模組都有同行邏輯審查記錄
- AgentEvaluator Score ≥ 90/100

### WHERE - 路徑工具
- 代碼位於 `03-implementation/` 目錄
- 使用 `quality_gate/doc_checker.py`
- 使用 `constitution/runner.py`（不加 --type）
- 使用 `pytest + pytest-cov` 執行測試

### WHY - 邏輯正確性保障
- Spec Logic Mapping 已完成（每條 FR 有量化驗證方法）
- 領域知識確認：TTS 標點=停頓、合併≤原文、Lazy Init

### HOW - 同行邏輯審查 + A/B 審查清單
1. 同行邏輯審查對話模板已填寫
2. A/B 審查清單：輸出長度 ≤ 輸入長度 確認
3. A/B 審查清單：分支邏輯（if len==1 與一般情況一致）確認
4. A/B 審查清單：外部依賴 Lazy Init 確認
5. A/B 審查清單：標點保留確認
6. A/B 審查清單：測試三類完整性確認
7. DEVELOPMENT_LOG 記錄 Agent A + Agent B Session ID

## 驗證 Checkpoint
完成後執行：
```bash
python cli.py phase-verify --phase 3
pytest --cov --cov-report=term-missing
```

## A/B 對話記錄
在 DEVELOPMENT_LOG.md 中記錄每個模組的：
- Agent A session_id
- Agent B session_id
- 審查結論
```

---

## Phase 4: 測試

### Agent Prompt

```markdown
# Phase 4: 測試

## 角色
- Agent A: qa persona（Tester ≠ Phase 3 Developer）
- Agent B: reviewer persona

## 前置條件
- Phase 3 STAGE_PASS.md 已發布
- 代碼存在且可執行

## 任務
設計並執行完整的測試計畫。

## 5W1H

### WHO - 角色分工
- Agent A (qa): 設計 TEST_PLAN、執行測試、記錄 TEST_RESULTS
- Agent A 從 SRS 推導 TC（禁止查看 Phase 3 代碼設計 TC）
- Agent B (reviewer): 審查 TEST_PLAN 完整性、審查 TEST_RESULTS 真實性
- 禁止 Agent A 自行判定測試通過
- 禁止 Agent B 幫 Agent A 補寫測試案例

### WHAT - TEST_PLAN + TEST_RESULTS 完整規格
- TEST_PLAN.md 包含測試目標、範圍、策略、環境、TC 清單、風險
- 每條 SRS FR 至少對應 1 個 TC
- P0 需求有正向 + 邊界 + 負面三類測試
- TEST_RESULTS.md 包含執行摘要、詳細結果、失敗分析、覆蓋率
- 失敗案例根本原因分析到具體模組 + 函數 + 行數
- 所有失敗案例已修復或有明確處置說明

### WHEN - 兩次 A/B 審查 + 退出條件
- 第一次 A/B 審查（TEST_PLAN，執行前）完成且 APPROVE
- Constitution test_plan 正確性 = 100%
- pytest 全部測試通過 = 100%（實際輸出）
- 代碼覆蓋率 ≥ 80%
- SRS FR 覆蓋率 = 100%
- 失敗案例全數修復（0 個 open 失敗）
- 第二次 A/B 審查（TEST_RESULTS，執行後）完成且 APPROVE
- TRACEABILITY_MATRIX FR→TC 欄位已更新

### WHERE - 路徑工具
- TEST_PLAN.md 位於 `04-testing/`
- TEST_RESULTS.md 位於 `04-testing/`
- 使用 `pytest + pytest-cov`
- 使用 `constitution/runner.py --type test_plan`
- 使用 `scripts/spec_logic_checker.py`

### WHY - 獨立驗證視角
- Tester 從使用者需求視角驗證，非從代碼視角
- Phase 3 自測 vs Phase 4 獨立測試發現不同缺陷

### HOW - 兩次 A/B 審查流程
1. 第一次審查填寫：需求追蹤完整性、測試設計品質、可執行性
2. 測試實際執行（非手動確認），pytest 輸出貼入 TEST_RESULTS
3. 第二次審查填寫：結果真實性、問題處理完整性、覆蓋完整性
4. Agent B Session ID 已記錄（兩次審查均記錄）

## 驗證 Checkpoint
完成後執行：
```bash
python cli.py phase-verify --phase 4
pytest --cov
```

## A/B 對話記錄
在 DEVELOPMENT_LOG.md 中記錄：
- 第一次審查：Agent A + B session_id、結論
- 第二次審查：Agent A + B session_id、結論
```

---

## Phase 5: 驗收與交付

### Agent Prompt

```markdown
# Phase 5: 驗收與交付

## 角色
- Agent A: devops persona（非 Phase 3 Developer）
- Agent B: architect 或 reviewer persona

## 前置條件
- Phase 4 STAGE_PASS.md 已發布
- 測試通過率 = 100%
- 代碼覆蓋率 ≥ 80%

## 任務
建立交付基線並啟動監控。

## 5W1H

### WHO - 角色分工
- Agent A (devops): 建立 BASELINE.md、執行驗收測試、啟動 A/B 持續監控
- Agent B (architect): 審查 BASELINE.md 完整性、確認 A/B 監控閾值
- 基線建立必須經 Agent B 確認，不能自簽

### WHAT - 必要交付物
- BASELINE.md 7 章節完整
- TEST_RESULTS.md（Phase 5 驗收版）
- VERIFICATION_REPORT.md
- MONITORING_PLAN.md（含 A/B 監控四個閾值）
- QUALITY_REPORT.md（初版）
- 邏輯正確性分數 ≥ 90 分

### WHEN - 兩次 A/B 審查 + 進入 Phase 6 條件
- Constitution 總分 ≥ 80%
- ASPICE 合規率 > 80%
- BASELINE 功能驗收 100%（無任何 ❌）
- 已知問題 HIGH 嚴重性 = 0 個
- 第一次 A/B 審查（基線審查）APPROVE
- 第二次 A/B 審查（驗收報告審查）APPROVE
- A/B 監控首次結果記錄到 MONITORING_PLAN.md

### WHERE - 路徑工具
- 產出位於 `05-verify/` 目錄
- 使用 `spec_logic_checker.py`（≥ 90 分）

### WHY - 轉折點
- Phase 5 是從「建構」轉為「保障」的轉折點

### HOW - 監控 SOP
1. A/B 監控已啟動（邏輯、回應時間、熔斷器、錯誤率）
2. 兩次 A/B 審查記錄含 Session ID
3. DEVELOPMENT_LOG 有 Phase 5 格式完整記錄

## 驗證 Checkpoint
完成後執行：
```bash
python cli.py phase-verify --phase 5
```

## A/B 對話記錄
在 DEVELOPMENT_LOG.md 中記錄：
- Agent A + B session_id（兩次審查）
- 監控閾值設定
- 首次監控結果
```

---

## Phase 6: 品質保證

### Agent Prompt

```markdown
# Phase 6: 品質保證

## 角色
- Agent A: qa persona
- Agent B: architect 或 pm persona

## 前置條件
- Phase 5 STAGE_PASS.md 已發布
- 測試通過率 = 100%

## 任務
進行深度品質分析並建立改進計畫。

## 5W1H

### WHO - 角色分工
- Agent A (qa): 品質深度分析、完成 QUALITY_REPORT 完整版
- Agent B (architect): 審查品質報告深度、確認改進建議可行性

### WHAT - QUALITY_REPORT 7 章節
- 品質指標全覽
- ASPICE 各 Phase 合規性分析
- Constitution 四維度深度分析
- 品質問題根源分析（Layer 1-3）
- 改進建議（P0/P1/P2 + 目標指標）
- A/B 監控數據分析
- 品質目標達成摘要

### WHEN - 進入條件
- Constitution 總分 ≥ 80%
- ASPICE 合規率 > 80%
- 邏輯正確性分數 ≥ 90 分
- 測試通過率 = 100%
- A/B 監控 Phase 6 全程穩定（熔斷 0 次、錯誤率 < 1%）
- Agent B APPROVE

### WHERE - 路徑工具
- 產出位於 `06-quality/` 目錄
- 每日監控執行記錄到 MONITORING_PLAN.md

### WHY - 品質分析必須跨 Phase
- 品質分析跨越所有 Phase 數據，非只看 Phase 5 快照

### HOW - 根源分析三層
1. Layer 1 問題識別：從 Phase 1-5 DEVELOPMENT_LOG 提取所有 REJECT/失敗記錄
2. Layer 2 分類彙整：依問題類型分類
3. Layer 3 根源 Phase 定位：追溯「最早應被攔截的 Phase」
4. 雙方 Session ID 已記錄

## 驗證 Checkpoint
完成後執行：
```bash
python cli.py phase-verify --phase 6
```

## A/B 對話記錄
在 DEVELOPMENT_LOG.md 中記錄：
- Agent A + B session_id
- 品質分析結論
- Agent B APPROVE/REJECT
```

---

## Phase 7: 風險評估

### Agent Prompt

```markdown
# Phase 7: 風險評估

## 角色
- Agent A: qa persona（保持悲觀視角）
- Agent B: architect persona

## 前置條件
- Phase 6 STAGE_PASS.md 已發布

## 任務
識別並評估專案風險，建立應對計畫。

## 5W1H

### WHO - 角色分工
- Agent A 保持悲觀視角（盡可能找出更多風險）
- Agent B 禁止接受「持續監控」作為唯一緩解措施

### WHAT - 五維度風險 + Decision Gate
- 五維度風險識別（技術、依賴、操作、商業、迭代）各至少 1 個
- HIGH/MEDIUM 風險有四層緩解措施（預防、偵測、應對、升級）
- 所有 MEDIUM/HIGH 風險有 Decision Gate 記錄
- check_decisions.py 執行結果 0 個未確認
- 至少 1 個 HIGH 風險演練記錄
- MONITORING_PLAN.md Phase 7 更新

### WHEN - 退出條件
- 邏輯正確性分數 ≥ 90 分
- 驗證測試通過率 = 100%
- Decision Gate 0 個未確認
- 高風險演練通過
- 雙方 Session ID 記錄
- Agent B APPROVE

### WHERE - 路徑工具
- 產出位於 `07-risk/` 目錄
- 決策記錄位於 `.methodology/decisions/`

### WHY - 前瞻視角
- Phase 7 是前瞻視角（未來威脅），非回顧（現有問題）

### HOW - Decision Gate + 演練
1. 每個 MEDIUM/HIGH 風險有 R*_decision.md
2. 演練記錄包含觸發條件、觀察、結果、RTO

## 驗證 Checkpoint
完成後執行：
```bash
python cli.py phase-verify --phase 7
python scripts/check_decisions.py
```

## A/B 對話記錄
在 DEVELOPMENT_LOG.md 中記錄：
- Agent A + B session_id
- 風險識別結論
- 演練記錄摘要
```

---

## Phase 8: 配置管理

### Agent Prompt

```markdown
# Phase 8: 配置管理

## 角色
- Agent A: devops persona
- Agent B: pm 或 architect persona

## 前置條件
- Phase 7 STAGE_PASS.md 已發布
- A/B 監控 Phase 5 至今全程穩定

## 任務
建立完整配置記錄，準備交付。

## 5W1H

### WHO - 角色分工
- Agent A (devops): 建立 CONFIG_RECORDS.md、執行發布清單、編製監控最終報告
- Agent B (pm): 確認版本配置完整可重現、發布清單無遺漏
- Agent A 禁止使用「最新版」等模糊版本描述

### WHAT - CONFIG_RECORDS 8 章節 + 發布清單 7 區塊
- 章節 1：版本資訊（含 Git Commit Hash）
- 章節 2：執行環境配置
- 章節 3：依賴套件清單（pip freeze 完整快照）
- 章節 4：環境變數與配置
- 章節 5：部署記錄
- 章節 6：配置變更記錄
- 章節 7：回滾 SOP
- 章節 8：配置合規性確認
- 發布清單 7 區塊全部 ✅
- Git Tag 已建立（v[Major.Minor.Patch]）

### WHEN - 封版前置條件
- A/B 監控（Phase 5 至 Phase 8 全程）邏輯分數平均 ≥ 90 分
- A/B 監控熔斷器（Phase 5 至今）= 0 次
- 發布清單七個區塊全部 ✅
- CONFIG_RECORDS.md 八章節完整
- Constitution 最終總分 ≥ 80%
- Agent B APPROVE

### WHERE - 路徑工具
- 產出位於 `08-config/` 目錄
- Git Tag 已建立並推送

### WHY - 治理行為
- 配置管理是治理行為，確保可審計、可重現

### HOW - 方法論閉環確認
1. 方法論閉環記錄完整（Phase 1-8 全部 Sign-off）
2. A/B 監控最終報告生成
3. 雙方 Session ID 記錄

## 驗證 Checkpoint
完成後執行：
```bash
python cli.py phase-verify --phase 8
git tag -l
pip freeze > requirements.txt
```

## A/B 對話記錄
在 DEVELOPMENT_LOG.md 中記錄：
- Agent A + B session_id
- 最終 APPROVE
- 版本標籤
```

---

*最後更新: 2026-03-31*
