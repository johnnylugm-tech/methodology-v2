# Phase 4 計劃：測試
## methodology-v2 | 5W1H 框架 × A/B 協作機制

> **版本基準**：SKILL.md v5.56 | 整理日期：2026-03-29
> **前置條件**：Phase 3 全部 Sign-off ✅（代碼 APPROVE、覆蓋率 ≥ 80%、phase_artifact_enforcer 通過）

---

## 🗺️ 一覽表

| 5W1H | 核心答案 |
|------|----------|
| **WHO**   | Agent A（Tester）設計 & 執行測試 × Agent B（QA Reviewer / Dev）審查測試計劃 & 結果 |
| **WHAT**  | 產出 TEST_PLAN.md + TEST_RESULTS.md；執行完整測試套件；更新 TRACEABILITY_MATRIX |
| **WHEN**  | Phase 3 完整通過後；TEST_PLAN 審查通過才能執行測試；測試結果審查通過才進 Phase 5 |
| **WHERE** | `04-testing/` 目錄；測試執行在 `tests/`；Quality Gate 在 `quality_gate/` |
| **WHY**   | Phase 3 的測試是「開發者自測」，Phase 4 是「獨立驗證」——視角不同才能發現不同缺陷 |
| **HOW**   | A 撰寫計劃 → B 審查計劃 → A 執行測試 → B 審查結果 → Quality Gate → sign-off |

---

## 1. WHO — 誰執行？（A/B 角色分工）

> ⚠️ **Phase 4 核心原則**：Tester（Agent A）必須與 Phase 3 的 Developer **不同 Agent**。
> 讓寫代碼的人設計測試，等同於讓人自己出題自己改卷。

### Agent A（Tester）—— 主責測試設計 & 執行

| 屬性 | 內容 |
|------|------|
| Persona | `qa` |
| Goal | 從**使用者需求**角度驗證系統行為，而非從「代碼實作」角度驗證 |
| 職責 | 撰寫 TEST_PLAN.md、設計測試案例、執行測試、記錄 TEST_RESULTS.md |
| 核心心態 | 「這個功能**應該**怎麼運作？」而不是「這段代碼**能不能**跑過？」|
| 禁止 | 查看 Phase 3 代碼再設計測試案例（避免確認偏誤）；自行判定測試通過 |

```python
# Phase 4 Agent A 啟動
from agent_spawner import spawn_with_persona

agent_a = spawn_with_persona(
    role="qa",
    task="依據 SRS.md 設計測試計劃，獨立驗證系統行為",
)
```

### Agent B（QA Reviewer / Senior Dev）—— 主責審查計劃 & 結果

| 屬性 | 內容 |
|------|------|
| Persona | `reviewer` |
| Goal | 確保測試計劃覆蓋所有 SRS 需求；測試結果真實可信 |
| 職責 | 審查 TEST_PLAN（計劃完整性）、審查 TEST_RESULTS（結果真實性）、執行 A/B 評估 |
| 核心問題 | 「測試案例是從 SRS 推導的嗎？」「失敗案例的根本原因分析夠深嗎？」|
| 禁止 | 幫 Agent A 補寫測試案例；接受「已手動確認」等無法重現的測試記錄 |

```python
# Phase 4 Agent B 啟動
agent_b = spawn_with_persona(
    role="reviewer",
    task="審查測試計劃完整性與測試結果真實性",
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

# Phase 4 特別確認：Tester ≠ Phase 3 Developer
phase3_dev_id = get_phase3_developer_session_id()
phase4_tester_id = agent_a.session_id
assert phase3_dev_id != phase4_tester_id, \
    "Tester 不能是 Phase 3 的 Developer！"
```

---

## 2. WHAT — 做什麼？（Phase 4 交付物）

### 必要交付物（Mandatory）

| 交付物 | 負責方 | 驗證方 | 位置 |
|--------|--------|--------|------|
| `TEST_PLAN.md` | Agent A | Agent B + Quality Gate | `04-testing/` |
| `TEST_RESULTS.md` | Agent A | Agent B | `04-testing/` |
| `TRACEABILITY_MATRIX.md`（更新）| Agent A | Agent B | 專案根目錄 |
| `DEVELOPMENT_LOG.md`（Phase 4 段落）| Agent A | Agent B | 專案根目錄 |

