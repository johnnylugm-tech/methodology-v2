# Phase 7 計劃：風險管理
## methodology-v2 | 5W1H 框架 × A/B 協作機制

> **版本基準**：SKILL.md v5.56 | 整理日期：2026-03-29
> **前置條件**：Phase 6 全部 Sign-off ✅（QUALITY_REPORT.md 完整版 APPROVE、Constitution ≥ 80%、A/B 監控穩定）

---

## 🗺️ 一覽表

| 5W1H | 核心答案 |
|------|----------|
| **WHO**   | Agent A（Risk Analyst）識別 & 評估風險 × Agent B（PM / Architect）審查風險矩陣與緩解計劃 |
| **WHAT**  | 建立 RISK_ASSESSMENT.md + RISK_REGISTER.md；制定風險緩解措施；確認所有 MEDIUM/HIGH 風險決策 |
| **WHEN**  | Phase 6 品質分析完成後；風險登錄必須 A/B 審查後才能進 Phase 8；A/B 監控持續貫穿 |
| **WHERE** | `07-risk/` 目錄；決策記錄在 `.methodology/decisions/`；Quality Gate 在 `quality_gate/` |
| **WHY**   | Phase 6 品質分析找出了「現有問題」，Phase 7 要預判「未來威脅」——兩者視角互補 |
| **HOW**   | 風險識別 → 量化評估 → 緩解設計 → Decision Gate → A/B 審查 → 演練計劃 → sign-off |

---

## 1. WHO — 誰執行？（A/B 角色分工）

> ⚠️ **Phase 7 核心原則**：風險評估必須保持悲觀視角。Agent A 的任務是「盡可能找出更多風險」，而不是「證明系統安全」。Agent B 的任務是挑戰緩解措施是否真的有效。

### Agent A（Risk Analyst）—— 主責風險識別 & 評估

| 屬性 | 內容 |
|------|------|
| Persona | `qa` 或 `devops` |
| Goal | 系統性識別所有潛在風險，量化風險等級，設計具體緩解措施 |
| 職責 | 撰寫 RISK_ASSESSMENT.md、建立 RISK_REGISTER.md、制定演練計劃、提交風險決策確認 |
| 核心心態 | 「如果這個風險發生，系統會怎樣？有沒有應對計劃？」|
| 輸入來源 | Phase 6 QUALITY_REPORT.md 根源分析 + A/B 監控數據 + RISK_REGISTER 技術風險 |
| 禁止 | 以「機率低」為由跳過 HIGH 影響風險；緩解措施寫「加強注意」等無法量化的文字 |

```python
# Phase 7 Agent A 啟動
from agent_spawner import spawn_with_persona

agent_a = spawn_with_persona(
    role="qa",
    task="系統性識別 Phase 1-6 所有潛在風險，建立 RISK_REGISTER，設計具體緩解措施",
)
```

### Agent B（PM / Architect）—— 主責風險審查 & 決策確認

| 屬性 | 內容 |
|------|------|
| Persona | `pm` 或 `architect` |
| Goal | 確認風險識別無重大遺漏；緩解措施切實可行；所有 MEDIUM/HIGH 風險有決策記錄 |
| 職責 | 審查 RISK_REGISTER 完整性、確認緩解措施有效性、執行 Decision Gate 確認、A/B 評估 |
| 核心問題 | 「這個緩解措施如果失效，有 Plan B 嗎？」「風險關閉條件是否過於寬鬆？」|
| 禁止 | 接受「持續監控」作為唯一緩解措施（無具體觸發動作）；跳過 Decision Gate |

```python
# Phase 7 Agent B 啟動
agent_b = spawn_with_persona(
    role="pm",
    task="審查風險矩陣完整性與緩解措施有效性，確認所有 MEDIUM/HIGH 風險決策",
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

# Phase 7 特別設定：Decision Gate 強制開啟
from methodology.decisions import DecisionGate
gate = DecisionGate(require_medium=True, require_high=True)
# MEDIUM/HIGH 風險決策未確認 → BLOCK
```

---

## 2. WHAT — 做什麼？（Phase 7 交付物）

### 必要交付物（Mandatory）

| 交付物 | 負責方 | 驗證方 | 位置 |
|--------|--------|--------|------|
| `RISK_ASSESSMENT.md` | Agent A | Agent B + Quality Gate | `07-risk/` |
| `RISK_REGISTER.md`（完整版）| Agent A | Agent B | `07-risk/` |
| `.methodology/decisions/` 風險決策記錄 | Agent A + Agent B | Decision Gate | `.methodology/decisions/` |
| `MONITORING_PLAN.md`（Phase 7 更新）| Agent A | Agent B | 專案根目錄 |
| `DEVELOPMENT_LOG.md`（Phase 7 段落）| Agent A | Agent B | 專案根目錄 |

---

### 風險識別來源（五個維度）

Phase 7 的風險識別必須涵蓋以下五個來源，不能只做技術風險：

