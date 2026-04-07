# 版本發布 SOP

> **版本**：v5.96
> **目標**：規範化版本發布流程，確保版本標籤連續

---

## 發布流程

### 1. 確認所有測試通過

在發布前，必須確認所有測試通過：

```bash
cd skills/methodology-v2

# 運行所有測試
python -m pytest tests/ -v

# 運行 smoke test
python -m pytest tests/test_phase_enforcer_smoke.py -v

# 運行覆蓋矩陣驗證
python -m tests.test_unified_gate_coverage --detail

# 確認退出碼為 0
echo $?  # 必須為 0
```

### 2. 更新 CHANGELOG.md

在 `CHANGELOG.md` 頂部新增版本區塊：

```markdown
## [vX.YY] - YYYY-MM-DD

### 🚀 Added
- 新功能描述

### 🛠️ Fixed
- 修復描述

### 🧪 Testing
- 測試相關變更

### 📝 Documentation
- 文檔更新
```

**規則**：
- 版本號必須遵循語義化版本（Semantic Versioning）
- 日期格式：`YYYY-MM-DD`
- 每個變更分類使用對應的 emoji
- 描述要具體，說明「什麼改變了」而非「做了什麼」

### 3. 更新版本號

確保以下位置的版本號一致：

| 位置 | 更新方式 |
|------|----------|
| `CHANGELOG.md` | 新增版本區塊 |
| `SKILL.md` 頂部 | 更新 `version` 字段 |
| `pyproject.toml` | 更新 `version` 字段 |
| `cli.py` `cmd_version` | 更新版本字符串 |

### 4. 建立版本標籤 (git tag)

```bash
# 確認當前狀態
git status

# 確認所有變更已提交
git log --oneline -1

# 建立版本標籤
git tag -a vX.YY -m "vX.YY: 版本簡短描述"

# 驗證標籤
git tag -l "vX.Y*"
```

**標籤命名規則**：
- 主版本：`vX.YY`（如 v5.96）
- 預發布：`vX.YY-alpha`、`vX.YY-beta`
- 候選版本：`vX.YY-rc1`、`vX.YY-rc2`

### 5. 推送標籤到 GitHub

```bash
# 推送主分支和標籤
git push origin main --tags

# 或僅推送標籤
git push origin vX.YY

# 驗證推送
git ls-remote --tags origin
```

### 6. 驗證發布

```bash
# 克隆標籤版本的歷史
git log --oneline vX.YY~3..vX.YY

# 確認版本號正確
python -m skills.methodology-v2.cli version
```

---

## 版本號規則

### 格式

```
v[major].[minor]
```

- **major**：主要版本（通常用於重大架構變更）
- **minor**：次要版本（用於功能新增、修正、優化）

### 版本遞增規則

| 變更類型 | 版本遞增 | 範例 |
|----------|----------|------|
| 重大功能/架構變更 | minor + 1 | v5.95 → v5.96 |
| 破壞性變更 | major + 1 | v5.96 → v6.00 |
| 小幅修正/文檔更新 | minor + 0.1 | v5.96 → v5.97 |
| 緊急修復 | patch | v5.96 → v5.96.1 |

### 標籤創建時機

**必須創建標籤**：
- ✅ 新功能發布
- ✅ 重大 Bug 修復
- ✅ 安全性更新
- ✅ 測試覆蓋顯著提升

**可選創建標籤**：
- ⚠️ 文檔更新（取決於變更重要性）
- ⚠️ 小幅代碼重構（不改變功能）

**不創建標籤**：
- ❌ 開發中的實驗性功能
- ❌ 臨時修復
- ❌ 純粹的格式化調整

---

## 常見問題

### Q: 忘記在發布前創建標籤怎麼辦？

```bash
# 找到對應的 commit
git log --oneline

# 為該 commit 創建標籤
git tag -a vX.YY <commit-hash> -m "vX.YY: 補發標籤"
git push origin vX.YY
```

### Q: 標籤和 CHANGELOG 版本不一致怎麼辦？

以 CHANGELOG.md 為準，立即補充缺失的標籤：

```bash
# 找到 CHANGELOG 中的版本 commit
git log --oneline --all -- CHANGELOG.md | head -5

# 為正確的 commit 創建標籤
git tag -a vX.YY <correct-commit-hash> -m "vX.YY: 補發"
git push origin vX.YY
```

### Q: 如何查看某個版本的所有變更？

```bash
# 查看版本間的所有 commit
git log v5.95..v5.96 --oneline

# 查看版本間的所有檔案變更
git diff v5.95..v5.96 --stat
```

---

## 自動化建議

可在 `.git/hooks/post-commit` 添加鉤子，自動檢查：

1. CHANGELOG.md 是否更新
2. 版本號是否一致
3. 測試是否通過

建議的鉤子檢查：

```bash
#!/bin/bash
# post-commit hook

# 檢查 CHANGELOG 是否包含當前版本
if ! grep -q "$(git describe --tags --abbrev=0)" CHANGELOG.md 2>/dev/null; then
    echo "⚠️  警告：CHANGELOG.md 可能需要更新"
fi
```

---

*最後更新：v5.96*
