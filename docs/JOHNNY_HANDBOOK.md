# Johnny 使用手冊 v6.27

> **版本**: v6.27
> **對象**: Johnny（Human-in-the-Loop）
> **用途**: 快速上手 methodology-v2

---

## 1. methodology-v2 今天長什麼樣？

### v6.20 ~ v6.27 帶來的改善

| 版本 | 改善內容 |
|------|----------|
| v6.20 | 四大 Python 類：KnowledgeCurator / ContextManager / SubagentIsolator / PermissionGuard |
| v6.21 | MAIN_AGENT_PLAYBOOK.md + 審計修復 |
| v6.22 | Enhanced Exceptions（suggest_fix）+ Session Manager CLI |
| v6.23 | PHASE3_SOP.md 完整操作手冊 |
| v6.24 | SKILL.md 瘦身（131行）|
| v6.25 | 三層架構：Layer 1/2/3 |
| v6.26 | **run-phase 單一入口**（強制 Pre-flight checks）|
| **v6.27** | **plan-phase + run-phase 完整流程**，所有 P{N}_SOP.md 標準化 |

### 三層文件架構

| 層級 | 檔案 | 用途 |
|------|------|------|
| Layer 1 | SKILL.md（73行）| 核心規則（HR/TH/Phase路由）|
| Layer 2 | docs/P{N}_SOP.md（8檔）| Phase 詳細步驟（按需載入）|
| Layer 3 | templates/*.md（16檔）| 交付物模板（按需載入）|

---

## 2. 執行流程：plan-phase → Johnny 審核 → run-phase

> ⚠️ **所有 Phase 執行必須經過此流程**，不可繞過。

### 完整流程

```
Johnny: 「執行 Phase {N}」
    ↓
Agent: plan-phase --phase {N} --goal "..."
    ↓
Johnny: 看執行計畫（透明）
    ↓
Johnny: 「確認執行」
    ↓
Agent: run-phase --phase {N}
    ↓
失敗 → plan-phase --repair --step {N}.{X}
    ↓
成功 → 下一 Phase
```

### plan-phase 用法

```bash
# 生成執行計畫
python cli.py plan-phase --phase 3 --goal "FR-01~FR-03 實作"

# 修復迭代
python cli.py plan-phase --phase 3 --repair --step 3.2

# 查看歷史
python cli.py plan-phase --phase 3 --history
```

### run-phase 用法

```bash
python cli.py run-phase --phase 3
python cli.py run-phase --phase 3 --step 3.1 --task "FR-01 實作"
```

---

## 3. plan-phase 自動做什麼

```
┌─────────────────────────────────────────────────────────────┐
│  SCAN（讀取所有相關資料）                                      │
│                                                             │
│  1. SKILL.md → 核心規則                                      │
│  2. docs/P{N}_SOP.md → Phase 步驟                            │
│  3. .methodology/state.json → FSM 狀態                       │
│  4. .methodology/iterations/{phase}.json → 歷史迭代          │
│  5. 上階段交付物 → SRS/SAD/代碼等                            │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  PRE-FLIGHT（任一失敗就停止）                                 │
│                                                             │
│  1. FSM State Check → FREEZE/PAUSED 阻擋                  │
│  2. Phase Sequence → 不可跳過 Phase                          │
│  3. Constitution Check → <80% 阻擋                          │
│  4. Tool Registry Check → 工具狀態                            │
│  5. Session Save → Pre-flight 存檔                           │
└─────────────────────────────────────────────────────────────┘
                              ↓
                    ✅ 全部通過
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  EXECUTE                                                     │
│  6. Load docs/P3_SOP.md                                      │
│  7. Execute via SubagentIsolator（不直接 sessions_spawn）      │
│  8. PermissionGuard.check() before exec/rm                   │
│  9. Log to .methodology/run-phase.log                        │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  POST-FLIGHT                                                 │
│  10. Final Constitution Check                                 │
│  11. Update state.json                                       │
│  12. Report Summary                                          │
└─────────────────────────────────────────────────────────────┘
```

### Johnny 看到什麼

- Pre-flight 結果（✅/❌）
- Constitution 分數
- Session ID
- Log 檔位置

---

## 4. 快速開始

### 新專案初始化（第一次）

```
對 Agent 說：
「請根據 TASK_INITIALIZATION_PROMPT.md 初始化專案」

Agent 會：
- 讀取 SRS.md
- 建立 GitHub 倉庫
- 初始化 state.json
```

### Step 1: 發布任務

```
對 Agent 說：
「請執行 Phase {N}
- 任務目標：{具體目標}
- 交付物：{清單}
」
```

### Step 2: Agent 生成計畫

Agent 必須使用 `plan-phase`：

```
Agent: python cli.py plan-phase --phase {N} --goal "{任務目標}"
```

Johnny 看執行計畫（Step-by-Step、HR/TH 對照、風險評估）。

### Step 3: Johnny 審核計畫

```
如果計畫合理 → 「確認執行」
如果計畫有問題 → 「修改：{具體要求}」
```

### Step 4: Agent 執行

```
Agent: python cli.py run-phase --phase {N}
```

Johnny 等到執行完成，看結果。

### Step 5: Johnny 最終審核

```
1. 看 run-phase 輸出
2. 問 2-3 題拷問法
3. 如果正確 → ✅ CONFIRM
4. 如果錯誤 → ❌ REJECT
```

```
1. Johnny: 看 run-phase 輸出
2. Johnny: 問 2-3 題拷問法
3. 如果正確 → ✅ CONFIRM
4. 如果錯誤 → ❌ REJECT
```

---

## 4. 每 Phase 審核流程

### Agent 完成 Phase N 後

```
1. Johnny: 看 run-phase 輸出結果
2. Johnny: 問 2-3 題拷問法

   Constitution 分數 ≥80% + 拷問正確:
   → ✅ CONFIRM 或 ⚠️ QUERY

   Constitution 分數 <80%:
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

## 5. 拷問法範例

在 Agent 完成 Phase 後，隨機問這些問題：

### Phase 1 相關
- 「Phase 1 的 Constitution 類型是什麼？」
- 「TH-14 的門檻是多少？」

### Phase 2 相關
- 「HR-05 的內容是什麼？」
- 「Phase 2 的 Agent B 是什麼角色？」

### Phase 3 相關
- 「SubagentIsolator 和直接 sessions_spawn 的差別？」
- 「Pre-flight 有哪 5 個檢查？」

### Phase 5-8 相關
- 「TH-02 的門檻是多少？」
- 「Phase 8 必須有哪些交付物？」

---

## 6. 新工具速查（v6.20-v6.22）

### 四大工具

| 工具 | 解決的問題 | Agent 什麼時候用 |
|------|-----------|----------------|
| `KnowledgeCurator` | 知識一致性 | 派遣前 verify_coverage() |
| `ContextManager` | 上下文膨脹 | context > 50 時 compress() |
| `SubagentIsolator` | 結果污染 | 派遣時 spawn() |
| `PermissionGuard` | 危險操作 | exec/rm 前 check() |

### 新 CLI 命令

```bash
# 單一入口（v6.26）
python cli.py run-phase --phase N

# Tool Registry（v6.22）
python cli.py tool-registry --list
python cli.py tool-registry --get <tool>

# Session 管理（v6.22）
python cli.py session-save --id <name>
python cli.py session-list
python cli.py session-load --id <name>
python cli.py session-delete --id <name>

# 三層壓縮（v6.20）
python cli.py context-compress --level L1
python cli.py context-compress --level L2
python cli.py context-compress --level L3
```

---

## 7. CLI 速查

```bash
# 單一入口（必用）
python cli.py run-phase --phase N

# Phase 真相驗證
python cli.py phase-verify --phase N

# FSM 狀態
python cli.py fsm-status
python cli.py fsm-transition --to PAUSED
python cli.py fsm-unfreeze

# 預熱程序
python cli.py skill-check --mode preheat --phase N

# Constitution Check
python cli.py constitution check --type <srs|sad|test_plan|...>

# Tool Registry
python cli.py tool-registry --list

# Session 管理
python cli.py session-save --id <name>
python cli.py session-list
python cli.py session-load --id <name>
python cli.py session-delete --id <name>

# 狀態查詢
python cli.py status
python cli.py phase-status
```

---

## 8. Johnny 的三個狀態

```
🤚 等待中 - Agent 在執行 run-phase
👀 審核中 - Agent 完成，等 Johnny
✅/❌ 決策後 - CONFIRM 或 REJECT
```

---

## 9. 緊急情況

### 發現作假跡象
1. 看 run-phase 輸出
2. Constitution 分數 < 50%
3. 問 Agent：「這個分數怎麼來的？」
4. 回答模糊 → REJECT
5. 記錄到 MEMORY.md

### Agent 跳過 Phase
1. 分數極低但 Agent 說完成了
2. Johnny: REJECT
3. Agent: 回到上一 Phase

### Project FREEZE
1. run-phase 報錯「Project is FREEZE」
2. Johnny: 執行全面審計
3. Johnny: `python cli.py fsm-unfreeze`

---

## 10. 關鍵閾值速查

| 閾值 | 數值 | 用在哪 |
|------|------|--------|
| TH-01 | ASPICE > 80% | 所有 Phase |
| TH-02 | Constitution ≥ 80% | 所有 Phase |
| TH-10 | pytest = 100% | Phase 3-8 |
| TH-11 | 覆蓋率 ≥ 70% | Phase 3 |
| TH-12 | 覆蓋率 ≥ 80% | Phase 4-8 |
| TH-14 | 規格完整性 ≥ 90% | Phase 1 |
| TH-15 | Phase Truth ≥ 70% | 所有 Phase |

---

## 11. 硬規則速查

| 規則 | 內容 |
|------|------|
| HR-01 | A/B 必須不同 Agent，禁止自寫自審 |
| HR-02 | Quality Gate 必須有實際命令輸出 |
| HR-03 | Phase 必須順序執行，不可跳過 |
| HR-08 | Phase 結束必須執行 Quality Gate |
| HR-11 | Phase Truth < 70% 禁止進入下一 Phase |
| HR-12 | A/B 審查 > 5 輪 → PAUSE |
| HR-13 | Phase 時間 > 3× 預估 → PAUSE |
| HR-14 | Integrity < 40 → FREEZE |

---

*此手冊基於 methodology-v2 v6.27*
*最後更新: 2026-04-04*
