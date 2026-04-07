# Phase 6 計劃：品質保證
## methodology-v2 | 5W1H 框架 × A/B 協作機制

> **版本基準**：SKILL.md v5.56 | 整理日期：2026-03-29
> **前置條件**：Phase 5 全部 Sign-off ✅（BASELINE.md 雙方簽收、A/B 監控三項通過、兩次 APPROVE）

---

## 🗺️ 一覽表

| 5W1H | 核心答案 |
|------|----------|
| **WHO**   | Agent A（QA Lead）深化品質分析 × Agent B（Architect / PM）審查品質報告與改進計劃 |
| **WHAT**  | 完成 QUALITY_REPORT.md（完整版）；執行 Constitution ≥ 80% 全面檢查；持續 A/B 監控並記錄 |
| **WHEN**  | Phase 5 BASELINE 建立後；品質報告審查通過才進 Phase 7；A/B 監控貫穿 Phase 6 全程 |
| **WHERE** | `06-quality/` 目錄；監控記錄在 `MONITORING_PLAN.md`；Quality Gate 在 `quality_gate/` |
| **WHY**   | Phase 5 建立的是「版本快照」，Phase 6 做的是「系統性品質分析」——找出模式、根源與改進路徑 |
| **HOW**   | 品質數據彙整 → 深度分析 → 改進建議 → A/B 審查 → 持續監控確認 → Quality Gate → sign-off |

---

## 1. WHO — 誰執行？（A/B 角色分工）

> ⚠️ **Phase 6 原則**：品質分析必須跨越所有 Phase 的數據，不能只看 Phase 5 的快照。Agent A 需要有能力橫向比對 Phase 1-5 的所有產出。

### Agent A（QA Lead）—— 主責品質深度分析

| 屬性 | 內容 |
|------|------|
| Persona | `qa` |
| Goal | 從 Phase 1-5 的全部數據中找出系統性品質問題，提出具體改進建議 |
| 職責 | 完成 QUALITY_REPORT.md 完整版、分析品質趨勢、設計改進建議、持續執行 A/B 監控 |
| 核心心態 | 「這些問題是個例還是系統性問題？根源在哪個 Phase？」|
| 禁止 | 只描述問題不分析根源；在監控數據不穩定時宣告品質通過 |

```python
# Phase 6 Agent A 啟動
from agent_spawner import spawn_with_persona

agent_a = spawn_with_persona(
    role="qa",
    task="深度分析 Phase 1-5 品質數據，完成 QUALITY_REPORT.md，持續 A/B 監控",
)
```

### Agent B（Architect / PM）—— 主責品質報告審查

| 屬性 | 內容 |
|------|------|
| Persona | `architect` 或 `pm` |
| Goal | 確保品質分析深度足夠、改進建議具體可行、監控數據真實有效 |
| 職責 | 審查 QUALITY_REPORT.md 分析深度、確認改進建議可行性、A/B 評估 |
| 核心問題 | 「改進建議有沒有回溯到具體 Phase 的具體動作？」「監控閾值有沒有根據實際數據調整？」|
| 禁止 | 接受只有數字沒有分析的品質報告；跳過改進建議的可行性確認 |

```python
# Phase 6 Agent B 啟動
agent_b = spawn_with_persona(
    role="architect",
    task="審查品質報告深度與改進建議可行性，確認 A/B 監控數據可信",
)
```

### A/B 協作啟動

```python
from methodology import quick_start
from hybrid_workflow import HybridWorkflow
from agent_evaluator import AgentEvaluator

team = quick_start("full")              # Architect + Dev + Reviewer + Tester
workflow = HybridWorkflow(mode="ON")    # 強制 A/B 審查
evaluator = AgentEvaluator()

# 確認 A/B 監控持續運行
workflow.mode   # 應為 "ON"
team.list_agents()  # 確認 ≥ 2 個 Agent
```

---

## 2. WHAT — 做什麼？（Phase 6 交付物）

### 必要交付物（Mandatory）

| 交付物 | 負責方 | 驗證方 | 位置 |
|--------|--------|--------|------|
| `QUALITY_REPORT.md`（完整版）| Agent A | Agent B + Quality Gate | `06-quality/` |
| `MONITORING_PLAN.md`（Phase 6 更新）| Agent A | Agent B | 專案根目錄 |
| `DEVELOPMENT_LOG.md`（Phase 6 段落）| Agent A | Agent B | 專案根目錄 |

