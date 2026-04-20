# Feature #8: Gap Detection Agent — 功能規格文檔

**版本：** 1.0  
**創建日期：** 2026-04-20  
**狀態：** 已完成（Phase 3-5 已実装）  

---

## 1.  Overview

### 1.1  功能定位

Gap Detection Agent（以下簡稱「Agent」）是 methodology-v2 框架內的核心品質把關工具。其職責是：

> **對比 `SPEC.md` 承諾功能與 `implement/` 目錄實際實現，自動識別並分類規格偏離（Gap）。**

Agent 運行於 CLI 環境，無需人類介入即可輸出結構化 gap 報告。

### 1.2  核心問題

在大規模多檔案協作開發中，規格（SPEC.md）與實際代碼之間常出現三種偏差：

| 偏差類型 | 描述 | 風險等級 |
|----------|------|----------|
| **MISSING** | SPEC 明確記載的功能，代碼完全未實作 | 🔴 高 |
| **INCOMPLETE** | 代碼已實作但未覆蓋完整需求（部分實作） | 🟡 中 |
| **ORPHANED** | 代碼實作了 SPEC 從未記載的功能 | ⚪ 低（資訊性） |

手工比對既慢又容易遺漏。Agent 將此流程自動化。

### 1.3  驗收標準

| 維度 | 閾值 | 說明 |
|------|------|------|
| 解析成功率 | > 95% | SPEC.md Markdown 結構解析成功率 |
| 掃描覆蓋率 | = 100% | 所有 `.py` 檔案皆被 AST 掃描 |
| Gap 檢測準確率 | > 90% | 人工抽樣比對，確認報告準確性 |

---

## 2.  功能列表

### 2.1  Core Features

#### F1: SPEC 解析器（parser.py）

| 項目 | 說明 |
|------|------|
| **輸入** | `SPEC.md` 檔案路徑 |
| **輸出** | 結構化 JSON（含 `feature_items[]`, `metadata`） |
| **解析規則** | 見 §3.1 |

**功能點：**

- F1.1: 解析 Markdown 標題層級（H1-H6）
- F1.2: 識別功能項目（Feature Item）：以 `### F{n}:` 或 `#### F{n}:` 開頭的章節
- F1.3: 提取功能名稱、描述、驗收標準（Acceptance Criteria）
- F1.4: 提取依賴關係（Depends on）、優先權（Priority）
- F1.5: 輸出結構化 JSON，含原始行號（line numbers）
- F1.6: 遇到解析失敗（malformed header）時，寫入 `error_log.json`，繼續處理剩餘內容
- F1.7: 計算並報告解析成功率

**邊界條件：**
- 空檔案 → 回傳空 `feature_items[]`，`success: false`
- 非 Markdown 檔案 → 回傳錯誤碼 `E_NOT_MARKDOWN`
- Feature header 格式異常 → 降級為「描述節點」處理，不中斷流程

---

#### F2: 代碼掃描器（scanner.py）

| 項目 | 說明 |
|------|------|
| **輸入** | `implement/` 目錄路徑 |
| **輸出** | 結構化 JSON（含 `modules[]`, `functions[]`, `classes[]`） |
| **掃描方式** | Python AST（`ast` 標準庫） |

**功能點：**

- F2.1: 遞迴掃描 `implement/` 下所有 `.py` 檔案（含 `__init__.py`）
- F2.2: 使用 `ast.parse()` 提取：
  - 模組名（module name from filepath）
  - 類別定義（class name, bases, decorators）
  - 函數定義（function name, parameters, docstring summary）
  - 公開介面（public methods, exported functions）
- F2.3: 忽略 `__pycache__`、`.pyc`、測試檔案（`test_*.py`, `conftest.py`）的干擾
- F2.4: 提取 docstring 首行作為功能描述（簡化）
- F2.5: 檢測 `__all__` 導出列表
- F2.6: 輸出結構化 JSON，含原始行號
- F2.7: **100% 覆蓋率保證**：若有任何 `.py` 檔案未掃描，回傳警告

**邊界條件：**
- syntax error 的 `.py` 檔案 → 跳過該檔，寫入 `scan_error_log.json`
- 空目錄 → 回傳空 `modules[]`
- 非 `.py` 檔案 → 自動忽略

---

#### F3: Gap 檢測器（detector.py）

| 項目 | 說明 |
|------|------|
| **輸入** | `spec_features[]`（來自 parser）+ `code_items[]`（來自 scanner） |
| **輸出** | `gaps[]`：結構化 gap 列表 |
| **比對邏輯** | 見 §3.3 |