---

### TEST_PLAN.md 完整規格

```markdown
# Test Plan - [專案名稱]

## 1. 測試目標
- 驗證所有 SRS FR 的功能行為符合預期
- 確認邊界條件與異常情況的處理正確
- 驗證跨模組集成行為無迴歸

## 2. 測試範圍

### 納入範圍
- 所有 SRS 功能需求（FR-01 ~ FR-XX）
- 非功能需求中可測試項目（效能、錯誤恢復）
- 跨模組集成點

### 排除範圍
- [明確說明哪些場景不在本次測試]

## 3. 測試策略

| 類型 | 方法 | 工具 | 覆蓋目標 |
|------|------|------|----------|
| 單元測試 | White-box | pytest | ≥ 80% |
| 集成測試 | Black-box | pytest / requests | 所有跨模組介面 |
| 系統測試 | End-to-End | 自動化腳本 | 所有 FR |
| 負面測試 | Fault Injection | pytest | 所有 L1-L6 錯誤路徑 |

## 4. 測試環境
| 項目 | 規格 |
|------|------|
| OS | Ubuntu 24 / macOS |
| Python | 3.11 |
| 測試框架 | pytest 8.x |
| 覆蓋率工具 | pytest-cov |

## 5. 測試案例清單（從 SRS 直接推導）

| TC ID | 對應 SRS ID | 測試案例名稱 | 測試類型 | 優先級 | 狀態 |
|-------|-------------|-------------|----------|--------|------|
| TC-001 | FR-01 | 正常文字分段 | 正向 | P0 | 待執行 |
| TC-002 | FR-01 | 空白輸入分段 | 邊界 | P0 | 待執行 |
| TC-003 | FR-01 | 合併後不多於原文 | 負面 | P0 | 待執行 |
| TC-004 | FR-05 | 單一 vs 多檔案格式一致 | 負面 | P0 | 待執行 |

## 6. 風險與緩解

| 風險 | 影響 | 緩解措施 |
|------|------|----------|
| 測試環境不穩定 | 高 | 容器化隔離 |
| 外部 API 不可用 | 中 | Mock 替代 |
```

---

### TEST_RESULTS.md 完整規格

```markdown
# Test Results - [專案名稱]

## 執行摘要

| 項目 | 數值 |
|------|------|
| 執行日期 | YYYY-MM-DD HH:MM |
| 總測試數 | XX |
| 通過 | XX |
| 失敗 | XX |
| 略過 | XX |
| 通過率 | XX% |
| 代碼覆蓋率 | XX% |

## 詳細結果

| TC ID | 測試案例 | 預期結果 | 實際結果 | 狀態 | 備註 |
|-------|----------|----------|----------|------|------|
| TC-001 | 正常文字分段 | 回傳 3 段 | 回傳 3 段 | ✅ PASS | |
| TC-003 | 合併後不多於原文 | len ≤ 原文 | len ≤ 原文 | ✅ PASS | |

## 失敗案例分析

### TC-XXX：[失敗案例名稱]
- **根本原因**：[具體技術原因，不能只說「邏輯錯誤」]
- **影響範圍**：[影響哪些 SRS FR]
- **修復方式**：[具體代碼修改說明]
- **修復驗證**：[重新執行後的結果]
- **狀態**：已修復 / 待修復 / 已知問題

## 覆蓋率報告

| 類型 | 覆蓋率 | 目標 | 狀態 |
|------|--------|------|------|
| 代碼覆蓋率 | XX% | ≥ 80% | ✅/❌ |
| 分支覆蓋率 | XX% | ≥ 70% | ✅/❌ |
| SRS FR 覆蓋率 | XX% | 100% | ✅/❌ |

## 回歸測試

| 之前失敗的案例 | 本次結果 | 說明 |
|--------------|----------|------|
| TC-XXX | ✅ PASS | 已修復並驗證 |
```

---

### A/B 測試計劃審查清單（Agent B，測試執行前）

**需求追蹤完整性**
- [ ] 每條 SRS FR 都有至少一個對應的 TC
- [ ] 高優先級 FR（P0）有正向 + 邊界 + 負面三類測試
- [ ] TRACEABILITY_MATRIX 的 FR → TC 欄位已填寫