---

### QUALITY_REPORT.md 完整版規格

> Phase 5 已建立初版（品質快照），Phase 6 在此基礎上完成**深度分析**版本。

```markdown
# Quality Report - [專案名稱]（完整版）

## 1. 品質指標全覽（Phase 5 初版 → Phase 6 更新）

| 指標 | 目標 | Phase 5 快照 | Phase 6 驗證 | 趨勢 | 狀態 |
|------|------|-------------|-------------|------|------|
| Constitution 總分 | ≥ 80% | XX% | XX% | ↑/↓/→ | ✅/❌ |
| 代碼覆蓋率 | ≥ 80% | XX% | XX% | ↑/↓/→ | ✅/❌ |
| 測試通過率 | 100% | 100% | 100% | → | ✅ |
| ASPICE 合規率 | > 80% | XX% | XX% | ↑/↓/→ | ✅/❌ |
| 邏輯正確性分數 | ≥ 90 分 | XX 分 | XX 分 | ↑/↓/→ | ✅/❌ |
| A/B 監控：回應時間偏差 | < 10% | X% | X% | ↑/↓/→ | ✅/❌ |
| A/B 監控：熔斷器觸發 | 0 次 | 0 次 | 0 次 | → | ✅ |
| A/B 監控：錯誤率 | < 1% | X% | X% | ↑/↓/→ | ✅/❌ |

## 2. ASPICE 各 Phase 合規性分析

| Phase | 文件 | 合規率 | 主要缺失 | 根源分析 |
|-------|------|--------|----------|----------|
| Phase 1 | SRS.md | XX% | [具體缺失] | [在哪個步驟遺漏] |
| Phase 2 | SAD.md | XX% | [具體缺失] | [在哪個步驟遺漏] |
| Phase 3 | 代碼 + 測試 | XX% | [具體缺失] | [在哪個步驟遺漏] |
| Phase 4 | TEST_PLAN + RESULTS | XX% | [具體缺失] | [在哪個步驟遺漏] |
| Phase 5 | BASELINE + VERIFY | XX% | [具體缺失] | [在哪個步驟遺漏] |

## 3. Constitution 四維度深度分析

### 3.1 正確性（目標 100%）

| 模組 | 正確性分數 | 問題描述 | 根源 Phase | 是否已修復 |
|------|-----------|----------|-----------|-----------|
| ModuleA | XX% | [具體問題] | Phase 3 | ✅/❌ |

### 3.2 安全性（目標 100%）

| 掃描項目 | 結果 | 風險等級 | 處置方式 |
|----------|------|----------|----------|
| SQL Injection | PASS | — | — |
| 敏感資料暴露 | PASS | — | — |

### 3.3 可維護性（目標 > 70%）

| 維度 | 分數 | 主要問題 | 改進建議 |
|------|------|----------|----------|
| 代碼複雜度 | XX% | [說明] | [具體動作] |
| 命名規範 | XX% | [說明] | [具體動作] |
| 文檔完整性 | XX% | [說明] | [具體動作] |

### 3.4 測試覆蓋率（目標 > 80%）

| 類型 | 覆蓋率 | 未覆蓋區域 | 優先補充項 |
|------|--------|-----------|-----------|
| 代碼覆蓋率 | XX% | [模組/函數] | [優先級] |
| 分支覆蓋率 | XX% | [條件分支] | [優先級] |

## 4. 品質問題根源分析（系統性）

### 4.1 問題分類彙整

| 問題類型 | 出現次數 | 首次出現 Phase | 根源原因 |
|----------|----------|---------------|----------|
| 邏輯錯誤（輸出 > 輸入）| X 次 | Phase 3 | 缺乏 Spec Logic Mapping |
| 文檔缺失 | X 次 | Phase 1 | Quality Gate 未嚴格執行 |
| 測試遺漏 | X 次 | Phase 4 | TC 未從 SRS 直接推導 |
| 架構偏離 | X 次 | Phase 3 | Phase 2 SAD 審查不足 |

### 4.2 根源 Phase 分布

```
Phase 1 根源問題：X 個（需求定義不清）
Phase 2 根源問題：X 個（架構設計疏漏）
Phase 3 根源問題：X 個（實作邏輯錯誤）
Phase 4 根源問題：X 個（測試設計不足）
```

## 5. 改進建議（具體可執行）

| 優先級 | 改進項目 | 對應根源 Phase | 具體動作 | 負責角色 | 目標指標 |
|--------|----------|---------------|----------|----------|----------|
| P0 | Spec Logic Mapping 強化 | Phase 3 | 每條 FR 必須有量化驗證方法 | Developer | 邏輯分數 ≥ 95 |
| P1 | Quality Gate 執行率 | Phase 1-4 | 每 Phase 結束前強制執行並貼輸出 | 所有 Agent | 執行率 100% |
| P2 | 負面測試覆蓋率 | Phase 4 | P0 需求強制三類測試 | Tester | FR 負面覆蓋 100% |

## 6. A/B 監控數據分析（Phase 6 期間）

| 日期 | 邏輯分數 | 回應時間偏差 | 錯誤率 | 熔斷器 | 結論 |
|------|----------|-------------|--------|--------|------|
| YYYY-MM-DD | XX/100 | X% | X% | 0 | ✅ |
| YYYY-MM-DD | XX/100 | X% | X% | 0 | ✅ |

### 監控閾值調整記錄（若有）

| 調整日期 | 調整項目 | 原閾值 | 新閾值 | 調整原因 | Agent B 確認 |
|----------|----------|--------|--------|----------|-------------|
| — | — | — | — | — | — |

## 7. 品質目標達成摘要

| 目標 | 達成狀態 | 說明 |
|------|----------|------|
| ASPICE 合規率 > 80% | ✅/❌ | 實際：XX% |
| Constitution 總分 ≥ 80% | ✅/❌ | 實際：XX% |
| 邏輯正確性 ≥ 90 分 | ✅/❌ | 實際：XX 分 |
| A/B 監控全程穩定 | ✅/❌ | 熔斷 0 次 / 錯誤率 X% |
```

