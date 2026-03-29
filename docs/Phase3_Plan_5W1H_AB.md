# Phase 3 計劃：代碼實現
## methodology-v2 | 5W1H 框架 × A/B 協作機制

> **版本基準**：SKILL.md v5.56 | 整理日期：2026-03-29
> **前置條件**：Phase 2 全部 Sign-off ✅（SAD.md 已 APPROVE、phase_artifact_enforcer 通過）

---

## 🗺️ 一覽表

| 5W1H | 核心答案 |
|------|----------|
| **WHO**   | Agent A（Developer）實作 × Agent B（Code Reviewer）審查；同行邏輯審查為強制程序 |
| **WHAT**  | 產出生產就緒代碼 + 單元測試（含邊界 & 負面測試）+ 邏輯審查對話記錄 |
| **WHEN**  | Phase 2 完整通過後；每個模組完成即觸發 A/B 審查，不等到全部完成才審 |
| **WHERE** | `03-implementation/` 目錄；測試在 `tests/`；Quality Gate 在 `quality_gate/` |
| **WHY**   | 邏輯缺陷在此階段攔截成本最低；「自己寫自己測」是 PolyTrade 44% 完整度的核心病因 |
| **HOW**   | 領域知識確認 → A 實作 → 邏輯自我檢查 → B 同行審查 → Quality Gate → sign-off |

---

## 1. WHO — 誰執行？（A/B 角色分工）

> ⚠️ **雙重禁止**：①禁止自寫自審；②禁止跳過同行邏輯審查對話（即使時間緊迫）。

### Agent A（Developer）—— 主責代碼實作

| 屬性 | 內容 |
|------|------|
| Persona | `developer` |
| Goal | 將 SAD.md 模組設計轉化為生產就緒代碼，單元測試覆蓋率 100% |
| 職責 | 實作所有模組、撰寫單元測試、填寫邏輯審查對話（Developer 回答部分）|
| 黃金準則 | 代碼註解標注對應規範條文；命名規則 100% 符合 methodology-v2 |
| 禁止 | 引入 SAD.md 與 methodology-v2 以外的框架；自行通過 Quality Gate |

```python
# Phase 3 Agent A 啟動
from agent_spawner import spawn_with_persona

agent_a = spawn_with_persona(
    role="developer",
    task="依據 SAD.md 實作所有模組，單元測試覆蓋率 100%",
)
```

### Agent B（Code Reviewer）—— 主責代碼審查

| 屬性 | 內容 |
|------|------|
| Persona | `reviewer` |
| Goal | 發現 Agent A 實作中的邏輯錯誤、覆蓋率漏洞、規範偏離 |
| 職責 | 同行邏輯審查（填寫 Architect 確認部分）、A/B 代碼評估、確認測試完整性 |
| 核心問題 | 「輸出是否可能多於輸入？」「單一情況與多情況邏輯一致嗎？」「Lazy Init 有沒有落實？」|
| 禁止 | 代替 Agent A 修改代碼；跳過 AgentEvaluator；僅看代碼不看測試 |

```python
# Phase 3 Agent B 啟動
agent_b = spawn_with_persona(
    role="reviewer",
    task="審查代碼邏輯正確性、測試完整性、規範符合度",
)
```

### A/B 協作啟動

```python
from methodology import quick_start
from hybrid_workflow import HybridWorkflow
from agent_evaluator import AgentEvaluator

team = quick_start("dev")              # Developer + Reviewer
workflow = HybridWorkflow(mode="ON")   # 強制 A/B 審查
evaluator = AgentEvaluator()

# 確認有 2+ Agent 運行
assert len(team.list_agents()) >= 2, "必須有 2+ Agent，禁止單人開發"
```

---

## 2. WHAT — 做什麼？（Phase 3 交付物）

### 必要交付物（Mandatory）

