# Phase 8 SOP — 配置管理

> 本檔案為 On-demand Lazy Load 檔案，僅在執行 Phase 8 時載入。

## 執行步驟

**ROLE**:
- Agent A: `devops` — 撰寫 CONFIG_RECORDS.md, Git Tag
- Agent B: `pm` 或 `architect` — 配置確認、封版審查
- 禁止：配置不完整、pip freeze 缺失

**ENTRY**: Phase 7 APPROVE

```
1. Agent A 撰寫 CONFIG_RECORDS.md（8 章節）
2. Agent A 執行 pip freeze / npm lock
3. Agent A 建立 Git Tag
4. Agent B 配置確認（七區塊逐項確認）
5. Agent B 封版審查
6. Quality Gate: 配置合規性確認
7. 生成 Phase8_STAGE_PASS.md
8. python cli.py update-step / end-phase
```

## 進入條件

Phase 7 APPROVE

## 退出條件

CONFIG_RECORDS.md 完整, pip freeze 存在, Git Tag 建立, Agent B APPROVE

## 關鍵交付物

CONFIG_RECORDS.md, Git Tag
