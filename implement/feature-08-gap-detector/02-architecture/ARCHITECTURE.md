# Feature #8: Gap Detection Agent — 架構設計文檔

**版本：** 1.0  
**創建日期：** 2026-04-20  
**狀態：** 已完成（Phase 3-5 已実装）  

---

## 1.  系統概述

### 1.1  架構目標

Gap Detection Agent 的架構設計遵循以下原則：

1. **單一職責（SRP）**：每個模組只負責一件事
2. **依賴注入（DI）**：高層模組不依賴低層模組，兩者皆依賴抽象
3. **資料流導向**：清晰的輸入 → 處理 → 輸出流向
4. **可測試性**：每個模組皆可獨立測試

### 1.2  系統邊界

```
┌─────────────────────────────────────────────────────────────────┐
│                        Gap Detection Agent                      │
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ SPEC.md  │───▶│  Parser  │───▶│ Detector │◀───│  Scanner │  │
│  │ (input)  │    │ (parser) │    │ (detector)│    │ (scanner)│  │
│  └──────────┘    └──────────┘    └────┬─────┘    └──────────┘  │
│                                        │                        │
│                               ┌────────▼────────┐               │
│                               │    Reporter     │               │
│                               │   (reporter)    │               │
│                               └────┬─────┬──────┘               │
│                                    │     │                       │
│                          ┌────────▼──┐ ┌▼──────────────┐       │
│                          │gap_report │ │gap_summary     │       │
│                          │  .json    │ │   .md         │       │
│                          └───────────┘ └────────────────┘       │
│                                                                  │
│  implement/  ──────────────────────────────────────────────────▶│
│  (input)     ──▶ Scanner                                         │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3  模組清單

| 模組 | 檔案 | 職責 |
|------|------|------|
| `Parser` | `parser.py` | 解析 SPEC.md，提取結構化 feature items |
| `Scanner` | `scanner.py` | 掃描 implement/ 目錄，提取 code items |
| `Detector` | `detector.py` | 比對 spec vs code，識別 gaps |
| `Reporter` | `reporter.py` | 生成 gap 報告（JSON + Markdown） |

---

## 2.  模組詳細設計

### 2.1  Parser 模組（parser.py）

**職責：** 將 Markdown 格式的 SPEC.md 轉換為結構化 JSON。

#### 2.1.1  公開 API

```python
class SpecParser:
    def __init__(self, spec_path: str) -> None:
        """
        初始化解析器。
        Args:
            spec_path: SPEC.md 檔案路徑
        """
    
    def parse(self) -> ParsedSpec:
        """
        執行解析。
        Returns:
            ParsedSpec: 含 feature_items[], metadata, parse_stats
        Raises:
            SpecParseError: 不可復原的解析錯誤
        """
    
    def get_error_log(self) -> list[ParseError]:
        """取得解析期間記錄的錯誤"""
```

#### 2.1.2  內部結構

```
SpecParser
├── __init__(spec_path)
├── parse() → ParsedSpec
├── _parse_features() → list[FeatureItem]
├── _parse_metadata() → SpecMetadata
├── _parse_header() → str
└── _normalize_markdown() → str
```

#### 2.1.3  資料結構

```python
@dataclass
class FeatureItem:
    id: str              # "F1", "F2", ...
    name: str            # 功能名稱
    description: str     # 描述文本
    acceptance_criteria: list[str]  # 驗收標準列表
    priority: str         # "P0" | "P1" | "P2"
    depends_on: list[str]  # 依賴的功能 ID
    line_number: int      # 在 SPEC.md 中的行號
    raw_text: str         # 原始 Markdown 文本

@dataclass
class ParsedSpec:
    feature_items: list[FeatureItem]
    metadata: SpecMetadata
    parse_stats: ParseStats

@dataclass
class SpecMetadata:
    title: str
    version: str
    created_date: str

@dataclass
class ParseStats:
    total_lines: int
    parsed_features: int
    parse_success_rate: float
    errors: list[ParseError]
