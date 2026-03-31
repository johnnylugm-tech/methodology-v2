# Johnny 使用手冊 v6.13

> **版本**: v6.13  
> **對象**: Johnny（Human-in-the-Loop）  
> **用途**: 快速上手 methodology-v2

---

## 1. methodology-v2 今天長什麼樣？

### v6.13 帶來的改善

| 版本 | 改善內容 |
|------|----------|
| v6.12 | SKILL.md 瘦身 88%（4,612 → 561 行）|
| v6.13 | STAGE_PASS Agent A/B 審查流程 + 三個防作假機制 |

### 三個新機制

| 機制 | 作用 | Johnny 需要做什麼 |
|------|------|-----------------|
| 預熱程序 | 確保 Agent 讀過 SKILL.md | 無（Agent 自動）|
| 強制引用 | Agent claims 有 SKILL.md 依據 | 檢查格式 `[SKILL.md line XXX]` |
| 拷問法 | 抽查 Agent 理解深度 | 隨機問 2-3 題 |

---

## 2. 快速開始

### Step 1: 初始化專案

```
1. 對 Agent 說：
   「請根據 TASK_INITIALIZATION_PROMPT.md 初始化專案」
   
2. Agent 會：
   - 讀取 SRS.md
   - 建立 GitHub 倉庫
   - 初始化 state.json
```

### Step 2: 確認 Agent 理解

```
1. 對 Agent 說：
   「請執行預熱程序並報告結果」
   
2. Agent 報告後，問 2-3 題拷問法
   
3. 如果回答正確 → 繼續
4. 如果回答錯誤 → 要求 Agent 重讀 SKILL.md
```

### Step 3: 發布任務

```
對 Agent 說：
「請開始 Phase {N}
- 任務目標：{具體目標}
- 交付物：{清單}
- 截止時間：{如有}
」
```

---

## 3. 每 Phase 審核流程

### Agent 完成 Phase N 後

```
1. Johnny: 執行 `python cli.py phase-verify --phase N`
2. Johnny: 看分數

   分數 ≥70%:
   → 抽查 1-2 項手動確認
   → ✅ CONFIRM 或 ⚠️ QUERY

   分數 <70%:
   → ❌ REJECT
   → 要求 Agent 修復後重新提交
```

### Johnny 決策表

| 分數 | 等級 | Johnny 動作 |
|------|------|-------------|
| ≥95 | 🟢 完全合規 | 快速確認 |
| 80-94 | 🟢 高度合規 | 抽查後確認 |
| 70-79 | 🟡 基本合規 | 仔細檢查 |
| <70 | 🔴 可疑 | REJECT + 原因 |

---

## 4. 拷問法範例

在 Agent 完成 Phase 後，隨機問這些問題：

### Phase 1 相關
- 「Phase 1 的 Constitution 類型是什麼？」
- 「TH-14 的門檻是多少？」

### Phase 2 相關
- 「HR-05 的內容是什麼？」
- 「Phase 2 的 Agent B 是什麼角色？」

### Phase 3 相關
- 「pytest 覆蓋率的門檻是多少？」
- 「TH-08 和 TH-09 的差別？」

### Phase 5-8 相關
- 「TH-02 的門檻是多少？」
- 「Phase 8 必須有哪些交付物？」

---

## 5. Johnny 常見問題

### Q: 分數高就一定沒問題嗎？
A: 不一定。分數只是參考，發現可疑就要深究。

### Q: Agent 回答不上來怎麼辦？
A: 要求 Agent 重讀 SKILL.md 相關章節，再來一次。

### Q: 可以跳過 Phase 嗎？
A: 不行。HR-03 明確禁止。

### Q: 發現作假怎麼辦？
A: REJECT + 記錄。累計 3 次，踢掉該 Agent。

---

## 6. CLI 速查

```bash
# 初始化專案
python cli.py init "專案名稱"

# Phase 真相驗證（必執行）
python cli.py phase-verify --phase N

# 預熱程序（Agent 執行）
python cli.py skill-check --mode preheat --phase N

# 拷問法（Johnny 執行）
python cli.py skill-check --mode interrogate --phase N

# 生成 STAGE_PASS
python cli.py stage-pass --phase N

# 快速狀態
python cli.py status
```

---

## 7. Johnny 的三個狀態

```
🤚 等待中 - Agent 在執行
👀 審核中 - Agent 完成，等 Johnny
✅/❌ 決策後 - CONFIRM 或 REJECT
```

---

## 8. 緊急情況

### 發現作假跡象
1. 執行 `phase-verify --phase N`
2. 分數 < 50%
3. 問 Agent：「這個分數怎麼來的？」
4. 回答模糊 → REJECT
5. 記錄到 MEMORY.md

### Agent 跳過 Phase
1. 分數極低但 Agent 說完成了
2. Johnny: REJECT
3. Agent: 回到上一 Phase

---

## 9. 關鍵閾值速查

| 閾值 | 數值 | 用在哪 |
|------|------|--------|
| TH-01 | ASPICE > 80% | 所有 Phase |
| TH-10 | pytest = 100% | Phase 3-8 |
| TH-11 | 覆蓋率 ≥ 70% | Phase 3 |
| TH-12 | 覆蓋率 ≥ 80% | Phase 4-8 |
| TH-14 | 規格完整性 ≥ 90% | Phase 1 |
| TH-15 | Phase Truth ≥ 70% | 所有 Phase |

---

## 10. 硬規則速查

| 規則 | 內容 |
|------|------|
| HR-01 | A/B 必須不同 Agent，禁止自寫自審 |
| HR-02 | Quality Gate 必須有實際命令輸出 |
| HR-03 | Phase 必須順序執行，不可跳過 |
| HR-11 | Phase Truth < 70% 禁止進入下一 Phase |

---

*此手冊基於 methodology-v2 v6.13*
*最後更新: 2026-03-31*
