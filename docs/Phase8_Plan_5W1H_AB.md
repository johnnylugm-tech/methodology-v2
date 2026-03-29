# Phase 8 計劃：配置管理
## methodology-v2 | 5W1H 框架 × A/B 協作機制

> **版本基準**：SKILL.md v5.56 | 整理日期：2026-03-29
> **前置條件**：Phase 7 全部 Sign-off ✅（RISK_REGISTER.md APPROVE、所有 MEDIUM/HIGH 決策確認、至少 1 個 HIGH 風險演練通過）

---

## 🗺️ 一覽表

| 5W1H | 核心答案 |
|------|----------|
| **WHO**   | Agent A（DevOps / Config Manager）建立配置記錄 × Agent B（PM / Architect）審查配置完整性與發布清單 |
| **WHAT**  | 完成 CONFIG_RECORDS.md；執行發布清單；封存完整版本；確認 A/B 監控最終穩定報告 |
| **WHEN**  | Phase 7 風險管理完成後；發布清單全部 ✅ 才能正式封版；A/B 監控最終報告作為封版依據 |
| **WHERE** | `08-config/` 目錄；配置記錄在 `CONFIG_RECORDS.md`；發布文件在專案根目錄 |
| **WHY**   | Phase 8 是整個方法論的**治理終點**——確保版本可重現、可審計、可回滾，而不只是「寫完就算完」 |
| **HOW**   | 配置盤點 → CONFIG_RECORDS.md → 發布清單逐項確認 → A/B 最終報告 → A/B 審查 → 封版 → sign-off |

---

## 1. WHO — 誰執行？（A/B 角色分工）

> ⚠️ **Phase 8 原則**：配置管理是「治理行為」，不是「技術行為」。重點不是「系統能跑」，而是「所有配置都有記錄、可被審計、可被重現」。

### Agent A（DevOps / Config Manager）—— 主責配置記錄建立

| 屬性 | 內容 |
|------|------|
| Persona | `devops` |
| Goal | 建立完整、精確、可重現的版本配置記錄，確保任何人拿到記錄都能還原當前環境 |
| 職責 | 完成 CONFIG_RECORDS.md、執行發布清單、編製 A/B 監控最終報告、封版前確認所有 Phase 產出完整 |
| 核心心態 | 「六個月後的工程師能不能憑這份記錄完整還原這個版本？」|
| 禁止 | 使用「最新版」、「當前版」等模糊版本描述；省略任何依賴套件的版本號；在 A/B 監控異常未解除前封版 |

```python
# Phase 8 Agent A 啟動
from agent_spawner import spawn_with_persona

agent_a = spawn_with_persona(
    role="devops",
    task="建立 CONFIG_RECORDS.md，執行發布清單，完成版本封存",
)
```

### Agent B（PM / Architect）—— 主責配置審查與發布確認

| 屬性 | 內容 |
|------|------|
| Persona | `pm` 或 `architect` |
| Goal | 確認版本配置完整可重現；發布清單無遺漏；A/B 監控最終狀態健康 |
| 職責 | 審查 CONFIG_RECORDS.md 完整性、逐項確認發布清單、審查 A/B 監控最終報告、A/B 評估 |
| 核心問題 | 「這份配置記錄六個月後還能用來還原環境嗎？」「發布清單有沒有跳過任何步驟？」|
| 禁止 | 在 A/B 監控最終報告顯示異常時 APPROVE 封版；接受「版本號待定」等未完成狀態 |

```python
# Phase 8 Agent B 啟動
agent_b = spawn_with_persona(
    role="pm",
    task="審查配置完整性，確認發布清單無遺漏，確認 A/B 監控最終穩定",
)
```

### A/B 協作啟動

```python
from methodology import quick_start
from hybrid_workflow import HybridWorkflow
from agent_evaluator import AgentEvaluator

team = quick_start("full")              # Architect + Dev + Reviewer + Tester
workflow = HybridWorkflow(mode="ON")    # 強制 A/B 審查（最終版本）
evaluator = AgentEvaluator()

# Phase 8 最終確認：整個方法論的最後一道 A/B
print("Phase 8 是方法論的最後一個 Phase，A/B 審查代表完整方法論閉環")
team.list_agents()  # 確認 ≥ 2 個 Agent
```

---

## 2. WHAT — 做什麼？（Phase 8 交付物）

### 必要交付物（Mandatory）

| 交付物 | 負責方 | 驗證方 | 位置 |
|--------|--------|--------|------|
| `CONFIG_RECORDS.md`（完整版）| Agent A | Agent B + Quality Gate | `08-config/` |
| 發布清單（Checklist）確認記錄 | Agent A + Agent B | 雙方逐項確認 | `DEVELOPMENT_LOG.md` |
| A/B 監控最終報告 | Agent A | Agent B | `MONITORING_PLAN.md`（最終段落）|
| 版本封存記錄（Git Tag / Release）| Agent A | Agent B | Git / CHANGELOG |
| `DEVELOPMENT_LOG.md`（Phase 8 段落）| Agent A | Agent B | 專案根目錄 |

---

### CONFIG_RECORDS.md 完整規格