---

### A/B 品質報告審查清單（Agent B）

**分析深度**
- [ ] 品質指標有 Phase 5 vs Phase 6 的趨勢對比（非只有當下數字）
- [ ] ASPICE 各 Phase 合規率有具體缺失項目（非只有百分比）
- [ ] Constitution 四維度有模組級別的細化分析
- [ ] 問題分類有「首次出現 Phase」的根源追溯

**改進建議可行性**
- [ ] 每條改進建議有具體動作（動詞 + 對象 + 門檻）
- [ ] 改進建議有對應的負責角色（不能是「系統自動改善」）
- [ ] P0 優先級改進建議有目標指標（可量化驗證）
- [ ] 改進建議已考慮對後續 Phase 6-8 的影響

**監控數據可信度**
- [ ] MONITORING_PLAN.md 的監控記錄連續（無空白日期）
- [ ] 監控閾值調整（若有）有 Agent B 書面確認
- [ ] A/B 監控數據有工具自動產生（非手動填入）

**Constitution 四維度完整**
- [ ] 正確性：模組級別有明細（非只有總分）
- [ ] 安全性：掃描結果有具體項目（非只說「通過」）
- [ ] 可維護性：有具體可維護性問題描述
- [ ] 測試覆蓋率：有未覆蓋區域的具體模組/函數

---

## 3. WHEN — 何時執行？（時序 & 門檻）

### Phase 6 完整時序圖

