# 檢查項目更新程序

> 當需要新增或修改檢查項目時，遵循本程序確保一致性

---

## 📋 更新流程

當需要新增檢查項目時：

### 步驟 1: 更新增強檢查清單

編輯 `quality_gate/enhanced_checklist.md`：

```markdown
## ⚠️ 關鍵檢查 (Critical) - 必須通過

### N. 新檢查項目
```
[ ] 新檢查項目描述
```

**典型錯誤模式**：
```python
# ❌ 錯誤：xxx
# ✅ 正確：xxx
```
```

### 步驟 2: 在 SPEC_TRACKING.md 標記新檢查項目

```markdown
### 技術架構

| 規格頁碼 | 規格要求 | 實作檔案/函數 | 狀態 | 備註 |
|----------|----------|--------------|------|------|
| PN | 新檢查項目對應的規格 | impl.py:func() | ⚠️ 待處理 | 新增檢查 |
```

### 步驟 3: 更新驗證腳本

編輯 `scripts/verify_spec_compliance.py`：

```python
def check_new_item(self):
    """檢查新項目"""
    new_file = self.project_path / "src" / "new.py"
    
    if not new_file.exists():
        self.issues.append("新項目：new.py 不存在")
        return
    
    content = new_file.read_text()
    
    if "expected_pattern" in content:
        self.passed.append("新項目：已正確實現")
    else:
        self.issues.append("新項目：未找到 expected_pattern")
```

### 步驟 4: 更新決策框架（如需要）

如果新檢查項目影響決策邏輯，更新 `DECISION_FRAMEWORK.md`：

```markdown
### QN: 新決策問題？

使用以下矩陣判斷：
...
```

### 步驟 5: 更新意圖分類（如需要）

如果涉及 PDF 規格書解讀，更新 `spec_intent_classifier.md`：

```markdown
### N. 新分類（MUST/SHOULD/MAY）

**關鍵詞識別**：
- 「xxx」
- 「yyy」

**處理方式**：
...
```

### 步驟 6: 提交前確認

確保所有檢查通過：

```bash
# 執行完整檢查流程
python3 cli.py spec-track check
python3 decision_gate/framework_integrator.py .
python3 scripts/verify_spec_compliance.py .
python3 cli.py quality-gate
```

---

## 🔄 版本管理

### 版本號規則

- **主版本 (v5.x.0)**：新增 major 功能或大幅修改檢查邏輯
- **次版本 (v5.49.x)**：新增檢查項目或修改現有檢查
- **修正版 (v5.49.1)**：修正錯誤或更新描述

### CHANGELOG 更新

每次更新需在 `CHANGELOG.md` 記錄：

```markdown
## v5.49.1 - YYYY-MM-DD

### 新增
- [quality_gate] 新增檢查項目：xxx

### 修改
- [enhanced_checklist.md] 更新檢查描述：xxx

### 修正
- [verify_spec_compliance.py] 修正檢查邏輯：xxx
```

---

## 📝 審查清單

更新前確認：

- [ ] 新檢查項目是否已有明確的「正確」和「錯誤」模式？
- [ ] 新檢查項目是否適合自動化？（如果不能自動化，標記為「手動檢查」）
- [ ] 是否需要更新 SPEC_TRACKING.md 模板？
- [ ] 是否需要更新 DECISION_FRAMEWORK.md？
- [ ] CHANGELOG.md 是否已更新？
- [ ] 所有現有檢查是否仍然通過？

---

## ⚠️ 注意事項

1. **不要破壞現有檢查**：修改時確保現有檢查仍然有效
2. **保持一致性**：新檢查的格式和風格應與現有檢查一致
3. **文件同步**：同時更新對應的文件，不要只更新代碼
4. **測試驗證**：修改後執行完整檢查流程確認

---

## 📞 整合進 Quality Gate

所有更新的檢查項目會在以下時機自動執行：

1. `python3 cli.py quality-gate` - 完整 quality gate
2. `python3 cli.py spec-track check` - 規格追蹤檢查
3. Pre-commit hook（如已啟用）

---

*建立日期：2026-03-26*
*整合進 methodology-v2 v5.49+*