```markdown
# Configuration Records - [專案名稱]

## 1. 版本資訊

| 元件 | 版本號 | 發布日期 | Git Commit | 備註 |
|------|--------|----------|------------|------|
| 核心系統 | v1.0.0 | YYYY-MM-DD | abc1234 | 初始發布 |
| API Gateway | v2.3.1 | YYYY-MM-DD | def5678 | 與 v1.0.0 同期 |

> ⚠️ 版本號必須精確（「最新版」不合格）；Git Commit Hash 必須填寫。

## 2. 執行環境配置

### 開發環境

| 項目 | 版本 / 規格 | 備註 |
|------|------------|------|
| OS | Ubuntu 24.04 LTS | |
| Python | 3.11.8 | 精確到 patch 版本 |
| Node.js | 20.11.0 LTS | |
| Docker | 25.0.3 | |

### 生產環境

| 項目 | 版本 / 規格 | 備註 |
|------|------------|------|
| OS | Ubuntu 24.04 LTS | |
| Python | 3.11.8 | 必須與開發環境一致 |
| 記憶體 | 8 GB | 最低需求 |
| CPU | 4 核心 | 最低需求 |
| 儲存空間 | 50 GB SSD | |

## 3. 依賴套件清單（完整版）

### Python 依賴（requirements.txt 快照）

```
# 生成命令：pip freeze > requirements_snapshot.txt
# 生成日期：YYYY-MM-DD
# Python 版本：3.11.8

requests==2.31.0
pytest==8.0.0
pytest-cov==4.1.0
# [完整列表，無省略]
```

### Node.js 依賴（package-lock.json 快照）

```json
{
  "name": "project-name",
  "version": "1.0.0",
  "lockfileVersion": 3,
  "dependencies": {
    "docx": {
      "version": "8.2.2",
      "resolved": "https://registry.npmjs.org/..."
    }
  }
}
```

## 4. 環境變數與配置

| 變數名稱 | 類型 | 預設值 / 範例 | 必填 | 說明 |
|----------|------|--------------|------|------|
| `API_ENDPOINT` | string | `https://api.example.com` | ✅ | 外部 API 端點 |
| `RETRY_COUNT` | int | `3` | ✅ | Retry 次數（對應 R1 風險緩解）|
| `CIRCUIT_BREAKER_THRESHOLD` | int | `5` | ✅ | 熔斷器觸發閾值 |
| `LOG_LEVEL` | string | `INFO` | ❌ | 日誌等級 |
| `SECRET_KEY` | secret | — | ✅ | 見金鑰管理 SOP |

> 🔐 **金鑰管理原則**：secret 類型的變數不記錄值，只記錄名稱與取得方式。

## 5. 部署記錄

| 日期 | 版本 | 部署環境 | 部署方式 | 執行人 | 變更內容摘要 |
|------|------|----------|----------|--------|-------------|
| YYYY-MM-DD | v1.0.0 | Production | Docker Compose | Agent A | 初始發布 |

## 6. 配置變更記錄（Change Log）

| 日期 | 變更項目 | 原值 | 新值 | 變更原因 | 審核人 |
|------|----------|------|------|----------|--------|
| YYYY-MM-DD | RETRY_COUNT | 2 | 3 | R1 風險緩解演練後調整 | Agent B |

## 7. 回滾 SOP

### 觸發條件

| 條件 | 閾值 |
|------|------|
| 錯誤率突增 | > 5%（持續 5 分鐘）|
| 熔斷器觸發 | 任何一次觸發 |
| A/B 邏輯分數下降 | < 85 分（預警）/ < 80 分（立即回滾）|

### 回滾步驟

```bash
# 1. 確認回滾目標版本
git log --oneline -5  # 選擇上一個穩定版本

# 2. 執行回滾
git checkout [previous_stable_tag]
docker-compose down && docker-compose up -d

# 3. 驗證回滾成功
python3 scripts/spec_logic_checker.py  # 確認 ≥ 90 分
python3 scripts/circuit_breaker_check.py  # 確認 0 觸發

# 4. 通知相關人員
# 5. 記錄回滾原因到 CONFIG_RECORDS.md 部署記錄
```

### 回滾後必做事項

- [ ] 在 CONFIG_RECORDS.md 記錄回滾原因與日期
- [ ] 更新 RISK_REGISTER.md（觸發了哪個風險）
- [ ] 啟動根本原因分析（回到 Phase 3 或 Phase 4）
- [ ] 通知 PM（Agent B）確認回滾決策

## 8. 配置合規性確認

| 配置項 | 對應規範 | 合規狀態 |
|--------|----------|----------|
| Retry 次數 = 3 | R1 緩解措施（Phase 7）| ✅ 符合 |
| 熔斷器閾值 = 5 | R1 緩解措施（Phase 7）| ✅ 符合 |
| Python 版本精確指定 | ASPICE 配置管理要求 | ✅ 符合 |
| 金鑰不記錄於文檔 | 安全性要求（Constitution）| ✅ 符合 |
```

---

### 發布清單（Release Checklist）完整規格

> **執行規則**：Agent A 逐項執行，Agent B 逐項確認；任何 ❌ 阻止封版。

```markdown
# Release Checklist - v[版本號] - [YYYY-MM-DD]

## 一、版本準備

- [ ] 版本號已更新（`__version__`, `package.json`, `pyproject.toml`）
- [ ] `CHANGELOG.md` 已記錄本版本所有變更
- [ ] `README.md` 已同步最新功能說明
- [ ] `docs/` 目錄文檔已同步

