# Feature #8: Gap Detection Agent — 部署指南

**版本：** 1.0  
**創建日期：** 2026-04-20  
**狀態：** 已完成  

---

## 1.  部署概覽

### 1.1  部署目標

本指南說明如何將 Gap Detection Agent 部署至目標環境，包含：
- 本地開發環境
- CI/CD 整合
- 框架自動調用

### 1.2  系統需求

| 項目 | 需求 |
|------|------|
| Python 版本 | ≥ 3.10 |
| 作業系統 | macOS / Linux / Windows (WSL) |
| 記憶體 | ≥ 512 MB |
| 磁碟空間 | ≥ 50 MB |

### 1.3  部署模式

| 模式 | 說明 | 適用場景 |
|------|------|----------|
| **CLI 模式** | 直接執行 `gap-detect` 命令 | 本地開發、快速驗證 |
| **框架整合模式** | 被 methodology-v2 框架調用 | 自動化品質把關 |
| ** Library 模式** | 作為 Python 套件被 import | 自訂整合 |

---

## 2.  本地開發環境部署

### 2.1  前置需求

```bash
# 確認 Python 版本
python3 --version  # 需 ≥ 3.10

# 確認 pip 可用
pip3 --version
```

### 2.2  安裝步驟

#### 2.2.1  方式一：直接複製（推薦用於框架整合）

```bash
# 導出 Gap Detection Agent 為 tarball
cd /Users/johnny/.openclaw/workspace-musk/projects/methodology-v2/implement
tar -czvf feature-08-gap-detector.tar.gz feature-08-gap-detector/

# 在目標機器解壓
tar -xzvf feature-08-gap-detector.tar.gz -C /path/to/target/
```

#### 2.2.2  方式二：pip 安裝（尚未發布至 PyPI）

```bash
# 從本地目錄安裝（開發中）
cd /Users/johnny/.openclaw/workspace-musk/projects/methodology-v2/implement/feature-08-gap-detector
pip install -e .
```

#### 2.2.3  方式三：作為 methodology-v2 子模組

```bash
cd /path/to/methodology-v2
ln -s /path/to/feature-08-gap-detector implement/feature-08-gap-detector
```

### 2.3  驗證安裝

```bash
# 方法一：檢查 CLI 可用性（需先配置）
gap-detect --version
# 預期輸出：gap-detect 1.0.0

# 方法二：檢查 Python 模組可導入
python3 -c "from gap_detector import SpecParser, CodeScanner, GapDetector, GapReporter; print('OK')"
# 預期輸出：OK
```

### 2.4  目錄結構

```
feature-08-gap-detector/
├── 01-spec/
│   └── SPEC.md                    # 功能規格
├── 02-architecture/
│   └── ARCHITECTURE.md           # 架構設計
├── 03-implement/
│   └── gap_detector/
│       ├── __init__.py
│       ├── parser.py             # SPEC 解析器
│       ├── scanner.py            # 代碼掃描器
│       ├── detector.py           # Gap 檢測器
│       └── reporter.py           # 報告生成器
├── 04-tests/
│   ├── conftest.py
│   ├── test_parser.py
│   ├── test_scanner.py
│   ├── test_detector.py
│   └── __init__.py
├── 06-quality/
│   └── DELIVERY_REPORT.md
├── 07-risk/
│   └── RISK_REGISTER.md
└── 08-deploy/
    └── DEPLOYMENT.md             # 本檔案
```

---

## 3.  CLI 使用指南

### 3.1  基本用法

```bash
gap-detect --spec SPEC.md --implement implement/
```

### 3.2  完整參數

| 參數 | 縮寫 | 必要 | 說明 |
|------|------|------|------|
| `--spec` | `-s` | ✅ | SPEC.md 檔案路徑 |
| `--implement` | `-i` | ✅ | 實作目錄路徑 |
| `--output` | `-o` | ❌ | 報告輸出目錄（預設：`reports/`） |
| `--format` | `-f` | ❌ | 輸出格式：`json`、`md`、`both`（預設：`both`） |
| `--verbose` | `-v` | ❌ | 顯示詳細日誌 |
| `--min-severity` | — | ❌ | 最小顯示 severity：`critical`、`major`、`minor` |
| `--similarity-threshold` | — | ❌ | 模糊比對相似度閾值（預設：`0.6`） |
| `--version` | — | ❌ | 顯示版本資訊 |

