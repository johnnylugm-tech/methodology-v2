# Phase 5 計劃：驗證與交付
## methodology-v2 | 5W1H 框架 × A/B 協作機制

> **版本基準**：SKILL.md v5.56 | 整理日期：2026-03-29
> **前置條件**：Phase 4 全部 Sign-off ✅（TEST_RESULTS 兩次 APPROVE、覆蓋率 ≥ 80%、SRS FR 覆蓋率 100%）

---

## 🗺️ 一覽表

| 5W1H | 核心答案 |
|------|----------|
| **WHO**   | Agent A（DevOps / Delivery）執行驗證交付 × Agent B（Architect / QA）審查基線與監控結果 |
| **WHAT**  | 建立 BASELINE.md + TEST_RESULTS（Phase 5）+ 啟動 A/B 持續監控；確立可交付基線版本 |
| **WHEN**  | Phase 4 完整通過後；基線建立前必須 A/B 審查；部署後立即啟動監控 |
| **WHERE** | `05-verify/` 目錄；監控結果在 `MONITORING_PLAN.md`；Quality Gate 在 `quality_gate/` |
| **WHY**   | Phase 5 是從「開發完成」到「可交付」的品質門檻；基線一旦建立，後續所有變更都以此為比較基準 |
| **HOW**   | 補齊文檔 → 邏輯正確性複查 → 建立基線 → A/B 審查 → 部署驗證 → 持續監控 → sign-off |

---

## 1. WHO — 誰執行？（A/B 角色分工）

> ⚠️ **Phase 5 原則**：驗證必須獨立於開發。Agent A 不能是 Phase 3 的 Developer；基線建立必須經 Agent B 確認，不能自簽。

### Agent A（DevOps / Delivery Engineer）—— 主責驗證與交付

| 屬性 | 內容 |
|------|------|
| Persona | `devops` |
| Goal | 將通過測試的系統轉化為可交付的基線版本，並確立監控機制 |
| 職責 | 補齊缺失文檔、建立 BASELINE.md、執行驗收測試、啟動 A/B 持續監控、記錄 TEST_RESULTS（Phase 5）|
| 核心心態 | 「這個版本**能不能安全交付**給下一個環境？」|
| 禁止 | 自行宣告基線通過；在監控數據不足時強行進入 Phase 6 |

```python
# Phase 5 Agent A 啟動
from agent_spawner import spawn_with_persona

agent_a = spawn_with_persona(
    role="devops",
    task="建立 Phase 5 基線版本，執行驗收測試，啟動 A/B 持續監控",
)
```

### Agent B（Architect / Senior QA）—— 主責基線審查與監控確認

| 屬性 | 內容 |
|------|------|
| Persona | `architect` 或 `reviewer` |
| Goal | 確認基線版本符合所有品質門檻；監控數據真實且閾值合理 |
| 職責 | 審查 BASELINE.md 完整性、確認 A/B 監控閾值、審查 VERIFICATION_REPORT.md |
| 核心問題 | 「基線版本有沒有遺漏任何 Phase 1-4 的承諾？」「監控閾值是防守型還是過於寬鬆？」|
| 禁止 | 跳過監控數據直接 APPROVE；接受基線版本中有「待修復」的已知缺陷 |

```python
# Phase 5 Agent B 啟動
agent_b = spawn_with_persona(
    role="architect",
    task="審查基線完整性、監控閾值合理性、驗收測試結果",
)
```

### A/B 協作啟動

```python
from methodology import quick_start
from hybrid_workflow import HybridWorkflow
from agent_evaluator import AgentEvaluator

team = quick_start("full")             # Architect + Dev + Reviewer + Tester
workflow = HybridWorkflow(mode="ON")   # 強制 A/B 審查
evaluator = AgentEvaluator()

# Phase 5 特別確認：Agent A ≠ Phase 3 Developer
assert agent_a.session_id != phase3_dev.session_id, \
    "Phase 5 驗證人員不能是 Phase 3 的開發者！"
```

---

## 2. WHAT — 做什麼？（Phase 5 交付物）

### 必要交付物（Mandatory）