**測試設計品質**
- [ ] 測試案例從 SRS 推導（不是從代碼推導）
- [ ] 負面測試包含：空輸入、超長輸入、合併後字符驗證、格式一致性
- [ ] 錯誤路徑測試覆蓋 L1-L6 分類
- [ ] 測試環境已明確定義

**可執行性**
- [ ] 每個 TC 有明確的「預期結果」（可量化，非主觀描述）
- [ ] 測試可自動化執行（非「手動確認」）
- [ ] Mock 策略已定義（外部依賴如何處理）

---

### A/B 測試結果審查清單（Agent B，測試執行後）

**結果真實性**
- [ ] 所有測試有實際 pytest 輸出（非「已確認通過」）
- [ ] 失敗案例有完整的根本原因分析
- [ ] 覆蓋率報告是工具自動生成的（非手寫數字）

**問題處理完整性**
- [ ] 每個失敗案例都有修復記錄或已知問題說明
- [ ] 修復後的回歸測試已執行
- [ ] SRS FR 覆蓋率 = 100%（無遺漏需求）

---

## 3. WHEN — 何時執行？（時序 & 門檻）

### Phase 4 完整時序圖

```
Phase 3 sign-off ✅
        │
        ▼
[前置確認] phase_artifact_enforcer.py
        │
        ├── ❌ Phase 3 未完成 → 停止
        └── ✅ 通過
                │
                ▼
        [Agent A] 讀取 SRS.md
        從需求出發設計測試（不看代碼）
                │
                ▼
        [Agent A] 撰寫 TEST_PLAN.md
        TC 與 SRS FR 一一對應
                │
                ▼
        [Agent A → Agent B]
        TEST_PLAN A/B 審查
        HybridWorkflow mode=ON 觸發
                │
                ├── ❌ REJECT
                │       │
                │       └── Agent A 修改 TEST_PLAN → 重新審查
                │
                └── ✅ APPROVE
                        │
                        ▼
                Constitution test_plan 檢查
                python3 quality_gate/constitution/runner.py --type test_plan
                        │
                        ├── 未通過 → 修正 → 重新 Gate
                        └── 通過
                                │
                                ▼
                        [Agent A] 執行完整測試套件
                        pytest tests/ -v --cov=src
                                │
                                ├── 有失敗案例
                                │       │
                                │       └── 根本原因分析
                                │           → 通知 Phase 3 Developer 修復
                                │           → 修復後重新執行
                                │
                                └── 全部通過
                                        │
                                        ▼
                                [Agent A → Agent B]
                                TEST_RESULTS A/B 審查
                                        │
                                        ├── ❌ REJECT（結果不可信）
                                        │       └── Agent A 補充說明 / 重新執行
                                        │
                                        └── ✅ APPROVE
                                                │
                                                ▼
                                        更新 TRACEABILITY_MATRIX
                                        （FR → TC 欄位）
                                                │
                                                ▼
                                        ASPICE 文檔完整性檢查
                                        python3 quality_gate/doc_checker.py
                                                │
                                                ▼
                                        記錄 DEVELOPMENT_LOG.md
                                                │
                                                ▼
                                        ✅ Phase 4 完成 → 進入 Phase 5
```

> **關鍵節點**：Phase 4 有**兩次** A/B 審查——
> 第一次在執行測試**前**（審查計劃），第二次在執行測試**後**（審查結果）。
> 兩次都必須 APPROVE 才能繼續。

### 進入 Phase 5 的前置條件（全部必須為 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| TEST_PLAN A/B 審查通過 | APPROVE | AgentEvaluator（計劃版）|
| Constitution test_plan | 正確性 100%、可維護性 > 70% | Constitution Runner |
| pytest 全部測試通過 | 通過率 = 100% | pytest 實際輸出 |
| 代碼覆蓋率 | ≥ 80% | pytest-cov 實際輸出 |
| SRS FR 覆蓋率 | = 100%（每條 FR 有對應 TC）| Agent B 確認 |
| 失敗案例全數修復 | 0 個 open 失敗 | TEST_RESULTS.md |
| TEST_RESULTS A/B 審查通過 | APPROVE | AgentEvaluator（結果版）|
| TRACEABILITY_MATRIX 更新 | FR → TC 欄位完整 | Agent B |
| ASPICE 合規率 | > 80% | doc_checker |

