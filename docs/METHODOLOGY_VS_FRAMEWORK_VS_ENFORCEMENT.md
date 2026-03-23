# 方法論 vs 框架 vs Enforcement

> 從「建議」到「強制」的進化之路

---

## 1️⃣ 三層次對照

| 維度 | 方法論 | 框架 | Enforcement |
|------|--------|------|-------------|
| **Agent 視角** | 「我可以這樣做」 | 「我應該這樣做」 | 「我必須這樣做」 |
| **自由度** | 完全自主 | 部分受限 | 零自主 |
| **驗證時機** | 之後再說 | 建議驗證 | 前置驗證 |
| **失敗後果** | 沒差 | 口頭警告 | 無法交付 |
| **分數** | 隨機浮動 6-9 | 7-8.5 | 固定 9.0+ |
| **強制性** | 0% | 30% | 100% |
| **可預測性** | 低 | 中 | 高 |

---

## 2️⃣ 為什麼 Agent 需要 Enforcement？

### Agent 的三個問題

| 問題 | 說明 | Enforcement 破解 |
|------|------|-----------------|
| **懶得做** | 跳過費時的驗證 | 沒選擇，不做無法繼續 |
| **想繞過** | 找捷徑走 | gates 擋路，繞不過 |
| **差不多就好** | 標準寬鬆 | 自動化驗證，標準嚴格 |

### 心理模型

```
方法論：
     ↓
Agent:「反正没人检查，跳过也没关系」
     ↓
結果：框架失效

Enforcement：
     ↓
Agent:「不做这件事就无法继续，没有选择」
     ↓
結果：框架生效
```

---

## 3️⃣ Enforcement 核心公式

```
Enforcement = Framework + 自動化鉤子 + 失敗阻斷

     Framework：定義要做什麼（SKILL.md, Constitution）
     自動化鉤子：確保真的做了（Git Hook, CI/CD）
     失敗阻斷：沒通過就無法前進（BLOCK 等級）
```

### 三層保護

| 層次 | 元件 | 職責 |
|------|------|------|
| **Layer 1** | Policy Engine | 流程政策、配額、資源控制 |
| **Layer 2** | Execution Registry | 記錄 + 可證明真的做了 |
| **Layer 3** | Constitution as Code | 業務規則、違反就阻擋 |

---

## 4️⃣ v5.27 Enforcement 實現

### 4.1 Policy Engine（政策引擎）

```python
from enforcement import PolicyEngine, EnforcementLevel

engine = PolicyEngine()

# 添加政策（沒有可選）
engine.add_policy(Policy(
    id="quality-gate-90",
    description="Quality Gate 分數必須 >= 90",
    check_fn=lambda: get_quality_score() >= 90,
    enforcement=EnforcementLevel.BLOCK,  # 阻擋
))

# 執行檢查（失敗就拋異常）
engine.enforce_all()
```

### 4.2 Pre-Commit Hook（自動化觸發）

```bash
#!/bin/bash
# 每次 git commit 自動執行

# 1. 檢查 commit message 格式
python3 cli.py commit-verify "$COMMIT_MSG" || exit 1

# 2. 執行 Policy Engine
python3 cli.py policy || exit 1

# 3. Quality Gate
python3 cli.py quality gate || exit 1
```

### 4.3 Constitution as Code（規範即代碼）

```python
from enforcement import ConstitutionAsCode

constitution = ConstitutionAsCode()

# 定義規則（不是文件，是代碼）
constitution.add_rule(Rule(
    id="R001",
    description="所有 commit 必須有 task_id",
    check_fn=lambda msg: bool(re.search(r'\[[A-Z]+-\d+\]', msg)),
    severity=RuleSeverity.CRITICAL,
))

# 執行檢查（違規就拋異常）
constitution.enforce({"commit_message": "[DEV-123] Add feature"})
```

### 4.4 Execution Registry（執行登記）

```python
from enforcement import ExecutionRegistry

registry = ExecutionRegistry()

# 記錄執行（不可偽造）
sig = registry.record(
    step="quality-gate",
    artifact={"score": 95, "passed": True}
)

# 驗證真的做了
if not registry.prove("quality-gate"):
    raise Exception("Quality Gate 未執行！不合規")
```