```
Phase 5 sign-off ✅（BASELINE 建立）
        │
        ▼
[前置確認] phase_artifact_enforcer.py
        │
        ├── ❌ Phase 5 未完成 → 停止
        └── ✅ 通過
                │
                ▼
        [持續] A/B 監控維持（每日執行）
        spec_logic_checker ≥ 90
        performance_check < 10% 偏差
        circuit_breaker_check = 0 次
                │
                ▼ （同時進行）
        [Agent A] 彙整 Phase 1-5 品質數據
        從所有 Phase 的 DEVELOPMENT_LOG 提取數字
                │
                ▼
        [Agent A] 執行 Constitution 全面檢查
        python3 quality_gate/constitution/runner.py
        目標：≥ 80%
                │
                ├── < 80% → 找出低分模組 → 修正 → 重新檢查
                └── ≥ 80%
                        │
                        ▼
                [Agent A] 品質根源分析
                問題分類 → 根源 Phase 定位 → 系統性規律識別
                        │
                        ▼
                [Agent A] 撰寫改進建議
                P0/P1/P2 優先級 + 具體動作 + 目標指標
                        │
                        ▼
                [Agent A] 完成 QUALITY_REPORT.md 完整版
                        │
                        ▼
                [Agent A → Agent B]
                品質報告 A/B 審查
                HybridWorkflow mode=ON 觸發
                        │
                        ├── ❌ REJECT
                        │       └── Agent A 深化分析 / 補充數據 → 重新提交
                        │
                        └── ✅ APPROVE
                                │
                                ▼
                        ASPICE 文檔完整性最終確認
                        python3 quality_gate/doc_checker.py
                                │
                                ▼
                        Framework Enforcement
                        methodology quality
                                │
                                ├── BLOCK 項目存在 → 解決 → 重新執行
                                └── 無 BLOCK
                                        │
                                        ▼
                                記錄 DEVELOPMENT_LOG.md
                                        │
                                        ▼
                                ✅ Phase 6 完成 → 進入 Phase 7
```

### 進入 Phase 7 的前置條件（全部必須為 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| Constitution 總分 | ≥ 80% | Constitution Runner 實際輸出 |
| ASPICE 合規率 | > 80% | doc_checker.py 實際輸出 |
| 邏輯正確性分數 | ≥ 90 分 | spec_logic_checker.py 實際輸出 |
| A/B 監控：Phase 6 全程穩定 | 熔斷 0 次、錯誤率 < 1% | MONITORING_PLAN.md 連續記錄 |
| QUALITY_REPORT.md 完整版 | 七個章節全部完成 | Agent B 審查確認 |
| 品質問題根源分析 | 有根源 Phase 定位 | Agent B 審查確認 |
| 改進建議 P0 全部有目標指標 | 可量化 | Agent B 審查確認 |
| Agent B APPROVE | AgentEvaluator 輸出 | AgentEvaluator |
| Framework Enforcement | 無 BLOCK | methodology quality 輸出 |

---

## 4. WHERE — 在哪裡執行？（路徑 & 工具位置）

### 文件結構（Phase 6 新增 / 更新）

```
project-root/
├── 01-requirements/           ← Phase 1（只讀）
├── 02-architecture/           ← Phase 2（只讀）
├── 03-implementation/         ← Phase 3（只讀）
├── 04-testing/                ← Phase 4（只讀）
├── 05-verify/                 ← Phase 5（只讀）
│
├── 06-quality/                ← Phase 6 主要工作區
│   └── QUALITY_REPORT.md      ← 完整版（Phase 5 初版升級）
│
├── scripts/
│   ├── spec_logic_checker.py  ← 邏輯正確性（每日監控）
│   ├── performance_check.py   ← 效能監控（每日監控）
│   └── circuit_breaker_check.py ← 熔斷器狀態（每日監控）
│
├── quality_gate/
│   ├── doc_checker.py         ← ASPICE 最終確認
│   ├── constitution/
│   │   └── runner.py          ← 全面檢查（門檻 ≥ 80%）
│   └── phase_artifact_enforcer.py
│
├── MONITORING_PLAN.md         ← Phase 6 期間監控記錄（每日更新）
└── DEVELOPMENT_LOG.md         ← Phase 6 段落
```

### 工具執行位置

```bash
# ── 前置確認 ────────────────────────────
python3 quality_gate/phase_artifact_enforcer.py

# ── 每日 A/B 監控（Phase 6 全程）────────
python3 scripts/spec_logic_checker.py
python3 scripts/performance_check.py
python3 scripts/circuit_breaker_check.py

# ── Constitution 全面檢查 ────────────────
python3 quality_gate/constitution/runner.py
# 門檻：≥ 80%（Phase 6 最終確認）

# ── ASPICE 文檔完整性 ────────────────────
python3 quality_gate/doc_checker.py

# ── Framework Enforcement ───────────────
methodology quality
# 預期：✅ 全部通過，無 BLOCK

# ── A/B 評估 ────────────────────────────
python -m agent_evaluator --check
```