```markdown
## 風險識別五個維度

### 維度 1：技術風險（來自 Phase 6 QUALITY_REPORT）
- Constitution 低分維度對應的技術債
- Phase 6 根源分析識別出的系統性問題
- A/B 監控期間出現的效能波動

### 維度 2：依賴風險（來自 SAD.md ADR）
- 外部 API / SDK 的版本鎖定與棄用風險
- 第三方服務的 SLA 不達標風險
- 網路依賴的可用性風險

### 維度 3：操作風險（來自 BASELINE.md 效能基線）
- 超出效能基線 10% 的降級場景
- 熔斷器觸發後的恢復時間
- 人工介入（HITL）的響應時間

### 維度 4：商業風險（來自 SRS.md 需求）
- 核心功能不可用的業務衝擊
- 資料完整性風險（資料損毀 / 遺失）
- 合規性風險（ASPICE 要求）

### 維度 5：迭代風險（面向未來版本）
- Phase 6 改進建議實施的風險
- 技術債累積的長期退化風險
- 知識轉移（Agent 更換）的風險
```

---

### RISK_ASSESSMENT.md 完整規格

```markdown
# Risk Assessment - [專案名稱]

## 1. 風險評估概述

| 項目 | 內容 |
|------|------|
| 評估日期 | YYYY-MM-DD |
| 評估版本 | v1.0.0（對應 BASELINE）|
| 評估人 | Agent A（session_id：______）|
| 審查人 | Agent B（session_id：______）|
| 輸入來源 | Phase 6 QUALITY_REPORT + A/B 監控數據 + Phase 1-5 全部文檔 |

## 2. 風險矩陣

> 風險等級 = 機率（H/M/L）× 影響（H/M/L）

| 機率 ↓ / 影響 → | 高（H）| 中（M）| 低（L）|
|----------------|--------|--------|--------|
| 高（H）         | 🔴 極高 | 🔴 高  | 🟡 中  |
| 中（M）         | 🔴 高  | 🟡 中  | 🟢 低  |
| 低（L）         | 🟡 中  | 🟢 低  | 🟢 低  |

## 3. 已識別風險清單（五個維度）

| ID | 維度 | 風險描述 | 機率 | 影響 | 等級 | 緩解措施 | 殘餘風險 |
|----|------|----------|------|------|------|----------|----------|
| R1 | 技術 | 網路中斷導致 API 呼叫失敗 | 中 | 高 | 🔴 高 | Retry 3 次 + Fallback | 🟡 中 |
| R2 | 依賴 | 外部 TTS SDK 版本棄用 | 低 | 高 | 🟡 中 | 版本鎖定 + 替代 SDK 評估 | 🟢 低 |
| R3 | 操作 | 熔斷器觸發後恢復超時 | 低 | 中 | 🟢 低 | 自動恢復 + HITL 通知 | 🟢 低 |
| R4 | 商業 | 核心功能降級影響用戶體驗 | 中 | 高 | 🔴 高 | 降級模式設計 + SLA 定義 | 🟡 中 |
| R5 | 迭代 | Phase 6 改進建議實施引入新缺陷 | 中 | 中 | 🟡 中 | 分批實施 + 回歸測試 | 🟢 低 |

## 4. 技術風險詳述（來自 Phase 6）

| 根源問題（Phase 6 識別）| 對應風險 ID | 風險等級 | 緩解措施 |
|------------------------|-------------|----------|----------|
| Constitution 可維護性偏低 | R-T1 | 🟡 中 | 重構計劃 + 代碼審查強化 |
| 測試覆蓋率邊緣值（82%）| R-T2 | 🟢 低 | P1 改進建議實施 |

## 5. 商業風險詳述

| 風險 | 影響場景 | 業務衝擊 | 緩解方案 | 負責人 |
|------|----------|----------|----------|--------|
| 核心 API 不可用 | 服務中斷 > 5 分鐘 | 用戶無法使用服務 | 降級模式 + 錯誤頁面 | DevOps |

## 6. 改進建議（來自 Phase 6）的風險

| Phase 6 改進建議 | 實施風險 | 風險等級 | 控制方式 |
|-----------------|----------|----------|----------|
| Spec Logic Mapping 強化（P0）| 增加開發時間 | 🟢 低 | 分批納入下個版本 |
| Quality Gate 執行率改善（P1）| 流程變更阻力 | 🟡 中 | 培訓 + 工具輔助 |
```

---

### RISK_REGISTER.md 完整規格