| 交付物 | 負責方 | 驗證方 | 位置 |
|--------|--------|--------|------|
| 生產就緒代碼（各模組）| Agent A | Agent B + Quality Gate | `03-implementation/src/` |
| 單元測試（含邊界 & 負面測試）| Agent A | Agent B | `tests/` |
| 集成測試 | Agent A | Agent B | `tests/test_integration.py` |
| 邏輯審查對話記錄 | A 回答 + B 確認 | 雙方 | `DEVELOPMENT_LOG.md` |
| 合規矩陣（Compliance Matrix）| Agent A | Agent B | `DEVELOPMENT_LOG.md` |
| `DEVELOPMENT_LOG.md`（Phase 3 段落）| Agent A | Agent B | 專案根目錄 |

---

### 代碼規範要求

每個模組必須包含規範標注：

```python
class TTSEngine:
    """
    TTS 引擎 - 語音合成核心

    對應 methodology-v2 規範：
    - SKILL.md - Core Modules
    - SKILL.md - Error Handling (L1-L6)
    - SAD.md FR-01, FR-05

    邏輯約束：
    - 輸出長度 ≤ 輸入長度（Spec Logic Mapping FR-01）
    - 外部依賴使用 Lazy Init（避免初始化崩潰）
    """

    def __init__(self):
        self._engine = None  # Lazy Init：不在 __init__ 直接呼叫

    def _get_engine(self):
        """Lazy Init：實際需要時才初始化外部依賴"""
        if self._engine is None:
            self._engine = ExternalTTSSDK()
        return self._engine
```

---

### 單元測試最低要求

每個模組的測試必須覆蓋以下三類：

```python
class TestTextProcessor:

    # ── 類型 1：正向測試（Happy Path）─────────────────
    def test_split_normal_text(self):
        """正常文字分段"""
        text = "大家好。我是導引員。今天天氣好。"
        result = processor.split(text)
        assert len(result) > 0

    # ── 類型 2：邊界測試（Boundary）──────────────────
    def test_split_empty_input(self):
        """空白輸入 → 應回傳空陣列"""
        assert processor.split("") == []

    def test_split_single_sentence_exceeds_chunk_size(self):
        """超過 chunk_size 的單一句子 → 應正確分割"""
        long_sentence = "A" * 1000
        result = processor.split(long_sentence)
        assert all(len(chunk) <= CHUNK_SIZE for chunk in result)

    # ── 類型 3：負面測試（Negative）──────────────────
    def test_output_not_exceed_input(self):
        """邏輯約束：合併後字符數不應多於原文"""
        text = "大家好。我是導引員。今天天氣好。"
        chunks = processor.split(text)
        merged = ''.join(chunks)
        assert len(merged) <= len(text), \
            f"輸出多於原文！merged={len(merged)}, input={len(text)}"

    def test_single_vs_multi_format_consistency(self):
        """單一檔案與多檔案格式必須一致"""
        single = merger.merge(["a.mp3"], "out.mp3")
        multi  = merger.merge(["a.mp3", "b.mp3"], "out.mp3")
        assert get_format(single) == get_format(multi), \
            "單一與多檔案格式不一致！"
```

---

### 集成測試模板（端到端）

```python
# tests/test_integration.py

class TestIntegration:
    """端到端集成測試——覆蓋跨模組邏輯"""

    def test_full_pipeline(self):
        """完整流程：文字 → 最終輸出"""
        text = "大家好。我是導引員。"
        result = pipeline.process(text)
        assert result.success
        assert result.output_file.exists()

    def test_output_not_exceed_input(self):
        """跨模組約束：輸出不應比輸入多字符"""
        text = "大家好。我是導引員。今天天氣好。"
        chunks = processor.split(text)
        merged = ''.join(chunks)
        assert len(merged) <= len(text)

    def test_single_file_format_consistency(self):
        """單一檔案 vs 多檔案：格式一致"""
        s = merger.merge(["a.mp3"], "s.mp3")
        m = merger.merge(["a.mp3", "b.mp3"], "m.mp3")
        assert get_format(s) == get_format(m)

    def test_error_recovery(self):
        """錯誤復原：失敗後可重新執行"""
        with pytest.raises(ExpectedError):
            pipeline.process(invalid_input)
        result = pipeline.process(valid_input)
        assert result.success
```