### 3.3  使用範例

**範例 1：基本執行**

```bash
gap-detect --spec SPEC.md --implement implement/
```

**範例 2：僅輸出 JSON，指定輸出目錄**

```bash
gap-detect --spec SPEC.md --implement implement/ --output ./gap-reports --format json
```

**範例 3：僅顯示 critical gaps**

```bash
gap-detect --spec SPEC.md --implement implement/ --min-severity critical
```

**範例 4：自訂相似度閾值**

```bash
gap-detect --spec SPEC.md --implement implement/ --similarity-threshold 0.7
```

**範例 5：詳細日誌模式**

```bash
gap-detect --spec SPEC.md --implement implement/ --verbose
```

### 3.4  輸出檔案

執行完成後，在 `--output` 目錄中生成：

```
reports/
├── gap_report.json      # 機器可讀格式
├── gap_summary.md       # 人類可讀摘要
├── error_log.json       # 解析錯誤日誌（若有）
└── scan_error_log.json # 掃描錯誤日誌（若有）
```

### 3.5  退出碼

| 退出碼 | 說明 |
|--------|------|
| 0 | 執行成功（可能有 gaps） |
| 1 | 一般錯誤（檔案不存在、參數錯誤等） |
| 2 | 嚴重錯誤（解析失敗、掃描失敗等） |
| 3 | 找不到任何 Feature Item |

---

## 4.  框架整合（methodology-v2）

### 4.1  自動調用機制

methodology-v2 框架可在以下時機自動調用 Gap Detection Agent：

| 時機 | 觸發條件 |
|------|----------|
| **Phase Check** | 每個 Feature 完成後，自動比對 SPEC vs 實作 |
| **Pre-Merge** | Pull Request 合併前，確保無 MISSING gaps |
| **Scheduled** | 每日定時執行，監控規格漂移 |

### 4.2  整合配置

在 `methodology-v2` 根目錄的配置檔中新增：

```yaml
# methodology-v2.yaml
gap_detection:
  enabled: true
  spec_path: SPEC.md
  implement_dir: implement/
  output_dir: reports/gap-detection/
  block_on_missing: true    # 若有 MISSING gaps，阻擋合併
  min_severity_to_block: critical  # blocking 等級
```

### 4.3  框架鉤子（Hooks）

Gap Detection Agent 提供以下鉤子供框架調用：

```python
from gap_detector import GapDetector, ParsedSpec, ScannedCode

def on_phase_complete(phase_id: str, spec: ParsedSpec, code: ScannedCode):
    """每個 Phase 完成後自動調用"""
    detector = GapDetector(spec, code)
    gaps = detector.detect()
    
    # 若有 critical gaps，阻擋合併
    critical_gaps = [g for g in gaps if g.severity == "critical"]
    if critical_gaps:
        raise BlockMergeError(f"Found {len(critical_gaps)} critical gaps")
```

---

## 5.  CI/CD 整合

### 5.1  GitHub Actions

```yaml
# .github/workflows/gap-detection.yml
name: Gap Detection

on:
  pull_request:
    paths:
      - 'implement/**'
      - 'SPEC.md'

jobs:
  gap-detection:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install Gap Detection Agent
        run: |
          pip install gap-detection-agent  # 尚未發布，可替換為本地路徑
      
      - name: Run Gap Detection
        run: |
          gap-detect --spec SPEC.md --implement implement/ --output reports/
      
      - name: Upload Reports
        uses: actions/upload-artifact@v4
        with:
          name: gap-report
          path: reports/
      
      - name: Block on Critical Gaps
        if: always()
        run: |
          if grep -q '"severity": "critical"' reports/gap_report.json; then
            echo "Found critical gaps. Blocking merge."
            exit 1
          fi
```

