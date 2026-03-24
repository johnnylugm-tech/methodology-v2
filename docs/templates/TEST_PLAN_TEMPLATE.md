# Software Test Plan

> 軟體測試計畫模板 - 符合 ASPICE SWE.7

---

## 📋 Document Information

| 項目 | 內容 |
|------|------|
| **專案名稱** | [Project Name] |
| **版本** | v1.0 |
| **作者** | [Author] |
| **日期** | YYYY-MM-DD |
| **相關 SRS 版本** | v[X.X] |
| **相關 SAD 版本** | v[X.X] |
| **狀態** | Draft / Review / Approved |

---

## 1. 介紹 (Introduction)

### 1.1 目的 (Purpose)

本文檔定義 [系統名稱] 的軟體測試策略、測試範圍、測試環境與資源安排。本文件作為測試團隊的執行指南，確保軟體品質符合 SRS 與 SAD 的要求。

### 1.2 範圍 (Scope)

本文檔涵蓋：
- 單元測試 (Unit Testing)
- 整合測試 (Integration Testing)
- 系統測試 (System Testing)
- 驗收測試 (Acceptance Testing)
- 效能測試 (Performance Testing)
- 安全測試 (Security Testing)

### 1.3 測試目標 (Test Objectives)

| 目標 | 說明 | 指標 |
|------|------|------|
| 功能覆蓋 | 所有 FR 都有對應測試 | Coverage > 95% |
| 缺陷發現 | 及早發現並修復缺陷 | Bug Escape < 5% |
| 品質保證 | 確保上線品質 | Pass Rate > 95% |
| 風險控制 | 降低上線風險 | Critical Bug = 0 |

---

## 2. 測試策略 (Test Strategy)

### 2.1 測試類型

| 測試類型 | 層級 | 執行時機 | 負責人 |
|----------|------|----------|--------|
| 單元測試 | Component | 每次 Commit | Developer |
| 整合測試 | Integration | Daily Build | QA Team |
| 系統測試 | System | Release Candidate | QA Team |
| 驗收測試 | Acceptance | UAT | Stakeholder |
| 效能測試 | System | Pre-release | Performance Team |
| 安全測試 | System | Pre-release | Security Team |

### 2.2 測試方法

```
┌─────────────────────────────────────────────────────────────────┐
│                      Test Pyramid                                │
└─────────────────────────────────────────────────────────────────┘

                        ┌─────────┐
                        │  E2E    │  ← Few, Slow, Expensive
                        │  Tests  │
                      ┌─┴─────────┴─┐
                      │ Integration │  ← More, Faster
                      │   Tests    │
                    ┌─┴─────────────┴─┐
                    │    Unit Tests   │  ← Many, Fast, Cheap
                    └─────────────────┘
```

### 2.3 進入/退出標準

#### 進入標準 (Entry Criteria)

- [ ] SRS 已批准
- [ ] 測試環境就緒
- [ ] 測試案例已完成 Review
- [ ] 相關模組已開發完成

#### 退出標準 (Exit Criteria)

- [ ] 測試案例執行率 > 95%
- [ ] 測試通過率 > 95%
- [ ] Critical/High 缺陷數 = 0
- [ ] Medium 缺陷數 < 5
- [ ] 測試報告已發布

---

## 3. 測試範圍 (Test Scope)

### 3.1 功能測試範圍

| ID | 功能模組 | FR 參考 | 測試類型 | 優先級 |
|----|----------|---------|----------|--------|
| FTM-001 | Agent Manager | FR-001 ~ FR-005 | Unit + Integration | P0 |
| FTM-002 | Workflow Engine | FR-006 ~ FR-010 | Unit + Integration | P0 |
| FTM-003 | Quality Gate | FR-011 ~ FR-015 | Unit + Integration | P1 |
| FTM-004 | Delivery Manager | FR-016 ~ FR-020 | Integration | P1 |

### 3.2 非功能測試範圍

| 測試類型 | 測試項目 | 目標指標 | 優先級 |
|----------|----------|----------|--------|
| 效能測試 | 回應時間 | p95 < 200ms | P0 |
| 效能測試 | 吞吐量 | > 1000 TPS | P0 |
| 效能測試 | 並發支援 | > 500 concurrent | P1 |
| 安全測試 | 滲透測試 | OWASP Top 10 | P0 |
| 安全測試 | 漏洞掃描 | 無 High/Critical | P0 |
| 可用性測試 | Failover | < 30 秒恢復 | P1 |

---

## 4. 測試環境 (Test Environment)

### 4.1 環境架構

```
┌─────────────────────────────────────────────────────────────────┐
│                     Test Environment                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐     ┌──────────────┐     ┌──────────────┐  │
│   │   Dev Env    │     │   Test Env   │     │   Staging    │  │
│   │  (Local)     │     │   (QA)       │     │   (Pre-prod) │  │
│   └──────────────┘     └──────────────┘     └──────────────┘  │
│         │                    │                    │             │
│         └────────────────────┼────────────────────┘             │
│                              │                                  │
│                              ▼                                  │
│                    ┌──────────────────┐                       │
│                    │   Test Database  │                       │
│                    │   (PostgreSQL)   │                       │
│                    └──────────────────┘                       │
└─────────────────────────────────────────────────────────────────┘
```

### 4.2 環境配置