---

### A/B 代碼審查清單（Agent B 逐項確認）

**邏輯正確性（來自 SKILL.md 3.x.1 ~ 3.x.2）**
- [ ] 所有字串操作：輸出長度 ≤ 輸入長度
- [ ] 分支邏輯：`if len(x)==1` 與一般情況結果一致
- [ ] 外部依賴：全部使用 Lazy Init，`__init__` 不直接呼叫
- [ ] 標點處理（TTS 領域）：標點有保留，未被刪除

**測試完整性**
- [ ] 正向測試覆蓋所有 Happy Path
- [ ] 邊界測試：空輸入、超長輸入、單一元素
- [ ] 負面測試：合併後字符數驗證、格式一致性驗證
- [ ] 集成測試覆蓋跨模組邏輯
- [ ] 單元測試覆蓋率 ≥ 80%（Constitution 門檻）

**規範符合度**
- [ ] 代碼命名符合 methodology-v2 命名規則
- [ ] 錯誤處理對應 L1-L6 分類
- [ ] 代碼註解標注對應規範條文
- [ ] 無引入 SAD.md 外的第三方框架

**合規矩陣完整性**
- [ ] 每個模組都在合規矩陣中有記錄
- [ ] 合規矩陣執行狀態均為「100% 落實」或有說明

---

## 3. WHEN — 何時執行？（時序 & 門檻）

### Phase 3 時序圖

```
Phase 2 sign-off ✅
        │
        ▼
[前置確認] phase_artifact_enforcer.py
        │
        ├── ❌ Phase 2 未完成 → 停止
        └── ✅ 通過
                │
                ▼
        [Agent A] 領域知識確認
        查閱 SKILL.md 附錄 X 領域知識清單
                │
                ▼
        ┌──────────────────────────────┐
        │   模組開發循環（每個模組）    │
        │                              │
        │  [Agent A] 實作模組代碼      │
        │       ↓                      │
        │  [Agent A] 邏輯自我檢查      │
        │  （填寫審查對話 Developer 部分）│
        │       ↓                      │
        │  [Agent A → Agent B]         │
        │  同行邏輯審查對話            │
        │  （B 填寫 Architect 確認部分）│
        │       ↓                      │
        │  ❌ B: 不通過                │
        │  → A 修改 → 重新審查         │
        │       ↓                      │
        │  ✅ B: 通過                  │
        │  → 繼續下一模組              │
        └──────────────────────────────┘
                │
                ▼
        所有模組完成 + 集成測試通過
                │
                ▼
        [A/B] AgentEvaluator 全域評估
                │
                ▼
        Quality Gate 執行
        （ASPICE + Constitution）
                │
                ├── 未通過 → Agent A 修正 → 重新 Gate
                └── 通過
                        │
                        ▼
                記錄 DEVELOPMENT_LOG.md
                        │
                        ▼
                ✅ Phase 3 完成 → 進入 Phase 4
```

> **關鍵原則**：A/B 審查以**模組為單位**觸發，不是等全部代碼完成才審。
> 每個模組完成 → 立即觸發該模組的同行邏輯審查 → 通過才開發下一個模組。

### 進入 Phase 4 的前置條件（全部必須為 ✅）

