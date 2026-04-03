# Phase 1 SOP — 需求規格

> 本檔案為 On-demand Lazy Load 檔案，僅在執行 Phase 1 時載入。

## 執行步驟

**ROLE**:
- Agent A: `architect` — 撰寫 SRS.md, SPEC_TRACKING.md, TRACEABILITY_MATRIX.md
- Agent B: `reviewer` — 審查 FR 完整性、A/B 評估
- 禁止：自寫自審

**ENTRY**: 專案初始化完成

```
1. Agent A 撰寫 SRS.md（含邏輯驗證方法）
2. Agent A 初始化 SPEC_TRACKING.md
3. Agent A 初始化 TRACEABILITY_MATRIX.md
4. Agent B A/B 審查（5W1H 清單逐項確認）
5. Quality Gate: doc_checker + constitution + spec-track
6. 生成 Phase1_STAGE_PASS.md
7. python cli.py update-step / end-phase
```

## 進入條件

專案初始化完成

## 退出條件

TH-01 > 80%, TH-03 = 100%, TH-14 ≥ 90%, Agent B APPROVE

## 關鍵交付物

SRS.md, SPEC_TRACKING.md, TRACEABILITY_MATRIX.md
