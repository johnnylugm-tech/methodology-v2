# methodology-v2 改善方案

**基於 v574 專案學習**  
**日期**: 2026-03-28

---

## 一、現有問題診斷

### 1.1 Quality Gate 盲點

| 檢查維度 | 現有能力 | 盲點 |
|----------|----------|------|
| 代碼結構 | ✅ | 不檢查業務邏輯 |
| 命名規範 | ✅ | 不檢查語意正確性 |
| 測試覆蓋 | ✅ | 不檢查邊界條件 |
| 格式合規 | ✅ | 不檢查執行期行為 |

**核心問題**：Quality Gate 能檢查「形式合規」，無法保證「邏輯正確」

---

### 1.2 Spec Compliance 不足

**現有腳本能力**：
- ✅ 檢查「有沒有這個功能」
- ❌ 檢查「功能對不對」
- ❌ 檢查「邏輯是否符合 Spec」

**範例**：
```python
# 現有檢查：功能存在性
def check_audio_merge(self):
    return 'merge' in code  # 只檢查有這個字

# 應該檢查：邏輯正確性
def check_audio_merge_logic(self):
    # 1. 單一檔案是否與多檔案一致？
    # 2. 輸出格式是否統一？
    # 3. 是否有格式不一致的分支？
```

---

### 1.3 領域知識缺口

**TTS 專案教訓**：
- 標點 = 停頓信號，刪除會讓合成不自然
- 語速 -2% = 略慢，適合簡報
- 單檔案 ≠ 直接複製，應保持格式一致
- ffmpeg 初始化失敗 = 整個模組無法使用

**問題**：Agent 缺乏領域知識，導致「看似合理」的邏輯錯誤

---

### 1.4 測試設計 shallow

**現狀**：
- 只測「正常情況」
- 不測「邊界條件」
- 不測「輸出是否多於輸入」

**v574 案例**：
```python
# 測試了：正常分段
split("大家好。我是導引員。") → ["大家好", "我是導引員"]

# 沒測試：合併後是否多於原文？
_merge_chunks(["大家好", "我是導引員"]) → "大家好。我是導引員"  # ❌ 多於原文
```

---

## 二、改善方案

### 2.1 新增：Spec Logic Mapping（強制度）

#### 目標
確保每個 SRS 需求都有「邏輯驗證」而非僅「功能存在性」

#### 實作方式

```markdown
## Spec → Code 對照表（強制填寫）

| SRS ID | 需求描述 | 實作函數 | 邏輯驗證方法 |
|--------|---------|---------|-------------|
| FR-05 | 按標點分段，**保留標點** | split() | 輸出長度 ≤ 輸入長度 |
| FR-07 | 分段不超過 800 字 | _merge_chunks() | **輸出不插入多餘字符** |
| FR-19 | 多分段合併為單一輸出 | merge() | 單一檔案與多檔案**格式一致** |
```

#### 檢查腳本新增

```python
class SpecLogicValidator:
    """邏輯層面 Spec 驗證"""
    
    def verify_output_not_exceed_input(self, func, input_data):
        """驗證：輸出不應比輸入多任何字符"""
        result = func(input_data)
        return len(result) <= len(input_data)
    
    def verify_format_consistency(self, func, single_input, multi_input):
        """驗證：單一與多輸入格式一致"""
        single_result = func([single_input])
        multi_result = func(multi_input)
        return single_result.format == multi_result.format
```

---

### 2.2 新增：領域知識清單（SKILL.md）

#### 目標
為不同領域提供「領域知識檢查清單」

#### 實作方式

```markdown
## TTS 領域知識檢查清單

### 音訊處理
- [ ] 標點是否保留？（刪除會破壞停頓）
- [ ] 單一檔案是否與多檔案格式一致？
- [ ] ffmpeg 初始化是否 lazy check？

### 文字處理
- [ ] 合併後是否多於原文？
- [ ] 標點是否只在句尾？
- [ ] chunk_size 邊界是否正確處理？

### 網路處理
- [ ] timeout 是否設定？
- [ ] 重試邏輯是否區分錯誤類型？
- [ ] 熔斷器是否有成功閾值？
```

---

### 2.3 強化：負面測試要求

#### 目標
Test Plan 必須包含負面測試

#### 實作方式

```markdown
## Test Plan 必填項目（負面測試）

### 文字處理
- [ ] 空白輸入 → 應回傳空陣列
- [ ] 單一字元 → 應正常處理
- [ ] 超過 chunk_size 的單一句子 → 應正確分割
- [ ] **合併後檢查：輸出是否多於原文？**
- [ ] 沒有標點的長文本 → 應不崩潰

### 音訊處理
- [ ] 不存在的檔案 → 應拋出 FileNotFoundError
- [ ] 損壞的音訊 → 應優雅處理
- [ ] **單一檔案 vs 多檔案：格式是否一致？**

### 網路處理
- [ ] timeout → 應拋出 TimeoutError
- [ ] 連續失敗 → 熔斷器是否觸發？
- [ ] 無效設定 → 建構時是否驗證？
```