| 條件 | 門檻 | 檢查方 |
|------|------|--------|
| ASPICE 文檔合規率 | > 80% | Quality Gate doc_checker |
| Constitution 正確性 | = 100% | Constitution Runner |
| Constitution 測試覆蓋率 | > 80% | Constitution Runner |
| Constitution 可維護性 | > 70% | Constitution Runner |
| 單元測試全部通過 | 通過率 100% | pytest |
| 集成測試全部通過 | 通過率 100% | pytest |
| 每個模組都有同行邏輯審查記錄 | 無遺漏 | Agent B 確認 |
| AgentEvaluator 評分 | ≥ 90 分 | AgentEvaluator |
| 合規矩陣完整 | 每個模組有記錄 | Agent B 確認 |

---

## 4. WHERE — 在哪裡執行？（路徑 & 工具位置）

### 文件結構（Phase 3 新增）

```
project-root/
├── 01-requirements/               ← Phase 1（只讀）
├── 02-architecture/               ← Phase 2（只讀）
│
├── 03-implementation/             ← Phase 3 主要工作區
│   └── src/
│       ├── module_a.py            ← Agent A 實作（含規範標注）
│       ├── module_b.py
│       └── ...
│
├── tests/
│   ├── test_module_a.py           ← 單元測試（正向 + 邊界 + 負面）
│   ├── test_module_b.py
│   └── test_integration.py        ← 集成測試（端到端）
│
├── scripts/
│   └── spec_logic_checker.py      ← 邏輯正確性自動檢查
│
├── quality_gate/
│   ├── doc_checker.py
│   ├── constitution/
│   │   └── runner.py              ← Phase 3 不指定 --type（全面檢查）
│   └── phase_artifact_enforcer.py
│
└── DEVELOPMENT_LOG.md             ← Phase 3 段落（含每個模組的審查對話）
```

### 工具執行位置

```bash
# ── 前置確認 ────────────────────────────
python3 quality_gate/phase_artifact_enforcer.py

# ── 測試執行 ────────────────────────────
pytest tests/ -v --cov=src --cov-report=term-missing

# ── 邏輯正確性檢查 ──────────────────────
python3 scripts/spec_logic_checker.py

# ── Phase 3 Quality Gate ────────────────
python3 quality_gate/doc_checker.py
python3 quality_gate/constitution/runner.py     # 不加 --type，全面檢查

# ── A/B 評估 ────────────────────────────
python -m agent_evaluator --check

# ── Framework Enforcement ───────────────
methodology quality
```

---

## 5. WHY — 為什麼這樣做？（設計理由）

### 「以模組為單位」觸發 A/B 的理由

等全部代碼完成才審查，等同於：
- 缺陷累積到最大量才發現
- Agent B 一次審查 1000 行，注意力分散
- 早期模組的邏輯錯誤已傳染至後期模組

**以模組為單位審查**：
- 每次審查範圍 ≤ 200 行，Agent B 專注度高
- 邏輯錯誤在當前模組攔截，不傳染
- 修改成本最低（僅影響當前模組）

### 同行邏輯審查為何是「強制」程序

來自 SKILL.md 3.x.4 的定義：

> 在 Phase 3 完成後，進行「邏輯審查對話」。
> Developer 回答假設、輸出預期、領域知識應用。
> Architect 確認假設合理、邏輯正確、通過審查。

這個對話的核心價值不是「找到 Bug」，而是**讓 Agent A 說出自己的假設**——假設一旦說出口，Agent B 就能判斷假設是否合理，而不是盲目相信代碼的表象。

### 三類測試缺一不可的理由

| 測試類型 | 如果省略 | 後果 |
|----------|----------|------|
| 正向測試 | 基本功能沒有驗證 | Phase 4 才發現主流程壞了 |
| 邊界測試 | 空輸入、超長輸入未處理 | 生產環境崩潰 |
| 負面測試 | 「輸出 > 輸入」未被捕捉 | **PolyTrade 的直接病因**——合併後插入額外字符，直到手動測試才發現 |

### 領域知識確認的核心價值

不同領域有各自的「反直覺規則」，不事先確認就開發，容易寫出「技術上正確但領域上錯誤」的代碼：

