# Framework 開發工作流程

## 核心原則

### 1. 根因分析優先（Root Cause First）

```
發現 bug
    ↓
不是立即修復
    ↓
而是問：為什麼會發生？
    ↓
還有其他工具也有同樣問題嗎？
    ↓
一次修復所有相關問題
    ↓
發布一個版本包含所有修復
```

### 2. 單一真相來源（Single Source of Truth）

所有路徑定義必須來自 `phase_paths.py`：
- ✅ `PHASE_ARTIFACT_PATHS[5]["BASELINE.md"]`
- ❌ `"05-verify/BASELINE.md"`（硬編碼）

### 3. 測試驅動（Test-Driven）

新功能 → 先寫測試 → 再實作

---

## Bug 修復流程

### Step 1: 分類（Classification）

根據 `docs/BUG_CLASSIFICATION.md` 分類：
- P0: 立即修復
- P1: 24小時內
- P2: 1週內
- P3: 規劃中

### Step 2: 根因分析（Root Cause Analysis）

```python
# 在修復 commit message 中包含根因分析
fix(<scope>): <what was fixed>

Root Cause Analysis:
1. <why it happened>
2. <what other tools might have the same issue>
3. <what was fixed together>
```

### Step 3: 影響範圍（Impact Assessment）

回答：
1. 哪些工具會受影響？
2. 哪些 Phase 會受影響？
3. 哪些現有功能可能 break？

### Step 4: 修復

```bash
# 一次修復所有相關問題
# 不是一個一個修
git commit -m "fix(path): comprehensive Phase 5 path fixes

Root Cause Analysis:
1. Decentralized path definitions across 5 tools
2. verification_constitution_checker, quality_report_constitution_checker,
   risk_management_constitution_checker all had hardcoded paths
3. Fixed all of them to use PHASE_ARTIFACT_PATHS

Impact:
- verification_constitution_checker.py: now uses centralized paths
- quality_report_constitution_checker.py: now uses centralized paths
- risk_management_constitution_checker.py: now uses centralized paths

Tests:
- Added path_contract_tests.py
- All tests pass"
```

### Step 5: 驗證（Verification）

```bash
# 修復後必須通過所有測試
python3 tests/test_phase_paths.py
python3 scripts/verify_path_consistency.py
```

### Step 6: 發布（Release）

根據分類發布：
- P0/P1: 立即或盡快
- P2: 累積多個修復後一起發布

---

## 新功能開發流程

### Step 1: 需求分析

```
## 功能需求
- 目標：<what>
- 原因：<why>
- 影響：<what it affects>
```

### Step 2: 測試設計

在寫代碼之前，先寫測試：
```python
def test_new_feature_<name>():
    """新功能應該做 X"""
    # 設計測試案例
```

### Step 3: 實作

```bash
git checkout -b feat/<feature-name>
# 實作功能
git commit -m "feat(<scope>): <description>"
```

### Step 4: 完整測試

```bash
python3 tests/test_phase_paths.py
python3 scripts/verify_path_consistency.py
# 其他相關測試
```

### Step 5: Code Review

確認：
- [ ] 測試覆蓋足夠
- [ ] 沒有破壞現有功能
- [ ] 路徑使用 centralized definitions
- [ ] Commit message 格式正確

### Step 6: 合併

```bash
git checkout main
git merge feat/<feature-name>
git tag vX.Y.Z
git push origin main --tags
```

---

## 路徑修改流程

### 當需要修改路徑時

1. **只修改 `phase_paths.py`**
   ```python
   PHASE_ARTIFACT_PATHS = {
       5: {
           "BASELINE.md": ["new-path/", "old-path/"],
       }
   }
   ```

2. **更新 `verify_path_consistency.py`**

3. **執行測試**
   ```bash
   python3 tests/test_phase_paths.py
   python3 scripts/verify_path_consistency.py
   ```

4. **確保所有工具仍能工作**

---

## 常見錯誤

### ❌ 一個一個修

```bash
# 錯誤做法
v7.79: fix phase_artifact_enforcer path
v7.80: fix constitution/__init__.py path
v7.81: fix phase_prerequisite path
v7.82: fix verification_constitution_checker path
# ... 10 個版本修 10 個地方
```

### ✅ 一次修完

```bash
# 正確做法
# 分析：所有工具都有路徑問題
# 修復：建立 centralized path system，一次更新所有工具
v7.85: fix: centralized path system - update all tools
```

---

## 驗證清單

每次 commit 前檢查：

- [ ] Commit message 格式正確？
- [ ] 包含根因分析？
- [ ] 路徑使用 PHASE_ARTIFACT_PATHS？
- [ ] 有對應測試？
- [ ] 通過所有測試？
- [ ] 影響範圍評估了？