## 二、文檔完整性（Phase 1-8 全部完成）

- [ ] `SRS.md`（Phase 1）存在且完整
- [ ] `SAD.md`（Phase 2）存在且完整
- [ ] `TEST_PLAN.md`（Phase 4）存在且完整
- [ ] `TEST_RESULTS.md`（Phase 4）存在且通過率 100%
- [ ] `QUALITY_REPORT.md`（Phase 6）存在且完整版
- [ ] `RISK_ASSESSMENT.md`（Phase 7）存在且完整
- [ ] `RISK_REGISTER.md`（Phase 7）存在，所有 HIGH 決策已確認
- [ ] `CONFIG_RECORDS.md`（Phase 8）存在且完整
- [ ] `BASELINE.md`（Phase 5）存在且已雙方簽收
- [ ] `TRACEABILITY_MATRIX.md` 存在且四欄完整（FR→設計→代碼→測試）

## 三、品質確認

- [ ] 測試通過率 = 100%（`pytest` 最後執行輸出）
- [ ] 代碼覆蓋率 ≥ 80%（`pytest-cov` 輸出）
- [ ] Constitution 總分 ≥ 80%（`constitution/runner.py` 輸出）
- [ ] ASPICE 合規率 > 80%（`doc_checker.py` 輸出）
- [ ] 邏輯正確性 ≥ 90 分（`spec_logic_checker.py` 輸出）

## 四、A/B 監控最終狀態

- [ ] 邏輯分數最近 7 天平均 ≥ 90 分
- [ ] 回應時間偏差最近 7 天 < 10%
- [ ] 熔斷器觸發次數（Phase 5 至今）= 0 次
- [ ] 錯誤率最近 7 天 < 1%

## 五、風險管理確認

- [ ] `check_decisions.py` 執行結果：0 個未確認決策
- [ ] 所有 HIGH 風險有演練記錄
- [ ] 回滾 SOP 已寫入 `CONFIG_RECORDS.md`
- [ ] 回滾觸發條件已明確定義

## 六、配置管理確認

- [ ] 所有依賴版本精確記錄（無「最新版」模糊描述）
- [ ] 開發環境 = 生產環境（版本一致）
- [ ] 環境變數清單完整（secret 類型只記名稱）
- [ ] Git Tag 已建立（`v[版本號]`）
- [ ] Git Release Notes 已建立

## 七、封版確認

- [ ] Agent A 確認：所有項目已逐一執行 ✅
- [ ] Agent B 確認：所有項目已逐一審查 ✅
- [ ] 封版決策：APPROVE 正式發布

Agent A：______（session_id：______）日期：______
Agent B：______（session_id：______）日期：______
```

---

### A/B 監控最終報告規格

```markdown
# A/B 監控最終報告 - [專案名稱] v[版本號]

## 監控期間概覽

| 項目 | 內容 |
|------|------|
| 監控起始日 | Phase 5 啟動日（YYYY-MM-DD）|
| 監控截止日 | Phase 8 封版日（YYYY-MM-DD）|
| 總監控天數 | XX 天 |

## 各監控指標最終統計

| 指標 | 閾值 | 最低值 | 最高值 | 平均值 | 達標天數 | 未達標天數 | 最終狀態 |
|------|------|--------|--------|--------|----------|-----------|----------|
| 邏輯正確性分數 | ≥ 90 | XX | XX | XX | XX | 0 | ✅ |
| 回應時間偏差 | < 10% | X% | X% | X% | XX | 0 | ✅ |
| 熔斷器觸發 | 0 次 | — | — | — | XX | 0 | ✅ |
| 錯誤率 | < 1% | X% | X% | X% | XX | 0 | ✅ |

## 異常事件記錄（Phase 5 至今）

| 日期 | 指標 | 異常描述 | 處置方式 | 結果 |
|------|------|----------|----------|------|
| （無異常）| — | — | — | — |

## 閾值調整記錄

| 調整日期 | 調整項目 | 原閾值 | 新閾值 | 調整原因 | Agent B 確認 |
|----------|----------|--------|--------|----------|-------------|
| — | — | — | — | — | — |

## 最終結論

| 項目 | 結論 |
|------|------|
| 整體監控穩定性 | ✅ 穩定（熔斷 0 次，錯誤率 < 1%）|
| 效能基線維持 | ✅ 回應時間偏差全程 < 10% |
| 邏輯正確性維持 | ✅ 全程 ≥ 90 分 |
| 可封版 | ✅ / ❌ |
```

---

### A/B 配置審查清單（Agent B）

**CONFIG_RECORDS 完整性**
- [ ] 所有元件版本號精確（有 Git Commit Hash）
- [ ] 依賴套件清單完整（有 `pip freeze` 或 `npm lock` 快照）
- [ ] 開發環境與生產環境版本一致（無版本漂移）
- [ ] 環境變數清單完整（secret 類型正確處理）
- [ ] 回滾 SOP 具體可執行（有命令列步驟）

**發布清單完整性**
- [ ] 七個區塊全部逐項確認（無跳過）
- [ ] Phase 1-8 文檔完整性逐一確認
- [ ] 品質指標全部有工具輸出支撐（非手填數字）
- [ ] A/B 監控最終 7 天狀態健康

**版本治理合規**
- [ ] Git Tag 已建立，格式正確（`v[Major.Minor.Patch]`）
- [ ] CHANGELOG.md 有本版本記錄
- [ ] 配置變更記錄完整（Phase 5 至今的所有配置調整）
- [ ] 配置合規性確認對應 Phase 7 風險緩解措施

**A/B 監控最終報告**
- [ ] 監控期間完整（Phase 5 至 Phase 8，無空白）
- [ ] 熔斷器觸發總計 = 0 次
- [ ] 邏輯正確性最近 7 天平均 ≥ 90 分
- [ ] 無未解決的異常事件

---

## 3. WHEN — 何時執行？（時序 & 門檻）

### Phase 8 完整時序圖

```
Phase 7 sign-off ✅（RISK_REGISTER APPROVE、Decision Gate 全部確認）
        │
        ▼
