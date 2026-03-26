# TRACEABILITY_MATRIX.md - 需求追蹤矩陣

> 本文件追蹤需求從規格到實作到測試的完整鏈路

## ⚠️ 重要說明

- **Constitution 欄位**：必須通過 Constitution 檢查才能標記 ✅
- **狀態欄位**：只有 Constitution 通過且測試通過才能標記 ✅

## 需求追蹤表

| 需求 ID | 規格頁碼 | 實作檔案 | 測試檔 | Constitution | 狀態 |
|---------|----------|----------|--------|--------------|------|
| F1.1 | P1 | src/tts_engine.py | tests/test_tts_engine.py | ✅ | ✅ |
| ... | ... | ... | ... | ... | ... |

## 狀態說明

| 狀態 | 含義 |
|------|------|
| ⬜ 待處理 | 尚未開始 |
| 🔄 進行中 | 實作中 |
| ✅ 完成 | 實作+測試+Constitution 都通過 |
| ❌ 失敗 | 失敗 |

## CLI 整合

```bash
# 初始化追蹤矩陣
methodology trace init

# 檢查狀態
methodology trace check

# 更新狀態
methodology trace update F1.1 --status completed

# 生成報告
methodology trace report
```