---

## 5. WHY — 為什麼這樣做？（設計理由）

### Phase 5 品質快照 vs Phase 6 品質分析：本質差異

| 維度 | Phase 5（快照）| Phase 6（分析）|
|------|----------------|----------------|
| 時間維度 | 某一時刻的狀態 | Phase 1-5 的完整趨勢 |
| 問題處理 | 記錄問題存在 | 追溯問題根源 Phase |
| 行動導向 | 確認可交付 | 提供具體改進路徑 |
| 監控角色 | 啟動監控 | 持續驗證監控穩定性 |
| 輸出用途 | 基線建立依據 | Phase 7 風險評估輸入 |

Phase 6 的核心價值不是「再做一次 Phase 5」，而是提供**系統性的品質透視**——找出跨 Phase 的規律，讓 Phase 7 的風險評估有數據基礎，讓未來專案的 Phase 1 能避免同樣的根源問題。

### 為什麼要做「根源 Phase 分析」？

表面問題 vs 根源問題的區別：

```
表面問題：Phase 4 測試覆蓋率只有 72%
↓ 根源追溯
根源問題：Phase 4 的 Tester 看著 Phase 3 代碼設計 TC（確認偏誤）
         → 沒有從 SRS 推導負面測試
         → 根源在 Phase 4 的 WHO 設計（Tester 角色不獨立）

改進動作（針對根源）：
  Phase 4 開始前，Tester persona 必須在讀 SRS 前被 enforcer 阻擋讀取代碼
```

沒有根源分析，改進建議就只是「下次要更仔細」——無法防止再發生。

### Constitution ≥ 80% 為何是 Phase 6 的核心門檻？

Phase 1-4 的 Constitution 要求各有側重（SRS 正確性 100%、SAD 可維護性 > 70%……），Phase 6 要求的是**整體總分 ≥ 80%**，代表所有維度加權後的系統性品質水準。

這個門檻的設計邏輯：
- Phase 5 建立基線時，Constitution 總分可能還在 75-79% 的邊緣
- Phase 6 透過修正低分模組，確保總分跨越 80% 門檻
- 進入 Phase 7（風險評估）時，品質基礎必須是穩固的

### 為什麼改進建議需要「P0/P1/P2 優先級 + 目標指標」？

沒有優先級和目標指標的改進建議是「裝飾性文字」：

```
❌ 差的改進建議：
「建議加強代碼審查」
「測試應該更全面」
「文檔需要補充」

✅ 好的改進建議（P0）：
改進項目：Spec Logic Mapping 強化
對應根源：Phase 3，缺乏量化邏輯驗證方法
具體動作：每條 SRS FR 必須在 Phase 3 開始前填寫「邏輯驗證方法」欄位
          Agent B 在 Phase 2 審查時確認填寫完整
          Quality Gate 阻擋「邏輯驗證方法為空」的 FR
負責角色：Developer（填寫）+ Reviewer（確認）
目標指標：邏輯正確性分數 ≥ 95 分（現為 XX 分）
可量化驗證：執行 spec_logic_checker.py，目標 ≥ 95
```

### A/B 監控在 Phase 6 的特殊意義

Phase 5 啟動監控，Phase 6 是**首次長期穩定性驗證**。如果監控在 Phase 6 期間出現波動：

- 說明 BASELINE.md 的效能基線可能設定不準確（需要校正）
- 說明系統在持續運行後有退化趨勢（需要 Phase 7 風險評估）
- 說明 Phase 3 的某些邏輯問題在壓力下才顯現

Phase 6 監控數據是 Phase 7 風險登錄表的**直接輸入**——穩定 = 低技術風險，不穩定 = 高技術風險需要緩解措施。

---

## 6. HOW — 如何執行？（完整 SOP）

### Step 0：前置確認 + 監控維持（Agent A）

```bash
# 確認 Phase 5 已完成
python3 quality_gate/phase_artifact_enforcer.py

# 確認 A/B 監控機制持續運行
python3 scripts/spec_logic_checker.py      # ≥ 90 分
python3 scripts/performance_check.py       # < 10% 偏差
python3 scripts/circuit_breaker_check.py   # 0 次觸發

# 確認監控記錄格式已設定（MONITORING_PLAN.md）
cat MONITORING_PLAN.md | tail -20
```