| 交付物 | 負責方 | 驗證方 | 位置 |
|--------|--------|--------|------|
| `BASELINE.md` | Agent A | Agent B + Quality Gate | `05-verify/` |
| `TEST_RESULTS.md`（Phase 5 驗收版）| Agent A | Agent B | `05-verify/` |
| `VERIFICATION_REPORT.md` | Agent A | Agent B | `05-verify/` |
| `MONITORING_PLAN.md`（A/B 監控）| Agent A | Agent B | 專案根目錄 |
| `QUALITY_REPORT.md`（初版）| Agent A | Agent B | `05-verify/` |
| `DEVELOPMENT_LOG.md`（Phase 5 段落）| Agent A | Agent B | 專案根目錄 |

---

### BASELINE.md 完整規格

```markdown
# Baseline - [專案名稱] v[版本號]

## 1. 基線概述

| 項目 | 內容 |
|------|------|
| 基線版本 | v1.0.0 |
| 建立日期 | YYYY-MM-DD |
| 建立階段 | Phase 5（驗證與交付）|
| 建立人 | Agent A（session_id：______）|
| 審查人 | Agent B（session_id：______）|
| 狀態 | APPROVED / PENDING |

## 2. 功能基線（對應 SRS FR）

| FR ID | 功能名稱 | 實作模組 | 測試案例 | 測試狀態 | 驗收狀態 |
|-------|----------|----------|----------|----------|----------|
| FR-01 | 按標點分段 | TextProcessor.split() | TC-001~003 | ✅ PASS | ✅ 驗收 |
| FR-05 | 多段合併   | AudioMerger.merge() | TC-004~005 | ✅ PASS | ✅ 驗收 |

> 驗收狀態必須 100% ✅，不允許任何 ❌ 進入基線。

## 3. 品質基線

| 指標 | 目標 | 實際 | 狀態 |
|------|------|------|------|
| Constitution 總分 | ≥ 80% | XX% | ✅/❌ |
| 代碼覆蓋率 | ≥ 80% | XX% | ✅/❌ |
| 測試通過率 | 100% | 100% | ✅ |
| ASPICE 合規率 | > 80% | XX% | ✅/❌ |
| 邏輯正確性分數 | ≥ 90 分 | XX 分 | ✅/❌ |

## 4. 效能基線（A/B 監控基準）

| 指標 | 基線值 | 允許偏差 | 量測方式 |
|------|--------|----------|----------|
| 回應時間 | XX ms | < +10% | 自動化壓測 |
| 記憶體使用 | XX MB | < +15% | 監控工具 |
| 錯誤率 | < 1% | = 0 增長 | 日誌分析 |
| 熔斷器觸發次數 | 0 次 | = 0 | Circuit Breaker 日誌 |

## 5. 已知問題登錄

| 問題 ID | 描述 | 嚴重性 | 處置決策 | 負責人 |
|---------|------|--------|----------|--------|
| （無 = 基線乾淨）|

> ⚠️ 若有 HIGH 嚴重性問題，禁止建立基線。

## 6. 變更記錄

| 日期 | 變更內容 | 變更者 | 審核人 |
|------|----------|--------|--------|
| YYYY-MM-DD | 初始基線建立 | Agent A | Agent B |

## 7. 驗收簽收

| 角色 | Agent | Session ID | 日期 |
|------|-------|------------|------|
| DevOps（交付）| Agent A | ______ | YYYY-MM-DD |
| Architect（審查）| Agent B | ______ | YYYY-MM-DD |
```

---

### MONITORING_PLAN.md（A/B 持續監控）完整規格

```markdown
# Monitoring Plan - [專案名稱]

## A/B 持續監控閾值（來自 SKILL.md v5.56）

| 監控項目 | 閾值 | 觸發動作 |
|----------|------|----------|
| 邏輯正確性分數 | ≥ 90 分 | 低於閾值 → 停止部署 |
| 回應時間 | 與基線偏差 < 10% | 超出 → 警告 + 人工確認 |
| 熔斷器觸發 | 不觸發 | 觸發 → 立即回滾 |
| 錯誤率 | < 1% | 超出 → 停止流量 |

## 每次部署後執行的快速回歸

```bash
# 邏輯正確性
python3 scripts/spec_logic_checker.py   # 分數 ≥ 90

# 效能基線比對
python3 scripts/performance_check.py   # 偏差 < 10%

