# methodology-v2 快速上手檢查清單

> 新團隊必看！使用 framework 前必須完成的事項

---

## 🚨 重要提醒

```
在使用 methodology-v2 之前，你必須完成以下設定。
沒有完成這些，Enforcement 無法正常運作。
```

---

## 📋 前置檢查清單

### ☐ Step 1: 環境確認

```bash
# 檢查 Python 版本（需要 3.11+）
python3 --version

# 如果低於 3.11，請升級 Python
```

| 檢項 | 標準 | 你的狀態 |
|------|------|----------|
| Python 版本 | >= 3.11 | ☐ 未檢查 |
| Git 已安裝 | 是 | ☐ 未檢查 |
| CLI 可執行 | `python3 cli.py version` | ☐ 未檢查 |

---

### ☐ Step 2: 取得 methodology-v2

```bash
# 方式一：Clone 專案
git clone https://github.com/johnnylugm-tech/methodology-v2.git
cd methodology-v2

# 方式二：如果你有自己的專案
# 在你的專案根目錄執行
git clone https://github.com/johnnylugm-tech/methodology-v2.git .methodology/
```

| 檢項 | 標準 | 你的狀態 |
|------|------|----------|
| methodology-v2 已取得 | 是 | ☐ |
| 在正確目錄 | 是 | ☐ |

---

### ☐ Step 3: 初始化 Enforcement 設定

```bash
# 初始化（預設 LOCAL 模式，適合個人/小專案）
python3 cli.py enforcement-config init

# 或者設定特定模式
python3 cli.py enforcement-config set local    # 個人
python3 cli.py enforcement-config set github   # GitHub 團隊
python3 cli.py enforcement-config set gitlab    # GitLab 團隊
python3 cli.py enforcement-config set jenkins   # Jenkins 團隊
```

| 檢項 | 標準 | 你的狀態 |
|------|------|----------|
| 設定檔已建立 | `.methodology/enforcement.json` 存在 | ☐ |
| 模式正確 | 是 | ☐ |

---

### ☐ Step 4: 安裝 Pre-Commit Hook

```bash
# 安裝 Local Hook
python3 cli.py enforcement install

# 驗證安裝
ls -la .git/hooks/pre-commit
```

| 檢項 | 標準 | 你的狀態 |
|------|------|----------|
| Hook 已安裝 | `.git/hooks/pre-commit` 存在 | ☐ |
| Hook 可執行 | `chmod +x` 已設定 | ☐ |

---

### ☐ Step 5: 安裝 Agent-Proof Hook（推薦）

```bash
# 安裝（放在 .methodology/，不易被發現/刪除）
python3 cli.py agent-proof-hook install

# 驗證
python3 cli.py agent-proof-hook verify
```

| 檢項 | 標準 | 你的狀態 |
|------|------|----------|
| Core module 已建立 | `.methodology/agent_hook_core.py` 存在 | ☐ |
| Wrapper 已建立 | `.git/hooks/pre-commit` 已更新 | ☐ |
| 驗證通過 | `verify` 返回成功 | ☐ |

---

### ☐ Step 6: 執行第一次檢查

```bash
# 執行所有 Enforcement 檢查
python3 cli.py enforcement run

# 如果看到「All enforcement checks passed」，表示設定成功
```

| 檢項 | 標準 | 你的狀態 |
|------|------|----------|
| Policy Engine | Passed | ☐ |
| Constitution Check | Passed | ☐ |
| Registry | Recorded | ☐ |

---

## ✅ 設定完成確認

全部完成後，執行：

```bash
python3 cli.py enforcement status
```

應該看到：

```
==================================================
Enforcement Configuration
==================================================
Mode: local
Platform: none
Strict: True
Allow Bypass: False

Enforcement Triggers:
  - Commit: True
  - Push: False
  - PR: False
  - Merge: False

Thresholds:
  - Quality Gate: 90.0
  - Security: 95.0
  - Coverage: 80.0
==================================================

⚙️ Policy Engine Status:
   Total Policies: 5
   Passed: 5
   Pass Rate: 100.0%
```

---

## 🎯 開始開發

設定完成後，每次 commit 都會自動執行檢查：

```bash
# 好範例 ✅
git add .
git commit -m "[TASK-123] add login feature"
# → Task ID 檢查通過
# → Policy Engine 檢查通過
# → 成功！

# 壞範例 ❌
git commit -m "add login feature"
# → ❌ 沒有 Task ID！被阻擋！
```

---

## ❓ 常見問題

### Q1: 遇到「Command not found」

```bash
# 確認在正確目錄
pwd
ls cli.py

# 如果不在正確目錄
cd path/to/methodology-v2
```

### Q2: Hook 安裝失敗

```bash
# 檢查 .git 目錄是否存在
ls -la .git

# 如果沒有，初始化 git
git init
```

### Q3: enforcement run 失敗

```bash
# 查看詳細錯誤
python3 cli.py enforcement run --verbose

# 或者檢查設定
python3 cli.py enforcement-config show
```

### Q4: 想跳過檢查（不建議！）

```bash
# ❌ 不要這樣做！
git commit --no-verify -m "fix"

# 這樣做會繞過 Enforcement，違背使用 framework 的目的
```

---

## 📞 需要幫助？

| 資源 | 連結 |
|------|------|
| 完整文件 | [docs/](./docs/) |
| 新手上路 | [docs/NEW_TEAM_GUIDE.md](./docs/NEW_TEAM_GUIDE.md) |
| Enforcement 指南 | [docs/ENFORCEMENT_GETTING_STARTED.md](./docs/ENFORCEMENT_GETTING_STARTED.md) |
| 問題回報 | GitHub Issues |

---

## 📝 團隊負責人確認

在團隊開始使用前，請確認：

- [ ] 已完成所有前置檢查
- [ ] 已向團隊說明 Enforcement 機制
- [ ] 知道如何調整閾值（如果需要）
- [ ] 知道如何回報問題

---

*最後更新：2026-03-23*