[前置確認] phase_artifact_enforcer.py
        │
        ├── ❌ Phase 7 未完成 → 停止
        └── ✅ 通過
                │
                ▼
        [確認] A/B 監控最近 7 天狀態
        全部健康才開始 Phase 8 主流程
                │
                ├── 有監控異常 → 診斷 → 修復 → 監控穩定 7 天後再繼續
                └── 健康 ✅
                        │
                        ▼
                [Agent A] 配置盤點
                所有環境的版本號、依賴套件、環境變數逐一記錄
                        │
                        ▼
                [Agent A] 完成 CONFIG_RECORDS.md
                回滾 SOP + 配置合規性確認
                        │
                        ▼
                [Agent A] 執行發布清單
                七個區塊逐項執行（非確認，是執行）
                        │
                        ├── 有 ❌ 項目
                        │       └── 修正後重新執行該項目
                        │
                        └── 全部 ✅
                                │
                                ▼
                        [Agent A] 編製 A/B 監控最終報告
                        Phase 5 至今全程統計
                                │
                                ▼
                        [Agent A → Agent B]
                        CONFIG_RECORDS + 發布清單 + 監控報告
                        A/B 審查（最終封版審查）
                        HybridWorkflow mode=ON 觸發
                                │
                                ├── ❌ REJECT
                                │       └── Agent A 修正 → 重新提交
                                │
                                └── ✅ APPROVE
                                        │
                                        ▼
                                [Agent A] 建立 Git Tag + Release
                                git tag v1.0.0 && git push --tags
                                        │
                                        ▼
                                Final Quality Gate
                                ASPICE + Constitution + Framework
                                        │
                                        ├── 有 BLOCK → 解決 → 重新執行
                                        └── 全部通過
                                                │
                                                ▼
                                        記錄 DEVELOPMENT_LOG.md
                                        （Phase 8 完整段落 + 方法論閉環記錄）
                                                │
                                                ▼
                                        ✅ Phase 8 完成
                                        ✅ 方法論完整閉環
```

> **Phase 8 的「7 天監控健康」前置條件**是整個方法論中唯一基於時間維度的前置條件。
> 其他 Phase 只需「執行完成」，Phase 8 需要「持續穩定」。

### 封版的前置條件（全部必須為 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| A/B 監控最近 7 天邏輯分數 | 平均 ≥ 90 分 | MONITORING_PLAN.md 連續記錄 |
| A/B 監控最近 7 天回應時間 | 偏差 < 10% | MONITORING_PLAN.md |
| A/B 監控熔斷器（Phase 5 至今）| = 0 次觸發 | MONITORING_PLAN.md |
| A/B 監控最近 7 天錯誤率 | < 1% | MONITORING_PLAN.md |
| 發布清單七個區塊 | 全部 ✅（無任何 ❌）| 雙方逐項確認 |
| CONFIG_RECORDS.md 完整 | 版本精確 + 依賴快照 + 回滾 SOP | Agent B 審查 |
| Phase 1-8 文檔完整 | `doc_checker.py` > 80% | doc_checker.py |
| Constitution 最終總分 | ≥ 80% | Constitution Runner |
| TRACEABILITY_MATRIX 四欄完整 | FR→設計→代碼→測試 全填 | Agent B 確認 |
| Git Tag 建立 | `v[Major.Minor.Patch]` 格式 | git log --tags |
| Agent B APPROVE | AgentEvaluator 輸出 | AgentEvaluator |
| Framework Enforcement | 無 BLOCK | methodology quality |

---

## 4. WHERE — 在哪裡執行？（路徑 & 工具位置）

### 文件結構（Phase 8 新增 / 完整版）

```
project-root/
├── 01-requirements/              ← Phase 1（封存）
├── 02-architecture/              ← Phase 2（封存）
├── 03-implementation/            ← Phase 3（封存）
├── 04-testing/                   ← Phase 4（封存）
├── 05-verify/                    ← Phase 5（封存）
├── 06-quality/                   ← Phase 6（封存）
├── 07-risk/                      ← Phase 7（封存）
│
├── 08-config/                    ← Phase 8 主要工作區
│   └── CONFIG_RECORDS.md         ← 完整配置記錄（版本+環境+依賴+回滾）
│
├── CHANGELOG.md                  ← 版本變更記錄（發布清單必要項）
├── TRACEABILITY_MATRIX.md        ← 完整四欄矩陣（FR→設計→代碼→測試）
├── SPEC_TRACKING.md              ← 規格追蹤（Framework Enforcement 必要）
├── MONITORING_PLAN.md            ← 最終報告（Phase 5 至 Phase 8 完整記錄）
│
├── quality_gate/
│   ├── doc_checker.py            ← 最終 ASPICE 確認
│   ├── constitution/
│   │   └── runner.py             ← 最終 Constitution（≥ 80%）
│   └── phase_artifact_enforcer.py
│
├── .methodology/
│   └── decisions/
│       └── check_decisions.py    ← 最終確認（0 個未確認）
│
└── DEVELOPMENT_LOG.md            ← Phase 8 完整段落 + 方法論閉環記錄
```

### 工具執行位置

```bash
# ── 前置確認 ────────────────────────────
python3 quality_gate/phase_artifact_enforcer.py