# 熔斷器狀態
python3 scripts/circuit_breaker_check.py  # 0 觸發
```

## 監控記錄格式

| 日期 | 部署版本 | 邏輯分數 | 回應時間 | 錯誤率 | 熔斷器 | 結論 |
|------|----------|----------|----------|--------|--------|------|
| YYYY-MM-DD | v1.0.0 | XX/100 | XX ms | XX% | 0 次 | ✅ 正常 |
```

---

### VERIFICATION_REPORT.md 完整規格

```markdown
# Verification Report - [專案名稱]

## 1. 驗證概述

| 項目 | 內容 |
|------|------|
| 驗證日期 | YYYY-MM-DD |
| 驗證版本 | v1.0.0 |
| 驗證人 | Agent A（session_id：______）|
| 審查人 | Agent B（session_id：______）|

## 2. Phase 1-4 承諾驗證

| Phase | 承諾 | 實際交付 | 驗證狀態 |
|-------|------|----------|----------|
| Phase 1 | SRS.md 完整，FR 覆蓋率 100% | FR-01~XX 全部交付 | ✅ |
| Phase 2 | SAD.md 架構完整，ADR 記錄 | 模組設計符合規範 | ✅ |
| Phase 3 | 代碼覆蓋率 ≥ 80%，邏輯審查通過 | XX% 覆蓋率 | ✅ |
| Phase 4 | 測試通過率 100%，SRS FR 覆蓋 100% | XX/XX TC PASS | ✅ |

## 3. 邏輯正確性複查結果

執行命令：python3 scripts/spec_logic_checker.py
結果：
- 總分：XX/100（門檻：≥ 90）
- 關鍵約束（輸出 ≤ 輸入）：✅/❌
- 分支一致性：✅/❌
- Lazy Init 完整：✅/❌

## 4. A/B 監控初次結果

| 監控項目 | 基線值 | 首次部署值 | 偏差 | 狀態 |
|----------|--------|------------|------|------|
| 回應時間 | XX ms | XX ms | X% | ✅/❌ |
| 錯誤率 | X% | X% | — | ✅/❌ |
| 熔斷器 | 0 次 | 0 次 | — | ✅ |

## 5. 結論

- [ ] ✅ 基線版本可交付，進入 Phase 6
- [ ] ❌ 不可交付（原因：______）
```

---

### QUALITY_REPORT.md 初版規格（Phase 5 建立，Phase 6-7 補充）

```markdown
# Quality Report - [專案名稱]

## 1. 品質指標摘要（Phase 5 初版）

| 指標 | 目標 | 實際 | 狀態 |
|------|------|------|------|
| ASPICE 合規率 | > 80% | XX% | ✅/❌ |
| Constitution 總分 | ≥ 80% | XX% | ✅/❌ |
| 代碼覆蓋率 | ≥ 80% | XX% | ✅/❌ |
| 邏輯正確性 | ≥ 90 分 | XX 分 | ✅/❌ |

## 2. Phase 1-4 ASPICE 合規性

| Phase | 文件 | 合規率 | 狀態 |
|-------|------|--------|------|
| Phase 1 | SRS.md | XX% | ✅/❌ |
| Phase 2 | SAD.md | XX% | ✅/❌ |
| Phase 3 | 代碼 + 測試 | XX% | ✅/❌ |
| Phase 4 | TEST_PLAN + TEST_RESULTS | XX% | ✅/❌ |

## 3. 已知問題清單

| ID | 嚴重性 | 描述 | 狀態 | 修復計劃 |
|----|--------|------|------|----------|
| （Phase 5 目標：HIGH 問題 = 0）|

## 4. 改進建議

[Phase 6-7 補充]
```

---

### A/B 基線審查清單（Agent B）

**功能完整性**
- [ ] BASELINE 功能基線覆蓋所有 SRS FR（無遺漏）
- [ ] 每條 FR 的驗收狀態均為 ✅（無任何 ❌）
- [ ] 已知問題登錄中無 HIGH 嚴重性問題

**品質基線合理性**
- [ ] 所有品質指標達到門檻（Constitution ≥ 80%、覆蓋率 ≥ 80%、邏輯分數 ≥ 90）
- [ ] 效能基線數值有實際量測依據（非估算）
- [ ] 允許偏差閾值是防守型（非過於寬鬆）

**監控計劃完整性**
- [ ] MONITORING_PLAN.md 的四個閾值合理
- [ ] 每次部署後的快速回歸腳本可自動執行
- [ ] 觸發動作明確（回滾 / 停止 / 警告）