### 5.2  GitLab CI

```yaml
# .gitlab-ci.yml
gap_detection:
  stage: test
  script:
    - pip install gap-detection-agent
    - gap-detect --spec SPEC.md --implement implement/ --output reports/
  artifacts:
    paths:
      - reports/
    expire_in: 1 week
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
```

### 5.3  Jenkins

```groovy
// Jenkinsfile
pipeline {
    agent any
    stages {
        stage('Gap Detection') {
            steps {
                sh '''
                    pip install gap-detection-agent
                    gap-detect --spec SPEC.md --implement implement/ --output reports/
                '''
            }
            post {
                always {
                    archive 'reports/**'
                }
            }
        }
    }
}
```

---

## 6.  Library 模式使用

### 6.1  基本用法

```python
from gap_detector import SpecParser, CodeScanner, GapDetector, GapReporter

# 1. 解析 SPEC
parser = SpecParser("SPEC.md")
spec = parser.parse()

# 2. 掃描代碼
scanner = CodeScanner("implement/")
code = scanner.scan()

# 3. 檢測 gaps
detector = GapDetector(spec, code)
gaps = detector.detect()

# 4. 生成報告
reporter = GapReporter(gaps, spec, code, output_dir="reports/")
paths = reporter.generate()

print(f"Report generated: {paths.json_path}")
```

### 6.2  自訂配置

```python
from gap_detector import GapDetector

detector = GapDetector(
    spec=spec,
    code=code,
    similarity_threshold=0.7  # 自訂相似度閾值
)
gaps = detector.detect()
```

### 6.3  錯誤處理

```python
from gap_detector import SpecParseError, ScanError, GapDetectionError

try:
    parser = SpecParser("SPEC.md")
    spec = parser.parse()
except SpecParseError as e:
    print(f"SPEC parse error: {e.code}")
    raise

try:
    scanner = CodeScanner("implement/")
    code = scanner.scan()
except ScanError as e:
    print(f"Scan error: {e.code}")
    raise
```

---

## 7.  卸載

### 7.1  pip 安裝卸載

```bash
pip uninstall gap-detection-agent
```

### 7.2  框架整合移除

```bash
# 移除符號連結
rm implement/feature-08-gap-detector

# 移除設定
# 從 methodology-v2.yaml 中移除 gap_detection 區塊
```

---

## 8.  故障排除

### 8.1  常見問題

| 問題 | 可能原因 | 解決方案 |
|------|----------|----------|
| `ModuleNotFoundError: No module named 'gap_detector'` | 未正確安裝 | 確認 pip install 或 PYTHONPATH |
| `E_FILE_NOT_FOUND` | 路徑錯誤 | 使用絕對路徑或相對路徑確認 |
| `E_SCAN_FAILED` | 有語法錯誤的 .py 檔案 | 檢查 scan_error_log.json |
| `gap_report.json` 為空 | 無 Feature Items | 確認 SPEC.md 格式正確 |

### 8.2  除錯模式

```bash
# 顯示完整錯誤堆疊
gap-detect --spec SPEC.md --implement implement/ --verbose 2>&1
```

### 8.3  日誌位置

| 日誌類型 | 位置 |
|----------|------|
| 解析錯誤 | `reports/error_log.json` |
| 掃描錯誤 | `reports/scan_error_log.json` |
| 詳細日誌 | stdout（`--verbose` 時） |

---

## 9.  版本相容性

| Agent 版本 | Python 版本 | 備註 |
|------------|-------------|------|
| 1.0.x | ≥ 3.10 | 初始版本 |
| 1.1.x（規劃中）| ≥ 3.10 | 新增多語言支援 |

---

## 10.  聯絡與支援

| 項目 | 說明 |
|------|------|
| **問題回報** | 請提交 Issue 至專案仓库 |
| **文件更新** | 請同步更新 SPEC.md |
| **版本更新日誌** | 請參考 CHANGELOG.md |