```markdown
# Risk Register - [專案名稱]

## 1. 風險概覽

| 總風險數 | 🔴 高風險 | 🟡 中風險 | 🟢 低風險 | 已關閉 |
|---------|-----------|-----------|-----------|--------|
| XX | X | X | X | X |

## 2. 風險登錄表（完整版）

| ID | 維度 | 風險描述 | 等級 | 機率 | 影響 | 狀態 | 緩解措施 | Plan B | 關閉條件 | 負責人 |
|----|------|----------|------|------|------|------|----------|--------|----------|--------|
| R1 | 技術 | 網路中斷導致失敗 | 🔴 高 | 中 | 高 | Open | Retry 3 次 + Fallback | 手動切換備用端點 | 連續 30 天無觸發 | Dev |
| R2 | 依賴 | SDK 版本棄用 | 🟡 中 | 低 | 高 | Open | 版本鎖定 | 替代 SDK 就緒 | 官方支援期 > 1 年 | DevOps |

## 3. MEDIUM/HIGH 風險應對計劃（Decision Gate 必審項）

### R1：網路中斷導致 API 呼叫失敗（🔴 高）

**觸發條件**：連線失敗超過 30 秒 / 連續 3 次失敗
**應對策略**：
1. 自動 Retry：指數退避，最多 3 次（1s → 2s → 4s）
2. Fallback：切換至備用端點或降級模式
3. Circuit Breaker：5 次失敗後開啟，30 秒後半開測試
4. HITL 通知：熔斷器開啟後立即通知人工

**Plan B（緩解措施失效時）**：手動切換備用服務端點，通知用戶預計恢復時間

**復原時間目標（RTO）**：< 5 分鐘
**演練頻率**：每月一次（模擬網路中斷）

**Decision Gate 記錄**：
- 確認人：Agent B（session_id：______）
- 確認日期：YYYY-MM-DD
- 決策：接受殘餘風險（🟡 中）/ 需進一步緩解

### R4：核心功能降級影響用戶體驗（🔴 高）

**觸發條件**：主流程錯誤率 > 5% 持續 5 分鐘
**應對策略**：
1. 自動切換降級模式（功能受限但可用）
2. 向用戶顯示明確的降級說明頁面
3. SLA：降級模式下響應時間 < 10 秒
4. 通知 PM 和 DevOps

**Plan B**：完全停止服務，返回維護頁面（優於提供錯誤結果）

**RTO**：< 3 分鐘（切換降級模式）
**演練頻率**：每季一次

**Decision Gate 記錄**：
- 確認人：Agent B（session_id：______）
- 確認日期：YYYY-MM-DD
- 決策：接受殘餘風險（🟡 中）

## 4. 風險監控計劃（與 A/B 監控整合）

| 風險 ID | 監控指標 | 監控頻率 | 觸發閾值 | 自動動作 |
|---------|----------|----------|----------|----------|
| R1 | 熔斷器觸發次數 | 持續（實時）| > 0 次 | HITL 通知 |
| R2 | SDK 版本號 | 每週 | 版本升級通知 | 評估相容性 |
| R4 | 錯誤率 | 持續（實時）| > 5% | 自動降級 |

## 5. 風險監控記錄（Phase 7 期間）

| 日期 | 風險 ID | 事件描述 | 處理結果 | 狀態變化 |
|------|---------|----------|----------|----------|
| YYYY-MM-DD | — | 無異常事件 | — | 維持 Open |

## 6. 風險關閉記錄

| 風險 ID | 關閉日期 | 關閉原因 | 關閉確認人 |
|---------|----------|----------|-----------|
| R3 | YYYY-MM-DD | 連續 30 天無觸發，自動恢復機制驗證通過 | Agent B |

## 7. 風險演練計劃

| 風險 ID | 演練場景 | 演練頻率 | 下次演練日期 | 負責人 |
|---------|----------|----------|-------------|--------|
| R1 | 模擬網路中斷 30 秒 | 每月 | YYYY-MM-DD | DevOps |
| R4 | 模擬核心 API 失敗 | 每季 | YYYY-MM-DD | Dev |
```

---

### Decision Gate 記錄格式（.methodology/decisions/）

```markdown
# Decision Record - [風險 ID] - [YYYY-MM-DD]

## 決策摘要

| 項目 | 內容 |
|------|------|
| 風險 ID | R1 |
| 風險等級 | 🔴 HIGH |
| 決策類型 | 接受 / 轉移 / 緩解 / 消除 |
| 決策日期 | YYYY-MM-DD |

## 風險描述
[來自 RISK_REGISTER.md 的完整風險描述]

## 決策理由
[為什麼選擇這個應對策略，而不是其他策略]

## 殘餘風險
- 採取緩解措施後，殘餘風險等級：🟡 中
- 殘餘風險可接受理由：[說明]

## 確認記錄

| 角色 | Agent | Session ID | 日期 | 確認 |
|------|-------|------------|------|------|
| Risk Analyst | Agent A | ______ | YYYY-MM-DD | ✅ 提交 |
| PM / Architect | Agent B | ______ | YYYY-MM-DD | ✅ 確認 |
```

---

### A/B 風險審查清單（Agent B）

**風險識別完整性**
- [ ] 五個識別維度都有風險項目（技術 / 依賴 / 操作 / 商業 / 迭代）
- [ ] Phase 6 QUALITY_REPORT 根源分析對應的風險已全部轉化
- [ ] A/B 監控期間出現的異常事件已轉化為風險項目
- [ ] 無「只有低風險」的過於樂觀識別結果（至少應有 1 個 HIGH）

**緩解措施有效性**
- [ ] 每個 HIGH 風險有具體觸發條件（非「發生時」等模糊描述）
- [ ] 每個 HIGH/MEDIUM 風險有 Plan B（緩解措施失效時的備案）
- [ ] 緩解措施有具體參數（Retry 次數、RTO 時間、閾值等）
- [ ] 無「持續監控」作為唯一緩解措施