**驗收簽收完整**
- [ ] BASELINE.md 有雙方 session_id 與日期
- [ ] VERIFICATION_REPORT.md Phase 1-4 承諾全部驗證
- [ ] 邏輯正確性複查分數 ≥ 90

---

## 3. WHEN — 何時執行？（時序 & 門檻）

### Phase 5 完整時序圖

```
Phase 4 sign-off ✅
        │
        ▼
[前置確認] phase_artifact_enforcer.py
        │
        ├── ❌ Phase 4 未完成 → 停止
        └── ✅ 通過
                │
                ▼
        [Agent A] 補齊缺失文檔
        doc_checker.py 確認所有文檔存在
                │
                ▼
        [Agent A] 邏輯正確性複查
        spec_logic_checker.py ≥ 90 分
                │
                ├── < 90 分 → 通知 Phase 3 Dev 修復 → 重新複查
                └── ≥ 90 分
                        │
                        ▼
                [Agent A] 建立 BASELINE.md
                + QUALITY_REPORT.md 初版
                + MONITORING_PLAN.md
                        │
                        ▼
                [Agent A → Agent B]
                基線 A/B 審查
                HybridWorkflow mode=ON 觸發
                        │
                        ├── ❌ REJECT
                        │       └── Agent A 修正 → 重新提交
                        │
                        └── ✅ APPROVE
                                │
                                ▼
                        Constitution ≥ 80% 檢查
                        python3 quality_gate/constitution/runner.py
                                │
                                ├── 未通過 → 修正 → 重新 Gate
                                └── 通過
                                        │
                                        ▼
                                [Agent A] 執行驗收測試
                                + 首次部署
                                + 啟動 A/B 持續監控
                                        │
                                        ├── 監控異常（熔斷 / 錯誤率超標）
                                        │       └── 回滾 → 診斷 → 修復 → 重新部署
                                        │
                                        └── 監控正常
                                                │
                                                ▼
                                        [Agent A → Agent B]
                                        VERIFICATION_REPORT A/B 審查
                                                │
                                                ├── ❌ REJECT
                                                │       └── 補充資料 / 重新執行
                                                │
                                                └── ✅ APPROVE
                                                        │
                                                        ▼
                                                記錄 DEVELOPMENT_LOG.md
                                                        │
                                                        ▼
                                                ✅ Phase 5 完成 → 進入 Phase 6
```

> **Phase 5 有兩次 A/B 審查**：
> 第一次在部署**前**（審查基線完整性），第二次在部署**後**（審查驗收報告）。
> 邏輯正確性分數必須在基線建立前確認，不在事後補救。

### 進入 Phase 6 的前置條件（全部必須為 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| 邏輯正確性分數 | ≥ 90 分 | spec_logic_checker.py 實際輸出 |
| Constitution 總分 | ≥ 80% | Constitution Runner |
| ASPICE 合規率 | > 80% | doc_checker.py |
| BASELINE 功能驗收 | 100% ✅（無任何 ❌）| Agent B 確認 |
| 已知問題 HIGH 嚴重性 | = 0 個 | BASELINE.md 問題登錄 |
| A/B 監控：邏輯正確性 | ≥ 90 分 | MONITORING_PLAN.md 首次記錄 |
| A/B 監控：熔斷器 | 0 次觸發 | Circuit Breaker 日誌 |
| A/B 監控：錯誤率 | < 1% | 日誌分析 |
| 第一次 A/B 審查（基線）| APPROVE | AgentEvaluator |
| 第二次 A/B 審查（驗收）| APPROVE | AgentEvaluator |

---

## 4. WHERE — 在哪裡執行？（路徑 & 工具位置）

### 文件結構（Phase 5 新增）