### Step 1：Phase 1-5 品質數據彙整（Agent A）

```markdown
數據來源（依序讀取）：
1. 各 Phase DEVELOPMENT_LOG.md 的 Quality Gate 結果
2. Constitution Runner 歷次輸出（Phase 1-5）
3. pytest 覆蓋率報告（Phase 3-4）
4. spec_logic_checker.py 歷次分數（Phase 5）
5. MONITORING_PLAN.md 的監控記錄（Phase 5-6）
6. TRACEABILITY_MATRIX.md（需求 → 測試完整度）

彙整格式：
- 每個 Phase 的 Constitution 四維度分數
- 每個 Phase 的 ASPICE 合規率
- 每次失敗案例的 TC ID 與根源描述
- 每次邏輯審查中發現的問題類型
```

### Step 2：Constitution 全面檢查（Agent A）

```bash
# 執行全面檢查（不加 --type）
python3 quality_gate/constitution/runner.py

# 預期輸出：
# 正確性:   XX%（目標 100%）
# 安全性:   XX%（目標 100%）
# 可維護性: XX%（目標 > 70%）
# 覆蓋率:   XX%（目標 > 80%）
# 總分:     XX%（Phase 6 門檻：≥ 80%）

# 若 < 80%：
# 1. 識別低分維度與具體模組
# 2. 修正低分項目（對應 Phase 3 代碼或 Phase 4 測試）
# 3. 重新執行 constitution/runner.py
# 4. 直到總分 ≥ 80% 才繼續
```

### Step 3：品質根源分析（Agent A）

```markdown
分析流程（三層遞進）：

Layer 1：問題識別
  → 從 Phase 1-5 的 DEVELOPMENT_LOG 提取所有「REJECT」、「失敗」、「未通過」記錄
  → 從 Constitution 低分維度找出具體問題描述

Layer 2：分類彙整
  → 依問題類型分類：邏輯錯誤 / 文檔缺失 / 測試遺漏 / 架構偏離 / 其他
  → 統計每類問題的出現次數

Layer 3：根源 Phase 定位
  → 對每類問題，追溯「最早應該被攔截的 Phase」
  → 識別該 Phase 哪個步驟、哪個門檻沒有發揮作用
  → 提出針對根源的具體改進動作（非泛泛建議）
```

### Step 4：撰寫改進建議（Agent A）

```markdown
改進建議撰寫標準：

每條改進建議必須包含：
1. 改進項目名稱（一句話）
2. 對應根源 Phase（具體）
3. 具體動作（動詞 + 對象 + 方法）
4. 負責角色（具體 persona）
5. 目標指標（可量化）
6. 可驗證方式（執行什麼命令或看什麼輸出）

優先級定義：
P0 = 影響品質門檻達成；下個版本必須改善
P1 = 顯著提升品質；建議下個版本改善
P2 = 漸進式改善；可在迭代中逐步落實
```

### Step 5：A/B 品質報告審查（Agent A → Agent B）

```python
from agent_evaluator import AgentEvaluator
from hybrid_workflow import HybridWorkflow

workflow = HybridWorkflow(mode="ON")
evaluator = AgentEvaluator()

# 品質報告 A/B 審查
quality_result = evaluator.evaluate(
    spec_a=quality_report_complete,   # QUALITY_REPORT.md 完整版
    spec_b=quality_review_checklist   # Agent B 的審查標準
)

if not quality_result.approved:
    raise Exception(
        f"品質報告未通過審查：{quality_result.rejection_reason}"
    )

print(f"✅ 品質報告審查通過：{quality_result.score}/100")
```

**Agent B 品質報告審查對話模板**：

