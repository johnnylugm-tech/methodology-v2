# methodology-v2 v6.22
> Agent Executable Specification — Need-to-know only. 詳細內容 on-demand lazy load。

---

## 0. 執行協議

```
1. READ  .methodology/state.json → current_phase
2. LOAD  本文件 Phase {N} 章節
3. CHECK 進入條件 → blocker fails → STOP
4. EXECUTE SOP → LAZY LOAD SKILL_TEMPLATES.md §T{N}.0
5.   RECORD actual command output | SPAWN A/B agent with persona
6. CHECK 退出條件 → fails → FIX + RETRY
7. UPDATE state.json phase=N+1 → GOTO 1
```

狀態鉤子：`python cli.py update-step --step N` / `python cli.py end-phase --phase N`
STAGE_PASS：`python cli.py stage-pass --phase N`
Phase Reset / CLI 完整命令 → **docs/CLI_REFERENCE.md**

---

## 1. 硬規則（違反即終止）

| ID | 規則 | 後果 |
|----|------|------|
| HR-01 | A/B 必須不同 Agent，禁自寫自審 | 終止 Integrity -25 |
| HR-02 | Quality Gate 必須有實際命令輸出 | 終止 -20 |
| HR-03 | Phase 順序執行，不可跳過 | 終止 -30 |
| HR-04 | HybridWorkflow mode=ON，強制 A/B | 終止 |
| HR-05 | 衝突時優先 methodology-v2 | 記錄 |
| HR-06 | 禁引入規格書/methodology-v2 外框架 | 終止 -20 |
| HR-07 | DEVELOPMENT_LOG 必須記錄 session_id | -15 |
| HR-08 | Phase 結束必須執行 Quality Gate | 終止 -10 |
| HR-09 | Claims Verifier 驗證必須通過 | 終止 -20 |
| HR-10 | sessions_spawn.log 必須存在有 A/B 記錄 | 終止 -15 |
| HR-11 | Phase Truth < 70% 禁進入下一 Phase | 終止 |
| HR-12 | A/B 審查 > 5 輪 | PAUSE 通知 Johnny |
| HR-13 | Phase 執行 > 預估 ×3 | PAUSE checkpoint |
| HR-14 | Integrity < 40 | FREEZE 全面審計 |

---

## 2. A/B 協作 + 負面約束

**禁止**：自寫自審(HR-01) · HybridWorkflow=OFF(HR-04) · sessions_spawn.log 缺失(HR-10) · 程式碼省略號`...`→任務失敗
**負面約束**：`unable_to_proceed` 不說明原因(-15) · 編造內容(-20) · Subagent 繼承父 context(-15)
**產出格式**（必填）：`status(success/error/unable_to_proceed)` | `result` | `confidence(1-10)` | `citations` | `summary(50字內)`
**Subagent 隔離**：每次 sessions_spawn 用獨立 fresh messages[]，不繼承父 Agent 上下文
詳細協議 → **docs/HYBRID_WORKFLOW_GUIDE.md**

---

## 3. 閾值（Quality Gate）

| ID | 指標 | 門檻 | 適用 Phase |
|----|------|------|-----------|
| TH-01 | ASPICE 合規率 | >80% | 1-8 |
| TH-02 | Constitution 總分 | ≥80% | 5-8 |
| TH-03 | Constitution 正確性 | =100% | 1-4 |
| TH-04 | Constitution 安全性 | =100% | 1-4 |
| TH-05 | Constitution 可維護性 | >70% | 2-4 |
| TH-06 | Constitution 測試覆蓋率 | >80% | 3-4 |
| TH-07 | 邏輯正確性分數 | ≥90 | 5-8 |
| TH-08 | AgentEvaluator 標準 | ≥80 | 1-2 |
| TH-09 | AgentEvaluator 嚴格 | ≥90 | 3-8 |
| TH-10 | 測試通過率 | =100% | 3-8 |
| TH-11 | 單元測試覆蓋率 | ≥70% | 3 |
| TH-12 | 單元測試覆蓋率 | ≥80% | 4-8 |
| TH-13 | SRS FR 覆蓋率 | =100% | 4-8 |
| TH-14 | 規格完整性 | ≥90% | 1 |
| TH-15 | Phase Truth | ≥70% | 1-8 |
| TH-16 | 代碼 ↔ SAD 映射率 | =100% | 3 |
| TH-17 | FR ↔ 測試映射率 | ≥90% | 4 |