---

## 4. WHERE — 在哪裡執行？（路徑 & 工具位置）

### 文件結構（Phase 4 新增 / 更新）

```
project-root/
├── 01-requirements/               ← Phase 1（只讀）
├── 02-architecture/               ← Phase 2（只讀）
├── 03-implementation/             ← Phase 3（只讀，修復除外）
│
├── 04-testing/                    ← Phase 4 主要工作區
│   ├── TEST_PLAN.md               ← Agent A 設計（從 SRS 推導）
│   └── TEST_RESULTS.md            ← 執行後填寫（含失敗分析）
│
├── tests/                         ← 測試代碼（Phase 3 建立，Phase 4 補充）
│   ├── test_unit_*.py             ← 單元測試
│   ├── test_integration.py        ← 集成測試
│   └── test_system.py             ← 系統測試（Phase 4 新增）
│
├── quality_gate/
│   ├── doc_checker.py
│   └── constitution/
│       └── runner.py              ← --type test_plan 執行
│
└── DEVELOPMENT_LOG.md             ← Phase 4 段落（含兩次審查記錄）
```

### 工具執行位置

```bash
# ── 前置確認 ────────────────────────────
python3 quality_gate/phase_artifact_enforcer.py

# ── TEST_PLAN 品質檢查 ──────────────────
python3 quality_gate/constitution/runner.py --type test_plan

# ── 測試執行 ────────────────────────────
pytest tests/ -v \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=html:coverage_report/ \
  --tb=short

# ── ASPICE 文檔檢查 ──────────────────────
python3 quality_gate/doc_checker.py

# ── A/B 評估（計劃 & 結果各一次）──────────
python -m agent_evaluator --check

# ── Framework Enforcement ───────────────
methodology quality
```

---

## 5. WHY — 為什麼這樣做？（設計理由）

### Phase 4 測試 vs Phase 3 測試：本質差異

| 維度 | Phase 3（開發者自測）| Phase 4（獨立驗證）|
|------|---------------------|-------------------|
| 設計視角 | 代碼能不能跑 | 需求有沒有被滿足 |
| 測試依據 | 看著代碼寫 | 看著 SRS 寫 |
| 確認偏誤 | 高（自己寫自己測）| 低（不同 Agent）|
| 缺陷發現率 | 發現「我沒想到的邊界」| 發現「需求理解偏差」|
| 目標 | 覆蓋率 ≥ 80% | SRS FR 覆蓋率 = 100% |

### 為什麼要「兩次 A/B 審查」？

**第一次（計劃審查）**：防止帶著錯誤的計劃執行大量測試，浪費時間。如果 TEST_PLAN 漏掉 5 條 FR，執行完才發現，等於整個 Phase 4 要重來。

**第二次（結果審查）**：防止「假通過」。常見的假通過模式：
- 失敗案例標記為「已知問題」但沒有修復計劃
- 覆蓋率數字是手動填入而非工具產生
- 根本原因分析只說「邏輯錯誤」而非具體代碼位置

### 為什麼 Tester 不能看代碼再設計測試？

這是**確認偏誤**（Confirmation Bias）的防護機制。Developer 寫代碼時有自己的「心智模型」，如果 Tester 看代碼設計測試，就會繼承同樣的心智模型，導致：
- 只測「代碼能做到的」，而不測「需求要求做到的」
- 遺漏代碼完全沒有實作的需求場景

正確做法：Tester 從 SRS.md 出發推導 TC，再執行代碼，讓代碼去符合需求，而不是讓測試去迎合代碼。

### 失敗案例根本原因分析的重要性

模糊的根本原因 = 無法防止再次發生：

```
❌ 差：根本原因「邏輯錯誤」
✅ 好：根本原因「TextProcessor.split() 在處理含有多個連續標點（。！？）
        的輸入時，錯誤地將標點作為分割點，導致輸出陣列長度超過預期。
        問題位於 module.py 第 47 行，需改用 regex 分割。」
```

---

## 6. HOW — 如何執行？（完整 SOP）

