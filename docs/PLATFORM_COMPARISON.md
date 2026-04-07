# 多平台 CI/CD 比較

## 概述

methodology-v2 支援多種 CI/CD 平台，每種平台都有其特點和適用場景。

## 平台比較表

| 平台 | 模式 | 設定值 | 適用場景 | 優點 | 缺點 |
|------|------|--------|----------|------|------|
| **本地** | LOCAL | `local` | 個人/小專案 | 簡單、快速、無需額外服務 | 無法跨機器共享 |
| **GitHub** | CLOUD | `github` | GitHub 托管專案 | 免費配額、深度整合 | 僅限 GitHub |
| **GitLab** | CLOUD | `gitlab` | GitLab 托管/自架 | CI/CD 功能完整 | 學習曲線 |
| **Jenkins** | SELF_HOSTED | `jenkins` | 自架/企業 | 完全控制、高度自訂 | 需維護伺服器 |
| **Azure** | CLOUD | `azure` | Azure 托管專案 | 企業整合、微軟生態 | 僅限 Azure |

## 各平台詳細說明

### 1. Local（本地模式）

**適用**：個人開發、小專案、快速原型

```bash
python3 cli.py enforcement-config set local
```

**觸發時機**：
- ✅ Commit 時
- ❌ Push 時
- ❌ PR 時
- ❌ Merge 時

**設定**：
```json
{
  "mode": "local",
  "platform": "none",
  "enforce_on_commit": true
}
```

### 2. GitHub Actions

**適用**：GitHub 托管的專案、開源專案

```bash
python3 cli.py enforcement-config set github
```

**觸發時機**：
- ✅ Commit 時
- ✅ Push 時
- ✅ PR 時
- ✅ Merge 時

**需要檔案**：
- `.github/workflows/enforcement.yml`

**設定**：
```json
{
  "mode": "cloud",
  "platform": "github",
  "platform_config": {
    "workflow_file": ".github/workflows/enforcement.yml"
  }
}
```

### 3. GitLab CI

**適用**：GitLab 托管或自架的專案

```bash
python3 cli.py enforcement-config set gitlab
```

**觸發時機**：
- ✅ Commit 時
- ✅ Push 時
- ✅ PR（Merge Request）時
- ✅ Merge 時

**需要檔案**：
- `.gitlab-ci.yml`

**設定**：
```json
{
  "mode": "cloud",
  "platform": "gitlab",
  "platform_config": {
    "workflow_file": ".gitlab-ci.yml"
  }
}
```

### 4. Jenkins

**適用**：企業自架、需要完全控制的團隊

```bash
python3 cli.py enforcement-config set jenkins
```

**觸發時機**：
- ✅ Commit 時
- ✅ Push 時
- ✅ PR 時
- ✅ Merge 時

**需要檔案**：
- `Jenkinsfile`

**設定**：
```json
{
  "mode": "self_hosted",
  "platform": "jenkins",
  "platform_config": {
    "jenkinsfile": "Jenkinsfile",
    "agent_label": "methodology-enforcement"
  }
}
```

### 5. Azure DevOps

**適用**：使用 Azure DevOps 的企業、微軟生態

```bash
python3 cli.py enforcement-config set azure
```

**觸發時機**：
- ✅ Commit 時
- ✅ Push 時
- ✅ PR 時
- ✅ Merge 時

**需要檔案**：
- `azure-pipelines.yml`

**設定**：
```json
{
  "mode": "cloud",
  "platform": "azure",
  "platform_config": {
    "pipeline_file": "azure-pipelines.yml"
  }
}
```

## 選擇指南

### 什麼時候用 LOCAL？

- 個人開發者
- 小專案（< 5 人）
- 快速原型和實驗
- 不需要跨機器共享 enforcement 結果

### 什麼時候用 CLOUD？

- 團隊協作（>= 5 人）
- 需要強制執行品質標準
- 需要集中記錄和報告
- 需要在 PR 階段阻擋不良程式碼

### 什麼時候用 SELF_HOSTED？

- 企業內部專案
- 有合規要求（資料不能上雲）
- 已經有 Jenkins 基礎設施
- 需要完全自訂 CI/CD 流程

## 常見問題

### Q: 可以同時使用多個平台嗎？

A: 不建議。EnforcementConfig 一次只能設定一個平台。如果需要混合使用，建議：
- 本地開發使用 LOCAL 模式
- CI/CD 使用 CLOUD 模式

### Q: 如何在不同環境切換？

A: 使用環境變數：

```bash
# 在 CI 環境中
export METHODOLOGY_ENFORCEMENT_CONFIG='{"mode": "cloud", "platform": "github"}'
python3 cli.py enforcement-config show
```

### Q: 可以自訂觸發時機嗎？

A: 可以。在設定檔中調整：

```json
{
  "enforce_on_commit": true,
  "enforce_on_push": false,
  "enforce_on_pr": true,
  "enforce_on_merge": false
}
```

### Q: 如何設定閾值？

A: 在設定檔中調整：

```json
{
  "quality_gate_threshold": 90.0,
  "security_threshold": 95.0,
  "coverage_threshold": 80.0
}
```

## 遷移指南

### 從 LOCAL 遷移到 CLOUD

1. 在 CI/CD 平台建立對應的設定檔
2. 執行 `python3 cli.py enforcement-config set <platform>`
3. 確認觸發時機符合需求
4. 測試 CI/CD Pipeline

### 從一個 CLOUD 平台遷移到另一個

1. 在新平台建立對應的設定檔
2. 執行 `python3 cli.py enforcement-config set <new-platform>`
3. 移除舊平台的設定檔（可選）
4. 測試新 CI/CD Pipeline

## 延伸閱讀

- [Getting Started](./ENFORCEMENT_GETTING_STARTED.md)
- [Case 58: Enforcement Config](../cases/case58_enforcement_config.md)
- [Case 54: Pre-commit Hook](../cases/case54_pre_commit_hook.md)
