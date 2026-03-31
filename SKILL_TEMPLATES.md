# methodology-v2 SKILL_TEMPLATES.md

> **版本**: v6.13
> **用途**: Phase 執行時使用的模板庫
> **載入方式**: Lazy Load — SOP 步驟需要模板時才載入

---

## T1: Phase 1 模板

### T1.1 SRS.md 模板

```markdown
# SRS - {專案名稱}

## 1. 需求概述
{簡要描述專案目標}

## 2. 功能需求

| ID | 需求描述 | 實作函數（預估） | 邏輯驗證方法 |
|----|----------|----------------|-------------|
| FR-01 | {需求描述} | {函數名} | {驗證方法} |
| FR-02 | ... | ... | ... |

## 3. 非功能需求（NFR）

| ID | 類型 | 需求描述 | 測試方法 |
|----|------|----------|---------|
| NFR-01 | 效能 | {需求} | {測試方法} |
| NFR-02 | 安全 | {需求} | {測試方法} |

## 4. 限制條件
- {限制1}
- {限制2}

## 5. 術語表
| 術語 | 定義 |
|------|------|
| {術語} | {定義} |
```

### T1.2 SPEC_TRACKING.md 模板

```markdown
# SPEC_TRACKING.md

## 專案資訊
- 專案名稱: {name}
- 版本: v1.0.0
- 建立日期: {date}

## 規格狀態

| FR ID | 規格描述 | 意圖分類 | 決策框架 | 狀態 | 備註 |
|-------|----------|----------|----------|------|------|
| FR-01 | {描述} | {分類} | {框架} | DRAFT | |
```

### T1.3 TRACEABILITY_MATRIX.md 模板

```markdown
# TRACEABILITY_MATRIX.md

## FR → SAD 映射

| FR ID | 對應模組 | 介面 | 備註 |
|-------|----------|------|------|
| FR-01 | ModuleName | API | |
```

### T1.4 Phase 1 A/B 審查清單

```markdown
## Phase 1 A/B 審查清單

- [ ] 所有 FR 編號唯一、無遺漏
- [ ] 每條 FR 有對應的邏輯驗證方法
- [ ] 無「輸出可能大於輸入」的隱患
- [ ] 分支邏輯（if/else）覆蓋完整
- [ ] 外部依賴已標記 Lazy Check 需求
- [ ] SPEC_TRACKING.md 已建立
- [ ] TRACEABILITY_MATRIX.md 已初始化
- [ ] Constitution 正確性 = 100%
```

---

## T2: Phase 2 模板

### T2.1 SAD.md 模板

```markdown
# SAD - {專案名稱}

## 1. 架構概述
{架構高層描述}

## 2. 模組設計

### 2.1 {模組名稱}

| 屬性 | 值 |
|------|-----|
| 職責 | {職責} |
| 對外介面 | {API} |
| 依賴 | {依賴模組} |

#### 邏輯約束
- {約束1}
- {約束2}

## 3. 錯誤處理
| 等級 | 處理策略 |
|------|---------|
| L1 | 立即返回 |
| L2 | 重試 3 次 |
| L3 | 降級處理 |

## 4. 技術選型
| 技術 | 理由 |
|------|------|
| {技術} | {理由} |
```

### T2.2 ADR 模板

```markdown
# ADR-{ID}: {標題}

## 狀態
{Proposed / Accepted / Deprecated}

## 背景
{上下文}

## 決策
{選擇的方案}

## 理由
{選擇理由}

## 後果
{正面影響 / 負面影響}
```

### T2.3 Phase 2 A/B 審查清單

