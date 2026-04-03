# Phase 3 SOP — 代碼實現

> 本檔案為 On-demand Lazy Load 檔案，僅在執行 Phase 3 時載入。

## 執行步驟

**ROLE**:
- Agent A: `developer` — 代碼實作、單元測試
- Agent B: `reviewer` — 同行邏輯審查
- 禁止：自寫自審、引入第三方框架

**ENTRY**: Phase 2 APPROVE

```
FOR EACH 模組:
  1. Agent A 實作模組（含規範標注）
  2. Agent A 撰寫單元測試（正向/邊界/負面三類）
  3. Agent A 填寫邏輯審查對話 Developer 部分
  4. Agent B 同行邏輯審查（填寫 Architect 確認部分）
  5. Agent B 確認測試完整性
  6. Quality Gate: pytest + coverage + constitution
  7. Verify_Agent（Agent B < 80 或自評差異 > 20 時觸發）
  8. 生成合規矩陣 + Phase3_STAGE_PASS.md
  9. python cli.py update-step / end-phase
```

**代碼規範**：`@FR`、`@SAD`、`@NFR` annotation → 詳見 `docs/ANNOTATION_GUIDE.md`

## 進入條件

Phase 2 APPROVE

## 退出條件

TH-06 > 80%, TH-08 ≥ 80/90, TH-10 = 100%, TH-11 ≥ 70%, TH-16 = 100%, Agent B APPROVE

## 關鍵交付物

src/, tests/