```
project-root/
├── 01-requirements/          ← Phase 1（只讀）
├── 02-architecture/          ← Phase 2（只讀）
├── 03-implementation/        ← Phase 3（修復後只讀）
├── 04-testing/               ← Phase 4（只讀）
│
├── 05-verify/                ← Phase 5 主要工作區
│   ├── BASELINE.md           ← 基線版本（雙方簽收）
│   ├── TEST_RESULTS.md       ← 驗收測試結果
│   ├── VERIFICATION_REPORT.md ← Phase 1-4 承諾驗證
│   └── QUALITY_REPORT.md     ← 品質報告初版
│
├── scripts/
│   ├── spec_logic_checker.py ← 邏輯正確性複查（門檻 ≥ 90）
│   ├── performance_check.py  ← 效能基線比對
│   └── circuit_breaker_check.py ← 熔斷器狀態
│
├── quality_gate/
│   ├── doc_checker.py        ← ASPICE 文檔完整性
│   ├── constitution/
│   │   └── runner.py         ← Phase 5 不加 --type（全面 ≥ 80%）
│   └── phase_artifact_enforcer.py
│
├── MONITORING_PLAN.md        ← A/B 持續監控計劃與記錄
└── DEVELOPMENT_LOG.md        ← Phase 5 段落（含兩次審查記錄）
```

### 工具執行位置

```bash
# ── 前置確認 ────────────────────────────
python3 quality_gate/phase_artifact_enforcer.py

# ── 文檔完整性 ──────────────────────────
python3 quality_gate/doc_checker.py

# ── 邏輯正確性複查（門檻 ≥ 90）───────────
python3 scripts/spec_logic_checker.py

# ── Constitution（門檻 ≥ 80%）────────────
python3 quality_gate/constitution/runner.py

# ── A/B 持續監控 ────────────────────────
python3 scripts/performance_check.py
python3 scripts/circuit_breaker_check.py

# ── 兩次 A/B 評估 ────────────────────────
python -m agent_evaluator --check   # 第一次：基線審查
python -m agent_evaluator --check   # 第二次：驗收報告審查

# ── Framework Enforcement ───────────────
methodology quality
```

---

## 5. WHY — 為什麼這樣做？（設計理由）

### Phase 5 的本質：從「技術完成」到「可交付」的品質門檻

前四個 Phase 解決的是「東西有沒有做出來」；Phase 5 解決的是「做出來的東西**能不能交給別人用**」。這兩個問題完全不同：

| 維度 | Phase 1-4 問的 | Phase 5 問的 |
|------|---------------|-------------|
| 功能 | FR 有沒有實作？ | FR 有沒有驗收通過？ |
| 品質 | 覆蓋率夠嗎？ | 整體品質是否達到可交付水準？ |
| 穩定性 | 測試通過了嗎？ | 部署後系統穩定嗎？ |
| 基準 | 各 Phase 各自的門檻 | 建立統一的版本基線 |

### 為什麼「邏輯正確性複查」在 Phase 5 重做一次？

Phase 3 已經做過邏輯審查，為什麼 Phase 5 還要再做？

三個理由：
1. **時間差**：Phase 4 發現的缺陷修復後，可能引入新的邏輯問題
2. **新鮮眼睛**：Phase 5 的 Agent A 是 `devops` 人格，與 Phase 3 開發者視角不同
3. **門檻更嚴**：Phase 3 的邏輯審查是定性的（對話），Phase 5 用 `spec_logic_checker.py` 量化（≥ 90 分）

### 為什麼基線版本不允許有 HIGH 嚴重性已知問題？

「帶著已知 HIGH 問題交付」是技術債的起點：
- 接收方不知道問題存在，無法防護
- 問題在生產環境發酵後修復成本 × 100
- 基線一旦被接受，問題就從「已知」變「遺忘」

**正確做法**：HIGH 問題修復完才能建立基線；MEDIUM / LOW 問題可記錄後帶入 Phase 6 風險管理。

### A/B 持續監控的三個閾值為何這樣設定（來自 SKILL.md）

```
邏輯正確性 ≥ 90 分  →  Phase 3 邏輯審查的量化延伸，確保交付後不退步
效能偏差 < 10%      →  給予合理波動空間，但防止效能懸崖式劣化
熔斷器不觸發        →  熔斷器觸發代表系統進入異常狀態，任何觸發都應停止
```

這三個閾值是**防守型**設計——寧可觸發假陽性（過於敏感），也不要漏掉真正的問題。

---

## 6. HOW — 如何執行？（完整 SOP）

### Step 0：前置確認 + 文檔補齊（Agent A）