---

### 2.4 新增：集成測試模板

#### 目標
確保每個專案都有「文字 → 輸出」的端到端測試

#### 實作方式

```python
# tests/test_integration.py
class TestTextToAudio:
    """端到端集成測試"""
    
    def test_text_to_audio_preserves_punctuation(self):
        """驗證：輸出不應比輸入多字符"""
        text = "大家好。我是導引員。今天天氣好。"
        processor = TextProcessor()
        chunks = processor.split(text)
        
        # 關鍵：合併後的字符不應多於原文
        merged = ''.join(chunks)
        assert len(merged) <= len(text), "輸出多於原文！"
    
    def test_single_file_format_consistency(self):
        """驗證：單一檔案與多檔案格式一致"""
        merger = AudioMerger()
        
        single_output = merger.merge(["file1.mp3"], "single.mp3")
        multi_output = merger.merge(["file1.mp3", "file2.mp3"], "multi.mp3")
        
        # 格式應一致（bitrate, codec 等）
        assert get_format(single_output) == get_format(multi_output)
```

---

### 2.5 改進：Code Review 檢查清單

#### 目標
在 Constitution 之外增加「邏輯正確性」檢查

#### 實作方式

```markdown
## Code Review 邏輯正確性檢查清單

### 一般檢查
- [ ] 這個邏輯有「假設」嗎？假設合理嗎？
- [ ] 有「隱式行為」嗎？（如：split 會刪除標點）
- [ ] 邊界條件（0, 1, max）是否正確處理？

### 特定領域檢查（TTS）
- [ ] 輸出是否可能多於輸入？（字串操作）
- [ ] 單一情况是否與多情况一致？（分支邏輯）
- [ ] 外部依賴是否 lazy check？（初始化）

### 測試檢查
- [ ] 有「負面測試」嗎？
- [ ] 有「邊界測試」嗎？
- [ ] 有「輸出不超過輸入」的驗證嗎？
```

---

### 2.6 自動化：新增檢查腳本

#### 目標
自動檢查「邏輯正確性」

#### 實作方式

```python
# scripts/spec_logic_checker.py

class SpecLogicChecker:
    """自動檢查 Spec 邏輯正確性"""
    
    def check_string_manipulation(self, code, function_name):
        """檢查字串操作是否可能多於輸入"""
        issues = []
        
        # 檢查是否有 "+" 連接但沒有對應來源
        patterns = [
            r'\+ ["\'][\。？！]',  # 插入句號
            r'\+ " "',              # 插入空格
        ]
        
        for pattern in patterns:
            if re.search(pattern, code):
                issues.append(f"{function_name}: 可能插入額外字符")
        
        return issues
    
    def check_branch_consistency(self, code, function_name):
        """檢查分支是否一致"""
        # 檢查 if len(x) == 1 的特殊處理
        # 與一般情況是否一致
        pass
    
    def check_lazy_initialization(self, code, class_name):
        """檢查外部依賴是否 lazy check"""
        # 檢查 __init__ 是否直接呼叫外部依賴
        pass
```

---

## 三、实施优先级

| 優先級 | 項目 | 預期效益 | 實施難度 |
|--------|------|---------|---------|
| **P0** | Spec Logic Mapping | 防止「看似合理」的邏輯錯誤 | 中 |
| **P0** | 領域知識清單 | 彌補領域知識缺口 | 低 |
| **P1** | 負面測試要求 | 發現邊界問題 | 中 |
| **P1** | 邏輯正確性 Code Review | 彌補 Quality Gate 盲點 | 低 |
| **P2** | 集成測試模板 | 確保端到端正確 | 中 |
| **P2** | 自動化邏輯檢查 | 減少人為遺漏 | 高 |

---

## 四、預期效果

### 改善前 vs 改善後

| 維度 | 改善前 | 改善後 |
|------|--------|--------|
| Spec 映射 | 只檢查存在性 | 檢查邏輯正確性 |
| 測試設計 | 只測正常情況 | 包含負面測試 |
| Code Review | 形式合規 | + 邏輯正確性 |
| 領域知識 | 無 | 有清單 |
| 自動化 | 功能存在性 | + 邏輯正確性 |

### 具體效益

- **減少「看似合理」的 bug**：透過 Spec Logic Mapping 提前發現
- **提升測試品質**：負面測試 + 邊界測試
- **彌補 Quality Gate 盲點**：邏輯正確性檢查清單
- **避免領域知識缺口**：領域知識清單

---

## 五、總結

**核心問題**：Quality Gate 只能檢查「形式合規」，無法保證「邏輯正確」

**解決方案**：
1. **Spec Logic Mapping**：每個需求都要有邏輯驗證方法
2. **領域知識清單**：不同領域有不同的「隱式規則」
3. **負面測試**：故意測試「不正常」輸入
4. **邏輯正確性 Code Review**：超越格式檢查

**最終目標**：讓 Agent 不仅「做对了」，还要「想对了」

---

*方案完成時間: 2026-03-28*  
*基於 v574 專案學習產出*