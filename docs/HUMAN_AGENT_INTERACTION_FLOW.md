# Human-Agent 互動流程 v6.13

> **版本**: v6.13  
> **目標**: Johnny -centric 審核流程  
> **核心原則**: Human-in-the-Loop (HITL) + AI 防作假機制

---

## 1. Johnny 工作流程總覽

```
初始化專案
    ↓
確認 Agent 理解（預熱程序 + 拷問法）
    ↓
發布任務
    ↓
Agent 執行
    ↓
HITL 審核（每 Phase 完成後）
    ↓
CONFIRM / QUERY / REJECT
    ↓
下一 Phase 或 修復
```

---

## 2. 三個核心機制（整合進流程）

### 2.1 預熱程序（每 Phase 開始前）

**目的**: 確保 Agent 已讀取並理解 SKILL.md

**Johnny 動作**: 無（Agent 自動執行）

**Agent 必須回答**:
1. Phase N 的 WHO（角色分工）定義是什麼？
2. Phase N 的 WHAT（交付物）清單有哪些？
3. Phase N 的 WHEN（時序門檻）是什麼？
4. Phase N 的 BLOCK 級別包含哪些檢查？
5. Phase N 的 Constitution 類型是什麼？

**通過標準**: 至少 3 題回答完整（每題 >20 字）

### 2.2 強制引用（所有 claims）

**目的**: Agent 的每個聲稱必須有 SKILL.md 依據

**Agent 格式**: `[SKILL.md line XXX]`

### 2.3 拷問法（Phase 完成後）

**目的**: 隨機抽查 Agent 對 SKILL.md 的理解深度

**Johnny 動作**: 隨機問 2-3 題

**範例問題**:
- FrameworkEnforcer BLOCK 級別包含幾項檢查？
- Constitution runner.py 的 command 是什麼？
- phase-verify 的分數門檻是多少？
- HR-05 的內容是什麼？

---

## 3. Johnny 標準作業流程

### Phase N 開始時

```
1. Johnny: 確認 Agent 通過預熱程序
2. Johnny: 發布任務目標和要求
3. Johnny: 設定 Phase N
4. Agent: 執行工作
5. Johnny: 執行拷問法（隨機 2-3 題）
6. Agent: 完成後通知 Johnny
7. Johnny: 執行 phase-verify --phase N
8. Johnny: 根據結果給出 CONFIRM/QUERY/REJECT
```

### Johnny 三種回應

| 回應 | 意義 | 動作 |
|------|------|------|
| ✅ CONFIRM | 通過 | 進入下一 Phase |
| ⚠️ QUERY | 有疑問 | Agent 必須回答問題 |
| ❌ REJECT | 不通過 | Agent 回到 Phase 重新執行 |

---

## 4. 每 Phase Johnny 必檢清單

### Johnny 只需要檢查這幾項

| Phase | 必檢內容 | CLI 指令 |
|-------|----------|----------|
| 1 | SRS.md 存在 + 隨機抽 3 條 FR | `python cli.py phase-verify --phase 1` |
| 2 | SAD.md 存在 + 模組邊界 | `python cli.py phase-verify --phase 2` |
| 3 | pytest 通過 + 覆蓋率 | `pytest --cov` |
| 4 | TEST_RESULTS.md pytest 輸出 | `python cli.py phase-verify --phase 4` |
| 5 | BASELINE.md 功能對照表 | `python cli.py phase-verify --phase 5` |
| 6 | QUALITY_REPORT.md 問題根源 | `python cli.py phase-verify --phase 6` |
| 7 | RISK_REGISTER.md 演練記錄 | `python cli.py phase-verify --phase 7` |
| 8 | CONFIG_RECORDS.md pip freeze | `python cli.py phase-verify --phase 8` |

---

## 5. CLI 速查（Johnny 最常用）

```bash
# Phase 真相驗證（必執行）
python cli.py phase-verify --phase N

# 預熱程序（Agent 執行）
python cli.py skill-check --mode preheat --phase N

# 拷問法（Johnny 執行）
python cli.py skill-check --mode interrogate --phase N

# Constitution 檢查
python quality_gate/constitution/runner.py --type srs

# Claims 驗證
python -c "from quality_gate.claims_verifier import ClaimsVerifier; print(ClaimsVerifier('.').verify_all())"
```

---

## 6. 常見問題處理

### 發現作假

```
1. Johnny: 執行 phase-verify --phase N
2. 分數 < 50%，高度可疑
3. Johnny: 詢問「這個分數是怎麼來的？」
4. 如果 Agent 回答模糊或矛盾
5. Johnny: REJECT
6. 累計 3 次，停止該 Agent 接任務
```

### Agent 跳過 Phase

```
1. 如果 Agent 聲稱完成 Phase N 但分數極低
2. Johnny: REJECT
3. Agent: 回到 Phase N-1 重新開始
```

---

## 7. 硬規則速查（Johnny 必知）

| ID | 規則 |
|----|------|
| HR-01 | A/B 必須不同 Agent，禁止自寫自審 |
| HR-02 | Quality Gate 必須有實際命令輸出 |
| HR-03 | Phase 必須順序執行，不可跳過 |
| HR-05 | 衝突時優先 methodology-v2 |
| HR-11 | Phase Truth 分數 < 70% 禁止進入下一 Phase |

---

## 8. 閾值速查（Johnny 必知）

| ID | 門檻 |
|----|------|
| TH-01 | ASPICE 合規率 > 80% |
| TH-10 | 測試通過率 = 100% |
| TH-11 | 單元測試覆蓋率 ≥ 70% |
| TH-12 | 單元測試覆蓋率 ≥ 80% |
| TH-14 | 規格完整性 ≥ 90% |
| TH-15 | Phase Truth 分數 ≥ 70% |

---

*最後更新: 2026-03-31*
*基於 methodology-v2 v6.13*