```bash
# 確認 Phase 4 已完成
python3 quality_gate/phase_artifact_enforcer.py

# 檢查缺失文檔
python3 quality_gate/doc_checker.py

# 預期需要的文檔清單：
# ✅ SRS.md（Phase 1）
# ✅ SAD.md（Phase 2）
# ✅ TEST_PLAN.md（Phase 4）
# ✅ TEST_RESULTS.md（Phase 4）
# ❓ QUALITY_REPORT.md（Phase 5 建立）
# ❓ RISK_ASSESSMENT.md（Phase 5 初版 / Phase 7 完整）
# ❓ CONFIG_RECORDS.md（Phase 8）
```

### Step 1：邏輯正確性複查（Agent A，必須 ≥ 90 分才繼續）

```bash
# 執行邏輯正確性自動檢查
python3 scripts/spec_logic_checker.py

# 預期輸出格式：
# ✅ FR-01 輸出 ≤ 輸入：通過
# ✅ FR-05 分支一致性：通過
# ✅ 外部依賴 Lazy Init：通過
# 邏輯正確性分數：XX/100

# 若 < 90：
# 1. 記錄具體失敗項目
# 2. 通知 Phase 3 Developer 修復
# 3. 修復後重新執行此步驟
```

### Step 2：Agent A 建立基線文檔

```markdown
建立順序：
1. BASELINE.md（功能基線 + 品質基線 + 效能基線）
2. QUALITY_REPORT.md 初版（Phase 5 品質快照）
3. MONITORING_PLAN.md（四個監控閾值 + 執行腳本）
4. VERIFICATION_REPORT.md（Phase 1-4 承諾逐一驗證）
```

### Step 3：第一次 A/B 審查（基線審查，部署前）

```python
from agent_evaluator import AgentEvaluator

evaluator = AgentEvaluator()

# 第一次：基線審查
baseline_result = evaluator.evaluate(
    spec_a=baseline_docs,          # BASELINE + QUALITY_REPORT + MONITORING_PLAN
    spec_b=baseline_checklist      # Agent B 的審查標準
)

if not baseline_result.approved:
    raise Exception(
        f"基線未通過審查：{baseline_result.rejection_reason}"
    )

print("✅ 基線審查通過，執行首次部署")
```

**Agent B 基線審查對話模板**：

```markdown
## Phase 5 基線 A/B 審查紀錄（第一次）

### 功能完整性
- [ ] BASELINE 功能基線覆蓋所有 SRS FR：✅/❌（數量：XX/XX）
- [ ] 每條 FR 驗收狀態全為 ✅：✅/❌
- [ ] 已知問題無 HIGH 嚴重性：✅/❌
- 說明：______

### 品質基線合理性
- [ ] Constitution ≥ 80%（實際：XX%）：✅/❌
- [ ] 覆蓋率 ≥ 80%（實際：XX%）：✅/❌
- [ ] 邏輯正確性 ≥ 90 分（實際：XX 分）：✅/❌
- 說明：______

### 監控計劃完整性
- [ ] 四個監控閾值明確定義：✅/❌
- [ ] 快速回歸腳本可自動執行：✅/❌
- [ ] 觸發動作明確（回滾/停止/警告）：✅/❌
- 說明：______

### 審查結論
- [ ] ✅ APPROVE — 執行首次部署
- [ ] ❌ REJECT — 返回 Agent A 修正（原因：______）

Agent B 簽名：______  Session ID：______  日期：______
```

### Step 4：首次部署 + A/B 持續監控啟動（Agent A）

```bash
# 執行驗收測試（部署後立即執行）
pytest tests/ -v --tb=short -m "acceptance"

# 啟動 A/B 持續監控（三項必須全部通過）

# 1. 邏輯正確性
python3 scripts/spec_logic_checker.py
# 門檻：≥ 90 分

# 2. 效能基線比對
python3 scripts/performance_check.py
# 門檻：回應時間偏差 < 10%

# 3. 熔斷器狀態
python3 scripts/circuit_breaker_check.py
# 門檻：0 次觸發

# 將結果記錄到 MONITORING_PLAN.md
```

**監控異常處理**：

```markdown
## 監控異常 SOP

若任一監控項目觸發：

熔斷器觸發 → 立即回滾 → 診斷根本原因 → Phase 3 修復 → 重新 Phase 4/5
錯誤率 ≥ 1% → 停止流量 → 分析日誌 → 修復 → 重新部署
回應時間偏差 ≥ 10% → 警告 + 人工確認 → 判斷是否可接受
邏輯分數 < 90 → 停止部署 → 邏輯複查 → 修復

原則：任何 HIGH 異常都優先回滾，不嘗試帶著異常繼續。
```

