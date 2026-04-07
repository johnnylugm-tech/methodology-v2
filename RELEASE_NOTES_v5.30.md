# v5.30.0 Release Notes

## 🚀 Enforcement Framework v5.30: 從「建議」到「強制執行」

**發布日期**: 2026-03-23  
**版本**: v5.30.0  
**標籤**: https://github.com/johnnylugm-tech/methodology-v2/releases/tag/v5.30.0

---

## 📋 版本亮點

### 🎯 v5.30 是 Enforcement Framework 的成熟版本

v5.30 解決了「框架只是建議，Agent 可以選擇不做」的問題：

| 問題 | v5.30 解決方案 |
|------|---------------|
| Agent 可選不做 | ✅ `enforcement run` 統一 CLI |
| 無法驗證做了 | ✅ `ExecutionRegistry` 執行記錄 |
| Hook 可被繞過 | ✅ `Agent-Proof Hook` |
| 政策需手動維護 | ✅ `Constitution → Policy` 自動生成 |
| 沒有測試 | ✅ 28 個單元測試 |

---

## 🆕 v5.30 新功能

### 1️⃣ CLI 整合（P0）

統一的 `enforcement` 命令：

```bash
# 執行所有檢查
python3 cli.py enforcement run

# 查看狀態
python3 cli.py enforcement status

# 安裝 Hook
python3 cli.py enforcement install
```

### 2️⃣ Agent-Proof Hook（P2）

讓 Agent 無法繞過的 Hook：

```bash
# 安裝（放在 .methodology/，不易被發現/刪除）
python3 cli.py agent-proof-hook install

# 驗證是否被篡改
python3 cli.py agent-proof-hook verify

# 解除安裝
python3 cli.py agent-proof-hook uninstall
```

### 3️⃣ Constitution → Policy 自動生成（P1）

從 Constitution.md 自動生成 Policy Engine 政策：

```bash
# 同步 Constitution 到 Policy
python3 cli.py constitution-sync
```

### 4️⃣ 單元測試覆蓋（P3）

28 個單元測試，全部通過：

| 測試檔案 | 測試數 |
|----------|--------|
| `test_policy_engine.py` | 9 |
| `test_execution_registry.py` | 8 |
| `test_constitution_as_code.py` | 11 |
| **總計** | **28** |

---

## 📦 完整 CLI 命令

```bash
# Enforcement（v5.30 新增）
python3 cli.py enforcement run       # 執行所有檢查
python3 cli.py enforcement check      # 檢查狀態
python3 cli.py enforcement status     # 顯示摘要
python3 cli.py enforcement install   # 安裝 Hook
python3 cli.py enforcement config     # 設定模式

# Agent-Proof Hook（v5.30 新增）
python3 cli.py agent-proof-hook install    # 安裝
python3 cli.py agent-proof-hook verify     # 驗證
python3 cli.py agent-proof-hook uninstall   # 解除

# Constitution Sync（v5.30 新增）
python3 cli.py constitution-sync      # 同步

# 現有命令
python3 cli.py install-hook          # 安裝 Pre-Commit Hook
python3 cli.py policy                # Policy Engine
python3 cli.py quality gate          # Quality Gate
python3 cli.py security scan         # Security Scan
```

---

## 🛡️ Enforcement Framework 架構

```
┌─────────────────────────────────────────────────────────────┐
│              Enforcement Framework v5.30                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  CLI Layer                                                 │
│  ────────                                                  │
│  enforcement run/check/status/install                       │
│  agent-proof-hook install/verify                            │
│  constitution-sync                                          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐  │
│  │                  三層保護                            │  │
│  ├─────────────────────────────────────────────────────┤  │
│  │                                                     │  │
│  │  Layer 1: Policy Engine                            │  │
│  │  ───────────────────────────────────                │  │
│  │  • Quality Gate >= 90                               │  │
│  │  • Security >= 95                                  │  │
│  │  • Coverage >= 80                                  │  │
│  │  • Commit 有 Task ID                                │  │
│  │                                                     │  │
│  │  Layer 2: Execution Registry                        │  │
│  │  ───────────────────────────────────                │  │
│  │  • timestamp + artifact → SHA-256                  │  │
│  │  • prove() 驗證執行                                 │  │
│  │  • verify_chain() 驗證完整性                       │  │
│  │                                                     │  │
│  │  Layer 3: Constitution as Code                    │  │
│  │  ───────────────────────────────────                │  │
│  │  • 7 條預設規則                                    │  │
│  │  • CRITICAL 違規直接 block                        │  │
│  │                                                     │  │
│  └─────────────────────────────────────────────────────┘  │
│                                                             │
│  Hook Layer                                                │
│  ──────────                                                 │
│  • pre-commit.template (Local Hook)                       │
│  • Agent-Proof Hook (放在 .methodology/)                  │
│  • CI/CD Server-Side (GitHub/GitLab/Jenkins/Azure)        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📚 文件更新

| 文件 | 更新內容 |
|------|----------|
| `WORKFLOW.md` | 新增 Enforcement Framework v5.30 章節 |
| `ENFORCEMENT_GETTING_STARTED.md` | 新增 CLI 命令說明 |
| `README.md` | 新增 v5.30 CLI 命令 |

---

## ⚠️ 遷移指南

### v5.29 → v5.30

**無破壞性變更**，這是純新增版本。

### 更新方式

```bash
git pull origin main

# 初始化 Enforcement
python3 cli.py enforcement-config init

# 安裝 Hook
python3 cli.py enforcement install
```

---

## 🙏 貢獻者

- Johnny Lu (@johnnylugm)

---

## 📖 完整文檔

- [GETTING_STARTED.md](./docs/GETTING_STARTED.md)
- [ENFORCEMENT_GETTING_STARTED.md](./docs/ENFORCEMENT_GETTING_STARTED.md)
- [NEW_TEAM_ENFORCEMENT_GUIDE.md](./docs/NEW_TEAM_ENFORCEMENT_GUIDE.md)
- [METHODOLOGY_VS_FRAMEWORK_VS_ENFORCEMENT.md](./docs/METHODOLOGY_VS_FRAMEWORK_VS_ENFORCEMENT.md)
- [PLATFORM_COMPARISON.md](./docs/PLATFORM_COMPARISON.md)

---

**methodology-v2: 讓 AI 開發從「隨機」變成「可預測」，從「建議」變成「強制執行」**
