# Annotation 規範手冊

> 讓 trace-check 能自動化追蹤 FR→SAD→代碼→測試 的覆蓋關係

---

## 1. 為什麼需要 Annotation

- 自動化溯源：trace-check 靠 annotation 比對覆蓋率
- 人工可讀：開發者一眼看出這段程式碼服務哪個需求
- 維護依据：重構時知道改動會影響哪些 FR

---

## 2. 代碼 Annotation（Phase 3）

### 位置
類別或函式的 docstring 開頭

### 三種 Annotation

| Annotation | 必要 | 位置 | 說明 | 範例 |
|------------|------|------|------|------|
| `@FR` | ✅ 必要 | docstring 開頭 | 對應的功能需求 ID | `@FR: FR-01` |
| `@SAD` | 建議 | 類別 docstring | 對應的 SAD 模組 | `@SAD: Module 1 - TextProc` |
| `@NFR` | 視需求 | docstring 開頭 | 對應的非功能需求 | `@NFR: NFR-02` |

### 正確範例

```python
class LexiconMapper:
    """
    @FR: FR-01
    @SAD: Module 1 - TextProc

    台灣中文詞彙映射器。
    對應 FR-01: LEXICON ≥ 50 詞
    """
    def map(self, text: str) -> list:
        """
        @FR: FR-01

        將文字中的國/異體字轉為候選詞。
        """
        pass
```

### 錯誤範例

```python
# ❌ 缺少 @FR
class LexiconMapper:
    """台灣中文詞彙映射器。"""

# ❌ @FR 放在錯誤位置（不在 docstring 開頭）
class LexiconMapper:
    """
    台灣中文詞彙映射器。
    @FR: FR-01  # ❌ 应该在最开头
    """

# ❌ FR-ID 格式錯誤
@FR: 01  # ❌ 应该是 FR-01
@FR: fr-01  # ❌ 应该是大寫 FR-01
```

### 多個 FR 的情況

```python
class AudioConverter:
    """
    @FR: FR-08, FR-09

    音訊格式轉換器，支援 MP3↔WAV。
    """
```

---

## 3. 測試 Annotation（Phase 4）

### 位置
測試函式的 docstring 開頭

### 兩種 Annotation

| Annotation | 必要 | 說明 | 範例 |
|------------|------|------|------|
| `@covers` | ✅ 必要 | 對應的功能需求 ID | `@covers: FR-01` |
| `@type` | ✅ 必要 | 測試類型 | `@type: positive` |

### 測試類型

| @type | 說明 | 何時使用 |
|-------|------|---------|
| `positive` | 正向測試 | 正常輸入，預期成功 |
| `negative` | 負向測試 | 錯誤輸入，預期失敗 |
| `boundary` | 邊界測試 | 邊界值測試 |

### 正確範例

```python
def test_lexicon_tone_word_replacement():
    """
    @covers: FR-01
    @type: positive

    測試「冬」替換為「技能」。
    """
    assert replace_tone("冬") == "技能"

def test_lexicon_empty_string():
    """
    @covers: FR-01
    @type: negative

    測試空字串回傳空 list。
    """
    assert replace_tone("") == []

def test_lexicon_250_char_boundary():
    """
    @covers: FR-01, FR-03
    @type: boundary

    測試 250 字 chunk 邊界。
    """
    result = chunk_text("a" * 250)
    assert len(result) == 2
```

### 錯誤範例

```python
# ❌ 缺少 @covers
def test_lexicon():
    """測試詞彙映射。"""

# ❌ 缺少 @type
def test_lexicon():
    """
    @covers: FR-01
    測試詞彙映射。
    """

# ❌ @type 值錯誤
@type: normal  # ❌ 应该是 positive/negative/boundary
```

---

## 4. Annotation 與 trace-check

### 命令

```bash
# SAD → 代碼溯源（Phase 3 EXIT）
python cli.py trace-check --from phase2 --to phase3

# FR → 測試溯源（Phase 4 EXIT）
python cli.py trace-check --from phase1 --to phase3-tests
```

### 輸出解讀

```markdown
### Mode: SAD → 代碼溯源
**覆蓋率: 85.7% (6/7)**

| FR-ID | SAD 模組 | 代碼檔案 | 狀態 |
|-------|---------|---------|------|
| FR-01 | TextProc | lexicon_mapper.py | ✅ |
| FR-02 | TextProc | ssml_parser.py | ✅ |
| FR-03 | TextProc | (missing) | ❌ ← 這裡有問題 |
```

---

## 5. 快速檢查清單

### Phase 3 代碼
- [ ] 每個類別有 `@FR: FR-XX`
- [ ] 每個 public 函式有 `@FR: FR-XX`
- [ ] FR-ID 格式正確（大寫 FR-XX）
- [ ] 多個 FR 用逗號分隔：`@FR: FR-01, FR-02`

### Phase 4 測試
- [ ] 每個測試函式有 `@covers: FR-XX`
- [ ] 每個測試函式有 `@type: positive/negative/boundary`
- [ ] FR-ID 格式正確（大寫 FR-XX）
- [ ] 關鍵 FR 有 boundary 測試

---

## 6. 常見問題

**Q: 一個函式服務多個 FR 怎麼辦？**
A: 用逗號分隔：`@FR: FR-01, FR-02`

**Q: 測試一個函式涵蓋多個 FR 怎麼辦？**
A: `@covers: FR-01, FR-03`

**Q: annotation 會影響程式效能嗎？**
A: 不會，annotation 只在 docstring 中，是純文字

**Q: trace-check 找不到 annotation 會怎樣？**
A: 該項目顯示 ❌（missing），不阻擋執行但影響覆蓋率