### Step 0：前置確認（Agent A）- 實地驗證 ⚠️

```bash
# 【NEW】實地驗證 Phase 3 產出（不只是看 Plan 假設）
echo "=== Phase 3 產出實地驗證 ==="
ls -la 03-development/src/  # 確認代碼存在
ls -la .methodology/sessions_spawn.log  # 確認日誌存在
cat SRS.md | grep "FR-" | wc -l  # 確認 FR 數量

# 若有任何產出不存在，Plan 需更新，不能假設 ✅
if [ ! -d "03-development/src/" ]; then
    echo "❌ Phase 3 代碼不存在，Plan 狀態需更新"
    exit 1
fi

# 確認 Phase 3 完成狀態（非假設）
if ! grep -q "APPROVE" sessions_spawn.log; then
    echo "⚠️ sessions_spawn.log 無 APPROVE 記錄，Phase 3 可能未完成"
fi

# 確認 Phase 3 已完成
python3 quality_gate/phase_artifact_enforcer.py

# 讀取 SRS.md（從需求出發，不看代碼）
cat 01-requirements/SRS.md

# 確認 TRACEABILITY_MATRIX 現狀
cat TRACEABILITY_MATRIX.md
```

### Step 1：Agent A 設計 TEST_PLAN（不看 Phase 3 代碼）

```markdown
設計流程：
1. 逐條閱讀 SRS.md 的 FR 清單
2. 為每條 FR 推導至少 1 個正向 TC
3. 為 P0 優先級 FR 增加邊界 + 負面 TC
4. 為所有 L1-L6 錯誤路徑設計負面 TC
5. 填寫 TC ID 與 SRS ID 對應表
6. 填寫測試環境、工具、Mock 策略
```

### Step 2：第一次 A/B 審查（TEST_PLAN 審查）

```python
from agent_evaluator import AgentEvaluator

evaluator = AgentEvaluator()

# 第一次：計劃審查
plan_result = evaluator.evaluate(
    spec_a=test_plan_draft,         # Agent A 的 TEST_PLAN.md
    spec_b=plan_review_checklist    # Agent B 的審查標準
)

if not plan_result.approved:
    raise Exception(f"TEST_PLAN 未通過審查：{plan_result.rejection_reason}")

print("✅ TEST_PLAN 審查通過，開始執行測試")
```

**Agent B 計劃審查對話模板**：

```markdown
## Phase 4 TEST_PLAN A/B 審查紀錄（第一次）

### 需求追蹤完整性
- [ ] SRS FR 條數：XX 條；TEST_PLAN TC 條數：XX 條
- [ ] 每條 FR 至少有 1 個對應 TC：✅/❌
- [ ] P0 需求有三類測試（正向 + 邊界 + 負面）：✅/❌
- 說明：______

### 測試設計品質
- [ ] TC 從 SRS 推導（非從代碼推導）：✅/❌
- [ ] 負面測試包含關鍵約束（合併字符驗證、格式一致性）：✅/❌
- [ ] 錯誤路徑測試覆蓋 L1-L6：✅/❌
- 說明：______

### 可執行性
- [ ] 每個 TC 預期結果可量化：✅/❌
- [ ] 可自動化執行（無手動確認項）：✅/❌
- [ ] Mock 策略已定義：✅/❌
- 說明：______

### 審查結論
- [ ] ✅ APPROVE — 執行測試
- [ ] ❌ REJECT — 返回 Agent A 修改（原因：______）

Agent B 簽名：______  Session ID：______  日期：______
```

### Step 3：Constitution test_plan 檢查

```bash
# TEST_PLAN 通過 A/B 後，執行 Constitution 檢查
python3 quality_gate/constitution/runner.py --type test_plan
```

### Step 4：Agent A 執行完整測試套件

```bash
# 執行全部測試 + 覆蓋率 + 詳細輸出
pytest tests/ -v \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=html:coverage_report/ \
  --tb=short \
  -o "log_cli=true"

# 輸出必須保存（貼入 DEVELOPMENT_LOG）
# 不能只寫「已通過」
```

**有失敗案例時的處理流程**：

