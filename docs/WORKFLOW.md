# methodology-v2 完整工作流程

> 從專案啟動到發布的完整流程

---

## 🛡️ Anti-Shortcut Framework

本流程已整合 **Anti-Shortcut Framework**，確保 AI Agent 無法走捷徑：

| 模組 | 功能 |
|------|------|
| **Blacklist (B)** | 阻止危險操作 |
| **Gatekeeper (A)** | 確保流程完整 |
| **Enforcer (F)** | 防範捷徑 |
| **Audit Logger (C)** | 記錄審計 |
| **Double Confirm (D)** | 雙重確認 |
| **Phase Hooks (E)** | 自動化驗證 |

📖 詳見：[ANTI_SHORTCUT_FRAMEWORK.md](ANTI_SHORTCUT_FRAMEWORK.md)

---

## 🧪 TDAD Testing Methodology

本流程已整合 **TDAD (Test-Driven AI Agent Development)**，用測試驅動 Agent 開發：

| 概念 | 實作 | 功能 |
|------|------|------|
| **Compiled Prompts** | `CompiledConstitution` | 將 Constitution 視為編譯後 artifact |
| **Visible/Hidden Tests** | `QualityGateTDAD` | 防止 specification gaming |
| **Mutation Testing** | `MutationTester` | 偵測測試有效性 |
| **Impact Analysis** | `ImpactAnalyzer` | 圖形化變更影響分析 |

📖 詳見：[TDAD_METHODOLOGY.md](TDAD_METHODOLOGY.md)

---

## 🛡️ Enforcement Framework (v5.30)

本流程已整合 **Enforcement Framework**，從「建議」進化到「強制執行」：

### 三層保護

| 層次 | 元件 | 職責 |
|------|------|------|
| **Layer 1** | Policy Engine | 流程政策、BLOCK 等級 |
| **Layer 2** | Execution Registry | 執行記錄、不可偽造 |
| **Layer 3** | Constitution as Code | 業務規則、違反阻擋 |

### CLI 命令

```bash
# 執行所有檢查
python3 cli.py enforcement run

# 查看狀態
python3 cli.py enforcement status

# 安裝 Hook
python3 cli.py enforcement install

# Agent-Proof Hook
python3 cli.py agent-proof-hook install
```

### 閾值

| 維度 | 閾值 |
|------|------|
| Quality Gate | >= 90 |
| Security | >= 95 |
| Coverage | >= 80 |
| Commit Message | 必須包含 `[TASK-XXX]` |

📖 詳見：[ENFORCEMENT_GETTING_STARTED.md](ENFORCEMENT_GETTING_STARTED.md)

---

## 完整工作流程圖

```
┌─────────────────────────────────────────────────────────────┐
│                     專案啟動                                 │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 1. Constitution 階段                                        │
│    - 建立團隊憲章                                           │
│    - 定義品質標準                                           │
│    - 設定錯誤分類                                           │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 2. Specify 階段                                            │
│    - 撰寫需求規格                                           │
│    - 建立 User Stories                                      │
│    - 定義驗收標準                                           │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 3. Plan 階段                                              │
│    - 設計架構                                               │
│    - 規劃 Roadmap                                           │
│    - 分配任務                                               │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 4. Tasks 階段                                              │
│    - 實作功能                                               │
│    - 單元測試                                               │
│    - Code Review                                            │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 5. Verification 階段                                       │
│    - Gate 1: 語法檢查                                       │
│    - Gate 2: 單元測試                                       │
│    - Gate 3: Quality Gate                                   │
│    - Gate 4: 安全掃描                                       │
└─────────────────────┬───────────────────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────────────────┐
│ 6. 發布                                                    │
│    - 整合測試                                               │
│    - 部署                                                   │
│    - 監控                                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 各階段產出

| 階段 | 產出 | 檔案位置 |
|------|------|----------|
| Constitution | CONSTITUTION.md | /constitution/ |
| Specify | requirements.md | /02-specify/ |
| Plan | architecture.md | /03-plan/ |
| Tasks | sprint_*.md | /04-tasks/ |
| Verification | gates.md | /05-verification/ |
| Outputs | src/, tests/ | /06-outputs/ |

---

## 錯誤處理流程

```
執行任務
    ↓
成功？ → 是 → 下一個任務
    ↓ 否
錯誤分類（L1-L6）
    ↓
L1-L2 → 自動重試 + Fallback
    ↓
L3-L4 → 記錄 + 降級
    ↓
L5-L6 → Human Intervention
```

---

## Quality Gate 閾值

| 維度 | 閾值 | 權重 |
|------|------|------|
| 正確性 | >= 80% | 30% |
| 安全性 | >= 100% | 25% |
| 可維護性 | >= 70% | 20% |
| 效能 | >= 80% | 15% |
| 覆蓋率 | >= 80% | 10% |

---

## 階段強制鉤子 (Phase Hooks)

每個階段結束時自動觸發驗證，確保品質標準不被繞過。

### 鉤子類型

| 階段 | 鉤子 | 說明 | 必填 |
|------|------|------|------|
| Development | `dev-lint` | 語法檢查 | ✓ |
| Development | `dev-test` | 單元測試 | ✓ |
| Development | `dev-constitution` | Constitution 合規 | ✓ |
| Verification | `verify-quality` | Quality Gate | ✓ |
| Verification | `verify-security` | 安全掃描 | ✓ |
| Verification | `verify-coverage` | 覆蓋率檢查 | ✗ |
| Release | `release-approval` | 審批確認 | ✓ |
| Release | `release-version` | 版本確認 | ✓ |
| Release | `release-changelog` | 更新日誌 | ✓ |

### 使用方式

```python
from anti_shortcut import PhaseHooks, Phase

hooks = PhaseHooks()

# 執行 development 階段的鉤子
result = hooks.execute_phase(Phase.DEVELOPMENT)

# 檢查是否可以進入下一階段
can_proceed, reason = hooks.can_proceed(
    from_phase=Phase.DEVELOPMENT,
    to_phase=Phase.VERIFICATION
)

if not can_proceed:
    print(f"Blocked: {reason}")
```

### 跳過鉤子

```python
# 有正當理由時可跳過（需要記錄）
hooks.skip_hook(
    hook_id="verify-coverage",
    reason="緊急修復，coverage 稍後補上"
)
```

---

*最後更新：2026-03-23*
