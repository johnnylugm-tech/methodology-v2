# Constitution - 團隊憲章

> 本文件定義團隊的不可變原則。所有專案必須遵守這些規則。

---

## 1. 核心價值觀

### 1.1 品質優先

```
品質 > 速度 > 功能
```

- 任何新功能必須通過 Quality Gate 才能合併
- 測試覆蓋率必須 >= 80%
- 安全掃描必須通過

### 1.2 可維護性

```
代碼是給人看的，其次是給機器跑的
```

- 所有公開 API 必須有 docstring
- 函數長度 <= 50 行
- Cyclomatic complexity <= 10

### 1.3 可追溯性

```
每個需求都可以追溯到實作，每個實作都可以追溯到驗證
```

- 所有任務必須有 ID
- 所有變更必須有 commit message
- 所有驗證必須有記錄

---

## 2. 技術原則

### 2.1 架構決策

| 原則 | 說明 |
|------|------|
| 單一職責 | 每個模組只做一件事 |
| 依賴注入 | 使用接口而非具體實現 |
| 配置分離 | 敏感資訊不放進代碼 |

### 2.2 錯誤處理

| 等級 | 定義 | 處理方式 |
|------|------|----------|
| L1 | 配置錯誤 | 不允許啟動 |
| L2 | API 錯誤 | 重試 + 回退 |
| L3 | 業務邏輯錯誤 | 記錄 + 降級 |
| L4 | 預期異常 | 記錄 + 忽略 |

### 2.3 日誌規範

```
[LEVEL] [TIMESTAMP] [MODULE] message
```

- DEBUG: 開發調試
- INFO: 正常流程
- WARNING: 異常但可處理
- ERROR: 需要關注的錯誤

---

## 3. 品質標準

### 3.1 Quality Gate 閾值

| 維度 | 閾值 | 權重 |
|------|------|------|
| 正確性 | >= 80% | 30% |
| 安全性 | >= 100% | 25% |
| 可維護性 | >= 70% | 20% |
| 效能 | >= 80% | 15% |
| 覆蓋率 | >= 80% | 10% |

### 3.2 審批規則

| 變更類型 | 審批者 | 必須通過 |
|----------|--------|----------|
| 新功能 | Tech Lead | Quality Gate |
| Bug 修復 | 同儕 | Unit Test |
| 重構 | 同儕 | Code Review |
| 文檔 | 自動化 | Linter |

---

## 4. 命名規範

### 4.1 代碼

| 類型 | 規則 | 範例 |
|------|------|------|
| 變數 | snake_case | `user_name` |
| 函數 | snake_case | `get_user()` |
| 類別 | PascalCase | `UserService` |
| 常量 | UPPER_SNAKE | `MAX_RETRY` |

### 4.2 Git

| 類型 | 格式 | 範例 |
|------|------|------|
| Feature | `feat: description` | `feat: add user auth` |
| Fix | `fix: description` | `fix: resolve login bug` |

---

## 5. 驗證關卡清單

### 5.1 Pre-commit Check
- [ ] 程式碼格式檢查通過
- [ ] 靜態分析無 high 問題
- [ ] 單元測試通過

### 5.2 Pre-merge Check
- [ ] Code Review 通過
- [ ] Quality Gate 分數 >= 80
- [ ] 安全掃描通過

---

---

## 6. TDAD 風格驗證

### 6.1 編譯後 Artifact

Constitution 被視為編譯後的 artifact，不可變更。

- 所有約束條件在編譯時固化
- 版本哈希用於驗證完整性
- 行為規格可供自動驗證

### 6.2 行為規格

所有 Agent 輸出必須符合 Constitution 的行為規格。

### 6.3 驗證機制

| 檢查項 | 說明 |
|--------|------|
| 關鍵詞檢查 | 禁止 bypass/skip/--no-verify |
| Task ID | 所有 commit 必須有 task_id |
| 審批流程 | 危險操作必須經過審批 |

### 6.4 CLI 命令

```bash
# 編譯 Constitution
python3 cli.py constitution compile

# 驗證輸出
python3 cli.py constitution verify "<agent_output>"
```

---

*本文檔最後更新：2026-03-23*
*版本：1.1.0*