```

#### 2.1.4  解析流程

```
parse()
  │
  ├─▶ _load_file()          載入 SPEC.md
  │       │
  │       ▼
  ├─▶ _normalize_markdown()  標準化 Markdown（如處理 CRLF）
  │       │
  │       ▼
  ├─▶ _parse_header()        解析頂層 header（F# Feature...）
  │       │
  │       ▼
  ├─▶ _parse_features()      識別並解析所有 Feature Item
  │       │   ┌───────────────────────────────┐
  │       │   │ 正規表示式比對：               │
  │       │   │ ^#{1,6}\s+F(\d+):\s+(.+)$     │
  │       │   └───────────────────────────────┘
  │       │
  │       ▼
  └─▶ _parse_metadata()      解析後續 metadata 區塊
          │
          ▼
      return ParsedSpec
```

#### 2.1.5  錯誤處理策略

| 錯誤類型 | 處理方式 |
|----------|----------|
| 檔案不存在 | 拋出 `SpecParseError(code="E_FILE_NOT_FOUND")` |
| 非 Markdown 格式 | 拋出 `SpecParseError(code="E_NOT_MARKDOWN")` |
| Feature header 格式異常 | 降級為描述節點，寫入 error_log，繼續處理 |
| 空檔案 | 回傳 `feature_items=[]`, `success=false` |

---

### 2.2  Scanner 模組（scanner.py）

**職責：** 使用 Python AST 掃描 `implement/` 目錄，提取所有代碼項目。

#### 2.2.1  公開 API

```python
class CodeScanner:
    def __init__(self, implement_dir: str) -> None:
        """
        初始化掃描器。
        Args:
            implement_dir: 實作目錄路徑
        """
    
    def scan(self) -> ScannedCode:
        """
        執行掃描。
        Returns:
            ScannedCode: 含 modules[], functions[], classes[]
        """
    
    def get_scan_error_log(self) -> list[ScanError]:
        """取得掃描期間記錄的錯誤"""
```

#### 2.2.2  內部結構

```
CodeScanner
├── __init__(implement_dir)
├── scan() → ScannedCode
├── _discover_files() → list[str]       發現所有 .py 檔案
├── _scan_file() → CodeFile             掃描單一檔案
├── _extract_from_ast() → CodeFile      AST 遍歷
├── _is_private() → bool               判斷是否私有成員
└── _normalize_docstring() → str        簡化 docstring
```

#### 2.2.3  資料結構

```python
@dataclass
class CodeItem:
    id: str              # 全域唯一 ID (module.item)
    kind: str            # "class" | "function" | "method"
    name: str            # 名稱
    module: str          # 所屬模組
    file_path: str       # 檔案路徑
    line_number: int     # 行號
    docstring: str       # 文件字串（首行）
    params: list[str]    # 參數列表
    is_public: bool      # 是否公開（非 _ 開頭）
    decorators: list[str]  # 裝飾器列表

@dataclass
class CodeFile:
    module_name: str
    file_path: str
    items: list[CodeItem]
    line_count: int

@dataclass
class ScannedCode:
    modules: list[CodeFile]
    scan_stats: ScanStats

@dataclass
class ScanStats:
    total_files: int
    scanned_files: int
    skipped_files: int
    total_items: int
    scan_coverage_rate: float
    errors: list[ScanError]
```

#### 2.2.4  掃描流程

```
scan()
  │
  ├─▶ _discover_files()           找出所有 .py 檔案（遞迴）
  │       │   排除：__pycache__, .pyc, test_*.py, conftest.py
  │       │
  │       ▼
  ├─▶ _scan_file() (for each)    逐檔掃描
  │       │
  │       ├─▶ ast.parse()         解析 AST
  │       │
  │       ├─▶ _extract_from_ast() 遍歷 AST 節點
  │       │       │
  │       │       ├── ClassDef  → CodeItem(kind="class")
  │       │       ├── FunctionDef → CodeItem(kind="function")
  │       │       └── AsyncFunctionDef → CodeItem(kind="function")
  │       │
  │       └─▶ _normalize_docstring()
  │       │
  │       ▼
  └─▶ return ScannedCode(modules=[...], scan_stats=...)
