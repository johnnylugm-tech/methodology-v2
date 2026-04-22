# Feature #1-13 整合評估報告 v1.0

**Date:** 2026-04-22
**Version:** 1.0
**Author:** Agent A (Reviewer/Main Agent)
**Status:** Complete — Awaiting Decision

---

## 一、當前狀態：13 個 Feature 是「封閉套件」

所有 Features #1-13 目前是獨立的 `implement/feature-XX-name/` 目錄（#1-5 在 `implement/{mcp,security,governance,kill_switch,llm_cascade}/`）。

**尚未與 methodology-v2 主流程 wire 在一起。**

---

## 二、完整 Layer 架構圖

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 6: Compliance    ← #12 EU AI Act / NIST / RSP v3.0       │
│  生成合規報告、audit trail、regulatory mapping                    │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 5: Risk Assessment ← #9 8-維度風險評估引擎                │
│  每 Phase 完成時主動識別/量化/追蹤風險                            │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 4: Executive Assurance ← #6 Hunter Agent                 │
│  Anomaly Detection + Self-Correction + MetaQA Baseline           │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 3: Intelligence                                           │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────────┐  │
│  │ UQLM (#7)    │ │ LangGraph    │ │ Gap Detector (#8)      │  │
│  │ Hallucination│ │ (#10)        │ │ (Phase 4 gate trigger) │  │
│  │ Detection    │ │ 有狀態多步    │ └────────────────────────┘  │
│  │ + CLAP Probe │ │ 驟規劃        │                             │
│  └──────────────┘ └──────────────┘                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ LLM Cascade (#5) — 多 provider 路由 + speculative debate │  │
│  └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 2: Governance & Reliability                               │
│  ┌──────────────┐ ┌──────────────┐                             │
│  │ #3 HOTL/HITL │ │ #4 Kill-Switch│                            │
│  │ Tiered Gov.  │ │ Circuit Breaker│                            │
│  └──────────────┘ └──────────────┘                             │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 1.7: Prompt Shields (#2) — Injection / PII detection     │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 1.5: MCP + SAIF 2.0 (#1) — Identity propagation          │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 0: Observability Foundation                               │
│  ┌──────────────┐ ┌──────────────────────────────────────────┐ │
│  │ Langfuse(#11)│ │ #13 UQLM metrics + Decision Log + Effort  │ │
│  │ Trace/Capture│ │  (enriches Langfuse spans)                 │ │
│  └──────────────┘ └──────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## 三、Feature 現況對照表

| Feature | 名稱 | Layer | 目前位置 | 獨立 Package？ |
|---------|------|-------|---------|--------------|
| #1 | MCP + SAIF 2.0 | Layer 1.5 | `implement/mcp/` | 否，已模組化 |
| #2 | Prompt Shields | Layer 1.7 | `implement/security/` | 否，已模組化 |
| #3 | HOTL/HITL/HOOTL | Layer 2 | `implement/governance/` | 否，已模組化 |
| #4 | Kill-Switch | Layer 2 | `implement/kill_switch/` | 否，已模組化 |
| #5 | LLM Cascade | Layer 3 | `implement/llm_cascade/` | 否，已模組化 |
| #6 | Hunter Agent | Layer 4 | `implement/feature-06-hunter/` | 是 |
| #7 | UQLM Ensemble | Layer 3 | `implement/feature-07-uqlm/` | 是 |
| #8 | Gap Detector | Phase Gate | `implement/feature-08-gap-detector/` | 是 |
| #9 | Risk Assessment | Layer 5 | `implement/feature-09-risk-assessment/` | 是 |
| #10 | LangGraph | Layer 3 | `implement/feature-10-langgraph/` | 是 |
| #11 | Langfuse | Layer 0 | `implement/feature-11-langfuse/` | 是 |
| #12 | EU AI Act / NIST | Layer 6 | `implement/feature-12-compliance/` | 是 |
| #13 | UQLM metrics + Decision Log + Effort | Layer 0 | `implement/feature-13-observability/` | 是 |

---

## 四、整合順序（5 個 Stage）

### Stage 1：Observability Foundation（最先做）

**為什麼先做**：所有上層功能都需要統一的 trace/log 基礎設施

| 順序 | Feature | 現況 | 整合目標 |
|------|---------|------|---------|
| **1-1** | #11 Langfuse | `feature-11-langfuse/` 獨立 package | 將 `ml_langfuse/` 追蹤寫入 `implement/langfuse/`，成為 gateway plugin |
| **1-2** | #13 Observability | `feature-13-observability/` 獨立 package | 串入 Langfuse：每個 span 附加 `uqlm.uaf_score`、`decision_log`、effort metrics |

**整合方法**：
```python
# gateway 啟動時初始化
from ml_langfuse import LangfuseClient, observe
from observability import setup_observability

lf = LangfuseClient()
uqlm, decision_log, effort = setup_observability(tracer=lf.tracer)

# 所有 agent step 都會自動寫入 Langfuse trace
@observe
async def agent_step(agent_id, task):
    effort.start(agent_id, trace_id=lf.trace_id)
    # ... execution ...
    effort.stop(effort_id)
```

**預期好處**：後續所有層的 trace 都包含完整 context，debug 效率提升 10x

**預估工期**：2-3 天

**風險**：低（不改動任何現有模組，只新增 adapter）

---

### Stage 2：Core Pipeline Wiring（第二步）

**為什麼第二步**：把 Features #1-5 的 standalone modules 變成真正的 cohesive pipeline

| 順序 | Feature | 現況 | 整合目標 |
|------|---------|------|---------|
| **2-1** | #1 MCP + SAIF | `implement/mcp/` 存在但未鉤入 | SAIF middleware 自動注入 agent_id/scopes 到每個 incoming/outgoing message |
| **2-2** | #2 Prompt Shields | `implement/security/` 存在但獨立 | 在 LLM call 前通過 Shield filter input/output |
| **2-3** | #3 Governance | `implement/governance/` 存在但未被調用 | 任何 LLM decision 都要經過 `TierClassifier.classify()` → 輸出 HOTL/HITL/HOOTL |
| **2-4** | #5 LLM Cascade | `implement/llm_cascade/` 存在但繞過 Governance | cascade 的 router 回讀 Governance decision 來決定是否多模型 consensus |
| **2-5** | #4 Kill-Switch | `implement/kill_switch/` 存在但未被觸發 | Governance Tier.HITL + HealthMonitor 雙重觸發條件 |

**整合方法**：
```python
# Agent runtime pipeline
async def agent_run(agent_id, task, message):
    # Layer 1.5: Identity propagation
    saif_token = SAIFMiddleware.create_token(agent_id, scopes=["read", "write"])
    message = saif_token.inject(message)

    # Layer 1.7: Prompt Shield
    shield_verdict = PromptShield.scan(message)
    if shield_verdict == Verdict.BLOCK:
        raise InjectionBlockedError()

    # Layer 2: Governance classification
    ctx = GovernanceContext(agent_id=agent_id, task=task, identity_propagated=True)
    tier = tier_classifier.classify(ctx)
    if tier == Tier.HITL:
        await wait_for_human_approval(task)

    # Layer 3: LLM Cascade (read governance decision)
    result = await llm_cascade.execute(task, require_consensus=(tier==Tier.HOTL))
```

**預期好處**：Features #1-5 從「獨立功能」變成「cohesive pipeline」，agent 行為一致性大幅提升

**預估工期**：3-4 天

**風險**：中（需要修改 Features #1-5 的調用方式，可能影響現有測試）

---

### Stage 3：Intelligence Layer Activation（第三步）

**為什麼第三步**：Layer 3（Intelligence）整合 UQLM、LangGraph、Hunter Agent

| 順序 | Feature | 現況 | 整合目標 |
|------|---------|------|---------|
| **3-1** | #10 LangGraph | `feature-10-langgraph/` 存在 | LangGraph 包裝 LLM Cascade，消除 stateless limitation；Planner 在 Graph nodes 間有狀態記憶 |
| **3-2** | #7 UQLM | `feature-07-uqlm/` 存在 | 每個 LLM response 後跑 `UqlmEnsemble.compute()` → 結果寫入 LangGraph state |
| **3-3** | #6 Hunter Agent | `feature-06-hunter/` 存在 | 訂閱 message bus；UQLM uncertainty > threshold 時自動介入做 anomaly detection |

**整合方法**：
```python
# LangGraph state machine
def planner_node(state: AgentState):
    response = llm_cascade.invoke(state.messages)
    uncertainty = uqlm.compute(prompt=state.messages, response=response)
    if uncertainty.uaf_score > 0.7:
        return {"next": "hunter_review", "uncertainty": uncertainty}
    elif uncertainty.uaf_score > 0.4:
        return {"next": "debate_round_2", "uncertainty": uncertainty}
    else:
        return {"next": "execute", "uncertainty": uncertainty}

def hunter_review_node(state: AgentState):
    anomaly = hunter.detect(state.messages, state.uncertainty)
    if anomaly.confirmed:
        return {"next": "regenerate", "reason": anomaly.reason}
    return {"next": "execute"}

def debate_round_2_node(state: AgentState):
    # Speculative debate: second model challenges first
    second_opinion = llm_cascade.execute(state.messages, model="claude-3")
    alignment = uqlm.compute_alignment(state.response, second_opinion)
    if alignment < 0.3:
        return {"next": "hunter_review", "uncertainty": state.uncertainty}
    return {"next": "execute"}
```

**預期好處**：
- Hallucination 早期攔截（預估減少 30-50% 錯誤決策）
- Stateless → Stateful 多步驟規劃
- Multi-model debate 提升答案質量

**預估工期**：4-5 天

**風險**：高（LangGraph 可能破壞現有 LLM Cascade 架構）

---

### Stage 4：Quality Gates Automation（第四步）

**為什麼第四步**：將 Phase gate 變成常態化品質檢查

| 順序 | Feature | 觸發時機 | 整合目標 |
|------|---------|---------|---------|
| **4-1** | #8 Gap Detector | Phase 4 測試完成 | 自動掃描 `04-tests/` 覆蓋缺口，產出 `GAP_REPORT.md` |
| **4-2** | #9 Risk Assessment | 每個 Phase 完成 | Phase outcome → `RiskAssessor.scan()` → 更新 risk register + 通知相關 layer |

**整合方法**：
```python
# Phase completion hook
def after_phase(phase_id, deliverables):
    if phase_id == 4:
        # Gap Detector: scan test coverage
        gaps = gap_detector.scan("04-tests/")
        if gaps:
            logger.warning(f"Coverage gaps found: {len(gaps)} gaps")
            deliver("GAP_REPORT.md", gaps)
    
    # Risk Assessment: register phase outcome
    risk_assessor.register_outcome(
        phase=phase_id,
        status="PASS" if all(deliverables) else "FAIL",
        artifacts=deliverables
    )

# Feature #9 risk assessment integration
def risk_phase_gate(phase_id):
    findings = risk_assessor.scan(phase_id)
    risk_register.update(findings)
    if any(f.severity > 0.8 for f in findings):
        notify_human(f"High-severity risks detected in Phase {phase_id}")
    return findings
```

**預期好處**：
- 測試覆蓋缺口在 Phase 4 即時發現（不是事後補救）
- 風險評估常態化，每個 Phase 都產出 risk register update

**預估工期**：2-3 天

**風險**：低（Phase gate hooks 是新增，不是修改現有邏輯）

---

### Stage 5：Compliance Enforcement（第五步）

**為什麼最後做**：需要所有上層組件就位才能生成完整的合規報告

| 順序 | Feature | 整合點 | 整合方法 |
|------|---------|--------|---------|
| **5-1** | #12 Compliance | Kill-Switch 觸發 | `compliance.report_kill_event(event)` → EU AI Act Art.14 report |
| **5-2** | #12 Compliance | HITL 審批 | `compliance.record_approval(decision)` → NIST AI RMF "Manage" 函數 |
| **5-3** | #12 Compliance | LLM Cascade routing | `compliance.log_model_choice(provider)` → NIST AI RMF "Measure" 函數 |

**整合方法**：
```python
# Kill-Switch trigger → EU AI Act Art.14 report
if circuit_breaker.should_trigger():
    compliance.report_kill_event(
        event=KillEvent(
            agent_id=agent_id,
            trigger="health_monitor",
            timestamp=datetime.utcnow()
        )
    )

# HITL approval → NIST AI RMF Manage function
if human.approved(decision):
    compliance.record_approval(
        decision=decision,
        NIST_function="Manage",
        EU_AI_Act_article="14(4)(b)"
    )

# Hunter Agent anomaly → NIST Monitor function
if hunter.anomaly_detected:
    compliance.log_monitoring_event(
        anomaly=hunter.anomaly,
        NIST_function="Monitor"
    )
```

**預期好處**：
- EU AI Act Art.14 合規 audit trail 自動生成
- NIST AI RMF 五函數（Govern/Monitor/Measure/Map/Manage）100% mapped
- Anthropic RSP v3.0 ASL-3 sign-off 自動化

**預估工期**：2-3 天

**風險**：低（#12 是新增合規層，不修改任何現有功能）

---

## 五、整合方式：6 種 Wire 類型

| 類型 | 適用場景 | 技術 | 範例 |
|------|---------|------|------|
| **Plugin Registration** | Gateway 啟動時加載 | `gateway.register_plugin("shield", PromptShield())` | Stage 2 |
| **Decorator Wrapper** | LLM call 前後 | `@observe` decorator 自動寫 Langfuse | Stage 1 |
| **Event Bus Subscription** | Cross-layer 訊息 | `message_bus.subscribe(agent_id="*", callback=hunter.on_message)` | Stage 3 |
| **State Pass-Through** | LangGraph node 間傳遞 | `state["uncertainty"]` / `state["risk_score"]` | Stage 3 |
| **Phase Gate Hook** | 每 Phase 完成時 | `after_phase(phase=4, callback=gap_detector.scan)` | Stage 4 |
| **Health Monitor Feed** | Kill-Switch 觸發條件 | `health_monitor.on_failure(provider)` → circuit breaker | Stage 2 |

---

## 六、預期好處（13 個 Feature 整合後）

| 好處 | 來自 Feature | 量化 |
|------|-------------|------|
| 身份盜用防護 | #1 MCP + SAIF 2.0 | 100% message 帶 valid token |
| Injection 攔截 | #2 Prompt Shields | 已知 pattern 100% 攔截 |
| 高風險決策人類把關 | #3 Governance + #12 | HOTL/HITL/HOOTL 100% 強制執行 |
| 多模型冗余共識 | #5 LLM Cascade + #7 UQLM | UAF > 0.7 時自動多模型共識 |
| 有狀態多步驟規劃 | #10 LangGraph | stateless → stateful |
| Hallucination 早期攔截 | #7 + #6 + #13 | 預估減少 30-50% 錯誤決策 |
| 測試覆蓋即時反饋 | #8 Gap Detector | Phase 4 gate 即時發現缺口 |
| 風險常態化監控 | #9 Risk Assessment | 每 Phase 產出 risk register update |
| 合規報告自動生成 | #12 Compliance | EU AI Act + NIST AI RMF 100% mapped |
| 完全 trace 覆蓋 | #11 + #13 | 100% span 帶 UQLM + decision + effort |
| 計算成本追蹤 | #13 Effort Metrics | 每 agent run tokens/time 完全量化 |
| Hunter Agent self-correction | #6 + #7 | MetaQA baseline 即時更新，anomaly 早期發現 |
| Speculative debate | #5 + #7 | 多模型挑戰同問題，減少幻觉 |

---

## 七、風險與緩解

| 風險 | 等級 | 緩解策略 |
|------|------|---------|
| Feature #10 LangGraph 破壞現有 LLM Cascade | 高 | Stage 1+2 確保所有 base pipeline 完整整合後，Stage 3 才包 LangGraph |
| 迴圈依賴（Hunter ↔ UQLM ↔ Governance）| 中 | 設定 max iteration（max 3 輪）+ explicit exit node |
| 13 個 Feature 啟動導致延遲增加 | 中 | UQLM/CLAP 只在高 uncertainty 時啟動（lazy evaluation）|
| #12 Compliance 覆蓋不到邊緣案例 | 低 | 先用 NIST AI RMF 五函數覆蓋主流場景，逐步擴展 |
| Stage 2 破壞 Features #1-5 的現有測試 | 中 | 整合前先跑完整 test suite，建立 baseline；每個改動後 regression test |
| 獨立 packages 刪除後路徑斷裂 | 低 | Stage 5 再刪除，Stage 1-4 期間完整保留所有 packages |

---

## 八、預估總工期

| Stage | 天數 | 累計 |
|-------|------|------|
| Stage 1: Observability Foundation | 2-3 天 | 2-3 天 |
| Stage 2: Core Pipeline Wiring | 3-4 天 | 5-7 天 |
| Stage 3: Intelligence Layer | 4-5 天 | 9-12 天 |
| Stage 4: Quality Gates | 2-3 天 | 11-15 天 |
| Stage 5: Compliance Enforcement | 2-3 天 | 13-18 天 |

**總計：13-18 個工作天**

---

## 九、推薦執行順序

```
Stage 1 (2-3天) → Stage 2 (3-4天) → Stage 3 (4-5天) → Stage 4 (2-3天) → Stage 5 (2-3天)
```

**Stage 1 最先做**：風險最低，且是所有上層的基礎

**Stage 3 最關鍵**：LangGraph 整合是最大風險，需要完整的前置準備

**Stage 5 最後做**：所有上層就位後，合規報告才能完整

---

## 十、判斷完成標準

每個 Stage 完成時，必須滿足：

| Stage | 完成標準 |
|-------|---------|
| Stage 1 | 所有 span 含 UQLM metrics + decision_log + effort；Langfuse dashboard 可見 100% trace |
| Stage 2 | Agent runtime 經過完整 5-layer pipeline（SAIF → Shield → Governance → LLM Cascade → Kill-Switch）|
| Stage 3 | LangGraph state 包含 uncertainty；Hunter Agent 可干預；speculative debate 可觸發 |
| Stage 4 | Gap Detector 在 Phase 4 gate 產出報告；Risk Assessment 在每 Phase 完成後更新 register |
| Stage 5 | EU AI Act Art.14 + NIST AI RMF report 可生成；Kill-Switch event 有完整 audit trail |

---

**Status:** Pending Johnny's decision on start Stage