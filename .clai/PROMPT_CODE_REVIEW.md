# Gemini CLI Code Review Prompt
# Version: 2.0 (Anti-Hallucination Edition)
# Project: methodology-v2
# Last Updated: 2026-04-08

---

## 鐵則：禁止幻覺

**你必須遵守以下規則，否則審查結果將被視為無效：**

1. **每個聲稱的問題，必須在檔案中實際看到**
   - 不要猜測 `~line X` 或 `~function Y`
   - 必須用 `grep` / `grep -n` / `cat file | head -N` 實際確認問題存在
   - 如果找不到，誠實寫「**未能在實際檔案中確認此問題，建議人工覆核**」

2. **每個檔案路徑，必須與 git diff 或 ls 結果一致**
   - 用 `git diff --name-only v6.60..HEAD` 取得實際變更的檔案清單
   - 不要引用不在這個清單裡的檔案

3. **每個修復建議，必須是實際可行的**
   - 引用實際存在的函數名、變數名、類別名
   - 不要發明不存在的 API 或方法

4. **嚴禁以下行為**
   - ❌ 「根據以往經驗，這類代碼通常會有...」
   - ❌ 「這個模組通常使用...模式」
   - ❌ 「大約在第 150 行左右有...」
   - ❌ 引用不在 git diff 範圍內的歷史程式碼

5. **驗證你的發現**
   - 發現任何問題後，用 `python3 -m py_compile <file>` 驗證語法
   - 發現 import 問題時，用 `python3 -c "from <module> import <class>"` 驗證是否真的會 crash
   - 不確定的情況，誠實標記「需人工覆核」

---

## 審查範圍

### 目標版本
v6.XX → v6.YY（由使用者指定）

### 審查目標
```
cd /path/to/methodology-v2
git diff --name-only v6.XX..v6.YY | grep '\.py$'
```

### 審查重點（按優先順序）

#### 1. 🔴 Critical — 必定導致 crash 或資料損毀
- Import error 未處理（`except ImportError:` 沒有 `as e`）
- `subprocess` 未在模組層級 import
- 可選模組無條件 import（導致 CLI 無法啟動）
- 錯誤處理導致資料永久損毀（如整個 library 被清空）
- `returncode` 未檢查導致靜默失敗

#### 2. 🟡 Medium — 功能錯誤或隱藏 bug
- 靜默吃掉例外（`except: pass`）
- 編碼不一致（UnicodeDecodeError）
- 截斷邏輯導致假失敗（如 10k char 截斷）
- 時區/時間不一致
- Index 未更新導致資料過期
- 直接 mutation 破壞 API contract
- 型別 contract 不匹配

#### 3. 🟢 Low — 可維護性問題
- `eval()` 而非 `ast.literal_eval()`
- O(N²) 效能問題
- CWD-based 路徑（應用 app dir）
- Docstring 缺少重要欄位說明
- 業務邏輯計算可能膨風

---

## 執行流程

### Step 1：取得實際變更檔案清單
```bash
cd /path/to/methodology-v2
FILES=$(git diff --name-only v6.XX..v6.YY | grep '\.py$' | tr '\n' ' ')
echo "Files to review: $FILES"
```

### Step 2：先跑語法檢查
```bash
cd /path/to/methodology-v2
python3 -m py_compile $FILES
```
任何語法錯誤立即記錄為 Critical。

### Step 3：按批次審查（每批次 5-8 個檔案）

**批次 A - Core 架構（Constitution/BVS）**
```bash
gemini -p "Code review these files for the issues listed in CLAUDE.md. Use --approval-mode plan. Before claiming any issue exists, verify it by grepping the actual file content. If you cannot confirm an issue, mark it as 'UNVERIFIED - needs human review'." --approval-mode plan
```

**批次 B - Quality Gate**
```bash
gemini -p "Code review these files for the issues listed in CLAUDE.md. Use --approval-mode plan." --approval-mode plan
```

（其餘批次類推）

### Step 4：驗證發現的每個問題
對於聲稱的每個問題，必須執行：
```bash
# 驗證檔案存在
ls -la path/to/file.py

# 驗證問題程式碼存在
grep -n "problematic pattern" path/to/file.py

# 驗證 import 是否真的會失敗
python3 -c "from module import Class" 2>&1
```

### Step 5：輸出結構化報告
```
# Code Review Report - methodology-v2 v6.XX-v6.YY

## 🔴 Critical Issues (Must Fix)
[每個問題都要附上：檔案、行號(actual line number)、實際程式碼片段]

## 🟡 Medium Issues (Should Fix)
[同上]

## 🟢 Low Priority / Suggestions
[同上]

## ❌ Unverified Issues (Human Review Required)
[任何你無法在實際檔案中確認的問題]

## ✅ No Issues Found
[這些檔案看起來沒問題]

## Verification Log
[列出你執行過的所有驗證命令和結果]
```

---

## 問題嚴重性判斷標準

| 等級 | 標準 | 修復時機 |
|------|------|----------|
| 🔴 Critical | 確定會 crash / 資料損毀 / Security | 立即修 |
| 🟡 Medium | 功能錯誤或隱藏 bug | 下個版本修 |
| 🟢 Low | 可維護性 | 有空再修 |
| ❌ Unverified | 找不到證據 | 人工覆核 |

---

## 輸出格式要求

每個問題必須包含：
1. **檔案 + 實際行號**（用 `grep -n` 驗證過的）
2. **問題描述**（1-2 句）
3. **實際程式碼片段**（copy-paste）
4. **影響範圍**（什麼情況會觸發）
5. **修復建議**（具體的代碼改法，不要空泛的建議）

---

## 反幻覺檢查清單（每次輸出前自我檢查）

- [ ] 每個問題的檔案路徑都有在 `git diff --name-only` 清單中嗎？
- [ ] 每個問題的行號是用 `grep -n` 實際找到的嗎？
- [ ] 每個修復建議中的函數名/類別名在檔案中確實存在嗎？
- [ ] 我有沒有把「猜測」當成「發現」？
- [ ] 不確定的問題，有沒有標記為「需人工覆核」？
