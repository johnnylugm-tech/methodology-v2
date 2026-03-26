# TRACEABILITY_MATRIX.md - 需求追蹤矩陣

> 本文件追蹤需求從規格到實作到測試的完整鏈路

## 使用方式

每次新增需求時，在下方表格新增一列。

## 需求追蹤表

| 需求 ID | 規格頁碼 | 實作檔案 | 測試檔 | Constitution 檢查 | 狀態 |
|---------|----------|----------|--------|-------------------|------|
| F1.1 | P1 | src/tts_engine.py | tests/test_tts_engine.py | ✅ | ✅ 完成 |
| F1.2 | P2 | src/text_processor.py | tests/test_text_processor.py | ✅ | ✅ 完成 |
| ... | ... | ... | ... | ... | ... |

## 更新原則

- 每次完成一個需求，更新狀態為 ✅
- 每次發現問題，在備註欄記錄
- 定期更新 Constitution 檢查結果

## CLI 整合

```bash
# 初始化追蹤矩陣
methodology trace init

# 更新狀態
methodology trace update F1.1 --status "in-progress"

# 生成報告
methodology trace report
```