# ── A/B 監控最終 7 天確認 ────────────────
python3 scripts/spec_logic_checker.py
python3 scripts/performance_check.py
python3 scripts/circuit_breaker_check.py

# ── 配置盤點輔助 ─────────────────────────
pip freeze > 08-config/requirements_snapshot.txt
cat package-lock.json > 08-config/npm_lock_snapshot.json

# ── Decision Gate 最終確認 ──────────────
python3 .methodology/decisions/check_decisions.py
# 預期：0 個未確認決策

# ── Spec Tracking 最終確認 ──────────────
python3 cli.py spec-track check
python3 cli.py spec-track report

# ── Final Quality Gate ───────────────────
python3 quality_gate/doc_checker.py
python3 quality_gate/constitution/runner.py   # ≥ 80%
methodology quality                            # 無 BLOCK

# ── A/B 評估 ────────────────────────────
python -m agent_evaluator --check

# ── 版本封存 ─────────────────────────────
git tag -a v1.0.0 -m "Release v1.0.0 - Phase 8 完成"
git push origin v1.0.0
# （可選）ClawHub 發布
```

---

## 5. WHY — 為什麼這樣做？（設計理由）

### Phase 8 的本質：從「完成」到「治理」

Phase 1-7 解決的是「把對的事情做好」；Phase 8 解決的是「確保做好的事情被記錄下來，可以被審計、重現、回滾」。

```
開發完成（Phase 3）≠ 測試通過（Phase 4）≠ 驗收交付（Phase 5）
≠ 品質分析（Phase 6）≠ 風險管理（Phase 7）≠ 配置治理（Phase 8）

每個等號的轉化都需要新的視角與工具
Phase 8 的視角是：「治理性」而非「技術性」
```

### 為什麼版本號必須精確到 patch，不能寫「最新版」？

```
❌ 不合格的配置記錄：
Python: 最新版
requests: latest
Node.js: v20.x

六個月後工程師執行安裝：
- Python 3.11.8 → Python 3.11.12（有 breaking change）
- requests latest → 2.32.0（API 有差異）
結果：環境無法還原，系統行為不可重現
```

```
✅ 合格的配置記錄：
Python: 3.11.8（精確 patch 版本）
requests: 2.31.0（來自 pip freeze 輸出）
Node.js: 20.11.0 LTS（精確版本號）

六個月後執行：pip install -r requirements_snapshot.txt
結果：環境完全還原，行為一致
```

配置管理的核心承諾是**可重現性（Reproducibility）**。模糊的版本號讓這個承諾成為謊言。

### 為什麼回滾 SOP 必須在 Phase 8 確立（而不是 Phase 7）？

Phase 7 定義了「什麼情況下需要回滾」（觸發條件），Phase 8 定義「怎麼回滾」（具體命令）。

這個分工的邏輯是：Phase 7 完成時，Git Tag 還不存在，無法寫出具體的 `git checkout [tag]` 命令。Phase 8 建立 Tag 後，才有完整的回滾目標，SOP 才能具體可執行。

### 為什麼需要「7 天監控健康」才能封版？

單日的監控數據可能是偶然穩定，7 天的連續穩定才代表系統在各種日常負載模式下都能正常運行。

7 天的設計參考：
- 涵蓋一個完整的工作週（週一到週日的負載模式不同）
- 足以觀察到任何週期性的效能波動
- 在發現問題後有足夠時間修復並重新穩定

### 為什麼發布清單要七個區塊，且要「執行」而非「確認」？

大多數發布清單的失效原因是：「我以為已經做了，但其實沒做」。

Phase 8 發布清單的設計原則：
- Agent A 是「執行者」——每個項目都要親自執行，而不是回想是否做了
- Agent B 是「見證者」——逐項看著 Agent A 執行，而不是事後審查結果
- 任何 ❌ 阻止封版——不因為「只差一個項目」而妥協

七個區塊的設計覆蓋了不同性質的發布前確認：版本準備、文檔完整性、品質確認、監控狀態、風險管理、配置管理、封版決策。少任何一個都會在未來埋下不可見的地雷。

### Phase 8 是方法論的閉環終點

```
Phase 1（需求）→ ... → Phase 8（配置）= 完整一個版本週期

Phase 8 完成後，TRACEABILITY_MATRIX 四欄全滿：
FR → 實作模組 → 實作函數 → 測試案例

