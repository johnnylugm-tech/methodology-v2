# Phase 5 SOP — 驗證交付

> 本檔案為 On-demand Lazy Load 檔案，僅在執行 Phase 5 時載入。

## 執行步驟

**ROLE**:
- Agent A: `devops` — 建立 BASELINE.md, MONITORING_PLAN.md
- Agent B: `architect` — 兩次審查
- 禁止：BASELINE 功能對照不完整

**ENTRY**: Phase 4 APPROVE, 測試通過率 = 100%

```
1. Agent A 建立 BASELINE.md（功能/品質/效能基線）
2. Agent B 基線審查
3. Agent A 建立 MONITORING_PLAN.md（四個監控維度）
4. Agent B 驗收報告審查
5. Quality Gate: logic checker ≥ 90 + constitution ≥ 80
6. 生成 Phase5_STAGE_PASS.md
7. python cli.py update-step / end-phase
```

## 進入條件

Phase 4 APPROVE, 測試通過率 = 100%

## 退出條件

TH-02 ≥ 80%, TH-07 ≥ 90, Agent B APPROVE

## 關鍵交付物

BASELINE.md, MONITORING_PLAN.md