| 領域 | 反直覺規則 | 如果不知道 |
|------|------------|------------|
| TTS | 標點 = 停頓信號，不能刪除 | 分段後標點消失，語音停頓異常 |
| 字串操作 | 合併操作不應插入額外字符 | 輸出比輸入多，邏輯驗證失敗 |
| 網路 | 外部 SDK 必須 Lazy Init | `__init__` 崩潰，測試無法啟動 |

---

## 6. HOW — 如何執行？（完整 SOP）

### Step 0：前置確認 + 領域知識確認（Agent A）

```bash
# 確認 Phase 2 已完成
python3 quality_gate/phase_artifact_enforcer.py

# 確認 SAD.md 可讀
cat 02-architecture/SAD.md
```

**領域知識確認清單（實作前必查，來自 SKILL.md 附錄 X）**：

```markdown
## 領域知識確認（Phase 3 開始前）

### TTS 領域
- [ ] 標點是否保留？（刪除會破壞停頓）
- [ ] 合併後是否多於原文？
- [ ] 單一檔案格式是否與多檔案一致？
- [ ] ffmpeg / 外部 SDK 是否 Lazy Init？

### 通用領域
- [ ] 輸出是否可能多於輸入？（字串操作）
- [ ] 單一情況是否與多情況邏輯一致？（分支邏輯）
- [ ] 外部依賴是否 Lazy Init？（初始化）

確認人：Agent A（______）
確認日期：______
```

### Step 1：模組實作循環（每個模組重複執行）

#### 1a. Agent A 實作代碼

```markdown
實作要求：
1. 依照 SAD.md 的模組設計（不得偏離）
2. 每個函數加上對應規範條文的注解
3. 所有外部依賴使用 Lazy Init
4. 錯誤處理對應 L1-L6 分類
5. 同步填寫 Spec Logic Mapping（實作函數欄位）
```

#### 1b. Agent A 邏輯自我檢查（填寫審查對話 Developer 部分）

```markdown
## 邏輯審查對話 — [模組名稱]（Phase 3）

### Developer 回答（Agent A 必須填寫）

**1. 我的假設是：**
- [ ] 標點處理邏輯：______（例：標點已保留，未被刪除）
- [ ] 輸出不超過輸入：______（例：split() 不插入額外字符）
- [ ] 分支一致性：______（例：單一元素與多元素走同一邏輯路徑）
- [ ] Lazy Init：______（例：_engine 在 _get_engine() 中初始化）

**2. 輸出預期：**
- [ ] 沒有插入額外字符（說明：______）
- [ ] 格式與多情況一致（說明：______）

**3. 領域知識應用：**
- [ ] TTS：標點 = 停頓，已保留
- [ ] 網路：timeout=30s、retry=3 次、熔斷在 5 次失敗後觸發
- [ ] 通用：輸出 ≤ 輸入，已有負面測試驗證

Agent A 簽名：______  Session ID：______
```

#### 1c. Agent B 同行邏輯審查（填寫 Architect 確認部分）

```markdown
### Architect 確認（Agent B 必須填寫）

**審查結果：**
- [ ] 假設合理（說明：______）
- [ ] 邏輯正確（說明：______）
- [ ] 領域知識已正確應用（說明：______）
- [ ] 負面測試覆蓋關鍵約束（說明：______）

**發現問題（若有）：**
| 問題描述 | 嚴重性 | 建議修改方式 |
|----------|--------|-------------|
|          |        |             |

**審查結論：**
- [ ] ✅ 通過 — 繼續下一模組
- [ ] ❌ 不通過 — 返回 Agent A 修改（原因：______）

Agent B 簽名：______  Session ID：______
```

### Step 2：A/B 全域代碼評估（所有模組完成後）