---

## 5️⃣ 現有漏洞分析（v5.27 評估）

### ⚠️ 潛在漏洞

| 漏洞 | 嚴重性 | 說明 | 修復方向 |
|------|--------|------|----------|
| **--no-verify 繞過** | 🔴 高 | `git commit --no-verify` 可跳過 hook | CI/CD server-side enforcement |
| **Hook 可被刪除** | 🔴 高 | `.git/hooks/pre-commit` 可被移除 | 使用 server-side hook |
| **檢查預設通過** | 🟡 中 | 無分數檔案時 `_check_*` 返回 True | 改為預設阻擋 |
| **GIT_COMMAND 不可靠** | 🟡 中 | 環境變數可能未設定 | 改用其他方式偵測 |
| **只檢查 local** | 🟡 中 | Remote push 可跳過 local hooks | CI/CD enforcement |

### 🔧 漏洞修復方案

#### 漏洞 1: --no-verify 繞過

```python
# 在 policy_engine.py 中新增：
def _check_no_verify_bypass(self) -> bool:
    """檢查是否使用了 --no-verify"""
    # 檢查 git 命令歷史
    import subprocess
    result = subprocess.run(
        ['git', 'var', 'GIT_COMMITGERMENT'],
        capture_output=True, text=True
    )
    return '--no-verify' not in result.stdout

# 並在 enforcement 級別改為：
"enforcement": EnforcementLevel.FAIL_BUILD  # 不只是 block，要讓 build 失敗
```

#### 漏洞 2: 預設通過

```python
# 修改 policy_engine.py：
def _check_quality_score(self) -> bool:
    """檢查 Quality Score"""
    score_file = ".methodology/.quality_score"
    if not os.path.exists(score_file):
        # 沒有分數檔案 = 從未執行 = 阻擋
        return False  # 改為 False
    ...
```

#### 漏洞 3: Server-Side Enforcement

```yaml
# .github/workflows/enforce.yml
name: Server-Side Enforcement

on:
  push:
    branches: [main]
  pull_request:

jobs:
  enforce:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      # Server-side 檢查（無法繞過）
      - name: Constitution Check
        run: |
          python3 cli.py constitution enforce || exit 1
      
      - name: All Policies Must Pass
        run: |
          python3 cli.py policy --strict || exit 1
```

---

## 6️⃣ 完整 Enforcement 矩陣

| 漏洞 | 預防 | 檢測 | 回應 |
|------|------|------|------|
| `--no-verify` | CI/CD server-side hook | 日誌記錄 | Block merge |
| Hook 刪除 | Server-side enforcement | 定期審計 | Block push |
| 預設通過 | Strict mode (default BLOCK) | Alert | Block |
| 直接 push | Server-side check | Audit log | Reject |

---

## 7️⃣ Enforcement 等級

| 等級 | 說明 | 適用場景 |
|------|------|----------|
| **LOG** | 僅記錄，不阻擋 | 開發中探索 |
| **WARN** | 警告但不放行 | 新團隊過渡 |
| **BLOCK** | 阻擋直到通過 | 生產環境 |
| **FAIL_BUILD** | 讓 build 失敗 | CI/CD |

---

## 8️⃣ 設計原則

### Enforcement 黃金法則

```
1. 沒有「可選」：只有「完成」或「失敗」
2. 前置驗證：不要事後補救
3. 自動化觸發：人會忘記，自動化不會
4. 失敗阻斷：沒通過就無法交付
5. 不可繞過：server-side enforcement
```

---

## 9️⃣ 總結

```
方法論：告訴 Agent 應該做什麼（建議）
框架：告訴 Agent 應該怎麼做（規範）
Enforcement：確保 Agent 一定這樣做（強制）

v5.27 解決了 80% 的問題：
✅ Policy Engine（BLOCK 等級）
✅ Pre-Commit Hook（自動化觸發）
✅ Constitution as Code（規則即代碼）
✅ Execution Registry（不可偽造記錄）

v5.28 需要修復：
🔴 CI/CD server-side enforcement
🔴 Strict mode（預設阻擋）
🔴 --no-verify 預防
```

---

*最後更新：2026-03-23*