```markdown
## Phase 2 A/B 審查清單

### 審查維度 1：需求覆蓋完整性
- [ ] 所有 FR 在 SAD 中有對應模組
- [ ] 所有 NFR 有架構級別的保障機制

### 審查維度 2：模組設計品質
- [ ] 模組邊界清晰，無職責重疊
- [ ] 依賴方向單向（無循環依賴）
- [ ] 每個模組可獨立測試

### 審查維度 3：錯誤處理完整性
- [ ] L1-L6 分類已明確對應到模組
- [ ] Retry / Fallback 策略有具體參數
- [ ] Circuit Breaker 觸發條件已定義

### 審查維度 4：技術選型合理性
- [ ] 所有技術選型都有 ADR 記錄
- [ ] 無引入規格書外的第三方框架
- [ ] 外部依賴均有 Lazy Init 設計

### 審查維度 5：實作可行性
- [ ] Phase 3 開發者能直接從 SAD 開始實作
- [ ] 無「設計上優美但無法測試」的模組
```

---

## T3: Phase 3 模板

### T3.1 代碼模組模板

```python
class {ModuleName}:
    """
    {模組名稱}

    對應 methodology-v2 規範：
    - SKILL.md - Core Modules
    - SKILL.md - Error Handling (L1-L6)
    - SAD.md FR-{ID}

    邏輯約束：
    - {約束1}
    - {約束2}

    作者: {author}
    日期: {date}
    """

    def __init__(self):
        self._engine = None  # Lazy Init

    def _get_engine(self):
        """Lazy Init：實際需要時才初始化外部依賴"""
        if self._engine is None:
            self._engine = ExternalSDK()
        return self._engine

    def process(self, input_data):
        """主要處理邏輯"""
        # {邏輯實現}
        pass
```

### T3.2 單元測試模板

```python
import pytest
from {module} import {ModuleName}

class Test{ModuleName}:
    """單元測試 - 三類覆蓋"""

    # ===== 正向測試（Happy Path）=====
    def test_process_normal_input(self):
        """正常輸入的預期行為"""
        module = {ModuleName}()
        result = module.process({valid_input})
        assert result == {expected}

    # ===== 邊界測試（Boundary）=====
    def test_process_empty_input(self):
        """空輸入"""
        module = {ModuleName}()
        result = module.process("")
        assert result == {expected}

    def test_process_max_length_input(self):
        """最大長度輸入"""
        module = {ModuleName}()
        result = module.process("x" * 10000)
        assert {constraint}

    def test_process_single_element(self):
        """單一元素"""
        module = {ModuleName}()
        result = module.process(["x"])
        assert {constraint}

    # ===== 負面測試（Negative）=====
    def test_process_output_lessthan_input(self):
        """輸出長度 ≤ 輸入長度"""
        module = {ModuleName}()
        input_data = {test_input}
        result = module.process(input_data)
        assert len(result) <= len(input_data)
```

### T3.3 邏輯審查對話模板

```markdown
## 邏輯審查對話 — [{模組名稱}]

### Developer 回答

1. **邏輯約束**：請描述本模組的核心邏輯約束
   回答：{回答}

2. **邊界條件**：本模組處理的邊界條件有哪些？
   回答：{回答}

3. **外部依賴**：本模組使用哪些外部依賴？是否使用 Lazy Init？
   回答：{回答}

### Architect 確認

1. **邏輯正確性**：上述約束是否正確？有無遺漏？
   確認：{✅/❌}  {備註}

2. **實作可行性**：從 SAD 角度，邏輯是否可實作？
   確認：{✅/❌}  {備註}

### Code Reviewer 確認

1. **測試完整性**：三類測試（正向/邊界/負面）是否完整？
   確認：{✅/❌}  {備註}

2. **規範符合度**：是否 100% 符合命名規則和註解要求？
   確認：{✅/❌}  {備註}
```

### T3.4 合規矩陣模板

```markdown
# 合規矩陣 - {模組名稱}

## FR 對應

| FR ID | 需求描述 | 實作函數 | 邏輯驗證 | 覆蓋狀態 |
|-------|----------|----------|----------|---------|
| FR-01 | {描述} | {函數} | {方法} | ✅ |

## NFR 對應

| NFR ID | 類型 | 保障機制 | 覆蓋狀態 |
|--------|------|----------|---------|
| NFR-01 | 效能 | {機制} | ✅ |
```

---

## T4: Phase 4 模板

### T4.1 TEST_PLAN.md 模板