這條矩陣代表：
每一個需求都有對應的設計、代碼、測試和配置記錄
沒有任何需求是「只在文字上」的
```

---

## 6. HOW — 如何執行？（完整 SOP）

### Step 0：前置確認 + 7 天監控檢查（Agent A）

```bash
# 確認 Phase 7 已完成
python3 quality_gate/phase_artifact_enforcer.py

# 確認最近 7 天 A/B 監控健康
# 讀取 MONITORING_PLAN.md 最近 7 天記錄
tail -20 MONITORING_PLAN.md

# 確認 Decision Gate 全部確認
python3 .methodology/decisions/check_decisions.py
# 預期：0 個未確認

# 若有監控異常：停止 Phase 8，診斷修復，穩定 7 天後重新開始
```

### Step 1：配置盤點（Agent A）

```bash
# Python 依賴快照（必須在生產環境執行）
pip freeze > 08-config/requirements_snapshot.txt

# Node.js 依賴快照
cp package-lock.json 08-config/npm_lock_snapshot.json

# 環境資訊收集
python3 --version       # 精確版本
node --version          # 精確版本
docker --version        # 精確版本
uname -r               # OS 版本

# 環境變數清單（不記錄 secret 值）
env | grep -E "^(API_|RETRY_|CIRCUIT_|LOG_)" | sort
```

### Step 2：完成 CONFIG_RECORDS.md（Agent A）

```markdown
填寫順序：
1. 版本資訊（元件 + Git Commit Hash）
2. 執行環境配置（開發環境 + 生產環境對比）
3. 依賴套件清單（貼上 pip freeze 輸出）
4. 環境變數清單（secret 類型只記名稱與取得方式）
5. 部署記錄（日期 + 版本 + 方式 + 執行人）
6. 配置變更記錄（Phase 5 至今所有配置調整）
7. 回滾 SOP（觸發條件 + 命令列步驟 + 後續必做）
8. 配置合規性確認（對應 Phase 7 風險緩解措施）
```

### Step 3：執行發布清單（Agent A 執行，Agent B 見證）

```markdown
執行原則：
- 每個項目：Agent A 執行 → 貼出實際輸出 → Agent B 確認
- 不允許「記得之前做過了」——必須當場執行
- 品質確認項目必須貼出工具輸出（非手填數字）
- 任何 ❌ 立即停止後續項目，修正後重新執行該項目
```

**品質確認項目執行方式**：

```bash
# 測試通過率（必須執行，不能引用 Phase 4 的舊數據）
pytest tests/ -v --tb=short 2>&1 | tail -5
# 輸出：XX passed, 0 failed

# 代碼覆蓋率
pytest tests/ --cov=src --cov-report=term-missing 2>&1 | grep TOTAL
# 輸出：TOTAL    XX%

# Constitution 最終確認
python3 quality_gate/constitution/runner.py 2>&1 | tail -10

# ASPICE 合規率
python3 quality_gate/doc_checker.py 2>&1 | grep "Compliance"

# 邏輯正確性
python3 scripts/spec_logic_checker.py 2>&1 | grep "分數"
```

### Step 4：編製 A/B 監控最終報告（Agent A）

```markdown
報告編製步驟：
1. 讀取 MONITORING_PLAN.md 的完整監控記錄（Phase 5 至今）
2. 計算每個指標的：最低值 / 最高值 / 平均值 / 達標天數
3. 整理異常事件（若有）的處置記錄
4. 整理閾值調整記錄（若有）
5. 撰寫最終結論（可封版 / 不可封版 + 理由）
```

### Step 5：A/B 最終封版審查（Agent A → Agent B）

```python
from agent_evaluator import AgentEvaluator
from hybrid_workflow import HybridWorkflow

workflow = HybridWorkflow(mode="ON")
evaluator = AgentEvaluator()

# 最終封版審查（方法論最後一次 A/B）
final_result = evaluator.evaluate(
    spec_a={
        "config_records": config_records,      # CONFIG_RECORDS.md
        "release_checklist": checklist_result, # 發布清單執行記錄
        "monitoring_report": monitoring_final, # A/B 監控最終報告
    },
    spec_b=final_release_checklist   # Agent B 的封版審查標準
)

if not final_result.approved:
    raise Exception(
        f"最終封版審查未通過：{final_result.rejection_reason}"
    )

print(f"✅ 最終封版審查通過：{final_result.score}/100")
print("🎉 方法論完整閉環達成")
```

**Agent B 最終封版審查對話模板**：

```markdown
## Phase 8 最終封版 A/B 審查紀錄

### CONFIG_RECORDS 完整性
- [ ] 所有元件版本精確（有 Git Commit Hash）：✅/❌
- [ ] 依賴快照完整（pip freeze / npm lock 輸出）：✅/❌
- [ ] 開發 vs 生產環境版本一致：✅/❌
- [ ] 回滾 SOP 具體可執行（有命令列）：✅/❌
- [ ] 配置合規性對應 Phase 7 緩解措施：✅/❌
- 說明：______

### 發布清單執行記錄
- [ ] 七個區塊全部 ✅（無任何 ❌）：✅/❌
- [ ] Phase 1-8 文檔完整性逐一確認：✅/❌
- [ ] 品質指標有工具輸出（非手填）：✅/❌
- [ ] TRACEABILITY_MATRIX 四欄完整：✅/❌
- 說明：______