**Decision Gate 完整性**
- [ ] 所有 HIGH 風險有 Decision Gate 記錄（`.methodology/decisions/`）
- [ ] 所有 MEDIUM 風險有 Decision Gate 記錄
- [ ] 每筆決策記錄有 Agent B 的 session_id 與日期
- [ ] `check_decisions.py` 執行無未確認決策

**演練計劃可執行性**
- [ ] HIGH 風險有演練頻率（≤ 每月一次）
- [ ] 演練場景具體（「模擬網路中斷 30 秒」而非「測試網路」）
- [ ] 下次演練日期已排定
- [ ] 演練負責角色明確

---

## 3. WHEN — 何時執行？（時序 & 門檻）

### Phase 7 完整時序圖

```
Phase 6 sign-off ✅（QUALITY_REPORT 完整版 APPROVE）
        │
        ▼
[前置確認] phase_artifact_enforcer.py
        │
        ├── ❌ Phase 6 未完成 → 停止
        └── ✅ 通過
                │
                ▼
        [持續] A/B 監控維持（每日執行）
        spec_logic ≥ 90 / 偏差 < 10% / 熔斷 = 0
                │
                ▼ （同時進行）
        [Agent A] 讀取 Phase 6 QUALITY_REPORT
        提取根源問題 → 轉化為技術風險
                │
                ▼
        [Agent A] 五維度風險識別
        技術 / 依賴 / 操作 / 商業 / 迭代
                │
                ▼
        [Agent A] 風險量化（機率 × 影響 → 等級）
        填寫 RISK_ASSESSMENT.md 風險矩陣
                │
                ▼
        [Agent A] 設計緩解措施 + Plan B
        建立 RISK_REGISTER.md 完整版
                │
                ▼
        [Agent A] 提交 Decision Gate 確認請求
        所有 MEDIUM/HIGH 風險 → .methodology/decisions/
                │
                ▼
        [Agent B] Decision Gate 確認
        python3 .methodology/decisions/check_decisions.py
                │
                ├── 有未確認的 MEDIUM/HIGH 風險
                │       └── Agent B 逐一確認 → 記錄決策
                │
                └── 全部確認完成
                        │
                        ▼
                [Agent A → Agent B]
                風險審查 A/B（RISK_REGISTER 完整性）
                HybridWorkflow mode=ON 觸發
                        │
                        ├── ❌ REJECT
                        │       └── Agent A 補充識別 / 強化緩解 → 重新提交
                        │
                        └── ✅ APPROVE
                                │
                                ▼
                        [執行演練計劃（至少 1 個 HIGH 風險）]
                        記錄演練結果 → 確認緩解措施有效
                                │
                                ├── 演練失敗 → 修正緩解措施 → 重新演練
                                └── 演練通過
                                        │
                                        ▼
                                ASPICE + Constitution 最終確認
                                        │
                                        ▼
                                記錄 DEVELOPMENT_LOG.md
                                        │
                                        ▼
                                ✅ Phase 7 完成 → 進入 Phase 8
```

> **Phase 7 獨有流程**：Decision Gate 確認必須在 A/B 審查**之前**完成。
> 原因：A/B 審查時 Agent B 需要確認「所有 MEDIUM/HIGH 風險都已有決策記錄」，
> 若決策尚未確認，審查無法有效執行。

### 進入 Phase 8 的前置條件（全部必須為 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| 五維度風險識別完整 | 每個維度至少 1 個風險項目 | Agent B 確認 |
| HIGH 風險數量 | ≥ 1 個（過少說明識別不完整）| Agent B 主觀判斷 |
| HIGH 風險緩解措施 | 有具體觸發條件 + Plan B + RTO | Agent B 確認 |
| MEDIUM/HIGH Decision Gate | 所有決策已確認 | `check_decisions.py` 無未確認項 |
| 至少 1 個 HIGH 風險演練 | 演練通過，緩解措施有效 | 演練記錄 |
| Agent B APPROVE | AgentEvaluator 輸出 | AgentEvaluator |
| Constitution 總分 | ≥ 80% | Constitution Runner |
| ASPICE 合規率 | > 80% | doc_checker.py |
| A/B 監控全程穩定 | 熔斷 0 次、錯誤率 < 1% | MONITORING_PLAN.md 連續記錄 |

---

## 4. WHERE — 在哪裡執行？（路徑 & 工具位置）

### 文件結構（Phase 7 新增 / 更新）