```markdown
## Phase 6 品質報告 A/B 審查紀錄

### 分析深度確認

**品質趨勢**
- [ ] 品質指標有 Phase 5 vs Phase 6 趨勢對比：✅/❌
- [ ] ASPICE 各 Phase 合規率有具體缺失（非只有百分比）：✅/❌
- 說明：______

**Constitution 四維度細化**
- [ ] 正確性：有模組級別明細：✅/❌
- [ ] 安全性：有具體掃描項目結果：✅/❌
- [ ] 可維護性：有具體問題描述：✅/❌
- [ ] 覆蓋率：有未覆蓋區域的模組/函數：✅/❌
- 說明：______

**根源分析深度**
- [ ] 每類問題有「首次出現 Phase」標記：✅/❌
- [ ] 根源定位到具體步驟（非只說「Phase X 問題」）：✅/❌
- [ ] 問題分類有系統性規律識別：✅/❌
- 說明：______

### 改進建議可行性

- [ ] P0 建議全部有目標指標（可量化）：✅/❌
- [ ] 每條建議有具體負責角色（非「系統」）：✅/❌
- [ ] P0 建議有可驗證方式（命令或輸出）：✅/❌
- [ ] 改進建議無「一般性建議」（如「更仔細」）：✅/❌
- 說明：______

### 監控數據可信度

- [ ] Phase 6 期間監控記錄連續（無空白）：✅/❌
- [ ] 監控數據有工具自動產生（非手填）：✅/❌
- [ ] 閾值調整（若有）有書面確認：✅/❌
- 說明：______

### 審查結論

- [ ] ✅ APPROVE — 進入 Quality Gate
- [ ] ❌ REJECT — 深化分析（原因：______）

Agent B 簽名：______  Session ID：______  日期：______
```

### Step 6：Quality Gate 最終確認（Agent A）

```bash
# ASPICE 文檔完整性
python3 quality_gate/doc_checker.py
# 預期：Compliance Rate > 80%

# Framework Enforcement（最嚴格的系統性檢查）
methodology quality
# 預期：
# ✅ SPEC_TRACKING.md 存在
# ✅ 規格完整性 > 90%
# ✅ Constitution Score > 60%（實際應 ≥ 80%）
# ✅ Framework Enforcement 通過
```

### Step 7：DEVELOPMENT_LOG.md 記錄（正確格式）

```markdown
## Phase 6 Quality Gate 結果（YYYY-MM-DD HH:MM）

### 前置確認
執行命令：python3 quality_gate/phase_artifact_enforcer.py
結果：Phase 5 完成 ✅

### A/B 監控摘要（Phase 6 全程）
監控期間：YYYY-MM-DD 至 YYYY-MM-DD（X 天）
- 邏輯正確性：最低 XX 分，最高 XX 分，平均 XX 分 ✅
- 回應時間偏差：最大 X%（門檻 < 10%）✅
- 熔斷器觸發：0 次（全程）✅
- 錯誤率：最高 X%（門檻 < 1%）✅
異常事件：[無 / 說明異常與處置]

### Constitution 全面檢查
執行命令：python3 quality_gate/constitution/runner.py
結果：
- 正確性:   XX%（目標 100%）
- 安全性:   XX%（目標 100%）
- 可維護性: XX%（目標 > 70%）
- 覆蓋率:   XX%（目標 > 80%）
- 總分:     XX%（目標 ≥ 80%）✅/❌

### 品質問題根源分析摘要
- 邏輯錯誤類：X 個，根源 Phase 3，改進 P0
- 文檔缺失類：X 個，根源 Phase 1，改進 P1
- 測試遺漏類：X 個，根源 Phase 4，改進 P0
- 架構偏離類：X 個，根源 Phase 2，改進 P1

### A/B 品質報告審查
- Agent A（QA Lead）：session_id ______
- Agent B（Architect）：session_id ______
- AgentEvaluator Score：XX/100
- 審查結論：APPROVE ✅
- 審查日期：______

### ASPICE 文檔完整性
執行命令：python3 quality_gate/doc_checker.py
結果：Compliance Rate: XX%

### Framework Enforcement
執行命令：methodology quality
結果：✅ Framework Enforcement 通過（無 BLOCK 項目）

### Phase 6 結論
- [ ] ✅ 通過，QUALITY_REPORT.md 完整版建立，進入 Phase 7
- [ ] ❌ 未通過（原因：______）
```

> ❌ **禁止這樣記錄**：
> ```markdown
> ### Phase 6 Quality Gate
> ✅ 品質良好，通過
> ```

---

## 7. Phase 6 完整清單（最終 Sign-off）