### A/B 監控最終報告
- [ ] 監控期間完整（Phase 5 至今無空白）：✅/❌
- [ ] 最近 7 天邏輯分數平均 ≥ 90 分：✅/❌（實際：XX 分）
- [ ] 熔斷器總觸發 = 0 次：✅/❌
- [ ] 錯誤率最近 7 天 < 1%：✅/❌
- [ ] 無未解決的異常事件：✅/❌
- 說明：______

### 版本治理合規
- [ ] Git Tag 已建立格式正確：✅/❌
- [ ] CHANGELOG.md 有本版本記錄：✅/❌
- [ ] Decision Gate 最終 0 個未確認：✅/❌
- 說明：______

### 方法論閉環確認
- [ ] Phase 1-8 全部 sign-off（DEVELOPMENT_LOG 有記錄）：✅/❌
- [ ] TRACEABILITY_MATRIX 從 FR 到測試案例縱向完整：✅/❌
- [ ] 所有 A/B 審查記錄可追溯（session_id 完整）：✅/❌
- 說明：______

### 封版決策
- [ ] ✅ APPROVE — 正式封版，v[版本號] 發布
- [ ] ❌ REJECT — 修正後重新審查（原因：______）

Agent A：______（session_id：______）日期：______
Agent B：______（session_id：______）日期：______
```

### Step 6：版本封存（A/B 審查通過後）

```bash
# 建立 Git Tag
git tag -a v1.0.0 -m "Release v1.0.0
Phase 8 配置管理完成
方法論版本：methodology-v2 v5.56
Agent A：[session_id]
Agent B：[session_id]
封版日期：YYYY-MM-DD"

git push origin v1.0.0

# 更新 CHANGELOG.md
cat >> CHANGELOG.md << 'EOF'
## [1.0.0] - YYYY-MM-DD
### 新增
- 初始版本發布
- Phase 1-8 完整方法論執行
- BASELINE v1.0.0 建立

### 方法論指標
- Constitution 總分：XX%
- 測試覆蓋率：XX%
- 邏輯正確性：XX 分
- A/B 監控穩定天數：XX 天
EOF

# （可選）ClawHub 發布
```

### Step 7：DEVELOPMENT_LOG.md 最終記錄

```markdown
## Phase 8 Quality Gate 結果（YYYY-MM-DD HH:MM）

### 前置確認
執行命令：python3 quality_gate/phase_artifact_enforcer.py
結果：Phase 7 完成 ✅

### A/B 監控最終 7 天確認
- 邏輯正確性（7 天平均）：XX 分（目標 ≥ 90）✅
- 回應時間偏差（7 天最高）：X%（目標 < 10%）✅
- 熔斷器觸發（Phase 5 至今）：0 次 ✅
- 錯誤率（7 天最高）：X%（目標 < 1%）✅

### Decision Gate 最終確認
執行命令：python3 .methodology/decisions/check_decisions.py
結果：0 個未確認決策 ✅

### 發布清單執行
- 七個區塊全部 ✅：✅
- 執行日期：YYYY-MM-DD
- Agent A 執行：______（session_id：______）
- Agent B 見證：______（session_id：______）

### Final Quality Gate
執行命令：python3 quality_gate/constitution/runner.py
結果：總分 XX%（目標 ≥ 80%）✅

執行命令：python3 quality_gate/doc_checker.py
結果：Compliance Rate: XX%（目標 > 80%）✅

執行命令：methodology quality
結果：✅ 無 BLOCK 項目

### A/B 最終封版審查
- Agent A（DevOps）：session_id ______
- Agent B（PM）：session_id ______
- AgentEvaluator Score：XX/100
- 審查結論：APPROVE ✅
- 封版決策：v1.0.0 正式發布

### 版本封存
- Git Tag：v1.0.0（commit：xxxxxxx）
- 封版日期：YYYY-MM-DD HH:MM
- CHANGELOG.md：已更新

### Phase 8 結論
✅ Phase 8 完成

### 方法論閉環記錄

| Phase | 完成日期 | Agent A | Agent B | 最終狀態 |
|-------|----------|---------|---------|----------|
| Phase 1 | YYYY-MM-DD | ______ | ______ | ✅ Sign-off |
| Phase 2 | YYYY-MM-DD | ______ | ______ | ✅ Sign-off |
| Phase 3 | YYYY-MM-DD | ______ | ______ | ✅ Sign-off |
| Phase 4 | YYYY-MM-DD | ______ | ______ | ✅ Sign-off |
| Phase 5 | YYYY-MM-DD | ______ | ______ | ✅ Sign-off |
| Phase 6 | YYYY-MM-DD | ______ | ______ | ✅ Sign-off |
| Phase 7 | YYYY-MM-DD | ______ | ______ | ✅ Sign-off |
| Phase 8 | YYYY-MM-DD | ______ | ______ | ✅ Sign-off |

