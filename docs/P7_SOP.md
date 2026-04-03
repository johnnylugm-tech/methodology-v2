# Phase 7 SOP — 風險管理

> 本檔案為 On-demand Lazy Load 檔案，僅在執行 Phase 7 時載入。

## 執行步驟

**ROLE**:
- Agent A: `qa` 或 `devops` — 撰寫 RISK_REGISTER.md
- Agent B: `pm` 或 `architect` — 風險確認、演練
- 禁止：Decision Gate 未確認

**ENTRY**: Phase 6 APPROVE

```
1. Agent A 五維度風險識別
2. Agent A 建立 RISK_REGISTER.md
3. Agent B Decision Gate 確認（MEDIUM/HIGH）
4. Agent B 風險演練（如有 HIGH 風險）
5. Quality Gate: 邏輯正確性 ≥ 90
6. 生成 Phase7_STAGE_PASS.md
7. python cli.py update-step / end-phase
```

## 進入條件

Phase 6 APPROVE

## 退出條件

TH-07 ≥ 90, Decision Gate 100% 確認, Agent B APPROVE

## 關鍵交付物

RISK_REGISTER.md