### Agent A 確認

- [ ] `phase_artifact_enforcer.py` 通過（Phase 5 完成確認）
- [ ] A/B 監控全程維持（每日記錄在 MONITORING_PLAN.md）
- [ ] Phase 1-5 品質數據彙整完成
- [ ] `constitution/runner.py` 總分 ≥ 80%（有實際輸出）
- [ ] 品質問題根源分析完成（三層：識別 → 分類 → 根源定位）
- [ ] 改進建議撰寫完成（P0 全部有目標指標與可驗證方式）
- [ ] `QUALITY_REPORT.md` 完整版七章節全部完成
- [ ] 已提交 A/B 品質報告審查

### Agent B 確認

- [ ] 分析深度四項確認（趨勢 + Constitution 四維度 + 根源分析）
- [ ] 改進建議四項確認（指標 + 角色 + 可驗證 + 非泛泛建議）
- [ ] 監控數據三項確認（連續 + 工具產生 + 閾值調整有書面）
- [ ] AgentEvaluator 評估完成
- [ ] 給出明確 APPROVE 或 REJECT（含理由）
- [ ] Session ID 已記錄

### Quality Gate 確認

- [ ] `constitution/runner.py` 總分 ≥ 80%（工具輸出）
- [ ] `doc_checker.py` Compliance Rate > 80%
- [ ] `methodology quality` 無 BLOCK 項目
- [ ] A/B 監控 Phase 6 全程記錄連續（MONITORING_PLAN.md）

### 記錄確認

- [ ] A/B 審查對話記錄在 `DEVELOPMENT_LOG.md`
- [ ] Constitution 實際輸出貼入 LOG（非摘要）
- [ ] A/B 監控全程摘要記錄在 LOG
- [ ] 雙方 session_id 已記錄（可追溯）

---

## 附錄：Phase 5 → Phase 6 知識傳遞

| Phase 5 產出 | Phase 6 使用方式 |
|--------------|----------------|
| BASELINE.md（品質基線數字）| Phase 6 品質趨勢對比的基準 |
| QUALITY_REPORT.md（初版）| Phase 6 升級為完整版的起點 |
| MONITORING_PLAN.md（啟動）| Phase 6 繼續填充監控記錄 |
| VERIFICATION_REPORT.md | Phase 6 根源分析的 Phase 1-5 承諾對照依據 |

## 附錄：Phase 6 在整體架構的位置

```
Phase 1-4（建構）→ Phase 5（驗收，建立基線）
                                    │
                                    ▼
                             Phase 6（品質分析）
                             ↙              ↘
                    輸出給 Phase 7        輸入來自 Phase 1-5
                   （風險登錄表依據）    （跨 Phase 數據彙整）
```

Phase 6 是整個方法論中**橫向整合最強**的 Phase：
- 縱向：彙整 Phase 1-5 的所有品質數據
- 橫向：同時維持 A/B 持續監控
- 前向：為 Phase 7 風險評估提供數據基礎

---

## 附錄：快速指令備查

```bash
# ── 前置確認 ────────────────────────────
python3 quality_gate/phase_artifact_enforcer.py

# ── 每日 A/B 監控（全程維持）────────────
python3 scripts/spec_logic_checker.py
python3 scripts/performance_check.py
python3 scripts/circuit_breaker_check.py

# ── Agent 啟動 ──────────────────────────
# Agent A（QA Lead）
python -c "from agent_spawner import spawn_with_persona; \
           spawn_with_persona(role='qa', task='Phase 6 品質深度分析')"

# Agent B（Architect）
python -c "from agent_spawner import spawn_with_persona; \
           spawn_with_persona(role='architect', task='Phase 6 品質報告審查')"

# ── Constitution 全面檢查 ────────────────
python3 quality_gate/constitution/runner.py   # 門檻 ≥ 80%

# ── A/B 評估 ────────────────────────────
python -m agent_evaluator --check

# ── Quality Gate ────────────────────────
python3 quality_gate/doc_checker.py
methodology quality
```

---

*整理依據：SKILL.md v5.56 | methodology-v2 Multi-Agent Collaboration Development Methodology*
*格式：5W1H × A/B 協作機制 | 整理日期：2026-03-29*