```
project-root/
├── 01-requirements/           ← Phase 1（只讀）
├── 02-architecture/           ← Phase 2（只讀）
├── 03-implementation/         ← Phase 3（只讀）
├── 04-testing/                ← Phase 4（只讀）
├── 05-verify/                 ← Phase 5（只讀）
├── 06-quality/                ← Phase 6（只讀）
│
├── 07-risk/                   ← Phase 7 主要工作區
│   ├── RISK_ASSESSMENT.md     ← 五維度風險矩陣
│   └── RISK_REGISTER.md       ← 完整風險登錄表（含 Plan B + 演練計劃）
│
├── .methodology/
│   └── decisions/             ← Decision Gate 記錄（MEDIUM/HIGH 風險）
│       ├── check_decisions.py ← 自動檢查是否有未確認決策
│       ├── R1_decision.md     ← 各風險個別決策記錄
│       └── R4_decision.md
│
├── scripts/
│   ├── spec_logic_checker.py  ← A/B 監控（每日）
│   ├── performance_check.py   ← A/B 監控（每日）
│   └── circuit_breaker_check.py ← A/B 監控（每日）
│
├── quality_gate/
│   ├── doc_checker.py
│   ├── constitution/
│   │   └── runner.py          ← Phase 7：≥ 80%
│   └── phase_artifact_enforcer.py
│
├── MONITORING_PLAN.md         ← Phase 7 期間監控記錄
└── DEVELOPMENT_LOG.md         ← Phase 7 段落（含演練記錄）
```

### 工具執行位置

```bash
# ── 前置確認 ────────────────────────────
python3 quality_gate/phase_artifact_enforcer.py

# ── 每日 A/B 監控（全程維持）────────────
python3 scripts/spec_logic_checker.py
python3 scripts/performance_check.py
python3 scripts/circuit_breaker_check.py

# ── Decision Gate 確認 ──────────────────
python3 .methodology/decisions/check_decisions.py
# 預期：所有 MEDIUM/HIGH 決策已確認，0 個未確認

# ── 風險演練執行 ─────────────────────────
# 依各風險演練場景手動執行（見 RISK_REGISTER.md）

# ── Constitution 確認 ────────────────────
python3 quality_gate/constitution/runner.py
# 門檻：≥ 80%

# ── ASPICE 文檔完整性 ────────────────────
python3 quality_gate/doc_checker.py

# ── Framework Enforcement ───────────────
methodology quality

# ── A/B 評估 ────────────────────────────
python -m agent_evaluator --check
```

---

## 5. WHY — 為什麼這樣做？（設計理由）

### Phase 6（品質分析）vs Phase 7（風險管理）：視角互補

| 維度 | Phase 6 | Phase 7 |
|------|---------|---------|
| 時間視角 | 回顧（Phase 1-5 發生了什麼）| 前瞻（未來可能發生什麼）|
| 問題性質 | 已發生的缺陷與根源 | 潛在的威脅與不確定性 |
| 輸出用途 | 改進建議（給下個版本）| 緩解措施（給當前版本運行）|
| 核心工具 | Constitution / Quality Gate | Risk Matrix / Decision Gate |
| Agent 心態 | 「哪裡出問題了？」| 「哪裡可能出問題？」|

Phase 6 告訴我們「昨天的傷疤在哪裡」，Phase 7 告訴我們「明天的地雷在哪裡」。兩者合起來才構成完整的品質保障視野。

### 為什麼 Decision Gate 必須在 A/B 審查前完成？

Decision Gate 的本質是**責任確認**——每個 MEDIUM/HIGH 風險必須有一個具名的 Agent B 確認「我了解這個風險，接受/緩解/轉移的決策是 X」。

如果 A/B 審查前不先做 Decision Gate：
- Agent B 在審查時無法確認「是否所有高風險都有人拍板」
- 決策責任模糊，後續出問題時無法追溯
- `check_decisions.py` 發現未確認決策，審查形同虛設

**正確順序**：
```
Agent A 識別風險 → 提交 Decision Gate → Agent B 逐一確認
→ check_decisions.py 驗證全部確認 → A/B 審查（此時 B 可以確信所有決策有記錄）
```

### 為什麼「持續監控」不能作為唯一緩解措施？

這是最常見的風險管理陷阱：

```
❌ 無效的緩解措施：
R1 網路中斷風險
緩解措施：持續監控網路狀態

問題：「持續監控」只是「發現問題更快」，
      不是「防止問題」或「問題發生後的應對」。
      監控系統告警後，工程師要做什麼？

✅ 有效的緩解措施：
R1 網路中斷風險
緩解措施：
  預防：Retry（指數退避，3 次，1s→2s→4s）
  偵測：持續監控 + 熔斷器（5 次失敗後觸發）
  應對：Fallback 切換備用端點
  升級：熔斷器觸發後 HITL 通知
Plan B：手動切換備用服務，通知用戶預計恢復時間
RTO：< 5 分鐘
```

有效緩解措施包含：預防 + 偵測 + 應對 + 升級，四個層次缺一不可。

### 為什麼 HIGH 風險至少要有 1 個演練？

文字上的緩解措施 ≠ 實際有效的緩解措施。

演練的目的不是「展示系統能用」，而是：
1. **驗證緩解措施有效**：Retry 真的在 1s/2s/4s 後執行了嗎？
2. **量測 RTO 是否達標**：聲稱 < 5 分鐘，實際演練時是多久？
3. **找出未預期的副作用**：熔斷器觸發後，日誌有沒有正確記錄？通知有沒有發出？
4. **建立應對肌肉記憶**：Agent 知道在什麼情況下執行 Plan B

未演練的緩解措施是「理論」，演練過的緩解措施才是「保障」。

