# Documentation Naming Convention

> methodology-v2 文檔命名標準 v1.0

---

## 🎯 目標

確保 methodology-v2 所有文檔具有一致的命名格式，便於檢索、版本追蹤和自動化處理。

---

## 📁 目錄結構

```
methodology-v2/
├── docs/
│   ├── templates/          # 文檔模板
│   ├── cases/              # 案例研究
│   └── workflows/          # 工作流程圖
├── release_notes/
│   └── RELEASE_NOTES_vX.XX.md
├── templates/
│   └── PROJECT_STRUCTURE.md
├── CHANGELOG.md
└── README.md
```

---

## 📝 文檔類型命名規則

### 1. Release Notes

```
RELEASE_NOTES_v{Major}.{Minor}[_{patch}].md
```

| 版本類型 | 範例 |
|----------|------|
| Major Release | `RELEASE_NOTES_v5.30.md` |
| Patch Release | `RELEASE_NOTES_v5.31_01.md` |

### 2. 文檔模板

```
{TYPE}_TEMPLATE.md
```

| 模板類型 | 檔名 |
|----------|------|
| Software Requirements Specification | `SRS_TEMPLATE.md` |
| Software Architecture Description | `SAD_TEMPLATE.md` |
| Test Plan | `TEST_PLAN_TEMPLATE.md` |
| Quality Report | `QUALITY_REPORT_TEMPLATE.md` |
| Risk Assessment | `RISK_ASSESSMENT_TEMPLATE.md` |

### 3. 專案指南

```
{GUIDE_TYPE}_GUIDE.md
```

| 指南類型 | 檔名 |
|----------|------|
| Getting Started | `GETTING_STARTED.md` |
| User Guide | `USER_GUIDE.md` |
| API Reference | `API_REFERENCE.md` |
| Configuration Guide | `CONFIG_GUIDE.md` |
| Customization Guide | `CUSTOMIZATION_GUIDE.md` |

### 4. 技術規範

```
{TOPIC}_{SPEC_TYPE}.md
```

| 範例 | 檔名 |
|------|------|
| Anti-Shortcut Framework | `ANTI_SHORTCUT_FRAMEWORK.md` |
| TADAD Methodology | `TDAD_METHODOLOGY.md` |
| Fault Tolerance Comparison | `FAULT_TOLERANCE_COMPARISON.md` |

### 5. 案例分析

```
case_{CASE_ID}_{SHORT_DESC}.md
```

| 範例 | 檔名 |
|------|------|
| Customer Service Bot | `case_cs001_customer_service.md` |
| Code Review Agent | `case_cr001_code_review.md` |

---

## 🏷️ 標籤系統

在文檔開頭使用標準標籤：

```markdown
> {標籤1} | {標籤2} | {標籤3}
```

### 常用標籤

| 標籤 | 用途 |
|------|------|
| `vX.XX` | 版本號 |
| `ASPICE` | 符合 ASPICE 標準 |
| `Enterprise` | 企業級功能 |
| `Beginner` | 入門指南 |
| `Advanced` | 高級用法 |
| `Deprecated` | 已廢棄功能 |
| `Breaking` | 重大變更 |

### 範例

```markdown
> v5.35 | ASPICE | Enterprise
```

---

## 📋 版本標註

### CHANGELOG 條目

```
## [{VERSION}] - {DATE}

### Added
- New feature description (#ISSUE)

### Changed
- Modified feature description (#ISSUE)

### Fixed
- Bug fix description (#ISSUE)

### Removed
- Removed feature description (#ISSUE)
```

### 語義化版本

```
{Major}.{Minor}.{Patch}[-{pre-release}][+{build}]
```

| 版本號 | 範例 | 說明 |
|--------|------|------|
| Major | v5.0.0 | 重大架構變更 |
| Minor | v5.1.0 | 新功能向下相容 |
| Patch | v5.1.1 | Bug 修復向下相容 |
| Pre-release | v5.2.0-alpha | 預發布版本 |

---

## 🔢 檔案命名最佳實踐

### ✅ 正確格式

```
RELEASE_NOTES_v5.35.md
SRS_TEMPLATE.md
user_guide_v5.35.md
api_reference.md
case_cs001_customer_service_bot.md
```

### ❌ 錯誤格式

```
release-notes-v5.35.md        # 使用連字符而非底線
Release Notes v5.35.md       # 包含空格
srs.md                       # 過於簡略
UserGuide.md                 # CamelCase 不一致
```

### 命名規則摘要

| 規則 | 說明 |
|------|------|
| 使用底線 `_` | 單字分隔 |
| 全小寫 | 除了 MD, HTML 等副檔名 |
| 版本號前綴 | `v` + 數字格式 |
| 明確描述 | 名稱要能表達內容 |
| 避免縮寫 | 除非眾所皆知 (API, SRS) |

---

## 🔗 自動化處理

文檔命名需支援以下自動化場景：

### 1. 版本檢索

```bash
# 列出所有 Release Notes
ls RELEASE_NOTES_v*.md | sort -V

# 取得最新版本
ls RELEASE_NOTES_v*.md | sort -V | tail -1
```

### 2. 文檔分類

```bash
# 模板
ls docs/templates/*_TEMPLATE.md

# 指南
ls docs/*_GUIDE.md

# 技術規範
ls docs/*_FRAMEWORK.md
ls docs/*_METHODOLOGY.md
```

### 3. Quality Gate 檢查

```python
DOCUMENT_TYPES = {
    "SRS": r"^SRS_TEMPLATE\.md$",
    "SAD": r"^SAD_TEMPLATE\.md$",
    "TEST_PLAN": r"^TEST_PLAN_TEMPLATE\.md$",
    "QUALITY_REPORT": r"^QUALITY_REPORT_TEMPLATE\.md$",
    "RISK_ASSESSMENT": r"^RISK_ASSESSMENT_TEMPLATE\.md$",
}
```

---

## 📦 對應 ASPICE 工作產品

| 文檔類型 | ASPICE 參考 | 檔名範例 |
|----------|-------------|----------|
| Software Requirements Spec | SWE.5 | `SRS_TEMPLATE.md` |
| Software Architecture Desc | SWE.5 | `SAD_TEMPLATE.md` |
| Software Test Plan | SWE.7 | `TEST_PLAN_TEMPLATE.md` |
| Quality Report | SUP.9 | `QUALITY_REPORT_TEMPLATE.md` |
| Risk Assessment | MAN.5 | `RISK_ASSESSMENT_TEMPLATE.md` |

---

*最後更新: 2026-03-24 | methodology-v2 v5.35.0*