```python
from agent_evaluator import AgentEvaluator
from hybrid_workflow import HybridWorkflow

workflow = HybridWorkflow(mode="ON")
evaluator = AgentEvaluator()

# 全域評估（所有模組 + 集成測試）
result = evaluator.evaluate(
    code_a=all_module_code,      # Agent A 的全部產出
    code_b=review_checklist      # Agent B 的審查標準
)

if result.score < 90:
    raise Exception(f"代碼評估未達門檻：{result.score}/100，需達 90+")

if not result.approved:
    raise Exception(f"A/B 評估未通過：{result.rejection_reason}")

print(f"✅ A/B 全域評估通過：{result.score}/100")
```

### Step 3：測試執行（Agent A，結果給 B 確認）

```bash
# 執行全部測試 + 覆蓋率報告
pytest tests/ -v \
  --cov=src \
  --cov-report=term-missing \
  --cov-report=html:coverage_report/

# 邏輯正確性自動檢查
python3 scripts/spec_logic_checker.py
```

**測試通過標準**：
- 全部測試通過率 = 100%
- 代碼覆蓋率 ≥ 80%
- `spec_logic_checker.py` 無 FAIL

### Step 4：Quality Gate（必須有實際輸出）

```bash
# ASPICE 文檔檢查
python3 quality_gate/doc_checker.py

# Constitution 全面檢查（Phase 3 不加 --type）
python3 quality_gate/constitution/runner.py

# Framework Enforcement
methodology quality
```

### Step 5：合規矩陣填寫（Agent A）

```markdown
## 合規矩陣（Compliance Matrix）— Phase 3

| 功能模組 | 對應 methodology-v2 規範 | 對應 SRS ID | 執行狀態 | 備註 |
|----------|--------------------------|-------------|----------|------|
| TTSEngine | SKILL.md - Core Modules | FR-01,FR-02 | 100% 落實 | 無 |
| TextProcessor | SKILL.md - Data Processing | FR-05,FR-07 | 100% 落實 | 無 |
| AudioMerger | SKILL.md - Error Handling | FR-19 | 100% 落實 | 無 |
| ErrorHandler | SKILL.md - L1-L6 分類 | NFR-02 | 100% 落實 | 無 |
```

### Step 6：DEVELOPMENT_LOG.md 記錄（正確格式）

```markdown
## Phase 3 Quality Gate 結果（YYYY-MM-DD HH:MM）

### 前置確認
執行命令：python3 quality_gate/phase_artifact_enforcer.py
結果：Phase 2 完成 ✅

### 領域知識確認
- TTS 領域：✅ 確認完成（Agent A，session_id：______）
- 通用領域：✅ 確認完成

### 模組審查記錄摘要
| 模組 | Agent A | Agent B | 結論 | 問題數 |
|------|---------|---------|------|--------|
| TTSEngine | ______ | ______ | ✅ 通過 | 0 |
| TextProcessor | ______ | ______ | ✅ 通過 | 1 → 已修復 |

### 測試結果
執行命令：pytest tests/ -v --cov=src
結果：
- 總測試數：XX
- 通過：XX / 失敗：0
- 代碼覆蓋率：XX%（目標 ≥ 80%）

### 邏輯正確性檢查
執行命令：python3 scripts/spec_logic_checker.py
結果：PASS（無邏輯錯誤）

### ASPICE 文檔檢查
執行命令：python3 quality_gate/doc_checker.py
結果：Compliance Rate: XX%

### Constitution 全面檢查
執行命令：python3 quality_gate/constitution/runner.py
結果：
- 正確性: XX%（目標 100%）
- 安全性: XX%（目標 100%）
- 可維護性: XX%（目標 > 70%）
- 測試覆蓋率: XX%（目標 > 80%）

### A/B 全域評估
- AgentEvaluator Score：XX/100（目標 ≥ 90）
- 評估結論：APPROVE ✅ / REJECT ❌

### Phase 3 結論
- [ ] ✅ 通過，進入 Phase 4
- [ ] ❌ 未通過（原因：______）
```

