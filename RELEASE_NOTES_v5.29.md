# v5.29.0 Release Notes

## 🚀 Enforcement Framework: 從「建議」到「強制執行」

**發布日期**: 2026-03-23  
**版本**: v5.29.0  
**標籤**: https://github.com/johnnylugm-tech/methodology-v2/releases/tag/v5.29.0

---

## 📋 版本亮點

### 🛡️ 這是迄今為止最重要的版本

從 **v5.14 → v5.29**，methodology-v2 完成了一次重大進化：

```
之前（脆弱）：
「框架只是建議，Agent 可以選擇不做」
     ↓
之後（強健）：
「Enforcement 機制，沒有選擇，必須執行」
```

### 🎯 核心價值

| 功能 | 解決什麼問題 |
|------|-------------|
| **Policy Engine** | 沒有「可選」，只有「完成」或「失敗」 |
| **Execution Registry** | 不可偽造的執行證明 |
| **Constitution as Code** | 規範不是文件，是可執行的代碼 |
| **Pre-Commit Hook** | 每次 commit 自動化觸發 |
| **Multi-Platform CI/CD** | GitHub / GitLab / Jenkins / Azure |

---

## 📦 v5.14 → v5.29 變更摘要

### v5.26: 突破 9.0 分數

| 模組 | 功能 |
|------|------|
| `ai_quality_gate` | 自動 Code Review，檢測 debug/secrets |
| `tdd_runner` | 測試驅動開發，覆蓋率計算 |
| `multi_agent_team` | 4 Agent 協作（Dev/Review/Test/Doc） |
| `security_scanner` | SAST 安全掃描，CWE Top 25 |

### v5.27: Enforcement 三層保護

| 層次 | 元件 | 功能 |
|------|------|------|
| Layer 1 | `policy_engine.py` | 政策引擎，BLOCK 等級 |
| Layer 2 | `execution_registry.py` | 執行登記，不可偽造 |
| Layer 3 | `constitution_as_code.py` | 規範即代碼 |

### v5.28: 填補漏洞

| 問題 | 解決方案 |
|------|----------|
| `--no-verify` 繞過 | CI/CD server-side enforcement |
| Hook 可被刪除 | ServerEnforcer + 多平台支援 |

### v5.29: 統一設定 + 新手上路

| 功能 | 說明 |
|------|------|
| `enforcement_config.py` | 統一設定，預設 LOCAL 模式 |
| Multi-Platform | GitHub/GitLab/Jenkins/Azure |
| `NEW_TEAM_ENFORCEMENT_GUIDE.md` | 新團隊上手文件 |

---

## 🛡️ Enforcement Framework 詳解

### 三層保護架構

```
┌─────────────────────────────────────────────────────────────┐
│                    Enforcement 三層保護                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: Policy Engine                                     │
│  ─────────────────────────────────                         │
│  「沒有可選，只有完成或失敗」                                  │
│  ✅ Quality Gate >= 90                                      │
│  ✅ Test Coverage >= 80                                     │
│  ✅ Security Score >= 95                                    │
│  ✅ Commit 有 Task ID                                       │
│                                                             │
│  Layer 2: Execution Registry                                 │
│  ─────────────────────────────────                         │
│  「不可偽造的執行證明」                                        │
│  ✅ timestamp + artifact → SHA-256 signature                │
│  ✅ verify_chain() 驗證步驟完整性                            │
│                                                             │
│  Layer 3: Constitution as Code                              │
│  ─────────────────────────────────                         │
│  「不是文件，是可執行的規則」                                  │
│  ✅ 7 條預設規則                                            │
│  ✅ CRITICAL 等級違規直接 block                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 多平台支援

| 平台 | 設定 | 適用場景 |
|------|------|----------|
| **LOCAL (預設)** | `set local` | 個人/小專案 |
| **GitHub Actions** | `set github` | 團隊/GitHub |
| **GitLab CI** | `set gitlab` | 自架 GitLab |
| **Jenkins** | `set jenkins` | 自架 Jenkins |
| **Azure DevOps** | `set azure` | Azure 環境 |

### 快速開始

```bash
# 1. 初始化（預設 LOCAL 模式）
python3 cli.py enforcement-config init

# 2. 安裝 Hook
python3 cli.py install-hook

# 3. 開發（每次 commit 自動檢查）
git commit -m "[TASK-123] add login feature"
# ✅ 成功
```

---

## 📚 新文件

| 文件 | 說明 |
|------|------|
| `NEW_TEAM_ENFORCEMENT_GUIDE.md` | Enforcement 新團隊上手 |
| `ENFORCEMENT_GETTING_STARTED.md` | Enforcement 快速上手 |
| `METHODOLOGY_VS_FRAMEWORK_VS_ENFORCEMENT.md` | 概念對比 |
| `PLATFORM_COMPARISON.md` | 多平台比較 |
| `ANTI_SHORTCUT_FRAMEWORK.md` | Anti-Shortcut 完整手冊 |
| `TDAD_METHODOLOGY.md` | TDAD 測試方法論 |

---

## 🔧 CLI 新增命令

| 命令 | 功能 |
|------|------|
| `python3 cli.py policy` | 執行 Policy Engine |
| `python3 cli.py install-hook` | 安裝 Pre-Commit Hook |
| `python3 cli.py enforcement-config init` | 初始化設定 |
| `python3 cli.py enforcement-config set <mode>` | 設定模式 |
| `python3 cli.py enforcement-config show` | 顯示設定 |
| `python3 cli.py trace impact --file <file>` | 變更影響分析 |

---

## 🧪 TDAD 測試方法論

根據最新研究 (arXiv:2603.08806, 2603.17973)：

| TDAD 概念 | methodology-v2 實作 |
|-----------|-------------------|
| **Compiled Prompts** | `CompiledConstitution` |
| **Mutation Testing** | `MutationTester` |
| **Hidden Tests** | `QualityGateTDAD` |
| **Impact Analysis** | `ImpactAnalyzer` |

---

## 📊 測試結果 (V14)

使用 v5.26 四方案，V14 達成 **9.1 分**：

| 方案 | 分數貢獻 |
|------|----------|
| AI Quality Gate | +0.3 |
| TDD Runner | +0.2 |
| Multi-Agent | +0.2 |
| Security Scanner | +0.1 |
| **總計** | **+0.8** |

---

## ⚠️ 遷移指南

### v5.29 破壞性變更

**無破壞性變更**，這是純新增版本。

### 更新方式

```bash
# 取得最新版本
git pull origin main

# 重新初始化 enforcement
python3 cli.py enforcement-config init
```

---

## 🙏 貢獻者

- Johnny Lu (@johnnylugm)

---

## 📖 完整文檔

- [GETTING_STARTED.md](./docs/GETTING_STARTED.md)
- [WORKFLOW.md](./docs/WORKFLOW.md)
- [NEW_TEAM_GUIDE.md](./docs/NEW_TEAM_GUIDE.md)
- [NEW_TEAM_ENFORCEMENT_GUIDE.md](./docs/NEW_TEAM_ENFORCEMENT_GUIDE.md)
- [ENFORCEMENT_GETTING_STARTED.md](./docs/ENFORCEMENT_GETTING_STARTED.md)
- [METHODOLOGY_VS_FRAMEWORK_VS_ENFORCEMENT.md](./docs/METHODOLOGY_VS_FRAMEWORK_VS_ENFORCEMENT.md)

---

## 🎯 下一步

| 版本 | 目標 |
|------|------|
| v5.30 | 修复 32 處 TODO |
| v6.0 | 穩定版 API |

---

**methodology-v2: 讓 AI 開發從「隨機」變成「可預測」**