### 為什麼需要五個識別維度，不能只做技術風險？

只做技術風險的常見遺漏：

| 遺漏維度 | 典型未被識別的風險 | 後果 |
|----------|-------------------|------|
| 依賴風險 | 外部 SDK 棄用 | 版本升級後系統崩潰 |
| 操作風險 | HITL 響應時間過長 | 熔斷器觸發後遲遲無人處理 |
| 商業風險 | 核心功能降級 SLA 未定義 | 用戶體驗惡化但無法量化責任 |
| 迭代風險 | Phase 6 改進建議實施帶入新缺陷 | 下個版本品質反而下降 |

---

## 6. HOW — 如何執行？（完整 SOP）

### Step 0：前置確認 + 監控維持（Agent A）

```bash
# 確認 Phase 6 已完成
python3 quality_gate/phase_artifact_enforcer.py

# 確認 A/B 監控持續運行
python3 scripts/spec_logic_checker.py
python3 scripts/performance_check.py
python3 scripts/circuit_breaker_check.py

# 讀取 Phase 6 QUALITY_REPORT 根源分析
cat 06-quality/QUALITY_REPORT.md | grep -A 20 "根源"
```

### Step 1：五維度風險識別（Agent A）

```markdown
識別流程：

**維度 1：技術風險**（來源：Phase 6 QUALITY_REPORT.md 第 4 章）
→ 逐條讀取「品質問題根源分析」中的每個問題
→ 轉化格式：「[根源問題] 在 [場景] 下可能導致 [後果]」
→ 例：「Constitution 可維護性偏低（72%）→ 在代碼修改時，
        可能因為高複雜度導致引入意外 bug」

**維度 2：依賴風險**（來源：Phase 2 SAD.md ADR）
→ 逐條讀取技術選型 ADR
→ 識別每個外部依賴的：版本支援期 / SLA / 替代方案成熟度

**維度 3：操作風險**（來源：Phase 5 BASELINE.md 效能基線 + MONITORING_PLAN.md）
→ 以效能基線為基準，識別超標場景的影響
→ 以 HITL 機制為基準，識別人工介入延遲的風險

**維度 4：商業風險**（來源：Phase 1 SRS.md NFR + Phase 5 BASELINE.md）
→ 逐條讀取非功能需求（NFR）
→ 識別每條 NFR 如果不達標，對業務的具體衝擊

**維度 5：迭代風險**（來源：Phase 6 QUALITY_REPORT.md 第 5 章改進建議）
→ 逐條讀取 P0/P1 改進建議
→ 識別每條建議實施時的潛在風險
```

### Step 2：風險量化（Agent A）

```markdown
量化標準：

機率評估：
- 高（H）：在類似系統中常見，或 A/B 監控已有前兆
- 中（M）：在特定條件下可能發生
- 低（L）：在正常操作下極少發生

影響評估：
- 高（H）：導致核心功能不可用 / 資料損毀 / SLA 嚴重違反
- 中（M）：導致功能降級 / 效能顯著下降 / 用戶體驗影響
- 低（L）：導致輕微影響 / 可快速恢復 / 用戶無感知

風險等級 = 機率 × 影響（參照風險矩陣）
```

### Step 3：緩解措施設計（Agent A）

```markdown
緩解措施設計標準（四層）：

1. 預防層（Prevent）
   - 降低風險發生機率的機制
   - 例：Retry、版本鎖定、輸入驗證

2. 偵測層（Detect）
   - 快速發現風險已發生的機制
   - 例：監控告警、熔斷器、錯誤率追蹤

3. 應對層（Respond）
   - 風險發生後的自動處置
   - 例：Fallback、降級模式、自動恢復

4. 升級層（Escalate）
   - 自動處置不足時的人工介入
   - 例：HITL 通知、on-call 流程

Plan B 設計標準：
- 假設緩解措施完全失效的情境下的備案
- 必須是立即可執行的動作（非「研究解決方案」）
- 有明確的 RTO 目標
```

### Step 4：Decision Gate 確認（Agent A 提交，Agent B 確認）

```bash
# Agent A：為每個 MEDIUM/HIGH 風險建立決策記錄
mkdir -p .methodology/decisions/
# 建立 R1_decision.md, R4_decision.md 等

# Agent B：逐一確認每個決策
# 在每個 decision.md 填寫確認資訊

# 驗證全部確認完成
python3 .methodology/decisions/check_decisions.py
# 預期輸出：
# ✅ R1（HIGH）：已確認（Agent B，YYYY-MM-DD）
# ✅ R2（MEDIUM）：已確認（Agent B，YYYY-MM-DD）
# ✅ R4（HIGH）：已確認（Agent B，YYYY-MM-DD）
# 0 個未確認決策
```

### Step 5：A/B 風險審查（Agent A → Agent B）