> ❌ **禁止這樣記錄**：
> ```markdown
> ### Phase 3 Quality Gate
> ✅ 已通過
> ```

---

## 7. Phase 3 完整清單（最終 Sign-off）

### Agent A 確認

- [ ] 領域知識確認清單已完成（Phase 3 開始前）
- [ ] 所有模組依照 SAD.md 設計實作（無偏離）
- [ ] 代碼命名 100% 符合 methodology-v2 規則
- [ ] 所有外部依賴使用 Lazy Init
- [ ] 錯誤處理對應 L1-L6 分類
- [ ] 每個函數有規範條文注解
- [ ] 單元測試三類完整：正向 + 邊界 + 負面
- [ ] 集成測試覆蓋跨模組邏輯
- [ ] 每個模組的邏輯審查對話（Developer 部分）已填寫
- [ ] 合規矩陣已填寫
- [ ] 已提交 A/B 全域評估請求

### Agent B 確認

- [ ] 每個模組的同行邏輯審查對話（Architect 部分）已填寫
- [ ] 邏輯正確性五項全部確認（假設、輸出、領域知識、分支、Lazy Init）
- [ ] 測試三類完整性已確認
- [ ] AgentEvaluator 全域評估完成（≥ 90 分）
- [ ] 合規矩陣完整性已確認
- [ ] 給出明確 APPROVE 或 REJECT（含理由）
- [ ] Session ID 已記錄

### Quality Gate 確認

- [ ] `pytest` 通過率 100%，覆蓋率 ≥ 80%
- [ ] `spec_logic_checker.py` 無 FAIL
- [ ] `doc_checker.py` Compliance Rate > 80%
- [ ] `constitution/runner.py` 正確性 = 100%
- [ ] `methodology quality` 無 BLOCK 項目

### 記錄確認

- [ ] 每個模組的審查對話記錄在 `DEVELOPMENT_LOG.md`
- [ ] 合規矩陣已完整填寫
- [ ] Quality Gate 有實際命令輸出（非空泛文字）
- [ ] 雙方 session_id 已記錄（可追溯）

---

## 附錄：Phase 2 → Phase 3 知識傳遞

| Phase 2 產出 | Phase 3 使用方式 |
|--------------|----------------|
| SAD.md 模組設計 | 代碼實作的直接藍圖 |
| Spec Logic Mapping（架構版）| 延伸為函數層級的邏輯驗證 |
| ADR 技術選型 | 實作時的技術選擇依據 |
| L1-L6 對應模組 | 每個模組的錯誤處理實作指引 |
| TRACEABILITY_MATRIX（FR → 模組）| Phase 3 新增「實作函數」欄位 |

---

## 附錄：快速指令備查

```bash
# ── 前置確認 ────────────────────────────
python3 quality_gate/phase_artifact_enforcer.py

# ── Agent 啟動 ──────────────────────────
# Agent A（開發者）
python -c "from agent_spawner import spawn_with_persona; \
           spawn_with_persona(role='developer', task='Phase 3 代碼實作')"

# Agent B（審查者）
python -c "from agent_spawner import spawn_with_persona; \
           spawn_with_persona(role='reviewer', task='Phase 3 同行邏輯審查')"

# ── A/B 強制模式 ────────────────────────
python -c "from hybrid_workflow import HybridWorkflow; HybridWorkflow(mode='ON')"
python -m agent_evaluator --check   # 門檻：≥ 90 分

# ── 測試 ────────────────────────────────
pytest tests/ -v --cov=src --cov-report=term-missing
python3 scripts/spec_logic_checker.py

# ── Quality Gate ────────────────────────
python3 quality_gate/doc_checker.py
python3 quality_gate/constitution/runner.py   # 不加 --type
methodology quality
```

---

*整理依據：SKILL.md v5.56 | methodology-v2 Multi-Agent Collaboration Development Methodology*
*格式：5W1H × A/B 協作機制 | 整理日期：2026-03-29*
