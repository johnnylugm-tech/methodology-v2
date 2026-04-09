# HR-15 Citations 改善方案

> **日期**: 2026-04-10
> **問題觀察**: Phase 3 執行中 7/9 FRs 在第一輪因 Citations 缺失或行號錯誤被 REJECT
> **根本原因**: Developer 估算行號而非驗證行號，Reviewer 無法有效把關

---

## 現況問題分析

| 現象 | 原因 |
|------|------|
| Developer confidence 高（9-10）但 Citations 錯 | 行號來自估算，非實際驗證 |
| FR-03 Developer 錯誤聲稱 SAD.md 不存在 | 沒有實際讀取 SAD.md，只靠印象 |
| 7/9 FRs 第一輪 REJECT | 自評和實際品質有巨大落差 |

---

## 三層改善方案

### Layer 1: Developer Prompt 強化（最快落地）

**位置**: `templates/plan_phase_template.md` → Developer Prompt 區塊

**新增 FORBIDDEN**:
```markdown
【FORBIDDEN 新增】
- ❌ 沒有執行 grep 確認行號就寫入 docstring
- ❌ 沒有執行 grep 確認 Citations 寫入就返回 JSON
```

**新增強制步驟**:
```markdown
【強制執行步驟】

STEP 1: 讀取 SRS.md §FR-XX 和 SAD.md §對應章節

STEP 2: 用 grep 確認函數的實際行號：
```bash
grep -n "def 函數名\|class 類別名" app/xxx.py
```
把輸出的行號記下來（不是估算）

STEP 3: 實作 + 寫 docstring 時用 STEP 2 的實際行號

STEP 4: 寫完後再次 grep 確認：
```bash
grep -A5 "def 函數名" app/xxx.py | grep "Citations:"
```
確認 Citations 確實寫入且行號正確

STEP 5: 只通過 STEP 4 才能返回 JSON
```

---

### Layer 2: Reviewer Prompt 強化

**位置**: `templates/plan_phase_template.md` → Reviewer Prompt 區塊

**新增 REJECT_IF**:
```markdown
【REJECT_IF 新增】
- ❌ 沒有執行以下命令驗證 Citations 存在：
  ```bash
  grep -n "Citations:" app/xxx.py
  ```
  就直接宣稱「有 Citations」→「未實際驗證」→ REJECT
```

**驗證流程調整**:
```markdown
【 Citations 驗證流程】

1. 先執行：
   ```bash
   grep -n "Citations:" app/xxx.py
   ```
   確認有多少處有 Citations

2. 對照 docstring 數量，確認每個函數都有

3. 驗證行號範圍是否合理：
   - 檢查 docstring 內的 `SRS.md#L` 和 `SAD.md#L` 是否落於合理區間
   - 如：SRS.md 總行數 200，但引用 L500 → 不合理 → REJECT
```

---

### Layer 3: Framework 自動化驗證工具

**位置**: `quality_gate/verify_citations.py`（新建）

**功能**:
```python
def verify_citations(project_path: str, fr_id: str) -> dict:
    """
    自動驗證 Citations：
    1. 解析 docstring 中的 SRS.md#L 和 SAD.md#L
    2. 用實際行號讀取檔案內容
    3. 比對是否與 FR 內容相關
    4. 回傳 PASS/FAIL + 具體問題
    """
```

**觸發時機**: 
- Reviewer APPROVE 前自動呼叫
- 或作為 Quality Gate 的一環

**好處**: 
- 人肉檢查容易被騙，工具不會
- Framework 直接擋住錯誤

---

## 實作優先順序

| 優先順序 | 項目 | 預計難度 | 預計時間 |
|----------|------|----------|----------|
| 1 | Layer 1: Developer Prompt | 低 | 10 分鐘 |
| 2 | Layer 2: Reviewer Prompt | 低 | 10 分鐘 |
| 3 | Layer 3: verify_citations.py | 中 | 2-4 小時 |

---

## 預期效果

| 改善前 | 改善後 |
|--------|--------|
| 7/9 FRs REJECT Round 1 | 目標 2/9 FRs REJECT Round 1 |
| Citations 錯誤靠 Reviewer 肉眼發現 | 工具自動檢測 |
| Developer 自信 9/10 但全錯 | 必須通過 grep 驗證才能交卷 |

---

## 驗證方式

在下一個 Phase 3 專案執行時：
1. 測量第一輪 REJECT 率
2. 對比改善前的 7/9
3. 目標：REJECT 率降至 30% 以下

---

*本文件為 Phase 3 執行後的回顧改善建議*