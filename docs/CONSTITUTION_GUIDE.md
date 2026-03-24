# Constitution - 品質憲法指南

> v5.40.0 - 定義團隊的「底線」

---

## 🎯 什麼是 Constitution？

Constitution 是 methodology-v2 的**品質憲法**，定義了團隊不可違背的原則。

### 與一般規則的區別

| 項目 | 一般規則 | Constitution |
|------|----------|--------------|
| 性質 | 建議性質 | 強制性質 |
| 違反時 | 警告 | BLOCK |
| 數量 | 可以很多 | 精簡（5-10條）|
| 修訂 | 容易 | 困難（需要共識）|

---

## 📜 Constitution 原則一覽

### 1. 正確性標準

```
目標: 100%
```

- 所有功能必須完全符合 SRS 規格
- 驗收標準 100% 通過
- 不允許已知錯誤進入生產環境

### 2. 安全性標準

```
目標: 100%
```

- 安全掃描必須通過（無漏洞）
- 敏感資訊不得明文存儲
- 所有 API 必須有認證機制

### 3. 可維護性標準

```
目標: > 70%
```

- Cyclomatic complexity <= 10
- 函數長度 <= 50 行
- 單一職責原則遵守

### 4. 測試覆蓋率

```
目標: > 80%
```

---

## 🔄 Constitution 與 Enforcement 的關係

```
Constitution (原則定義)
       ↓
       ↓ 轉換
       ↓
Enforcement (強制執行)
       ↓
Policy Engine (政策引擎)
       ↓
Quality Gate (品質閘道)
```

### 三層保護

| 層次 | 元件 | 職責 |
|------|------|------|
| **Layer 1** | Constitution | 定義原則 |
| **Layer 2** | Enforcement | 強制執行 |
| **Layer 3** | Quality Gate | 檢查把關 |

---

## 🚀 快速開始

### Step 1: 查看 Constitution

```bash
cat docs/CONSTITUTION.md
```

### Step 2: 運行 Constitution 檢查

```bash
python3 cli.py quality-gate constitution
```

### Step 3: 查看違反項目

```bash
python3 cli.py quality-gate check
# 或
python3 quality_watch.py status
```

---

## 📋 檢查器說明

### SRS Constitution Checker

檢查 `SRS.md`（需求規格）是否符合 Constitution：

| 檢查項目 | 標準 |
|----------|------|
| 完整性 | 所有章節齊備 |
| 可追溯性 | 需求 ID 唯一 |
| 清晰度 | 無模糊描述 |

### SAD Constitution Checker

檢查 `SAD.md`（架構設計）是否符合 Constitution：

| 檢查項目 | 標準 |
|----------|------|
| 模組化 | 職責分明 |
| 依賴關係 | 清晰定義 |
| 擴展性 | 預留擴展點 |

### Test Plan Constitution Checker

檢查 `TEST_PLAN.md`（測試計畫）是否符合 Constitution：

| 檢查項目 | 標準 |
|----------|------|
| 覆蓋率 | > 80% |
| 優先級 | 明確 |
| 可執行性 | 可自動化 |

---

## ⚙️ 自定義 Constitution

### 修改閾值

在 `quality_gate/constitution/__init__.py` 中：

```python
CONSTITUTION_THRESHOLDS = {
    "correctness": 100,      # 調低為 90
    "security": 100,
    "maintainability": 70,
    "coverage": 80,
}
```

### 新增檢查規則

在對應的 checker 中新增規則：

```python
# quality_gate/constitution/srs_constitution_checker.py
RULES = [
    # ... existing rules ...
    {
        "id": "NEW_RULE",
        "description": "新規則描述",
        "check_fn": lambda doc: check_new_rule(doc),
        "severity": "CRITICAL"
    }
]
```

---

## 🤔 常見問題

### Q: 如果 Constitution 和 Enforcement 衝突？

A: Constitution 優先。Enforcement 只是執行 Constitution 的工具。

### Q: 可以暫時繞過 Constitution 嗎？

A: 不可以。Constitution 是底線，沒有例外。

### Q: Constitution 如何修訂？

A: 需要團隊共識，建議每季檢視一次。

---

## 📚 相關文件

| 文件 | 內容 |
|------|------|
| [ENFORCEMENT_HANDBOOK.md](./ENFORCEMENT_HANDBOOK.md) | Enforcement 完整手冊 |
| [QUALITY_WATCH_GUIDE.md](./QUALITY_WATCH_GUIDE.md) | 持續監控指南 |
| [WORKFLOW.md](./WORKFLOW.md) | 完整工作流程 |

---

*最後更新：2026-03-24*