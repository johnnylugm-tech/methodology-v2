# Case 58: Unified Enforcement Configuration

## 概述

將 Enforcement 的相依性包裝成統一設定，預設使用輕量級 Local Hook，支援多平台 CI/CD。

## 問題背景

方法論 enforcement 需要在多種環境中運作：
- 個人開發者：只需要本地 CLI + Git Hook
- 小團隊：可能使用 Jenkins 或 GitLab 自架
- 企業：使用 GitHub Actions、Azure DevOps 等雲端 CI/CD

不同環境需要不同的 enforcement 設定，但核心邏輯應該相同。

## 解決方案

### EnforcementConfig 類

```python
from enforcement_config import EnforcementConfig, ConfigGenerator

# 自動偵測環境
config = EnforcementConfig.load()

# 手動設定模式
config = ConfigGenerator.github_actions()
config.save()
```

### 三種模式

| 模式 | 適用場景 | 相依性 |
|------|----------|--------|
| **LOCAL** (預設) | 個人/小專案 | 只有 Local Hook |
| **SELF_HOSTED** | 自架 CI/CD | Jenkins / GitLab |
| **CLOUD** | 雲端 CI/CD | GitHub Actions / Azure |

### 支援的平台

- `local` - 本地 only（預設）
- `github` - GitHub Actions
- `gitlab` - GitLab CI
- `jenkins` - Jenkins
- `azure` - Azure DevOps

## 使用方式

### 1. 初始化

```bash
python3 cli.py enforcement-config init
```

### 2. 設定模式

```bash
# LOCAL（預設）
python3 cli.py enforcement-config set local

# GitHub Actions
python3 cli.py enforcement-config set github

# GitLab CI
python3 cli.py enforcement-config set gitlab

# Jenkins
python3 cli.py enforcement-config set jenkins

# Azure DevOps
python3 cli.py enforcement-config set azure
```

### 3. 查看目前設定

```bash
python3 cli.py enforcement-config show
```

### 4. 自動偵測

```bash
python3 cli.py enforcement-config detect
```

## 設定檔案

設定儲存在 `.methodology/enforcement.json`:

```json
{
  "mode": "local",
  "platform": "none",
  "enforce_on_commit": true,
  "enforce_on_push": false,
  "enforce_on_pr": false,
  "enforce_on_merge": false,
  "strict_mode": true,
  "allow_bypass": false,
  "quality_gate_threshold": 90.0,
  "security_threshold": 95.0,
  "coverage_threshold": 80.0
}
```

## 環境變數

可以透過環境變數覆寫設定：

```bash
export METHODOLOGY_ENFORCEMENT_CONFIG='{"mode": "cloud", "platform": "github"}'
```

## CI/CD 整合

### GitHub Actions

使用 `.github/workflows/enforcement.yml` 或透過 `enforcement-config set github` 自動產生。

### GitLab CI

使用 `.gitlab-ci.yml`。

### Jenkins

使用 `Jenkinsfile`。

### Azure DevOps

使用 `azure-pipelines.yml`。

詳見 [PLATFORM_COMPARISON.md](../PLATFORM_COMPARISON.md)

## 閾值設定

```python
config = EnforcementConfig(
    quality_gate_threshold=90.0,  # 品質閾值
    security_threshold=95.0,      # 安全閾值
    coverage_threshold=80.0,       # 覆蓋率閾值
)
```

## 嚴格模式

```python
config = EnforcementConfig(
    strict_mode=True,      # True = 預設阻擋
    allow_bypass=False,    # 是否允許繞過
)
```

## 觸發時機

```python
config = EnforcementConfig(
    enforce_on_commit=True,   # commit 時
    enforce_on_push=True,     # push 時
    enforce_on_pr=True,       # PR 時
    enforce_on_merge=True,    # merge 時
)
```

## 優點

1. **統一的介面** - 所有環境使用相同的方式管理 enforcement
2. **自動偵測** - 根據環境變數自動偵測合适的模式
3. **多平台支援** - 支援所有主流 CI/CD 平台
4. **靈活設定** - 可以針對不同環境微調參數
5. **預設安全** - 預設使用最嚴格的 Local 模式

## 最佳實踐

1. **個人開發**：使用預設 LOCAL 模式
2. **團隊協作**：使用 CLOUD 模式配合 PR enforcement
3. **企業環境**：使用 CLOUD 模式 + 嚴格閾值

## 相關案例

- [Case 54: Pre-commit Hook](./case54_pre_commit_hook.md)
- [Case 55: Execution Registry](./case55_execution_registry.md)
- [Case 56: Constitution as Code](./case56_constitution_as_code.md)
- [Case 57: Server-side Enforcement](./case57_server_side_enforcement.md)
