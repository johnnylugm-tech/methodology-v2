# TTS 專案改善建議報告

## 一、本次問題總結

本次檢測發現 tts-v2-full 專案與 PDF 規格書之間存在顯著落差，核心問題如下：

| 問題類型 | 數量 | 嚴重性 |
|----------|------|--------|
| 致命缺陷（功能不可用） | 1 | P0 |
| 重要缺失 | 2 | P1 |
| 部分實現 | 2 | P2 |

**根本原因**：PDF 規格書已提供正確實作，但專案實作者未完全參照。

---

## 二、已修復項目

| 項目 | 修復內容 |
|------|----------|
| 音訊合併 | 修正為逐一合併所有段落（cli.py） |
| 換行符分段 | 新增 `\n` 至分段標記（text_processor.py） |
| 熔斷器實作 | 完成狀態機制（CircuitBreaker 類別） |
| WAV 輸出 | 新增 audio_converter.py + CLI 參數 |

---

## 三、methodology-v2 需要調整之處

### 1. 規格書追蹤機制

**問題**：無法快速確認「實作是否完全遵循規格書」

**建議**：
```
# 在專案根目錄建立 SPEC_TRACKING.md
## 規格 vs 實作對照表
| 規格頁碼 | 規格要求 | 實作檔案/函數 | 狀態 |
|----------|----------|---------------|------|
| P6 | 音訊合併 | cli.py:75 | ✅ 已修復 |
| P8 | 換行符分段 | text_processor.py:16 | ✅ 已修復 |
| P6 | WAV 輸出 | audio_converter.py | ✅ 新增 |
```

**Action**：建立 `SPEC_TRACKING.md` 文件，逐條對照規格書與實作

---

### 2. Code Review 檢查清單

**問題**：致命缺陷（只複製第一段音訊）未在 Review 階段被發現

**建議**：在 methodology-v2 的 Code Review 階段增加以下檢查：

```
##  критичні перевірки (關鍵檢查)
- [ ] 迴圈是否處理所有項目（不只是第一筆）？
- [ ] 是否有空值/空陣列防護？
- [ ] 資源是否正確釋放（檔案、連線）？
- [ ] 錯誤處理是否完整（不只是 try-except-pass）？
```

**Action**：更新 `code_review_checklist.md`

---

### 3. 測試覆蓋策略

**問題**：核心功能（多段合併）缺乏測試

**建議**：在測試策略中強制要求「路徑完整性測試」：

```python
def test_multi_chunk_merge():
    """驗證所有段落都被正確合併"""
    chunks = ["第一段", "第二段", "第三段"]
    result = synthesize(chunks)
    
    # 驗證輸出檔案存在且大小合理
    assert os.path.exists(result)
    assert os.path.getsize(result) > sum(CHUNK_MIN_SIZE * len(chunks))
```

**Action**：更新 `test_strategy.md`，增加「路徑完整性」測試要求

---

### 4. 設計決策文件化

**問題**：部分實作與規格不符，但無從得知「為何偏離規格」

**建議**：建立 `DECISIONS.md`，記錄所有與規格書不同的實作：

```markdown
## 2026-03-26: 音訊合併實作

- **規格書要求**：逐一合併所有段落（PDF P6）
- **原始實作**：shutil.copy(temp_files[0])
- **偏離原因**：開發者誤解為「取第一段代表整體」
- **修復日期**：2026-03-26
- **修復方式**：改為逐一寫入
```

**Action**：建立 `DECISIONS.md` 模板

---

### 5. 自動化驗證 Script

**問題**：人工檢查容易遺漏

**建議**：建立 `scripts/verify_spec_compliance.py`

```python
#!/usr/bin/env python3
"""規格書合規性驗證"""
import ast
import re

def check_audio_merge_compliance():
    """檢查音訊合併是否正確"""
    with open("cli.py") as f:
        content = f.read()
    
    # 錯誤模式：shutil.copy(temp_files[0], ...)
    if re.search(r"shutil\.copy\(temp_files\[0\]", content):
        return False, "只複製第一段，未合併所有段落"
    
    # 正確模式：for ... in temp_files: ... write
    if "for temp_file in temp_files" in content and "write(f.read())" in content:
        return True, "正確合併所有段落"
    
    return False, "未找到合併邏輯"
```

**Action**：新增驗證腳本

---

## 四、調整優先級

| 優先級 | 項目 | 預期價值 |
|--------|------|----------|
| P0 | SPEC_TRACKING.md | 防止規格脫鉤 |
| P1 | Code Review 檢查清單 | 快速發現問題 |
| P2 | 自動化驗證 Script | 長期品質保障 |
| P3 | DECISIONS.md | 記錄偏離原因 |

---

## 五、總結

本次問題源於「規格書閱讀不完整」與「缺乏對照機制」，而非技術能力不足。

**methodology-v2 的核心強化方向**：
1. 建立「規格→實作」的追蹤表
2. Code Review 增加關鍵路徑檢查
3. 自動化合規性驗證

這樣可以確保未來專案不會再出現「規格書有正解但實作漏掉」的狀況。