**methodology-v2 v5.56 完整閉環達成 🎉**
**版本：v1.0.0 | 封版日期：YYYY-MM-DD**
```

---

## 7. Phase 8 完整清單（最終 Sign-off）

### Agent A 確認

- [ ] `phase_artifact_enforcer.py` 通過（Phase 7 完成確認）
- [ ] 最近 7 天 A/B 監控全部健康（有連續記錄）
- [ ] `check_decisions.py` 結果：0 個未確認決策
- [ ] 配置盤點完成（pip freeze + npm lock 快照）
- [ ] `CONFIG_RECORDS.md` 完整（八個章節）
- [ ] 發布清單七個區塊全部執行完成（全 ✅）
- [ ] A/B 監控最終報告編製完成
- [ ] 已提交最終封版 A/B 審查
- [ ] Git Tag `v[版本號]` 已建立並 push
- [ ] `CHANGELOG.md` 已更新
- [ ] `DEVELOPMENT_LOG.md` 方法論閉環記錄完成

### Agent B 確認

- [ ] CONFIG_RECORDS 五個維度確認（版本 + 依賴 + 環境一致 + 回滾 + 合規）
- [ ] 發布清單逐項見證確認（七個區塊無遺漏）
- [ ] A/B 監控最終報告確認（熔斷 0 次 + 7 天健康）
- [ ] 版本治理合規確認（Git Tag + CHANGELOG + Decision Gate）
- [ ] 方法論閉環確認（Phase 1-8 全部 sign-off 可追溯）
- [ ] AgentEvaluator 最終評估完成
- [ ] 給出明確 APPROVE 或 REJECT（封版決策）
- [ ] Session ID 已記錄

### Quality Gate 確認

- [ ] `constitution/runner.py` 最終總分 ≥ 80%
- [ ] `doc_checker.py` Compliance Rate > 80%
- [ ] `methodology quality` 無 BLOCK 項目
- [ ] `spec-track check` 通過
- [ ] `check_decisions.py` 0 個未確認

### 記錄確認

- [ ] 最終 A/B 審查對話完整記錄在 `DEVELOPMENT_LOG.md`
- [ ] 方法論閉環記錄表（Phase 1-8）已填寫
- [ ] 所有 session_id 可追溯
- [ ] Git Tag commit hash 記錄在案

---

## 附錄：Phase 7 → Phase 8 知識傳遞

| Phase 7 產出 | Phase 8 使用方式 |
|--------------|----------------|
| RISK_REGISTER.md（緩解措施參數）| CONFIG_RECORDS 配置合規性確認的對照依據 |
| 演練記錄（RTO 實測值）| 回滾 SOP 的 RTO 目標設定依據 |
| Decision Gate 記錄 | 發布清單「風險管理確認」區塊的驗證依據 |
| 風險觸發條件定義 | CONFIG_RECORDS 回滾觸發條件的具體化 |

## 附錄：methodology-v2 完整閉環總覽

```
版本週期完整地圖：

Phase 1 需求    → SRS.md + SPEC_TRACKING + TRACEABILITY（建立 FR）
Phase 2 設計    → SAD.md + ADR（FR → 模組）
Phase 3 實作    → 代碼 + 單元測試（模組 → 函數）
Phase 4 測試    → TEST_PLAN + TEST_RESULTS（函數 → TC）
                  ↓ TRACEABILITY 四欄全滿
Phase 5 驗收    → BASELINE + MONITORING 啟動
Phase 6 品質    → QUALITY_REPORT 完整版（回顧）
Phase 7 風險    → RISK_REGISTER + Decision Gate（前瞻）
Phase 8 配置    → CONFIG_RECORDS + 封版（治理）

每個 Phase 都有：
✅ A/B 雙 Agent 協作（不同 Persona）
✅ HybridWorkflow mode=ON
✅ AgentEvaluator 評估
✅ Quality Gate（ASPICE + Constitution）
✅ DEVELOPMENT_LOG 實際輸出記錄
✅ 雙方 session_id 可追溯
```

---

## 附錄：快速指令備查

```bash
# ── 前置確認 ────────────────────────────
python3 quality_gate/phase_artifact_enforcer.py
python3 .methodology/decisions/check_decisions.py   # 0 個未確認

# ── A/B 監控最終確認（7 天）────────────
python3 scripts/spec_logic_checker.py
python3 scripts/performance_check.py
python3 scripts/circuit_breaker_check.py

# ── 配置盤點 ─────────────────────────────
pip freeze > 08-config/requirements_snapshot.txt

# ── Agent 啟動 ──────────────────────────
# Agent A（DevOps）
python -c "from agent_spawner import spawn_with_persona; \
           spawn_with_persona(role='devops', task='Phase 8 配置記錄與版本封存')"

# Agent B（PM）
python -c "from agent_spawner import spawn_with_persona; \
           spawn_with_persona(role='pm', task='Phase 8 封版審查與方法論閉環確認')"

# ── Final Quality Gate ───────────────────
python3 quality_gate/constitution/runner.py   # ≥ 80%
python3 quality_gate/doc_checker.py           # > 80%
python3 cli.py spec-track check
methodology quality                            # 無 BLOCK

# ── A/B 最終評估 ─────────────────────────
python -m agent_evaluator --check

# ── 版本封存 ─────────────────────────────
git tag -a v1.0.0 -m "Release v1.0.0 - methodology-v2 v5.56"
git push origin v1.0.0
```

---

*整理依據：SKILL.md v5.56 | methodology-v2 Multi-Agent Collaboration Development Methodology*
*格式：5W1H × A/B 協作機制 | 整理日期：2026-03-29*
*Phase 8 是 methodology-v2 的治理終點，本文件為完整八個 Phase 計劃系列的最終篇*