```

#### 2.2.5  AST 遍歷策略

```python
class ASTVisitor(ast.NodeVisitor):
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.items: list[CodeItem] = []
    
    def visit_ClassDef(self, node: ast.ClassDef):
        self.items.append(self._make_code_item(node, "class"))
        self.generic_visit(node)
    
    def visit_FunctionDef(self, node: ast.FunctionDef):
        self.items.append(self._make_code_item(node, "function"))
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef):
        self.items.append(self._make_code_item(node, "function"))
        self.generic_visit(node)
```

---

### 2.3  Detector 模組（detector.py）

**職責：** 對比 SPEC features 與 code items，識別並分類 gaps。

#### 2.3.1  公開 API

```python
class GapDetector:
    def __init__(
        self,
        spec: ParsedSpec,
        code: ScannedCode
    ) -> None:
        """
        初始化檢測器。
        Args:
            spec: Parser 輸出的結構化規格
            code: Scanner 輸出的結構化代碼
        """
    
    def detect(self) -> list[Gap]:
        """
        執行 gap 檢測。
        Returns:
            list[Gap]: Gap 列表
        """
    
    def get_summary(self) -> GapSummary:
        """取得統計摘要"""
```

#### 2.3.2  內部結構

```
GapDetector
├── __init__(spec, code)
├── detect() → list[Gap]
├── _detect_missing() → list[Gap]
├── _detect_incomplete() → list[Gap]
├── _detect_orphaned() → list[Gap]
├── _match_spec_to_code() → list[Match]
├── _compute_similarity() → float
├── _check_params() → bool
├── _check_docstring() → bool
└── _assign_severity() → str
```

#### 2.3.3  資料結構

```python
@dataclass
class Match:
    spec_item: FeatureItem
    code_item: CodeItem | None
    match_type: str      # "exact" | "fuzzy" | "none"
    similarity: float   # 0.0 ~ 1.0

@dataclass
class Gap:
    gap_type: str        # "MISSING" | "INCOMPLETE" | "ORPHANED"
    spec_item: str | None
    code_item: str | None
    spec_location: str | None   # "SPEC.md:Line N"
    code_location: str | None  # "path/to/file.py:Line N"
    severity: str       # "critical" | "major" | "minor"
    reason: str         # 人類可讀描述
    recommended_action: str  # 建議行動
    downstream_missing: bool = False

@dataclass
class GapSummary:
    total_gaps: int
    missing: int
    incomplete: int
    orphaned: int
    critical: int
    major: int
    minor: int
```

#### 2.3.4  檢測流程

```
detect()
  │
  ├─▶ _match_spec_to_code()     建立 SPEC ↔ Code 比對
  │       │
  │       ├─▶ exact match       同名（canonical form 相同）
  │       └─▶ fuzzy match       相似度 > 0.6
  │       │
  │       ▼
  ├─▶ _detect_missing()         對無 match 的 spec 標記 MISSING
  │       │
  ├─▶ _detect_incomplete()      對 partial match 標記 INCOMPLETE
  │       │   ├─▶ _check_params()      參數完整性
  │       │   └─▶ _check_docstring()   文件存在性
  │       │
  ├─▶ _detect_orphaned()        對無對應 spec 的 code 標記 ORPHANED
  │       │
  └─▶ _assign_severity()        根據 gap 類型賦予 severity
          │
          ▼
      return list[Gap]
```

#### 2.3.5  相似度計算

```python
def _compute_similarity(name_a: str, name_b: str) -> float:
    """
    計算兩個名稱的正規化 Levenshtein 相似度。
    1. 轉小寫
    2. 移除底線和連字符
    3. 計算 Levenshtein distance
    4. 回傳 1 - (distance / max_len)
    """
    a_norm = name_a.lower().replace('_', '').replace('-', '')
    b_norm = name_b.lower().replace('_', '').replace('-', '')
    if not a_norm and not b_norm:
        return 1.0
    distance = levenshtein(a_norm, b_norm)
    max_len = max(len(a_norm), len(b_norm))
    return 1 - (distance / max_len)