**功能點：**

- F3.1: **MISSING 檢測**  
  對每個 SPEC feature，檢查是否有對應的 code item（類別/函數）。若無 → `gap_type: "MISSING"`。

- F3.2: **INCOMPLETE 檢測**  
  對每個 SPEC feature，若有對應 code item 但：
  - 缺少必要參數（params mismatch > 20%）
  - 缺少文件說明（無 docstring）
  → `gap_type: "INCOMPLETE"`。

- F3.3: **ORPHANED 檢測**  
  對每個 code item，檢查是否出現在任何 SPEC feature 中。若無 → `gap_type: "ORPHANED"`。

- F3.4: **相似度比對**  
  使用 Levenshtein distance（ normalised similarity > 0.6）對 feature name 做模糊比對，減少大小寫/底線差異的誤判。

- F3.5: **優先權繼承**  
  若某 feature 有 `Depends on`，所依賴的功能若為 MISSING，被依賴者也標記為 `downstream_missing: true`。

- F3.6: **輸出結構化 gap 列表**，含：
  - `gap_type`: `MISSING` | `INCOMPLETE` | `ORPHANED`
  - `spec_item`: 規格項目名稱
  - `spec_location`: `SPEC.md` 行號
  - `code_item`: 對應代碼項目（若有）
  - `code_location`: 檔案:行號
  - `severity`: `critical` | `major` | `minor`
  - `reason`: 人類可讀描述

**Gap 分類規則：**

```
MISSING:
  severity = critical (若為核心功能) 或 major (若為次要功能)
  
INCOMPLETE:
  severity = major (params 缺失) 或 minor (docstring 缺失)
  
ORPHANED:
  severity = minor (資訊性)
```

---

#### F4: 報告生成器（reporter.py）

| 項目 | 說明 |
|------|------|
| **輸入** | `gaps[]`（來自 detector）+ `spec_features[]` + `code_items[]` |
| **輸出** | `gap_report.json` + `gap_summary.md` |

**功能點：**

- F4.1: 生成 `gap_report.json`（機器可讀格式）
- F4.2: 生成 `gap_summary.md`（人類可讀摘要，含 Markdown 表格）
- F4.3: 統計資訊：
  - 總 gap 數
  - 按類型分布（MISSING/INCOMPLETE/ORPHANED）
  - 按 severity 分布（critical/major/minor）
  - 解析成功率
  - 掃描覆蓋率
  - Gap 檢測準確率
- F4.4: 差異說明（delta description）：每個 gap 的具體偏離內容
- F4.5: 建議行動（recommended_action）：針對每個 gap 給出修復建議
- F4.6: **輸出位置**：預設寫入 `implement/feature-08-gap-detector/reports/`

**報告格式（gap_report.json）：**

```json
{
  "generated_at": "ISO8601 timestamp",
  "spec_file": "SPEC.md path",
  "implement_dir": "implement/ path",
  "summary": {
    "total_gaps": 0,
    "missing": 0,
    "incomplete": 0,
    "orphaned": 0,
    "critical": 0,
    "major": 0,
    "minor": 0,
    "parsing_success_rate": 1.0,
    "scan_coverage_rate": 1.0,
    "gap_detection_accuracy": null
  },
  "gaps": [...]
}
```

**報告格式（gap_summary.md）：**

```markdown
# Gap Summary Report

## Overview
| Metric | Value |
|--------|-------|
| Total Gaps | N |
| MISSING | N |
| INCOMPLETE | N |
| ORPHANED | N |

## Gap Details

### MISSING (Critical/Major)
| Feature | Location | Reason | Recommended Action |
|---------|----------|--------|-------------------|
| ... | ... | ... | ... |

...
```

---

## 3.  詳細規格

### 3.1  SPEC.md 解析規則

SPEC.md 採用以下 Markdown 結構：

```markdown
# Feature #{id}: {Feature Name}

## Overview
{描述}

## 功能列表
### F1: {功能名稱}
**描述：** {簡要描述}
**驗收標準：** {標準1}; {標準2}
**優先權：** {P0/P1/P2}
**依賴：** F{n}, F{n}

### F2: {功能名稱}
...
```

