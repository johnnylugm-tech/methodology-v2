# Phase 2 SOP — 架構設計

> 本檔案為 On-demand Lazy Load 檔案，僅在執行 Phase 2 時載入。

## 執行步驟

**ROLE**:
- Agent A: `architect` — 撰寫 SAD.md, ADR
- Agent B: `reviewer` — 架構審查、Conflict Log
- 禁止：引入規格書外框架

**ENTRY**: Phase 1 APPROVE

```
1. Agent A 撰寫 SAD.md（含模組邊界圖）
2. Agent A 建立 ADR（如有技術選型）
3. Agent B 架構審查（5 維度）
4. Quality Gate: doc_checker + constitution + spec-track
5. 生成 Phase2_STAGE_PASS.md
6. python cli.py update-step / end-phase
```

## 進入條件

Phase 1 APPROVE

## 退出條件

TH-01 > 80%, TH-03 = 100%, TH-05 > 70%, Agent B APPROVE

## 關鍵交付物

SAD.md, ADR
