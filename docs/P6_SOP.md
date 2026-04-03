# Phase 6 SOP — 品質保證

> 本檔案為 On-demand Lazy Load 檔案，僅在執行 Phase 6 時載入。

## 執行步驟

**ROLE**:
- Agent A: `qa` — 撰寫 QUALITY_REPORT.md
- Agent B: `architect` 或 `pm` — 品質確認
- 禁止：session_id 缺失

**ENTRY**: Phase 5 APPROVE

```
1. Agent A 收集 Phase 6 監控數據
2. Agent A 撰寫 QUALITY_REPORT.md（完整版）
3. Agent B 品質確認
4. Quality Gate: constitution ≥ 80 + 邏輯正確性
5. 生成 Phase6_STAGE_PASS.md
6. python cli.py update-step / end-phase
```

## 進入條件

Phase 5 APPROVE

## 退出條件

TH-02 ≥ 80%, TH-07 ≥ 90, Agent B APPROVE

## 關鍵交付物

QUALITY_REPORT.md
