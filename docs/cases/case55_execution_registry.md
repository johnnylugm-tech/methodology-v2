# Case 55: Execution Registry - 執行登記處

## 問題

**「無法證明真的做了」**

現有 framework 的問題：
- 聲稱有 Quality Gate，但只檢查分數，不記錄誰執行、何時執行
- 聲稱有 TDD 流程，但無法證明測試真的跑了
- 審計時只能靠截圖，截圖可以偽造

## 解決方案：Execution Registry

核心概念：
- **不可偽造的記錄** — SHA-256 signature
- **時間戳記** — 精確到毫秒
- **產出物附件** — 記錄執行的具體輸出

### 核心機制

```
步驟執行 → 記錄 timestamp + artifact → 生成 signature → 存入 SQLite
                                           ↓
                                可隨時驗證：真的做過嗎？
```

### 使用範例

```python
from enforcement import ExecutionRegistry

registry = ExecutionRegistry()

# 記錄 Quality Gate 執行
sig = registry.record(
    step="quality-gate",
    artifact={
        "score": 95,
        "passed": True,
        "files_checked": 42,
        "violations": []
    },
    note="v2.5.1 release gate"
)

# 驗證步驟是否執行
if registry.prove("quality-gate"):
    print("✅ Quality Gate 已執行")
else:
    print("❌ Quality Gate 未執行（不合規）")
```

### 驗證鏈

```python
# 驗證整個流程是否完整
result = registry.verify_chain([
    "task-creation",
    "code-review", 
    "quality-gate",
    "security-scan",
    "deployment"
])

print(f"完整度: {result['executed']}/{result['total']}")
if not result['complete']:
    print(f"缺失步驟: {result['missing']}")
```

### 證據報告

```python
report = registry.get_evidence_report("quality-gate")
# {
#     "step": "quality-gate",
#     "executed": True,
#     "evidence": {
#         "timestamp": "2026-03-23T20:57:00.123456",
#         "artifact": {...},
#         "signature": "a1b2c3d4...",
#         "verified": True
#     }
# }
```

## 與 Constitution 整合

```python
from enforcement import ExecutionRegistry, ConstitutionAsCode

registry = ExecutionRegistry()
constitution = ConstitutionAsCode()

# 執行 Quality Gate
quality_result = run_quality_gate()

# 1. 先記錄到 Registry（可證明做了）
registry.record(
    step="quality-gate",
    artifact=quality_result
)

# 2. 再用 Constitution 檢查（可阻擋不合規的）
constitution.enforce({
    "quality_score": quality_result["score"]
})
```

## 資料庫結構

```sql
CREATE TABLE executions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    step TEXT NOT NULL,           -- 步驟名稱
    timestamp TEXT NOT NULL,      -- ISO 格式時間
    artifact TEXT NOT NULL,        -- JSON 產出物
    signature TEXT NOT NULL UNIQUE, -- SHA-256 簽名
    verified INTEGER DEFAULT 1,    -- 是否已驗證
    note TEXT                      -- 備註
);
```

## 優勢

| 特性 | 傳統方式 | Execution Registry |
|------|----------|---------------------|
| 證明方式 | 截圖/截文 | cryptographic signature |
| 可驗證性 | 難以驗證 | 随时查询 |
| 時間精確度 | 人為填寫 | 毫秒級自動 |
| 偽造難度 | 容易 | 几乎不可能 |
| 審計友好 | 需人工整理 | 自動生成報告 |

## 何時使用

**必須記錄的關鍵步驟：**
- ✅ Quality Gate 執行
- ✅ Security Scan 執行
- ✅ Code Review 審批
- ✅ Deployment 操作
- ✅ Critical 決策

**不需記錄的普通步驟：**
- ❌ 一般的代碼編輯
- ❌ 普通的文件更新
- ❌ 常規的溝通記錄

---

**核心原則**：不是所有事情都要記錄，只記錄「需要能夠證明真的做了」的事情。