**解析邏輯：**
1. 以 `# Feature #{id}:` 或 `## Feature #{id}:` 識別 feature 區塊
2. 解析 `### F{n}:` 或 `#### F{n}:` 識別功能項目（Feature Item）
3. 正規表示式：`^(#{1,6})\s+F(\d+):\s+(.+)$`
4. 提取 metadata（驗收標準、優先權、依賴）時使用後續行掃描
5. 若連續多行無 header，歸類為描述文本

### 3.2  代碼掃描規則

使用 Python `ast` 標準庫：

```python
import ast

def scan_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        tree = ast.parse(f.read(), filename=filepath)
    # walk tree, extract ClassDef/FunctionDef/Module
```

**掃描對象：**
- `ast.ClassDef` → 類別名、基底類、裝飾器、docstring
- `ast.FunctionDef` / `ast.AsyncFunctionDef` → 函數名、參數、docstring
- `ast.Module` → 模組級導出（`__all__`）

**過濾規則：**
- 以下劃線 `_` 開頭的類別/函數預設為私有，不計入 ORPHANED
- `__init__.py` 中的類別視為模組初始化，不單獨報告

### 3.3  Gap 比對邏輯

```
For each SPEC feature item S:
    1. Normalize S.name → canonical form (lowercase, underscores)
    2. Search code_items for match (exact or fuzzy similarity > 0.6)
    3. If no match → MISSING
    4. If match found:
       a. Check params completeness
       b. Check docstring presence
       c. If incomplete → INCOMPLETE
       d. If complete → mark as COVERED

For each CODE item C:
    1. If C not in any SPEC feature → ORPHANED
```

**模糊比對（Levenshtein）：**
```python
def similarity(a, b):
    a_norm = a.lower().replace('_', '').replace('-', '')
    b_norm = b.lower().replace('_', '').replace('-', '')
    distance = levenshtein(a_norm, b_norm)
    max_len = max(len(a_norm), len(b_norm))
    return 1 - (distance / max_len) if max_len > 0 else 1.0
```

---

## 4.  使用者介面

### 4.1  CLI 命令

```bash
gap-detect --spec SPEC.md --implement implement/ [--output reports/] [--format json|md|both]
```

**參數：**
- `--spec`: SPEC.md 檔案路徑（必要）
- `--implement`: 實作目錄路徑（必要）
- `--output`: 報告輸出目錄（預設：`reports/`）
- `--format`: 輸出格式（預設：`both`）
- `--verbose`: 顯示詳細日誌

### 4.2  整合方式

Agent 可被 `methodology-v2` 框架自動調用，無需手動執行。

---

## 5.  輸出產物

| 檔案 | 位置 | 用途 |
|------|------|------|
| `gap_report.json` | `reports/` | 機器可讀 gap 報告 |
| `gap_summary.md` | `reports/` | 人類可讀摘要 |
| `error_log.json` | `reports/` | 解析錯誤日誌（若有） |
| `scan_error_log.json` | `reports/` | 掃描錯誤日誌（若有） |

---

## 6.  錯誤處理

| 錯誤碼 | 說明 | 處理方式 |
|--------|------|----------|
| `E_NOT_MARKDOWN` | 輸入檔案非 Markdown | 終止，回傳錯誤 |
| `E_FILE_NOT_FOUND` | 檔案/目錄不存在 | 終止，回傳錯誤 |
| `E_PARSE_FAILED` | SPEC.md 解析失敗 | 寫入 error_log，繼續 |
| `E_SCAN_FAILED` | 掃描時遇到 syntax error | 寫入 scan_error_log，繼續 |
| `E_NO_FEATURES` | SPEC.md 中無功能項目 | 回傳警告，gaps = [] |

---

## 7.  已知限制

- **跨語言支援**：目前僅支援 Python（使用 AST）
- **模糊比對閾值**：0.6 的相似度閾值為主觀設定，可能需根據實際使用調整
- **私有成員**：以 `_` 開頭的類別/函數不計入 ORPHANED，可能遺漏某些實作
- **動態生成代碼**：使用 `eval()` / `exec()` 動態生成的符號無法被 AST 掃描

---

## 8.  附錄

### 8.1  術語定義

| 術語 | 定義 |
|------|------|
| Feature Item | SPEC.md 中以 `F{n}:` 標記的功能單元 |
| Code Item | 代碼中實際存在的 class/function 定義 |
| Gap | SPEC 與實際實現之間的偏離 |
| Coverage | 代碼覆蓋規格的比例 |

### 8.2  參考文獻

- Python AST 文件：`https://docs.python.org/3/library/ast.html`
- Levenshtein Distance：標準字串距離演算法