```markdown
## 失敗案例處理 SOP

1. Agent A 記錄失敗 TC ID、錯誤訊息、堆疊追蹤
2. Agent A 分析根本原因（具體到代碼行數）
3. Agent A 通知 Phase 3 Developer 修復
   （注意：Tester 不直接修改代碼，保持角色分離）
4. Developer 修復後，Agent A 重新執行受影響的 TC
5. 確認修復無迴歸後，繼續執行剩餘 TC
6. 在 TEST_RESULTS.md 記錄修復過程
```

### Step 5：第二次 A/B 審查（TEST_RESULTS 審查）

```python
# 第二次：結果審查
results_result = evaluator.evaluate(
    spec_a=test_results,              # Agent A 的 TEST_RESULTS.md
    spec_b=results_review_checklist   # Agent B 的審查標準
)

if not results_result.approved:
    raise Exception(
        f"TEST_RESULTS 未通過審查：{results_result.rejection_reason}"
    )

print("✅ TEST_RESULTS 審查通過")
```

**Agent B 結果審查對話模板**：

```markdown
## Phase 4 TEST_RESULTS A/B 審查紀錄（第二次）

### 結果真實性
- [ ] 所有 TC 有 pytest 實際輸出（非手動填寫）：✅/❌
- [ ] 覆蓋率由工具自動生成：✅/❌
- [ ] 通過率計算正確（通過數/總數）：✅/❌
- 說明：______

### 問題處理完整性
- [ ] 所有失敗案例有具體根本原因（到代碼行數）：✅/❌
- [ ] 所有失敗案例已修復或有明確處置說明：✅/❌
- [ ] 修復後的回歸測試已執行：✅/❌
- 說明：______

### 覆蓋完整性
- [ ] SRS FR 覆蓋率 = 100%：✅/❌
- [ ] 代碼覆蓋率 ≥ 80%：✅/❌（實際：XX%）
- [ ] P0 測試全部 PASS：✅/❌
- 說明：______

### 審查結論
- [ ] ✅ APPROVE — 進入 Quality Gate
- [ ] ❌ REJECT — 補充資料 / 重新執行（原因：______）

Agent B 簽名：______  Session ID：______  日期：______
```

### Step 6：更新 TRACEABILITY_MATRIX.md

```markdown
## TRACEABILITY_MATRIX.md 更新（Phase 4 新增欄位）

| FR ID  | 需求描述 | 實作模組 | 測試案例（Phase 4 填入）| 測試狀態 |
|--------|----------|----------|------------------------|----------|
| FR-01  | 按標點分段 | TextProcessor.split() | TC-001, TC-002, TC-003 | ✅ PASS |
| FR-05  | 多段合併   | AudioMerger.merge()   | TC-004, TC-005         | ✅ PASS |
```

### Step 7：DEVELOPMENT_LOG.md 記錄（正確格式）

```markdown
## Phase 4 Quality Gate 結果（YYYY-MM-DD HH:MM）

### 前置確認
執行命令：python3 quality_gate/phase_artifact_enforcer.py
結果：Phase 3 完成 ✅

### 第一次 A/B 審查（TEST_PLAN 計劃審查）
- Agent A（Tester）：session_id ______
- Agent B（QA Reviewer）：session_id ______
- 審查結論：APPROVE ✅
- 審查日期：______

### Constitution test_plan 檢查
執行命令：python3 quality_gate/constitution/runner.py --type test_plan
結果：
- 正確性: XX%（目標 100%）
- 可維護性: XX%（目標 > 70%）

### 測試執行結果
執行命令：pytest tests/ -v --cov=src --cov-report=term-missing
結果：
- 總測試數：XX
- 通過：XX / 失敗：0
- 代碼覆蓋率：XX%（目標 ≥ 80%）
- SRS FR 覆蓋率：100%（XX/XX 條 FR）

### 失敗案例記錄（若有）
| TC ID | 根本原因 | 修復方式 | 修復狀態 |
|-------|----------|----------|----------|
| TC-XXX | [具體到代碼行] | [具體修改] | 已修復 ✅ |

### 第二次 A/B 審查（TEST_RESULTS 結果審查）
- 審查結論：APPROVE ✅
- 審查日期：______

### ASPICE 文檔檢查
執行命令：python3 quality_gate/doc_checker.py
結果：Compliance Rate: XX%

### Phase 4 結論
- [ ] ✅ 通過，進入 Phase 5
- [ ] ❌ 未通過（原因：______）
```

