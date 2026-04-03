# Phase 4 SOP — 測試

> 本檔案為 On-demand Lazy Load 檔案，僅在執行 Phase 4 時載入。

## 執行步驟

**ROLE**:
- Agent A: `qa` — 撰寫 TEST_PLAN.md, TEST_RESULTS.md
- Agent B: `reviewer` — 兩次審查
- 禁止：Tester = Developer

**ENTRY**: Phase 3 APPROVE

```
1. Agent A 撰寫 TEST_PLAN.md
2. Agent B 第一次審查（測試策略）
3. Agent A 執行測試、記錄 TEST_RESULTS.md
4. Agent B 第二次審查（pytest 輸出真實性）
5. Quality Gate: pytest + constitution + spec_logic
6. Verify_Agent（Agent B < 80 或自評差異 > 20 時觸發）
7. 生成 Phase4_STAGE_PASS.md
8. python cli.py update-step / end-phase
```

**測試 Annotation**：`@covers`、`@type` → 詳見 `docs/ANNOTATION_GUIDE.md`

## 進入條件

Phase 3 APPROVE

## 退出條件

TH-01 > 80%, TH-03 = 100%, TH-06 > 80%, TH-10 = 100%, TH-12 ≥ 80%, TH-17 ≥ 90%

## 關鍵交付物

TEST_PLAN.md, TEST_RESULTS.md
