# methodology-v2 新團隊上手指南

> 從零開始：如何讓團隊正確使用 methodology-v2

---

## 1️⃣ 這份文件給誰看？

| 角色 | 這份文件幫你了解 |
|------|------------------|
| **新團隊** | 第一次接觸 methodology-v2 |
| **個人開發者** | 想用但不知道從哪開始 |
| **團隊 Lead** | 需要向團隊推廣這套方法論 |
| **DevOps** | 需要理解 CI/CD 整合 |

---

## 2️⃣ 三分鐘理解 methodology-v2

### 傳統開發的問題

```
任務來了
    ↓
我覺得這樣做比較好
    ↓
做完再說
    ↓
問題一堆（爛程式碼、沒測試、不安全）
```

### methodology-v2 的做法

```
任務來了
    ↓
先問：Constitution 怎麼說？
    ↓
按照流程：Specify → Plan → Tasks → Verification
    ↓
每個步驟都有 enforcement
    ↓
按時交付高品質程式碼
```

---

## 3️⃣ 核心概念

### 3.1 方法論 vs 框架 vs Enforcement

| 層次 | 口號 | 你是誰 |
|------|------|--------|
| **方法論** | 「建議這樣做」 | 老師 |
| **框架** | 「應該這樣做」 | 教練 |
| **Enforcement** | 「必須這樣做」 | 老闆 |

**methodology-v2 是 Enforcement 等級：不做不行。**

### 3.2 為什麼需要 Enforcement？

| 問題 | Enforcement 破解 |
|------|-----------------|
| 「我懶得測試」 | → 沒測試不能 commit |
| 「差不多就好」 | → 分數不夠不能交付 |
| 「我想繞過」 | → 繞不過，被擋住 |

---

## 4️⃣ 快速上手（五步驟）

### Step 1: 了解基本概念

```
methodology-v2 = 流程 + 工具 + Enforcement

流程：Constitution → Specify → Plan → Tasks → Verification → Release
工具：CLI、Quality Gate、Security Scanner
Enforcement：Policy Engine、Pre-Commit Hook、Registry
```

### Step 2: 設定環境

```bash
# 1. 取得 methodology-v2
cd your-project
git clone https://github.com/johnnylugm-tech/methodology-v2.git
cd methodology-v2

# 2. 設定路徑（可選）
export PATH=$PATH:$(pwd)

# 3. 初始化專案
python3 cli.py init
```

### Step 3: 安裝 Enforcement Hook

```bash
# 安裝 Local Hook（預設，適合個人/小專案）
python3 cli.py install-hook

# 驗證安裝
ls -la .git/hooks/pre-commit
```

### Step 4: 了解基本流程

```
1. Constitution → 定義團隊憲章
2. Specify → 制定需求
3. Plan → 規劃架構
4. Tasks → 實作
5. Verification → 驗證
6. Release → 發布
```

### Step 5: 開始開發

```bash
# 壞範例（會被阻擋）
git commit -m "fix bug"
# ❌ 被阻擋：沒有 task ID

# 好範例
git commit -m "[TASK-123] fix login bug"
# ✅ 成功
```

---

## 5️⃣ Enforcement 機制詳解

### 5.1 為什麼需要 Enforcement？

| 問題 | Enforcement 解決 |
|------|-----------------|
| 「我有寫文件但沒人看」 | → Hook 自動檢查 |
| 「我覺得品質夠好」 | → 分數 < 90 被阻擋 |
| 「快速修復就好」 | → Security < 95 被阻擋 |

### 5.2 三層保護

```
┌─────────────────────────────────────────────────────────────┐
│                    Enforcement 三層保護                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Layer 1: Policy Engine                                     │
│  ─────────────────────────────────                         │
│  「沒有可選，只有完成或失敗」                                  │
│  政策：Quality Gate >= 90, Coverage >= 80, Security >= 95    │
│                                                             │
│  Layer 2: Execution Registry                                 │
│  ─────────────────────────────────                         │
│  「不可偽造的執行證明」                                        │
│  每次執行都記錄 timestamp + signature                        │
│                                                             │
│  Layer 3: Constitution as Code                                │
│  ─────────────────────────────────                         │
│  「不是文件，是可執行的規則」                                  │
│  違反就直接 block                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 什麼是 Policy Engine？

```python
# Policy Engine 做什麼？
# 1. 定義政策（policy）
# 2. 執行檢查（check）
# 3. 失敗就 block

from enforcement import PolicyEngine, EnforcementLevel

engine = PolicyEngine()

# 添加政策（沒有可選！）
engine.add_policy(Policy(
    id="quality-gate-90",
    description="Quality Gate 分數必須 >= 90",
    check_fn=lambda: get_quality_score() >= 90,
    enforcement=EnforcementLevel.BLOCK,  # 阻擋
))