### Step 5：第二次 A/B 審查（驗收報告審查，部署後）

```python
# 第二次：驗收報告審查
verification_result = evaluator.evaluate(
    spec_a=verification_report,       # VERIFICATION_REPORT.md
    spec_b=verification_checklist     # Agent B 的審查標準
)

if not verification_result.approved:
    raise Exception(
        f"驗收報告未通過審查：{verification_result.rejection_reason}"
    )

print("✅ 驗收報告審查通過，Phase 5 完成")
```

**Agent B 驗收報告審查對話模板**：

```markdown
## Phase 5 驗收報告 A/B 審查紀錄（第二次）

### Phase 1-4 承諾驗證
- [ ] Phase 1 SRS 承諾全部驗收：✅/❌
- [ ] Phase 2 架構承諾全部驗收：✅/❌
- [ ] Phase 3 代碼品質承諾驗收：✅/❌
- [ ] Phase 4 測試結果承諾驗收：✅/❌
- 說明：______

### A/B 監控初次結果
- [ ] 邏輯正確性 ≥ 90 分（實際：XX 分）：✅/❌
- [ ] 回應時間偏差 < 10%（實際：X%）：✅/❌
- [ ] 熔斷器 0 次觸發：✅/❌
- [ ] 錯誤率 < 1%（實際：X%）：✅/❌
- 說明：______

### 文檔完整性
- [ ] BASELINE.md 雙方簽收完整：✅/❌
- [ ] MONITORING_PLAN.md 首次記錄已填寫：✅/❌
- [ ] QUALITY_REPORT.md 初版完整：✅/❌
- 說明：______

### 審查結論
- [ ] ✅ APPROVE — Phase 5 完成，進入 Phase 6
- [ ] ❌ REJECT — 補充資料（原因：______）

Agent B 簽名：______  Session ID：______  日期：______
```

### Step 6：DEVELOPMENT_LOG.md 記錄（正確格式）

```markdown
## Phase 5 Quality Gate 結果（YYYY-MM-DD HH:MM）

### 前置確認
執行命令：python3 quality_gate/phase_artifact_enforcer.py
結果：Phase 4 完成 ✅

### 邏輯正確性複查
執行命令：python3 scripts/spec_logic_checker.py
結果：
- 邏輯正確性分數：XX/100（目標 ≥ 90）
- 輸出 ≤ 輸入約束：✅
- 分支一致性：✅
- Lazy Init 完整：✅

### 文檔完整性檢查
執行命令：python3 quality_gate/doc_checker.py
結果：Compliance Rate: XX%

### Constitution 全面檢查
執行命令：python3 quality_gate/constitution/runner.py
結果：
- 正確性: XX%（目標 100%）
- 可維護性: XX%（目標 > 70%）
- Constitution 總分: XX%（目標 ≥ 80%）

### 第一次 A/B 審查（基線審查）
- Agent A（DevOps）：session_id ______
- Agent B（Architect）：session_id ______
- 審查結論：APPROVE ✅
- 審查日期：______

### A/B 持續監控首次結果
執行命令：python3 scripts/spec_logic_checker.py && python3 scripts/performance_check.py
結果：
- 邏輯正確性：XX/100 ✅
- 回應時間偏差：X%（< 10%）✅
- 熔斷器觸發：0 次 ✅
- 錯誤率：X%（< 1%）✅

### 第二次 A/B 審查（驗收報告審查）
- 審查結論：APPROVE ✅
- 審查日期：______

### Phase 5 結論
- [ ] ✅ 通過，BASELINE v1.0.0 建立，進入 Phase 6
- [ ] ❌ 未通過（原因：______）
```

> ❌ **禁止這樣記錄**：
> ```markdown
> ### Phase 5 Quality Gate
> ✅ 基線建立完成
> ```

---

## 7. Phase 5 完整清單（最終 Sign-off）

### Agent A 確認

