# Enforcement 快速上手

## 三種模式

| 模式 | 適用場景 | 相依性 |
|------|----------|--------|
| **LOCAL** (預設) | 個人/小專案 | 只有 Local Hook |
| **SELF_HOSTED** | 自架 CI/CD | Jenkins / GitLab |
| **CLOUD** | 雲端 CI/CD | GitHub Actions / Azure |

## 快速開始

### 1. 初始化（預設 LOCAL 模式）

```bash
cd /path/to/your/project
python3 /Users/johnny/.openclaw/workspace-musk/skills/methodology-v2/cli.py enforcement-config init
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

### 4. 自動偵測環境

```bash
python3 cli.py enforcement-config detect
```

## 各平台比較

| 平台 | 設定值 | 需要的東西 |
|------|--------|-----------|
| 本地 only | `local` | Local Hook |
| GitHub | `github` | GitHub Actions |
| GitLab | `gitlab` | GitLab CI |
| Jenkins | `jenkins` | Jenkins Server |
| Azure | `azure` | Azure DevOps |

詳見 [PLATFORM_COMPARISON.md](./PLATFORM_COMPARISON.md)

## 設定檔案位置

`.methodology/enforcement.json`

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
  "coverage_threshold": 80.0,
  "enable_registry": true,
  "enable_constitution_check": true,
  "enable_policy_engine": true
}
```

## CLI 用法

```
usage: cli.py enforcement-config [-h] [action] [mode]

positional arguments:
  action      Action: init, set, show, detect (default: show)
  mode        Mode for 'set' action: local, github, gitlab, jenkins, azure

examples:
  python cli.py enforcement-config init
  python cli.py enforcement-config set github
  python cli.py enforcement-config show
  python cli.py enforcement-config detect
```

## 觸發時機

Enforcement 在以下時機觸發（根據設定）：

- **Commit** - `enforce_on_commit: true` 時，每次 `git commit` 會觸發
- **Push** - `enforce_on_push: true` 時，每次 `git push` 會觸發
- **PR** - `enforce_on_pr: true` 時，每次開啟/更新 PR 會觸發
- **Merge** - `enforce_on_merge: true` 時，每次合併 PR 會觸發

## 閾值說明

| 閾值 | 預設值 | 說明 |
|------|--------|------|
| `quality_gate_threshold` | 90.0 | 品質閾值，低於此值會阻擋 |
| `security_threshold` | 95.0 | 安全閾值，低於此值會阻擋 |
| `coverage_threshold` | 80.0 | 覆蓋率閾值，低於此值會阻擋 |

## 嚴格模式

```json
{
  "strict_mode": true,
  "allow_bypass": false
}
```

- `strict_mode: true` - 預設阻擋不符合標準的程式碼
- `allow_bypass: false` - 不允許繞過 enforcement

## 程式碼使用

```python
from enforcement_config import EnforcementConfig, ConfigGenerator

# 載入設定（自動偵測環境）
config = EnforcementConfig.load()
print(config.get_summary())

# 手動建立特定平台的設定
config = ConfigGenerator.github_actions()
config.save()

# 根據設定執行對應的 enforcement
if config.mode.value == "local":
    print("Running local enforcement...")
elif config.mode.value == "cloud":
    print(f"Running cloud enforcement on {config.platform.value}...")
```

## 常見問題

### Q: 為什麼預設是 LOCAL 模式？

A: LOCAL 模式最簡單，不需要任何額外服務，適合個人和小型專案。

### Q: 如何在 CI/CD 中使用？

A: 在 CI/CD 環境中執行 `enforcement-config set <platform>` 來設定對應平台，然後 Pipeline 會自動使用 Enforcement。

### Q: 可以同時啟用多種觸發嗎？

A: 可以。例如：

```json
{
  "enforce_on_commit": true,
  "enforce_on_push": true,
  "enforce_on_pr": true
}
```

### Q: 如何調整閾值？

A: 直接編輯 `.methodology/enforcement.json`：

```json
{
  "quality_gate_threshold": 95.0,
  "security_threshold": 98.0,
  "coverage_threshold": 90.0
}
```

## 相關檔案

- `enforcement_config.py` - 統一設定模組
- `enforcement_config.default.json` - 預設設定
- `.gitlab-ci.yml` - GitLab CI 設定
- `Jenkinsfile` - Jenkins Pipeline 設定
- `azure-pipelines.yml` - Azure DevOps 設定
- [Case 58](./cases/case58_enforcement_config.md) - 詳細案例
- [PLATFORM_COMPARISON.md](./PLATFORM_COMPARISON.md) - 多平台比較