```

---

### 2.4  Reporter 模組（reporter.py）

**職責：** 將 Gap 列表轉換為結構化報告（JSON + Markdown）。

#### 2.4.1  公開 API

```python
class GapReporter:
    def __init__(
        self,
        gaps: list[Gap],
        spec: ParsedSpec,
        code: ScannedCode,
        output_dir: str = "reports/"
    ) -> None:
        """
        初始化報告生成器。
        Args:
            gaps: Gap 列表
            spec: ParsedSpec
            code: ScannedCode
            output_dir: 報告輸出目錄
        """
    
    def generate(self) -> ReportPaths:
        """
        生成報告。
        Returns:
            ReportPaths: 生成的檔案路徑
        """
```

#### 2.4.2  內部結構

```
GapReporter
├── __init__(gaps, spec, code, output_dir)
├── generate() → ReportPaths
├── _generate_json() → str
├── _generate_markdown() → str
├── _compute_summary() → GapSummary
├── _format_gap_detail() → str
└── _format_recommendation() → str
```

#### 2.4.3  資料結構

```python
@dataclass
class ReportPaths:
    json_path: str
    md_path: str

@dataclass
class GapReportJSON:
    generated_at: str
    spec_file: str
    implement_dir: str
    summary: GapSummary
    gaps: list[Gap]
    spec_features_count: int
    code_items_count: int
```

#### 2.4.4  生成流程

```
generate()
  │
  ├─▶ _compute_summary()         計算統計摘要
  │       │
  ├─▶ _generate_json()           生成 gap_report.json
  │       │   └─▶ JSON.dump()
  │       │
  ├─▶ _generate_markdown()      生成 gap_summary.md
  │       │   ├─▶ Overview 表格
  │       │   ├─▶ Gap Details 表格（按類型分組）
  │       │   └─▶ Recommended Actions
  │       │
  └─▶ return ReportPaths(json_path, md_path)
```

---

## 3.  資料流

### 3.1  完整資料流

```
[SPEC.md]              [implement/]
     │                      │
     ▼                      ▼
[Parser]            [Scanner]
     │                      │
     ▼                      ▼
[ParsedSpec]        [ScannedCode]
     │                      │
     └──────────┬───────────┘
                ▼
           [Detector]
                │
                ▼
           [list[Gap]]
                │
                ▼
           [Reporter]
                │
        ┌───────┴───────┐
        ▼               ▼
 [gap_report.json] [gap_summary.md]
```

### 3.2  錯誤資料流

```
[Parser Error]  ──▶ error_log.json ──▶ 繼續處理
[Scanner Error] ──▶ scan_error_log.json ──▶ 繼續處理
[Critical Error] ──▶ 終止，回傳錯誤碼
```

---

## 4.  依賴關係

### 4.1  模組依賴圖

```
         ┌─────────┐
         │ Parser  │
         └────┬────┘
              │
              ▼
         ┌─────────┐
         │Detector │◀──┌─────────┐
         └────┬────┘    │ Scanner │
              │         └────┬────┘
              │              │
              ▼              ▼
         ┌─────────┐
         │Reporter │
         └─────────┘
```

### 4.2  外部依賴

| 依賴 | 版本 | 用途 |
|------|------|------|
| Python | ≥ 3.10 | 運行環境 |
| `ast` | 標準庫 | Python AST 解析 |
| `json` | 標準庫 | JSON 序列化 |
| `pathlib` | 標準庫 | 路徑操作 |
| `Levenshtein` | ≥ 0.20 | 字串相似度計算（可選，純 Python fallback） |

---

## 5.  擴展點

### 5.1  新增 Gap 類型

如需新增 Gap 類型（例如 `RENAMED`），修改流程：

1. 在 `detector.py` 的 `Gap` dataclass 新增 `gap_type` 取值
2. 在 `_detect_*()` 新增對應方法
3. 在 `reporter.py` 新增對應的 Markdown 格式化邏輯
4. 在 `test_detector.py` 新增對應測試案例

### 5.2  新增語言支援

目前僅支援 Python。如需支援其他語言：

1. 新增 `scanner_{lang}.py`（如 `scanner_js.py`）
2. 新增對應的 `CodeItem` dataclass
3. 在 `detector.py` 新增語言特定比對邏輯
4. 在 `reporter.py` 新增語言標註

### 5.3  自訂比對規則

相似度閾值 `0.6` 可外部化為設定參數：

```python
class GapDetector:
    def __init__(
        self,
        spec: ParsedSpec,
        code: ScannedCode,
        similarity_threshold: float = 0.6
    ) -> None:
```

---

## 6.  安全性考量

| 考量點 | 說明 | 緩解措施 |
|--------|------|----------|
| 路徑遍歷 | `implement_dir` 可能含符號連結導致目錄外掃描 | 在 `_discover_files()` 中 validate path |
| 大檔案掃描 | 超過 10MB 的 `.py` 檔案可能導致記憶體問題 | 在 `scanner.py` 中設定單檔大小上限 |
| 循環引用 | SPEC feature 間的 `Depends on` 造成循環 | 在 `_detect_missing()` 中做 DAG 檢測 |

---

## 7.  效能考量

| 優化點 | 目標 |
|--------|------|
| 掃描 1000 個 `.py` 檔案 | < 10 秒 |
| SPEC.md 解析（含 500 個 Feature） | < 2 秒 |
| Gap 檢測 | < 1 秒 |
| 報告生成 | < 0.5 秒 |
| 記憶體使用峰值 | < 500 MB |

**優化策略：**
- Scanner 使用多執行緒（ThreadPoolExecutor）並列掃描
- Levenshtein 計算使用 C extension（python-Levenshtein）
- JSON 生成使用 `orjson`（若可用）

---

## 8.  附錄

### 8.1  類圖（UML-like）

```
┌─────────────────────┐
│      SpecParser     │
├─────────────────────┤
│ - spec_path: str    │
│ - _errors: list     │
├─────────────────────┤
│ + parse(): ParsedSpec │
│ + get_error_log()  │
└─────────────────────┘
         │
         │ produces
         ▼
┌─────────────────────┐
│     ParsedSpec       │
├─────────────────────┤
│ feature_items[]      │
│ metadata             │
│ parse_stats          │
└─────────────────────┘

┌─────────────────────┐
│     CodeScanner      │
├─────────────────────┤
│ - implement_dir: str │
│ - _errors: list      │
├─────────────────────┤
│ + scan(): ScannedCode│
│ + get_scan_error_log│
└─────────────────────┘
         │
         │ produces
         ▼
┌─────────────────────┐
│     ScannedCode      │
├─────────────────────┤
│ modules[]            │
│ scan_stats           │
└─────────────────────┘

┌─────────────────────┐
│     GapDetector      │
├─────────────────────┤
│ - spec: ParsedSpec   │
│ - code: ScannedCode  │
├─────────────────────┤
│ + detect(): list[Gap]│
│ + get_summary()     │
└─────────────────────┘
         │
         │ produces
         ▼
┌─────────────────────┐
│        Gap          │
├─────────────────────┤
│ gap_type: str       │
│ spec_item: str      │
│ code_item: str      │
│ severity: str      │
│ reason: str         │
└─────────────────────┘

┌─────────────────────┐
│    GapReporter      │
├─────────────────────┤
│ - gaps: list[Gap]   │
│ - spec: ParsedSpec  │
│ - code: ScannedCode │
├─────────────────────┤
│ + generate(): ReportPaths│
└─────────────────────┘
```

### 8.2  異常類層級

```
SpecParseError (Exception)
├── E_FILE_NOT_FOUND
├── E_NOT_MARKDOWN
└── E_PARSE_FAILED

ScanError (Exception)
├── E_FILE_NOT_FOUND
└── E_SCAN_FAILED

GapDetectionError (Exception)
└── E_NO_FEATURES
```
