# SRS - {專案名稱}

> 本檔案為 On-demand Lazy Load 模板，僅在需要產生此文件時載入。
> 來自：SKILL_TEMPLATES.md §T1.1

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

---

## 6. FR Block（機器可讀格式）

<!-- FR:START -->
```json
{
  "version": "1.0",
  "created_at": "{YYYY-MM-DD}",
  "phase": 1,
  "project": "{專案名}",
  "functional_requirements": [
    {
      "id": "FR-01",
      "description": "{需求描述}",
      "implementation_functions": ["{函數名}"],
      "verification_method": "{驗證方法}"
    }
  ],
  "non_functional_requirements": [
    {
      "id": "NFR-01",
      "type": "performance|security|reliability|maintainability",
      "description": "{需求描述}",
      "test_method": "{測試方法}"
    }
  ]
}
```
<!-- FR:END -->

**說明**：請填寫上方的 JSON 結構，這用於後續需求可追溯性追蹤。
