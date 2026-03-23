# Case 57: Server-Side Enforcement — 堵住 Local Hook 漏洞

**作者**: AI Enforcement Team  
**日期**: 2026-03-23  
**版本**: v5.28  
**狀態**: ✅ 已實現

---

## 問題背景

### Local Hook 的致命缺陷

```
攻擊向量：
git commit --no-verify    # 繞過所有 pre-commit hooks
git commit -m "hack"      # 直接 push 到 main
```

| 漏洞 | 嚴重性 | 說明 |
|------|--------|------|
| `--no-verify` 繞過 | 🔴 致命 | 一行命令即可跳過所有 local hooks |
| Hook 可被刪除 | 🔴 致命 | `rm .git/hooks/pre-commit` 後什麼都不會觸發 |
| 只驗證 local | 🔴 致命 | Remote push 可以夾帶沒有執行 enforcement 的程式碼 |

### 為什麼 Local Hook 不夠

```
Local Hook：
  ❌ 可被 --no-verify 繞過
  ❌ 可被刪除
  ❌ 只在開發者機器執行
  ❌ 依賴開發者環境（Python 版本、依賴等）

Server-Side Enforcement：
  ✅ 無法繞過（GitHub Actions 強制執行）
  ✅ 無法刪除（在 CI/CD 環境運行）
  ✅ 在隔離的乾淨環境執行
  ✅ 合併前必須通過
```

---

## 解決方案：Server-Side Enforcement

### 架構圖

```
┌─────────────────────────────────────────────────────────────┐
│                      GitHub Repository                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────┐      ┌──────────────┐      ┌───────────┐ │
│  │ Local Hook    │ ───▶ │ GitHub       │ ───▶ │ Server    │ │
│  │ (可被繞過)     │      │ Actions      │      │ Enforcement│ │
│  └──────────────┘      └──────────────┘      └───────────┘ │
│        │                      │                     │       │
│        │                      │                     │       │
│        ▼                      ▼                     ▼       │
│   ❌ 繞過捷徑              觸發 workflow        ✅ 強制的     │
│                              執行                五關檢查     │
│                                                              │
│  PR/Merge 請求時：                                           │
│  1. Constitution Check（第一關）                              │
│  2. Policy Engine（第二關）                                   │
│  3. Quality Gate（第三關）                                    │
│  4. Security Scan（第四關）                                   │
│  5. Registry Audit（第五關）                                  │
│                                                              │
│  全部通過 → ✅ Ready to Merge                                 │
│  任何失敗 → ❌ Blocked（無法合併）                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 實現細節

### 1. CI/CD Workflow（`.github/workflows/enforcement.yml`）

```yaml
name: 🚀 Methodology-v2 Enforcement

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  merge_group:

jobs:
  constitution-check: ...
  policy-engine: ...
  quality-gate: ...
  security-scan: ...
  registry-audit: ...
  final-gate: ...
```

**觸發時機**：
- `push` 到 main/develop → 確保所有變更都經過驗證
- `pull_request` → 合併前必經檢查
- `merge_group` → GitHub Merge Queue 支援

### 2. 五關檢查流程

```
                    ┌─────────────────────┐
                    │ Constitution Check   │
                    │ (第一關 - 規則定義)   │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Policy Engine       │
                    │ (第二關 - 政策執行)   │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Quality Gate        │
                    │ (第三關 - 品質標準)   │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Security Scan       │
                    │ (第四關 - 安全檢查)   │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Registry Audit      │
                    │ (第五關 - 執行證明)   │
                    └──────────┬──────────┘
                               ▼
                    ┌─────────────────────┐
                    │ Final Gate         │
                    │ (所有關卡通過才放行)  │
                    └─────────────────────┘
```

### 3. ServerEnforcer 類

```python
from enforcement import ServerEnforcer

enforcer = ServerEnforcer()
results = enforcer.enforce_all()

if not results['all_passed']:
    enforcer.report_failure(results)
    sys.exit(1)  # CI/CD 會回報失敗
```

---

## 漏洞修復對照表

| 漏洞 | 修復方案 | 狀態 |
|------|----------|------|
| `--no-verify` 繞過 | CI/CD workflow 無法使用 CLI 參數 | ✅ 已修復 |
| Hook 可被刪除 | Server-side enforcement 不依賴 local hooks | ✅ 已修復 |
| 只驗證 local | PR/Merge 前強制執行 server-side checks | ✅ 已修復 |
| 環境不一致 | CI/CD 使用統一的 ubuntu-latest + Python 3.11 | ✅ 已修復 |

---

## 與 Local Hook 的關係

```
不是取代，是彌補：

Local Hook（快速反饋）：
  ✅ 開發時即時檢查
  ✅ 快的 feedback loop
  ❌ 可被繞過

Server-Side（最終把關）：
  ❌ 不是即時的（需要 CI 時間）
  ✅ 無法繞過
  ✅ 合併前的最後防線

兩者結合 = 完整的保護：
  Local Hook → 開發時快速檢查（可能被繞過）
  Server-Side → 合併前最終把關（無法繞過）
```

---

## 使用方式

### 對於維護者

1. **首次設定**：觸發 `hook-installer.yml` workflow 來安裝 local hooks
2. **常態使用**：push 到 main 時自動執行
3. **手動觸發**：`workflow_dispatch` 可以手動執行

### 對於開發者

1. **正常開發**：Local hooks 提供快速反饋
2. **提交流程**：跟以前一樣 `git commit && git push`
3. **PR 合併**：Server-side 自動檢查，失敗則 block merge

### 對於 CI/CD

```bash
# 在 CI 環境中使用
python3 enforcement/server_enforcer.py

# 或使用 CLI
python3 cli.py server-enforce
```

---

## 測試驗證

### 測試 1: --no-verify 繞不過

```bash
git commit --no-verify -m "try to bypass"
git push

# 結果：
# ❌ GitHub Actions 會失敗
# ❌ PR 會被 block
```

### 測試 2: Hook 被刪除也沒用

```bash
rm .git/hooks/pre-commit
git commit -m "deleted hook"
git push

# 結果：
# ✅ Server-side 仍然會檢查
# ✅ PR 仍然會被 block 如果不合格
```

### 測試 3: 乾淨的 PR 可以合併

```bash
git commit -m "[TASK-123] Clean implementation"
python3 cli.py quality gate  # 本地檢查
git push

# 結果：
# ✅ GitHub Actions 通過
# ✅ PR 可以合併
```

---

## 結論

**v5.28 完成了什麼**：

```
✅ CI/CD Server-Side Enforcement（無法被繞過）
✅ 五關檢查流程（Constitution → Policy → Quality → Security → Registry）
✅ ServerEnforcer 類（可在 CI 中直接使用）
✅ 與 Local Hook 互補（快速反饋 + 最終把關）
✅ Block merge 直到所有檢查通過
```

**防護模型**：

```
攻擊者視角：
  ❌ git commit --no-verify → 沒用，Server-Side 會 block
  ❌ rm .git/hooks/pre-commit → 沒用，Server-Side 仍然檢查
  ❌ 直接 push main → 沒用，PR 需要通過所有 checks

防禦者視角：
  ✅ 開發時有 Local Hook 提供快速反饋
  ✅ 合併前有 Server-Side 強制執行五關檢查
  ✅ 任何繞過嘗試都會被發現和阻擋
```

---

*最後更新：2026-03-23*