# 執行
engine.enforce_all()  # 失敗就拋異常
```

### 5.4 什麼是 Execution Registry？

```python
# 記錄每個步驟執行過
registry = ExecutionRegistry()

sig = registry.record(
    step="quality-gate",
    artifact={"score": 95, "files_checked": 42}
)

# 驗證
if not registry.prove("quality-gate"):
    raise Exception("❌ Quality Gate 未執行！")
```

### 5.5 什麼是 Constitution as Code？

```python
# 不是「建議閱讀 Constitution」
# 是「違反 Constitution 就阻擋」

constitution = ConstitutionAsCode()

# 添加規則
constitution.add_rule(Rule(
    id="R001",
    description="所有 commit 必須有 task_id",
    check_fn=lambda msg: bool(re.search(r'\[[A-Z]+-\d+\]', msg)),
    severity=RuleSeverity.CRITICAL,
))

# 執行（違規就拋異常）
constitution.enforce({"commit_message": "[TASK-123] fix bug"})
```

---

## 6️⃣ 日常使用

### 6.1 提交程式碼

```bash
# 1. 開始任務
# TASK-123: 新增使用者登入功能

# 2. 開發
vim src/login.py

# 3. 提交（必須有 task ID）
git add .
git commit -m "[TASK-123] add login feature"
# ✅ 成功，或 ❌ 被阻擋

# 4. 如果被阻擋
# 看錯誤訊息，修正後再提交
```

### 6.2 查看狀態

```bash
# 查看 Enforcement 狀態
python3 cli.py policy

# 查看 Quality Score
python3 cli.py quality status

# 查看所有檢查結果
python3 cli.py status
```

### 6.3 常見錯誤

| 錯誤訊息 | 解決方式 |
|----------|----------|
| `❌ No task ID in commit` | 改成 `[TASK-123] message` |
| `❌ Quality score < 90` | 提高程式碼品質，增加測試 |
| `❌ Security score < 95` | 移除硬編碼密碼，修復漏洞 |
| `❌ Coverage < 80%` | 增加單元測試 |

---

## 7️⃣ 團隊協作

### 7.1 設定 Enforcement 模式

```bash
# 個人/小專案（預設）
python3 cli.py enforcement-config set local

# 團隊（建議 GitHub Actions）
python3 cli.py enforcement-config set github

# 自架 CI/CD
python3 cli.py enforcement-config set gitlab
python3 cli.py enforcement-config set jenkins
```

### 7.2 CI/CD 整合

**LOCAL 模式（預設）**：
- 每人本地執行
- 無法被 `--no-verify` 繞過（除非刪除 hook）

**CLOUD 模式（團隊）**：
- Server-side enforcement
- PR/Merge 前全部檢查
- Block 直到全部通過

### 7.3 團隊紀律

```
1. 不要刪除 .git/hooks/pre-commit
2. 不要使用 git commit --no-verify
3. 不要跳過 quality gate
4. 分數不夠就改善，不要繞過
```

---

## 8️⃣ 疑難解答

### Q1: Enforcement 會拖慢開發嗎？

**不會**。一開始可能需要適應，但：
- 問題在提交前被抓到 → 修復成本低
- 品質稳定 → 長遠來說更快

### Q2: 分數總是達不到怎麼辦？

| 情況 | 建議 |
|------|------|
| 第一次使用 | 先從 70 開始，逐步提高 |
| 覺得閾值不合理 | 調整 `enforcement_config.json` |
| 真的做不到 | 看文件問問題 |

### Q3: 可以繞過嗎？

**LOCAL 模式**：`git commit --no-verify` 可以，但**不建議**。

**CLOUD 模式**：無法繞過，server-side 強制執行。

### Q4: 誰來維護這些規則？

| 角色 | 責任 |
|------|------|
| Team Lead | 調整閾值，添加新規則 |
| DevOps | 維護 CI/CD |
| 所有人 | 遵守並回報問題 |

---

## 9️⃣ 下一步

| 文件 | 內容 |
|------|------|
| [GETTING_STARTED.md](./GETTING_STARTED.md) | 技術安裝指南 |
| [ENFORCEMENT_GETTING_STARTED.md](./ENFORCEMENT_GETTING_STARTED.md) | Enforcement 設定 |
| [WORKFLOW.md](./WORKFLOW.md) | 完整工作流程 |
| [PLATFORM_COMPARISON.md](./PLATFORM_COMPARISON.md) | 多平台比較 |
| [METHODOLOGY_VS_FRAMEWORK_VS_ENFORCEMENT.md](./METHODOLOGY_VS_FRAMEWORK_VS_ENFORCEMENT.md) | 概念詳解 |

---

## 📞 需要幫助？

| 問題類型 | 去哪裡 |
|----------|--------|
| 文件缺失 | 提 Issue |
| 功能建議 | 提 PR |
| 使用問題 | GitHub Discussion |

---

*最後更新：2026-03-23*