| 環境 | 主機規格 | 用途 |
|------|----------|------|
| Dev | 4 Core / 8GB RAM | 開發測試 |
| Test | 8 Core / 16GB RAM | QA 測試 |
| Staging | 16 Core / 32GB RAM | UAT / 效能測試 |

### 4.3 測試工具

| 工具類型 | 工具名稱 | 版本 | 用途 |
|----------|----------|------|------|
| Unit Test | pytest | 7.x | 單元測試 |
| Mock | pytest-mock | 3.x | 模擬物件 |
| Coverage | pytest-cov | 4.x | 覆蓋率 |
| API Test | requests | 2.x | API 測試 |
| Performance | locust | 2.x | 負載測試 |
| Security | OWASP ZAP | 3.x | 安全掃描 |

---

## 5. 測試案例 (Test Cases)

### 5.1 功能測試案例

#### TC-001: Agent 建立測試

| 項目 | 內容 |
|------|------|
| **ID** | TC-001 |
| **模組** | Agent Manager |
| **FR 參考** | FR-001 |
| **描述** | 驗證可以成功建立新 Agent |
| **前置條件** | 1. 系統正常運作<br>2. 使用者已登入 |
| **測試步驟** | 1. 發送 POST `/api/v1/agents`<br>2. 攜帶正確參數<br>3. 驗證回傳 201 |
| **預期結果** | 1. 回傳 201 Created<br>2. 回傳 Agent 物件<br>3. ID 已產生 |
| **優先級** | P0 |
| **狀態** | [Ready] |

#### TC-002: Agent 列表查詢測試

| 項目 | 內容 |
|------|------|
| **ID** | TC-002 |
| **模組** | Agent Manager |
| **FR 參考** | FR-002 |
| **描述** | 驗證可以查詢 Agent 列表 |
| **前置條件** | 系統中有至少 1 個 Agent |
| **測試步驟** | 1. 發送 GET `/api/v1/agents`<br>2. 驗證回傳 200 |
| **預期結果** | 1. 回傳 200 OK<br>2. 回傳陣列<br>3. 包含分頁資訊 |
| **優先級** | P0 |
| **狀態** | [Ready] |

### 5.2 效能測試案例

#### TC-PERF-001: API 回應時間測試

| 項目 | 內容 |
|------|------|
| **ID** | TC-PERF-001 |
| **場景** | 100 concurrent users, 持續 5 分鐘 |
| **目標** | p95 < 200ms |
| **Script** | `perf_api_response.py` |

#### TC-PERF-002: 負載測試

| 項目 | 內容 |
|------|------|
| **ID** | TC-PERF-002 |
| **場景** | 逐漸增加負載至 2000 TPS |
| **目標** | 系統不崩潰，保持穩定 |
| **Script** | `perf_load_test.py` |

### 5.3 安全測試案例

#### TC-SEC-001: SQL Injection 測試

| 項目 | 內容 |
|------|------|
| **ID** | TC-SEC-001 |
| **測試點** | 所有輸入欄位 |
| **方法** | 注入 SQL 惡意字串 |
| **預期** | 請求被阻擋或參數化查詢 |

#### TC-SEC-002: XSS 測試

| 項目 | 內容 |
|------|------|
| **ID** | TC-SEC-002 |
| **測試點** | 輸出顯示欄位 |
| **方法** | 注入 `<script>alert(1)</script>` |
| **預期** | 腳本被編碼或移除 |

---

## 6. 測試排程 (Test Schedule)

### 6.1 里程碑

| 階段 | 日期 | 交付物 |
|------|------|--------|
| Unit Test Complete | Week 2 | 測試報告 |
| Integration Test Complete | Week 4 | 測試報告 |
| System Test Complete | Week 6 | 測試報告 |
| UAT Complete | Week 8 | UAT 報告 |
| Release | Week 9 | Release Note |

### 6.2 每日進度追蹤

| 日期 | 執行數 | 通過數 | 失敗數 | 阻塞數 |
|------|--------|--------|--------|--------|
| YYYY-MM-DD | 50 | 45 | 3 | 2 |

---

## 7. 風險與緩解 (Risk Management)

| 風險 | 影響 | 可能性 | 緩解措施 |
|------|------|--------|----------|
| 測試環境不穩定 | High | Medium | 預備環境 |
| 進度延遲 | High | High | 加班 / 增援 |
| 缺陷數過多 | Medium | Medium | 增加測試覆蓋 |
| 第三方系統延遲 | Medium | Low | Mock 服務 |

---

## 8. 附件 (Attachments)

### A. 測試工具配置

```python
# conftest.py
import pytest

@pytest.fixture
def mock_agent():
    return {
        "name": "Test Agent",
        "role": "developer",
        "model": "gpt-4"
    }
```

### B. CI/CD 整合

```yaml
# .gitlab-ci.yml
test:
  script:
    - pytest --cov=. --cov-report=xml
  coverage: '/TOTAL.*\s+(\d+%)$/'
```

---

## ✅ Test Plan Review Checklist

- [ ] 測試策略完整定義
- [ ] 測試範圍涵蓋所有 FR
- [ ] 非功能測試項目齊全
- [ ] 測試環境配置妥當
- [ ] 測試案例已 Review
- [ ] 進入/退出標準明確
- [ ] 排程合理可行
- [ ] 風險已識別並有緩解措施

---

*Template Version: 1.0 | Based on IEEE 829 & ASPICE SWE.7*