```python
from agent_evaluator import AgentEvaluator
from hybrid_workflow import HybridWorkflow

workflow = HybridWorkflow(mode="ON")
evaluator = AgentEvaluator()

# 風險審查（Decision Gate 確認後才執行）
risk_result = evaluator.evaluate(
    spec_a=risk_register,          # RISK_REGISTER.md 完整版
    spec_b=risk_review_checklist   # Agent B 的審查標準
)

if not risk_result.approved:
    raise Exception(
        f"風險審查未通過：{risk_result.rejection_reason}"
    )

print(f"✅ 風險審查通過：{risk_result.score}/100")
```

**Agent B 風險審查對話模板**：

```markdown
## Phase 7 風險審查 A/B 紀錄

### 風險識別完整性
- [ ] 五個維度都有風險項目：✅/❌
- [ ] HIGH 風險數量合理（≥ 1 個）：✅/❌（實際：X 個）
- [ ] Phase 6 根源問題已全部轉化為風險：✅/❌
- [ ] A/B 監控異常事件已納入風險：✅/❌
- 說明：______
- 是否有明顯遺漏的風險領域？：______

### 緩解措施有效性
- [ ] HIGH 風險有四層緩解（預防/偵測/應對/升級）：✅/❌
- [ ] 所有 HIGH/MEDIUM 有 Plan B：✅/❌
- [ ] 緩解措施有具體參數（Retry 次數、RTO、閾值）：✅/❌
- [ ] 無「持續監控」作為唯一緩解：✅/❌
- 說明：______

### Decision Gate 完整性
- [ ] `check_decisions.py` 執行結果：0 個未確認：✅/❌
- [ ] 每筆決策有 Agent B session_id 與日期：✅/❌
- [ ] 殘餘風險評估合理（非全部降為「低」）：✅/❌
- 說明：______

### 演練計劃可行性
- [ ] HIGH 風險有演練頻率（≤ 每月）：✅/❌
- [ ] 演練場景具體（有明確的模擬步驟）：✅/❌
- [ ] 下次演練日期已排定：✅/❌
- 說明：______

### 審查結論
- [ ] ✅ APPROVE — 執行演練
- [ ] ❌ REJECT — 補充識別 / 強化緩解（原因：______）

Agent B 簽名：______  Session ID：______  日期：______
```

### Step 6：風險演練執行（至少 1 個 HIGH 風險）

```markdown
演練 SOP（以 R1 網路中斷為例）：

## 演練記錄 - R1 網路中斷（YYYY-MM-DD）

### 演練場景
模擬網路連線中斷 30 秒（使用 iptables 封鎖外部連線）

### 執行步驟
1. 觸發：iptables -A OUTPUT -j DROP（30 秒）
2. 觀察：系統是否在 1s/2s/4s 後執行 Retry
3. 觀察：熔斷器是否在 5 次失敗後觸發
4. 觀察：Fallback 是否切換至備用端點
5. 恢復：iptables -F（移除封鎖）
6. 觀察：系統是否在 30 秒後自動恢復

### 實際結果
- Retry 執行：✅/❌（實際間隔：____ms / ____ms / ____ms）
- 熔斷器觸發：✅/❌（第 X 次失敗後觸發）
- Fallback 切換：✅/❌（切換時間：____ms）
- HITL 通知：✅/❌（通知延遲：____s）
- 自動恢復：✅/❌（恢復時間：____s，目標 < 300s）

### RTO 達成
- 聲明 RTO：< 5 分鐘
- 實際 RTO：____分____秒
- 達成：✅/❌

### 演練結論
- [ ] ✅ 通過——緩解措施有效，RTO 達成
- [ ] ❌ 未通過（原因：______）→ 修正緩解措施 → 重新演練
```

### Step 7：DEVELOPMENT_LOG.md 記錄（正確格式）

```markdown
## Phase 7 Quality Gate 結果（YYYY-MM-DD HH:MM）

### 前置確認
執行命令：python3 quality_gate/phase_artifact_enforcer.py
結果：Phase 6 完成 ✅

### A/B 監控摘要（Phase 7 全程）
監控期間：YYYY-MM-DD 至 YYYY-MM-DD（X 天）
- 邏輯正確性：平均 XX 分，最低 XX 分 ✅
- 回應時間最大偏差：X%（門檻 < 10%）✅
- 熔斷器觸發：0 次 ✅
- 錯誤率最高：X%（門檻 < 1%）✅

### 風險識別摘要
- 總風險數：XX 個
- 🔴 HIGH：X 個 / 🟡 MEDIUM：X 個 / 🟢 LOW：X 個
- 五維度覆蓋：技術 ✅ / 依賴 ✅ / 操作 ✅ / 商業 ✅ / 迭代 ✅

### Decision Gate 確認
執行命令：python3 .methodology/decisions/check_decisions.py
結果：
- 總決策數：XX 個（HIGH：X / MEDIUM：X）
- 已確認：XX 個
- 未確認：0 個 ✅

### A/B 風險審查
- Agent A（Risk Analyst）：session_id ______
- Agent B（PM）：session_id ______
- AgentEvaluator Score：XX/100
- 審查結論：APPROVE ✅
- 審查日期：______

### 風險演練記錄
| 風險 ID | 演練場景 | RTO 目標 | 實際 RTO | 結論 |
|---------|----------|----------|----------|------|
| R1 | 網路中斷 30 秒 | < 5 分鐘 | X 分 X 秒 | ✅ 通過 |

### Constitution 確認
執行命令：python3 quality_gate/constitution/runner.py
結果：總分 XX%（目標 ≥ 80%）✅

### ASPICE 文檔確認
執行命令：python3 quality_gate/doc_checker.py
結果：Compliance Rate: XX%（目標 > 80%）✅

### Framework Enforcement
執行命令：methodology quality
結果：✅ 無 BLOCK 項目

### Phase 7 結論
- [ ] ✅ 通過，RISK_REGISTER.md 建立，所有決策已確認，進入 Phase 8
- [ ] ❌ 未通過（原因：______）
```