> ❌ **禁止這樣記錄**：
> ```markdown
> ### Phase 4 Quality Gate
> ✅ 已通過，所有測試通過
> ```

---

## 7. Phase 4 完整清單（最終 Sign-off）

### Agent A 確認

- [ ] 領域知識確認：測試設計前未查看 Phase 3 代碼
- [ ] `TEST_PLAN.md` 完成，每條 SRS FR 有對應 TC
- [ ] P0 需求有三類測試（正向 + 邊界 + 負面）
- [ ] 已提交第一次 A/B 審查（計劃審查）
- [ ] `pytest` 完整執行，有實際輸出
- [ ] 所有失敗案例有根本原因分析（具體到代碼行）
- [ ] `TEST_RESULTS.md` 完成（含失敗修復記錄）
- [ ] 已提交第二次 A/B 審查（結果審查）
- [ ] `TRACEABILITY_MATRIX.md` 已更新（FR → TC 欄位）

### Agent B 確認

- [ ] **第一次審查**：TEST_PLAN 三個維度全部確認（需求追蹤、設計品質、可執行性）
- [ ] **第二次審查**：TEST_RESULTS 三個維度全部確認（真實性、問題處理、覆蓋完整性）
- [ ] SRS FR 覆蓋率確認 = 100%
- [ ] 兩次 AgentEvaluator 評估完成
- [ ] 兩次均給出明確 APPROVE 或 REJECT（含理由）
- [ ] 雙方 Session ID 已記錄

### Quality Gate 確認

- [ ] `constitution/runner.py --type test_plan` 通過（正確性 100%）
- [ ] `pytest` 通過率 = 100%，覆蓋率 ≥ 80%（工具產生，非手填）
- [ ] `doc_checker.py` Compliance Rate > 80%
- [ ] `methodology quality` 無 BLOCK 項目

### 記錄確認

- [ ] 兩次 A/B 審查對話記錄在 `DEVELOPMENT_LOG.md`
- [ ] `pytest` 實際輸出貼入 LOG（非摘要）
- [ ] 失敗案例修復過程有記錄
- [ ] 雙方 session_id 已記錄（可追溯）

---

## 附錄：Phase 3 → Phase 4 知識傳遞

| Phase 3 產出 | Phase 4 使用方式 |
|--------------|----------------|
| 代碼（`03-implementation/src/`）| 測試執行的對象；Tester **不讀**，直接執行 |
| 單元測試（`tests/`）| Phase 4 補充系統測試；回歸測試基礎 |
| 合規矩陣 | 確認測試覆蓋到所有模組 |
| TRACEABILITY_MATRIX（FR → 模組）| Phase 4 新增「測試案例」與「測試狀態」欄位 |
| 邏輯審查對話記錄 | Phase 4 負面測試的設計依據 |

---

## 附錄：快速指令備查

```bash
# ── 前置確認 ────────────────────────────
python3 quality_gate/phase_artifact_enforcer.py

# ── Agent 啟動 ──────────────────────────
# Agent A（測試員）
python -c "from agent_spawner import spawn_with_persona; \
           spawn_with_persona(role='qa', task='Phase 4 測試計劃與執行')"

# Agent B（QA 審查者）
python -c "from agent_spawner import spawn_with_persona; \
           spawn_with_persona(role='reviewer', task='Phase 4 計劃與結果審查')"

# ── 兩次 A/B 評估 ────────────────────────
python -m agent_evaluator --check   # 第一次：計劃審查
python -m agent_evaluator --check   # 第二次：結果審查

# ── 測試執行 ────────────────────────────
pytest tests/ -v --cov=src \
  --cov-report=term-missing \
  --cov-report=html:coverage_report/ \
  --tb=short

# ── Quality Gate ────────────────────────
python3 quality_gate/constitution/runner.py --type test_plan
python3 quality_gate/doc_checker.py
methodology quality
```

---

*整理依據：SKILL.md v5.56 | methodology-v2 Multi-Agent Collaboration Development Methodology*
*格式：5W1H × A/B 協作機制 | 整理日期：2026-03-29*