驗證命令 → **docs/CLI_REFERENCE.md**

---

## 4. Phase 路由 + EXIT 條件

| Ph | 名稱 | Agent A/B | 關鍵交付物 | EXIT 條件 |
|----|------|-----------|-----------|----------|
| 1 | 需求規格 | architect/reviewer | SRS, SPEC_TRACKING, TRACEABILITY | TH-01,03,14; APPROVE |
| 2 | 架構設計 | architect/reviewer | SAD, ADR | TH-01,03,05; APPROVE |
| 3 | 代碼實現 | developer/reviewer | src/, tests/ | TH-06,08,10,11,16; APPROVE |
| 4 | 測試 | qa/reviewer | TEST_PLAN, TEST_RESULTS | TH-01,03,06,10,12,17 |
| 5 | 驗證交付 | devops/architect | BASELINE, MONITORING_PLAN | TH-02,07; APPROVE |
| 6 | 品質保證 | qa/architect | QUALITY_REPORT | TH-02,07; APPROVE |
| 7 | 風險管理 | qa/devops/architect | RISK_REGISTER | TH-07; Decision Gate 100%; APPROVE |
| 8 | 配置管理 | devops/architect | CONFIG_RECORDS, Git Tag | pip freeze 存在; APPROVE |

Phase SOP 詳細步驟 → **LAZY LOAD `SKILL_TEMPLATES.md §T{N}.0`**
Verify_Agent → Phase 3+，Agent B<80 或自評差異>20 時觸發 → **docs/VERIFIER_GUIDE.md**

---

## 5. STAGE_PASS 查核

**流程**：Agent A 自評(confidence+summary+citations) → Agent B 批判審查 → [疑問→回修 | APPROVE→下一 Phase]
**分數行動**：≥95 快速確認 | 80–94 仔細審查 | 70–79 特別注意 | <70 🔴 Flag 禁止進入
**Johnny 介入**：分數<50 | 作假(L6) | AB>5輪(HR-12) | 時間>3×(HR-13) | Integrity<40(HR-14) | BLOCK>5同維度

---

## 6. 錯誤處理 + 資源限制

**L1-L6**：輸入→立即返回 | 工具→重試3次 | 執行→降級 | 系統→熔斷+警報 | 驗證→停在Step修復 | 作假→終止扣分
**資源限制**：工具呼叫 60s | Step 最大 30min | Phase 最大 預估×3 (HR-13) | A/B 最多 5輪 (HR-12)

---

## 7. 外部文檔索引（Lazy Load）

| 觸發時機 | 文檔 |
|---------|------|
| Phase N SOP 執行步驟 | `SKILL_TEMPLATES.md §T{N}.0` |
| Phase N 文件模板 | `SKILL_TEMPLATES.md §T{N}.1+` |
| Phase 3 實作前（領域知識） | `SKILL_DOMAIN.md` |
| A/B 協作細節 | `docs/HYBRID_WORKFLOW_GUIDE.md` |
| CLI 命令 / Phase Reset | `docs/CLI_REFERENCE.md` |
| @FR/@covers Annotation | `docs/ANNOTATION_GUIDE.md` |
| Verify_Agent 流程 | `docs/VERIFIER_GUIDE.md` |
| Runtime Metrics / 煞車系統 | `docs/RUNTIME_METRICS_MANUAL.md` |
| Constitution 規範 | `docs/CONSTITUTION_GUIDE.md` |
| 開發日誌格式 | `docs/COWORK_PROTOCOL_v1.0.md` |
| 任務初始化 Prompt | `docs/TASK_INITIALIZATION_PROMPT.md` |

---
*methodology-v2 v6.22 | Agent Executable Specification | Last Updated: 2026-04-03*