```markdown
# TEST_PLAN.md - {專案名稱}

## 1. 測試目標
{測試目標描述}

## 2. 測試範圍
- {範圍1}
- {範圍2}

## 3. 測試策略
| 類型 | 策略 |
|------|------|
| 單元測試 | {策略} |
| 集成測試 | {策略} |
| 系統測試 | {策略} |

## 4. 測試環境
- 環境：{環境}
- 工具：{工具}

## 5. 測試案例清單

| ID | 類型 | 描述 | 預期結果 | 狀態 |
|----|------|------|---------|------|
| TC-01 | 正向 | {描述} | {結果} | DRAFT |
```

### T4.2 TEST_RESULTS.md 模板

```markdown
# TEST_RESULTS.md - {專案名稱}

## 執行摘要
- 總測試數：{N}
- 通過：{N}
- 失敗：{N}
- 通過率：{X}%

## 詳細結果

### 通過的測試
| ID | 描述 | 執行時間 |
|----|------|---------|
| TC-01 | {描述} | {時間} |

### 失敗的測試
| ID | 描述 | 失敗原因 | 根本原因 |
|----|------|---------|---------|
| TC-XX | {描述} | {原因} | {分析} |

## 失敗案例分析
### {TC-ID}
**問題**：{描述}
**根本原因**：{分析}
**修復方式**：{方法}
```

---

## T5: Phase 5 模板

### T5.1 BASELINE.md 模板

```markdown
# BASELINE.md - {專案名稱}

## 1. 基線概述
- 建立人：{name}
- 審查人：{name}
- session_id：{session_id}
- 日期：{date}

## 2. 功能基線（對應 SRS FR，100% ✅）

| FR ID | 功能描述 | 基線狀態 | 備註 |
|-------|----------|---------|------|
| FR-01 | {描述} | ✅ | |

## 3. 品質基線

| 指標 | 門檻 | 實際值 | 狀態 |
|------|------|--------|------|
| Constitution | ≥ 80% | {value} | ✅/❌ |
| 覆蓋率 | ≥ 80% | {value} | ✅/❌ |
| 邏輯正確性 | ≥ 90 分 | {value} | ✅/❌ |

## 4. 效能基線（A/B 監控基準）

| 指標 | 基線值 |
|------|--------|
| 回應時間 | {value} ms |
| 記憶體 | {value} MB |
| 錯誤率 | {value}% |

## 5. 已知問題登錄
| 嚴重性 | 數量 | 說明 |
|--------|------|------|
| HIGH | {N} | {說明} |

> ⚠️ HIGH 嚴重性 = 0 才能建立基線

## 6. 驗收簽收
- Agent A：{name} ({session_id}) - {date}
- Agent B：{name} ({session_id}) - {date}
```

### T5.2 MONITORING_PLAN.md 模板

```markdown
# MONITORING_PLAN.md

## 監控維度

| 維度 | 指標 | 告警閾值 | 數據來源 |
|------|------|---------|---------|
| 效能 | 回應時間 | > {value} ms | {source} |
| 可靠性 | 錯誤率 | > {value}% | {source} |
| 資源 | 記憶體 | > {value} MB | {source} |
| 熔斷器 | 觸發次數 | > {N}/min | {source} |
```

---

## T6: Phase 6 模板

### QUALITY_REPORT.md 模板

```markdown
# QUALITY_REPORT.md - {專案名稱}

## 1. 品質指標全覽

| 指標 | Phase 5 基線 | Phase 6 實際 | 變化 |
|------|-------------|-------------|------|
| Constitution | {v5} | {v6} | {Δ} |
| 覆蓋率 | {v5} | {v6} | {Δ} |

## 2. ASPICE 合規性
| Phase | 狀態 |
|-------|------|
| Phase 1-4 | ✅/❌ |
| Phase 5 | ✅/❌ |

## 3. Constitution 四維度
| 維度 | 分數 |
|------|------|
| 正確性 | {value}% |
| 安全性 | {value}% |
| 可維護性 | {value}% |
| 測試覆蓋率 | {value}% |

## 4. 品質問題根源分析
| 問題 | 等級 | 根源 | 解決方案 |
|------|------|------|---------|
| {問題} | {等級} | {根源} | {方案} |

## 5. 改進建議
1. {建議1}
2. {建議2}
```