---

## 7. Phase 7 完整清單（最終 Sign-off）

### Agent A 確認

- [ ] `phase_artifact_enforcer.py` 通過（Phase 6 完成確認）
- [ ] A/B 監控全程維持（每日記錄在 MONITORING_PLAN.md）
- [ ] 五維度風險識別完成（每個維度 ≥ 1 個風險）
- [ ] Phase 6 QUALITY_REPORT 根源問題已全部轉化為風險
- [ ] 每個 HIGH/MEDIUM 風險有四層緩解措施（非只有監控）
- [ ] 每個 HIGH/MEDIUM 風險有 Plan B 與 RTO
- [ ] `RISK_ASSESSMENT.md` 完成（風險矩陣 + 五維度詳述）
- [ ] `RISK_REGISTER.md` 完成（完整版含演練計劃）
- [ ] 所有 MEDIUM/HIGH 風險決策記錄已提交 `.methodology/decisions/`
- [ ] 已提交 A/B 風險審查
- [ ] 至少 1 個 HIGH 風險演練完成

### Agent B 確認

- [ ] Decision Gate：逐一確認所有 MEDIUM/HIGH 決策（含 session_id 與日期）
- [ ] `check_decisions.py` 結果：0 個未確認
- [ ] 風險審查四個維度確認（識別完整性 + 緩解有效性 + Decision Gate + 演練可行性）
- [ ] 是否有明顯遺漏的風險領域（主觀判斷）
- [ ] 殘餘風險評估合理（非全部過於樂觀降為「低」）
- [ ] AgentEvaluator 評估完成
- [ ] 給出明確 APPROVE 或 REJECT（含理由）
- [ ] Session ID 已記錄

### Quality Gate 確認

- [ ] `check_decisions.py` 0 個未確認決策
- [ ] 至少 1 個 HIGH 風險演練通過（有演練記錄）
- [ ] `constitution/runner.py` 總分 ≥ 80%
- [ ] `doc_checker.py` Compliance Rate > 80%
- [ ] `methodology quality` 無 BLOCK 項目
- [ ] A/B 監控全程穩定（MONITORING_PLAN.md 連續記錄）

### 記錄確認

- [ ] A/B 審查對話完整記錄在 `DEVELOPMENT_LOG.md`
- [ ] Decision Gate 確認記錄在 `.methodology/decisions/`（可追溯）
- [ ] 演練記錄完整（步驟 + 實際結果 + RTO）
- [ ] 雙方 session_id 已記錄

---

## 附錄：Phase 6 → Phase 7 知識傳遞

| Phase 6 產出 | Phase 7 使用方式 |
|--------------|----------------|
| QUALITY_REPORT 第 4 章（根源分析）| 技術風險識別的直接輸入 |
| QUALITY_REPORT 第 5 章（改進建議）| 迭代風險識別的來源 |
| MONITORING_PLAN.md（Phase 6 記錄）| 操作風險識別的數據基礎 |
| Constitution 低分維度詳述 | 技術債風險的具體化 |

## 附錄：Phase 7 在整體架構的位置

```
Phase 6（品質分析）→ Phase 7（風險管理）→ Phase 8（配置管理）
    ↑                      ↑                      ↑
「現有問題」          「未來威脅」             「版本控制」
  回顧視角              前瞻視角               治理視角

Phase 7 的輸出同時服務：
  → Phase 8：風險等級影響配置管理嚴格程度
  → 下個版本的 Phase 1：迭代風險轉化為新版本的需求約束
```

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
# Agent A（Risk Analyst）
python -c "from agent_spawner import spawn_with_persona; \
           spawn_with_persona(role='qa', task='Phase 7 五維度風險識別與緩解設計')"

# Agent B（PM）
python -c "from agent_spawner import spawn_with_persona; \
           spawn_with_persona(role='pm', task='Phase 7 風險審查與 Decision Gate 確認')"

# ── Decision Gate ────────────────────────
python3 .methodology/decisions/check_decisions.py

# ── A/B 評估 ────────────────────────────
python -m agent_evaluator --check

# ── Quality Gate ────────────────────────
python3 quality_gate/constitution/runner.py   # ≥ 80%
python3 quality_gate/doc_checker.py
methodology quality
```

---

*整理依據：SKILL.md v5.56 | methodology-v2 Multi-Agent Collaboration Development Methodology*
*格式：5W1H × A/B 協作機制 | 整理日期：2026-03-29*
