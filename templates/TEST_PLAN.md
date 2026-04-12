# TEST_PLAN.md - {專案名稱}

> 本檔案為 On-demand Lazy Load 模板，僅在需要產生此文件時載入。
> 來自：SKILL_TEMPLATES.md §T4.1

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

---

## 6. Test Block（機器可讀格式）

<!-- TEST:START -->
```json
{
  "version": "1.0",
  "created_at": "{YYYY-MM-DD}",
  "phase": 4,
  "project": "{專案名}",
  "test_cases": [
    {
      "id": "TC-01",
      "type": "unit|integration|e2e",
      "description": "{描述}",
      "expected_result": "{預期結果}",
      "fr_coverage": ["FR-01", "FR-02"]
    }
  ],
  "test_strategy": {
    "unit_coverage_target": 80,
    "branch_coverage_target": 70,
    "integration_coverage_target": 60
  }
}
```
<!-- TEST:END -->

**說明**：請填寫上方的 JSON 結構，這用於測試覆蓋率追蹤。