---

## T7: Phase 7 模板

### RISK_REGISTER.md 模板

```markdown
# RISK_REGISTER.md - {專案名稱}

## 風險矩陣

| ID | 風險描述 | 維度 | 等級 | 概率 | 影響 | 緩解措施 | 狀態 |
|----|----------|------|------|------|------|---------|------|
| R-01 | {描述} | {維度} | {等級} | {prob}% | {impact} | {措施} | {狀態} |

## Decision Gate 確認

| 風險 ID | 決策 | 確認人 | session_id | 日期 |
|---------|------|--------|------------|------|
| R-01 | {決策} | {name} | {session_id} | {date} |
```

---

## T8: Phase 8 模板

### CONFIG_RECORDS.md 模板

```markdown
# CONFIG_RECORDS.md - {專案名稱}

## 1. 版本資訊
- 版本：v{version}
- Git Commit：{hash}
- 發布日期：{date}

## 2. 執行環境配置
| 環境 | 配置 |
|------|------|
| 開發 | {config} |
| 生產 | {config} |

## 3. 依賴套件清單
```
{pip freeze / npm lock output}
```

## 4. 環境變數
| 變數 | 類型 | 說明 |
|------|------|------|
| {VAR} | secret | {說明} |

## 5. 部署記錄
| 日期 | 版本 | 方式 | 執行人 |
|------|------|------|--------|
| {date} | {ver} | {method} | {name} |

## 6. 配置變更記錄
| Phase | 變更內容 | 理由 |
|-------|---------|------|
| Phase 5 | {變更} | {理由} |

## 7. 回滾 SOP
**觸發條件**：{條件}
**命令**：
```bash
{rollback commands}
```

## 8. 配置合規性確認
- [ ] Phase 7 風險緩解措施已落實
- [ ] 監控閾值已配置
- [ ] 熔斷器已啟用
```

---

## §T18 STAGE_PASS 查核日誌模板

# Phase {N} STAGE_PASS

## Agent A 自評

### 5W1H 合規性檢查
| 項目 | 狀態 | 說明 |
|------|------|------|
| WHO | ✅/❌ | |
| WHAT | ✅/❌ | |
| WHEN | ✅/❌ | |
| WHERE | ✅/❌ | |
| WHY | ✅/❌ | |
| HOW | ✅/❌ | |

### 發現的問題
| # | 問題 | 嚴重性 | 修復方式 | 狀態 |
|---|------|--------|----------|------|

### 交付物清單
| 交付物 | 狀態 | 路徑 |
|--------|------|------|

**誠實分數**: {score}/100

Agent A: {name} Session: {session_id}

---

## Agent B 審查

### 疑問清單
| # | 疑問 | 針對項目 | 回應 |
|---|------|----------|------|

### 審查結論
| 結論 | 說明 |
|------|------|
| ✅ APPROVE | 無重大疑問 |
| ❌ REJECT | 有疑問需修復 |

Agent B: {name} Session: {session_id}

---

## Johnny 介入（如有）
（僅在 Agent B 提出重大問題時填寫）

---

*由 methodology-v2 v6.13 STAGE_PASS Generator 產生*

---

## A/B 審查通用模板

```markdown
# A/B 審查紀錄 - Phase {N}

## 審查資訊
- Phase：{N}
- 審查人：Agent B
- session_id：{session_id}
- 日期：{date}

## 審查維度
{逐項檢查清單}

## 審查結論
- [ ] ✅ APPROVE — {理由}
- [ ] ❌ REJECT — {理由}

## Conflict Log（如有）
| 衝突點 | 規格書建議 | methodology-v2 選擇 | 理由 |
|--------|------------|---------------------|------|
| | | | |

## Agent B 簽名：{name}
```

---

*SKILL_TEMPLATES.md v6.13 | Template Library*