- [ ] `phase_artifact_enforcer.py` 通過（Phase 4 完成確認）
- [ ] 缺失文檔已補齊（`doc_checker.py` 無缺失）
- [ ] `spec_logic_checker.py` 分數 ≥ 90（有實際輸出）
- [ ] `BASELINE.md` 建立（功能 + 品質 + 效能基線完整）
- [ ] `QUALITY_REPORT.md` 初版完成
- [ ] `MONITORING_PLAN.md` 四個閾值與腳本完整
- [ ] `VERIFICATION_REPORT.md` Phase 1-4 承諾逐一驗證
- [ ] 已提交第一次 A/B 審查（基線審查）
- [ ] 首次部署完成
- [ ] A/B 持續監控三項全部通過
- [ ] 已提交第二次 A/B 審查（驗收報告審查）

### Agent B 確認

- [ ] **第一次審查**：功能完整性 + 品質基線 + 監控計劃三維度全部確認
- [ ] **第二次審查**：Phase 1-4 承諾 + 監控初次結果 + 文檔完整性三維度確認
- [ ] 已知問題無 HIGH 嚴重性（親自確認）
- [ ] BASELINE.md 雙方簽收（含 session_id 與日期）
- [ ] 兩次 AgentEvaluator 評估完成
- [ ] 給出明確 APPROVE 或 REJECT（含理由）

### Quality Gate 確認

- [ ] `spec_logic_checker.py` ≥ 90 分（工具輸出）
- [ ] `constitution/runner.py` 總分 ≥ 80%
- [ ] `doc_checker.py` Compliance Rate > 80%
- [ ] A/B 監控三項全通過（日誌記錄）
- [ ] `methodology quality` 無 BLOCK 項目

### 記錄確認

- [ ] 兩次 A/B 審查對話完整記錄在 `DEVELOPMENT_LOG.md`
- [ ] `spec_logic_checker.py` 實際輸出貼入 LOG
- [ ] `MONITORING_PLAN.md` 首次監控記錄已填寫
- [ ] `BASELINE.md` 中雙方 session_id 已記錄（可追溯）

---

## 附錄：Phase 4 → Phase 5 知識傳遞

| Phase 4 產出 | Phase 5 使用方式 |
|--------------|----------------|
| TEST_RESULTS.md | 基線品質數據來源；BASELINE 品質基線的依據 |
| TRACEABILITY_MATRIX（完整版）| VERIFICATION_REPORT Phase 1-4 承諾驗證的骨架 |
| 失敗案例修復記錄 | BASELINE 已知問題登錄的輸入 |
| 代碼覆蓋率報告 | 品質基線的覆蓋率欄位 |

## 附錄：Phase 5 在整體架構的位置

```
Phase 1 需求  ──→  Phase 2 設計  ──→  Phase 3 開發  ──→  Phase 4 測試
                                                               │
                                                               ▼
Phase 8 配置  ←──  Phase 7 風險  ←──  Phase 6 品質  ←──  Phase 5 驗收
                                                         （建立基線）
                                                               ↑
                                                        這是轉折點：
                                                        從「建構」轉為「保障」
```

---

## 附錄：快速指令備查

```bash
# ── 前置確認 ────────────────────────────
python3 quality_gate/phase_artifact_enforcer.py

# ── 文檔與邏輯複查 ──────────────────────
python3 quality_gate/doc_checker.py
python3 scripts/spec_logic_checker.py       # 門檻 ≥ 90

# ── Agent 啟動 ──────────────────────────
# Agent A（DevOps）
python -c "from agent_spawner import spawn_with_persona; \
           spawn_with_persona(role='devops', task='Phase 5 驗證與基線建立')"

# Agent B（Architect）
python -c "from agent_spawner import spawn_with_persona; \
           spawn_with_persona(role='architect', task='Phase 5 基線與驗收審查')"

# ── 兩次 A/B 評估 ────────────────────────
python -m agent_evaluator --check   # 第一次：基線審查（部署前）
python -m agent_evaluator --check   # 第二次：驗收報告（部署後）

# ── A/B 持續監控 ────────────────────────
python3 scripts/spec_logic_checker.py
python3 scripts/performance_check.py
python3 scripts/circuit_breaker_check.py

# ── Quality Gate ────────────────────────
python3 quality_gate/constitution/runner.py   # 門檻 ≥ 80%
methodology quality
```

---

*整理依據：SKILL.md v5.56 | methodology-v2 Multi-Agent Collaboration Development Methodology*
*格式：5W1H × A/B 協作機制 | 整理日期：2026-03-29*
