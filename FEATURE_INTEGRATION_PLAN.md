# Feature #1-13 整合評估報告 v2.0

**Date:** 2026-04-23
**Version:** 2.0
**Author:** Agent A (Reviewer/Main Agent)
**Status:** Complete — Awaiting Decision

---

## CHANGELOG v1.0 → v2.0

| 調整 | v1.0 | v2.0 |
|------|------|------|
| Stage 1 焦點 | Observability Foundation（被動/事後）| Foundation + **Phase Gate Enforcement（即時/強制）** |
| Gap Detector 時機 | 只在 Phase 4 | **每個 Phase** 結束時跑簡單結構性檢查 |
| Stage 2 內容 | Core Pipeline Wiring | **Governance Pipeline**（Governance 成為第一個防護層）|
| Effort Metrics | 只在 Stage 1 附帶 | **整合進 Phase Gate**（每 Phase gate 檢查 effort 是否合理）|
| Phase 1-2 約束 | 無 | **加入結構性強制要求**（SPEC.md 含所有 FR IDs、ARCHITECTURE.md 覆蓋所有 Module Designs）|
| Risk Assessment | 每 Phase 結束 | **持續性風險監控**（非只在 Phase 完成時）|
| Stage 數量 | 5 | **6**（拆出 Phase Gate Enforcement 成為獨立 Stage）|

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
│  重要：Risk Assessment 也是持續性監控，不是只在 Phase 結束時       │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 4: Executive Assurance ← #6 Hunter Agent               │
│  Anomaly Detection + Self-Correction + MetaQA Baseline           │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 3: Intelligence                                           │
│  ┌──────────────┐ ┌──────────────┐ ┌────────────────────────┐  │
│  │ UQLM (#7)    │ │ LangGraph    │ │ Gap Detector (#8)      │  │
│  │ Hallucination│ │ (#10)        │ │ (Phase Gate trigger)   │  │
│  │ Detection    │ │ 有狀態多步    │ │ 每 Phase 都跑！         │  │
│  │ + CLAP Probe │ │ 驟規劃        │ └────────────────────────┘  │
│  └──────────────┘ └──────────────┘                             │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ LLM Cascade (#5) — 多 provider 路由 + speculative debate │  │
│  └──────────────────────────────────────────────────────────┘  │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 2: Governance & Reliability                               │
│  ┌──────────────┐ ┌──────────────┐                             │
│  │ #3 HOTL/HITL│ │ #4 Kill-Switch│                            │
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

## 四、整合順序（6 個 Stage）

### 核心調整：防護機制要即時，不能等

```
v1.0 問題：Stage 1 只有 Observability，4 個核心問題（偷懶/走捷徑/幻覺/自我感覺良好）
          要等到 Stage 2-4 才陸續被防護

v2.0 解決：每個 Stage 都包含即時防護機制，不再有「完全無防護的空窗期」
```

---

### Stage 1：Foundation + Phase Gate Enforcement（最先做）

**為什麼先做**：沒有基礎設施，後面的防護都沒有 evidence store；沒有 Phase Gate，Agent 在每個 Phase 結尾都可以偷懶

| 順序 | Feature | 現況 | 整合目標 |
|------|---------|------|---------|
| **1-1** | Phase Gate Hook | 無 | 每個 Phase 完成時自動觸發品質檢查 |
| **1-2** | #13 Decision Log | 獨立 package | 每個 Agent decision 寫 YAML，日後可審查 |
| **1-3** | #11 Langfuse | 獨立 package | 成為 gateway plugin，寫入所有 span trace |
| **1-4** | Phase 1-2 結構性檢查 | 無 | SPEC.md 含所有 FR IDs、ARCHITECTURE.md 覆蓋所有 Module Designs |

**Phase Gate Hook 的即時防護**：
```python
# Phase completion hook — 每個 Phase 結束時自動觸發
def after_phase(phase_id: int, deliverables: list[str]):
    # 1. 結構性檢查（所有 Phase 都做）
    checks = {
        "files_exist": _check_files_exist(phase_id, deliverables),
        "effort_reasonable": effort.is_reasonable(phase_id),  # 不能太快（<1min = 疑似偷懶）
        "decision_logged": decision_log.has_entry(phase_id),
    }
    
    if not all(checks.values()):
        raise PhaseGateFailed(f"Phase {phase_id} gate failed: {checks}")
    
    # 2. Phase 特有的檢查
    if phase_id == 1:
        _check_spec_completeness()
    elif phase_id == 2:
        _check_architecture_coverage()
    elif phase_id == 4:
        # Gap Detector 只在 Phase 4 跑完整版
        gaps = gap_detector.scan_full("04-tests/")
        if gaps:
            logger.warning(f"Coverage gaps: {len(gaps)}")
    
    return True
```

**Effort Metrics 的「太快」檢測**：
```python
# 如果一個 Phase 在 < 1 分鐘內完成，幾乎肯定是偷懶
def is_effort_reasonable(phase_id: str) -> bool:
    record = effort.get_record(phase_id)
    if record.time_spent_ms < 60_000:  # < 1 分鐘
        if phase_id in ("2-architecture", "3-implement"):
            return False  # 這兩個 Phase 不可能 1 分鐘完成
    return True
```

**Phase 1-2 的結構性強制要求**：
```python
# Phase 1 gate: SPEC.md 必須包含所有 FR IDs
def check_spec_completeness():
    spec = read("01-spec/SPEC.md")
    fr_ids = extract_fr_ids(spec)  # 例如 FR-13-01, FR-13-02
    module_names = extract_module_names("03-implement/")
    # 每個 module 必須有對應的 FR ID
    for module in module_names:
        if module not in fr_ids:
            raise PhaseGateFailed(f"Module {module} has no FR ID in SPEC.md")

# Phase 2 gate: ARCHITECTURE.md 必須覆蓋所有 Module Designs
def check_architecture_coverage():
    arch = read("02-architecture/ARCHITECTURE.md")
    module_names = extract_module_names("03-implement/")
    for module in module_names:
        if module not in arch:
            raise PhaseGateFailed(f"Module {module} not covered in ARCHITECTURE.md")
```

**預期好處**：
- Agent 知道「每個 Phase 結尾都會被自動檢查」，偷懶成本大幅提高
- Decision Log 讓造假成本提高（事後可審查）
- Phase 1-2 的結構性要求杜絕「規格寫一半」

**預估工期**：2-3 天

**風險**：低（新增 hook，不改現有邏輯）

---

### Stage 2：Governance Pipeline（第二步）

**為什麼第二步**：Governance 是第一個「主動防護層」— 不是事後觀察，是即時阻擋

| 順序 | Feature | 現況 | 整合目標 |
|------|---------|------|---------|
| **2-1** | #3 Governance | `implement/governance/` 存在但未調用 | 每個 LLM decision 經過 `TierClassifier.classify()` → 輸出 HOTL/HITL/HOOTL |
| **2-2** | #1 MCP + SAIF | 存在但未鉤入 | SAIF middleware 自動驗證 agent_id/token |
| **2-3** | #2 Prompt Shields | 存在但獨立 | 在 LLM call 前自動 scan input/output |
| **2-4** | #4 Kill-Switch | 存在但未觸發 | HealthMonitor + Governance 雙重觸發 |

**整合方法**：
```python
# Agent runtime pipeline — 核心執行順序
async def agent_run(agent_id: str, task: str, message: dict):
    # ── Layer 1.5: Identity propagation ──
    saif_token = SAIFMiddleware.extract_or_create(agent_id)
    if not saif_token.is_valid():
        raise UnauthorizedError("Invalid or missing SAIF token")
    ctx = saif_token.to_context()

    # ── Layer 1.7: Prompt Shield ──
    shield_verdict = PromptShield.scan(message.get("content", ""))
    if shield_verdict == Verdict.BLOCK:
        decision_log.write(agent_id, "BLOCK", "Prompt injection detected")
        raise InjectionBlockedError(shield_verdict.reason)

    # ── Layer 2: Governance classification ──
    gov_ctx = GovernanceContext(
        agent_id=agent_id,
        task=task,
        identity_propagated=True,
        shield_verdict=shield_verdict,
    )
    tier = tier_classifier.classify(gov_ctx)
    
    decision_log.write(agent_id, f"Tier={tier.value}", f"task={task[:50]}")
    
    if tier == Tier.BLOCK:
        return {"status": "blocked", "reason": "Governance BLOCK"}
    
    if tier == Tier.HITL:
        # 暫停，等人類批准
        await wait_for_human_approval(task, timeout=300)
    
    # ── Layer 3: LLM Cascade（根據 tier 決定行為）──
    require_consensus = (tier == Tier.HOTL)
    result = await llm_cascade.execute(
        task, 
        require_consensus=require_consensus,
        governance_tier=tier  # Cascade 知道這是 HOTL/HITL/LOOP
    )
    
    # ── Kill-Switch monitoring ──
    health_monitor.record_result(result)
    if health_monitor.should_circuit_break():
        await kill_switch.trigger(agent_id, reason="health_monitor_threshold")

    return result
```

**Governance Decision 如何影響後續**：

| Tier | LLM Cascade 行為 | Kill-Switch 敏感度 |
|------|----------------|-----------------|
| **LOOP**（最低）| 單一模型，快速執行 | 低 |
| **HOTL**（自動）| 多模型 consensus冗余驗證 | 中 |
| **HITL**（人類）| 先通過再執行，紀錄人類批准 | 高 |
| **BLOCK**（阻擋）| 不執行，直接返回錯誤 | N/A |

**預期好處**：
- **走捷徑被阻擋**：Governance 是第一個看到 request 的「裁判」，不是最後
- **高風險決策（HOTL/HITL）被強化**：這些 tier 的 decision 會被多模型驗證
- **Prompt injection 被 L1.7 + L2 雙重把關**

**預估工期**：3-4 天

**風險**：中（需要確保 Governance 不成為效能瓶頸 — TierClassifier 必須 < 10ms）

---

### Stage 3：Intelligence Layer Activation（第三步）

**為什麼第三步**：Intelligence Layer 是「第二層防護」— Governance 只決定「能不能做」，UQLM 判斷「做出來的東西對不對」

| 順序 | Feature | 現況 | 整合目標 |
|------|---------|------|---------|
| **3-1** | #7 UQLM | 存在 | 每個 LLM response 後跑 uncertainty score |
| **3-2** | #6 Hunter Agent | 存在 | 訂閱 message bus；uncertainty > threshold 時介入 |
| **3-3** | #10 LangGraph | 存在 | structured multi-step workflow，stateful |

**整合方法**：
```python
# LangGraph state machine with UQLM + Hunter
class AgentState(TypedDict):
    messages: list
    uncertainty: Optional[UncertaintyScore]
    governance_tier: Tier
    hunter_flags: list[HuntingFlag]

def planner_node(state: AgentState):
    # 根據 Governance tier 決定如何執行
    if state.governance_tier == Tier.HOTL:
        response = llm_cascade.invoke(state.messages, multi_model=True)
    else:
        response = llm_cascade.invoke(state.messages, multi_model=False)
    
    # UQLM: 計算這個 response 的 uncertainty
    uncertainty = uqlm.compute(
        prompt=state.messages,
        response=response.content,
        model_name=llm_cascade.current_model
    )
    
    decision_log.write(
        agent_id=state.agent_id,
        decision=f"UAF={uncertainty.uaf_score:.3f}",
        reasoning=f"model={llm_cascade.current_model}, components={uncertainty.components}"
    )
    
    # UQLM 分數決定下一個 node
    if uncertainty.uaf_score > 0.7:
        return {"next": "hunter_review", "uncertainty": uncertainty}
    elif uncertainty.uaf_score > 0.4:
        return {"next": "debate_round_2", "uncertainty": uncertainty}
    else:
        return {"next": "execute", "uncertainty": uncertainty}

def hunter_review_node(state: AgentState):
    """Hunter Agent: 第二雙眼睛，檢查 LLM output 是否異常"""
    anomaly = hunter.detect(
        messages=state.messages,
        response=state.response,
        uncertainty=state.uncertainty
    )
    
    if anomaly.is_confirmed:
        # Hunter 確認 anomaly：要求重新生成
        return {
            "next": "regenerate",
            "hunter_flags": state.hunter_flags + [anomaly],
            "reason": anomaly.reason
        }
    
    if anomaly.isSuspicious but not confirmed:
        # 不確定，但值得注意：降級 tier，要求多模型共識
        return {
            "next": "debate_round_2",
            "governance_tier": Tier.HOTL  # 升級 tier
        }
    
    return {"next": "execute"}

def debate_round_2_node(state: AgentState):
    """Speculative debate: 第二個模型挑戰第一個模型的答案"""
    second_model = llm_cascade.get_alternative_model()
    challenge = llm_cascade.invoke(
        state.messages + [state.response],
        model=second_model,
        system_prompt="你是一個批評者，挑戰前一個答案的弱點"
    )
    
    alignment = uqlm.compute_alignment(state.response, challenge.content)
    
    decision_log.write(
        agent_id=state.agent_id,
        decision=f"debate alignment={alignment:.3f}",
        reasoning=f"model_1={llm_cascade.current_model}, model_2={second_model}"
    )
    
    if alignment < 0.3:
        # 兩個模型結論差太多：觸發 Hunter + 通知人類
        return {
            "next": "hunter_review",
            "uncertainty": UncertaintyScore(uaf_score=0.9)  # 人為提高
        }
    
    return {"next": "execute", "consensus_score": alignment}
```

**即時防護效果**：

| 問題 | 解決機制 |
|------|---------|
| **幻覺** | UQLM > 0.7 → hunter_review；多模型 debate 驗證共識 |
| **自我感覺良好** | UQLM 外部客觀分數，Agent 看不見自己信心和分數的對比 |
| **偷懶（不驗證）** | HOTL tier 強制多模型共識，偷懶者無法用單一模型矇混 |

**預估工期**：4-5 天

**風險**：高（LangGraph 可能破壞現有 Cascade；需要完整的 Stage 2 穩定後才能整合）

---

### Stage 4：Observability Enrichment（第四步）

**為什麼第四步**：Intelligence Layer 上線後，trace 數據變得更豐富；此時把 #13 的 enrichment 完整串進去

| 順序 | Feature | 現況 | 整合目標 |
|------|---------|------|---------|
| **4-1** | #11 Langfuse | 部分整合（Stage 1 已有基礎）| 完整 enriched span：含 UQLM 分數、Governance tier、Hunter flags |
| **4-2** | #13 Effort Metrics | Stage 1 已有鉤子 | 完整的 tokens/time/iteration 追蹤，並與 phase gate 掛鉤 |
| **4-3** | #13 Decision Log | Stage 1 已有鉤子 | 完整的 decision reasoning 持久化，含 metadata |

**整合後的 enriched span**：
```python
@observe
async def agent_span(agent_id: str, task: str):
    # 啟動時
    effort.start(agent_id, trace_id=trace.id)
    
    # 執行時（每個 step）
    span.set_attribute("uqlm.uaf_score", uncertainty.uaf_score)
    span.set_attribute("uqlm.components", uncertainty.components)
    span.set_attribute("governance.tier", tier.value)
    span.set_attribute("hunter.flags", hunter.flags)
    
    # 結束時
    effort.stop(effort_id)
    decision_log.write(agent_id, decision, reasoning, options_considered, chosen_action)
```

**Langfuse Dashboard 能看到**：
- 每個 agent decision 的 UAF 分數
- Governance tier 分布
- Hunter Agent 介入頻率
- Effort tokens/time per phase

**預估工期**：2 天

**風險**：低（強化現有基礎設施）

---

### Stage 5：Quality Gates Full Automation（第五步）

**為什麼第五步**：Stage 3 的 Intelligence 上線後，Agent 行為數據更完整；此時做完整的 Gap Detection 和 Risk Assessment

| 順序 | Feature | 觸發時機 | 整合目標 |
|------|---------|---------|---------|
| **5-1** | #8 Gap Detector | 每個 Phase 完成 | 完整測試覆蓋掃描，不只是結構性檢查 |
| **5-2** | #9 Risk Assessment | 每個 Phase 完成 | 量化風險評估，與 Governance tier 聯動 |
| **5-3** | Effort Metrics | 每個 Phase 完成 | 測量每個 phase 的 tokens/time 是否合理 |

**整合方法**：
```python
def full_phase_gate(phase_id: int, deliverables: dict):
    # 1. Effort Metrics — 是否合理？
    effort_record = effort.get(phase_id)
    if effort_record.tokens_consumed < MIN_TOKENS_PER_PHASE.get(phase_id, 0):
        risk.register(
            f"Phase {phase_id} effort suspiciously low",
            severity=HIGH,
            type="偷懶"
        )
    
    # 2. Gap Detector — 測試覆蓋缺口
    if phase_id == 4:
        gaps = gap_detector.scan_full("04-tests/")
        if gaps:
            risk.register_bulk(gaps)
            deliver("GAP_REPORT.md", gaps)
    
    # 3. Risk Assessment — 量化評估
    risk_score = risk_assessor.evaluate(phase_id, deliverables)
    
    # 4. Governance tier drift — tier 有沒有異常？
    tier_drift = governance.get_tier_drift_since_last_phase()
    if tier_drift > 2:  # 連續 2 個 phase tier 上升 = 風險信號
        risk.register(
            "Governance tier escalation pattern",
            severity=MEDIUM,
            type="架構風險"
        )
    
    # 5. Hunter Agent flags — anomaly 頻率
    hunter_freq = hunter.get_anomaly_rate_since_last_phase()
    if hunter_freq > 0.3:  # > 30% 的 requests 被 flag = 系統性問題
        risk.register(
            f"Hunter anomaly rate elevated: {hunter_freq:.1%}",
            severity=HIGH,
            type="幻覺風險"
        )
```

**預期好處**：
- **偷懶**：Effort 太低馬上被發現
- **幻覺**：Hunter anomaly 頻率超標馬上預警
- **走捷徑**：Governance tier drift 追蹤，發現捷徑傾向

**預估工期**：2-3 天

**風險**：低（鉤子系統已有，Stage 1-3 已建立基礎）

---

### Stage 6：Compliance Enforcement（第六步）

**為什麼最後做**：合規報告需要所有上層組件就位

| 順序 | Feature | 整合點 |
|------|---------|--------|
| **6-1** | #12 Compliance | Kill-Switch 觸發 → EU AI Act Art.14 report |
| **6-2** | #12 Compliance | HITL 審批 → NIST AI RMF "Manage" 函數 |
| **6-3** | #12 Compliance | Hunter Agent anomaly → NIST "Monitor" 函數 |
| **6-4** | #12 Compliance | LLM Cascade routing → NIST "Measure" 函數 |
| **6-5** | #6 Hunter Agent | MetaQA baseline → 合規的「系統正常行為基準」|

**整合方法**：
```python
# Kill-Switch → EU AI Act Art.14
if circuit_breaker.should_trigger():
    compliance.report(
        event_type="circuit_break",
        EU_article="14(4)(a)",  # Human oversight mechanism
        NIST_function="Manage",
        evidence={
            "health_metrics": health_monitor.snapshot(),
            "governance_tier": governance.current_tier,
            "effort_record": effort.get_latest()
        }
    )

# HITL approval → NIST AI RMF Manage
if human.approved(task):
    compliance.record(
        action="human_approval",
        NIST_function="Manage",
        EU_article="14(4)(b)",  # Human oversight for high-risk
        approver=human.id,
        evidence={"task": task, "governance_tier": Tier.HITL}
    )

# Hunter anomaly → NIST Monitor
if hunter.anomaly_detected:
    compliance.log_monitoring_event(
        event_type="anomaly_detected",
        NIST_function="Monitor",
        evidence=hunter.get_latest_anomaly()
    )

# Auto-generated compliance report (quarterly)
def generate_compliance_report():
    return {
        "EU_AI_Act_Art14": {
            "total_humans_approved": human_approvals.count(),
            "total_blocked": governance.get_blocked_count(),
            "total_circuit_breaks": circuit_breaker.count(),
            "anomaly_rate": hunter.get_anomaly_rate()
        },
        "NIST_AI_RMF": {
            "Govern": governance.get_govern_decisions(),
            "Monitor": hunter.get_anomaly_events(),
            "Measure": llm_cascade.get_model_distribution(),
            "Map": gap_detector.get_coverage_map(),
            "Manage": human_approvals.get_approvers()
        }
    }
```

**預期好處**：
- EU AI Act Art.14 合規 audit trail 自動生成
- NIST AI RMF 五函數 100% mapped
- Anthropic RSP v3.0 ASL-3 sign-off 有完整數據支持

**預估工期**：2-3 天

**風險**：低（合規層是新增，不修改任何現有功能）

---

## 五、整合方式：6 種 Wire 類型

| 類型 | 適用場景 | 技術 | 範例 |
|------|---------|------|------|
| **Phase Gate Hook** | 每 Phase 完成時 | `after_phase(phase_id, callback)` | Stage 1, 5 |
| **Plugin Registration** | Gateway 啟動時加載 | `gateway.register_plugin("shield", PromptShield())` | Stage 2 |
| **Decorator Wrapper** | LLM call 前後 | `@observe` decorator 自動寫 Langfuse | Stage 4 |
| **Event Bus Subscription** | Cross-layer 訊息 | `message_bus.subscribe(agent_id="*", callback=hunter.on_message)` | Stage 3 |
| **State Pass-Through** | LangGraph node 間傳遞 | `state["uncertainty"]` / `state["governance_tier"]` | Stage 3 |
| **Health Monitor Feed** | Kill-Switch 觸發條件 | `health_monitor.on_failure(provider)` → circuit breaker | Stage 2 |

---

## 六、對 4 個核心問題的即時防護覆蓋

| 問題 | 即時防護 Stage | 機制 |
|------|--------------|------|
| **偷懶** | Stage 1 + 5 | Phase Gate Effort 檢查（太快 = 疑似偷懶）；Gap Detector 發現測試覆蓋缺口 |
| **走捷徑** | Stage 2 | Governance TierClassifier 是第一個看到 request 的裁判；BLOCK tier 直接阻擋 |
| **幻覺/造假** | Stage 3 + 5 | UQLM uncertainty score > 0.7 → Hunter 介入；Hunter anomaly rate 超標 → Risk Assessment 預警；Decision Log 事後可審查 |
| **自我感覺良好** | Stage 3 + 5 | UQLM 外部客觀分數（Agent 自己看不見自己的 UAF）；Risk Assessor 說「高風險」不等於 Agent 說了算 |

**關鍵改善 vs v1.0**：每個 Stage 都有即時防護，不再有「完全無防護的空窗期」。

---

## 七、風險與緩解

| 風險 | 等級 | 緩解策略 |
|------|------|---------|
| Governance TierClassifier 成為效能瓶頸 | 高 | 測量延遲，目標 < 10ms；必要時 cache tier decisions |
| LangGraph 破壞現有 LLM Cascade | 高 | Stage 2 確保 Cascade 完全整合後再包 LangGraph |
| 迴圈依賴（Hunter ↔ UQLM ↔ Governance）| 中 | max iteration = 3 + explicit exit node |
| Phase Gate 太多鉤子拖慢 development | 中 | Stage 1 只做關鍵檢查（effort 合理性 + decision_log）；完整檢查在 Stage 5 |
| 13 個 Feature 啟動導致延遲增加 | 中 | UQLM/CLAP 只在高 uncertainty 時啟動（lazy evaluation）|
| Effort Metrics 隱私問題 | 低 | 只記 tokens/time，不記 task 內容 |

---

## 八、預估總工期

| Stage | 天數 | 累計 | 即時防護 |
|-------|------|------|---------|
| Stage 1: Foundation + Phase Gate | 2-3 天 | 2-3 天 | 偷懶/造假 |
| Stage 2: Governance Pipeline | 3-4 天 | 5-7 天 | 走捷徑 |
| Stage 3: Intelligence Layer | 4-5 天 | 9-12 天 | 幻覺/自我感覺良好 |
| Stage 4: Observability Enrichment | 2 天 | 11-14 天 | 追蹤能力強化 |
| Stage 5: Quality Gates Full | 2-3 天 | 13-17 天 | 偷懶/幻覺 |
| Stage 6: Compliance Enforcement | 2-3 天 | 15-20 天 | 合規 audit |

**總計：15-20 個工作天**

---

## 九、推薦執行順序

```
Stage 1 (2-3天) → Stage 2 (3-4天) → Stage 3 (4-5天) → Stage 4 (2天) → Stage 5 (2-3天) → Stage 6 (2-3天)
```

**Stage 1 最先做**：每個 Phase 結尾的 gate 是最低成本、最高效益的初期防護

**Stage 2 第二做**：Governance 是第一個主動阻擋層，在 Intelligence 之前就該就位

**Stage 3 第三做**：Intelligence Layer 是最複雜的，需要 Stage 1+2 穩定後才能整合

**Stage 4-6 最後做**：基礎設施和防護層就位後，合規和 observability 的價值才完整

---

## 十、判斷完成標準

| Stage | 完成標準 |
|-------|---------|
| Stage 1 | Phase Gate hook 可攔截 < 1 分鐘完成的 Phase；Decision Log 每次 decision 有 record |
| Stage 2 | Agent runtime 經過完整 5-layer pipeline；Governance tier decision 可追蹤 |
| Stage 3 | LangGraph state 含 uncertainty；Hunter 可干預；speculative debate 可觸發 |
| Stage 4 | Langfuse Dashboard 可見 enriched span（UQLM + Governance + Hunter）|
| Stage 5 | Gap Detector 發現 > 10% 覆蓋缺口會被標記；Risk Assessor 每 Phase 更新 |
| Stage 6 | EU AI Act + NIST AI RMF report 可自動生成 |

---

## 十一、v2.0 與 v1.0 的關鍵差異

| 面向 | v1.0 | v2.0 |
|------|------|------|
| **第一個 Stage** | 被動的 Observability | 即時的 Phase Gate Enforcement |
| **防護時機** | Stage 2-4 才陸續上線 | Stage 1 就有偷懶/造假檢測 |
| **Governance 位置** | Stage 2，pipeline 中間 | Stage 2，但作為第一層主動阻擋 |
| **UQLM 位置** | Stage 3 | Stage 3（Intelligence Layer）|
| **Gap Detector** | 只在 Phase 4 | 每個 Phase 結尾都跑結構性檢查；Phase 4 跑完整版 |
| **Effort Metrics** | Stage 1 被動收集 | Stage 1 主動參與 Phase Gate（太快 = 偷懶信號）|
| **Phase 1-2 約束** | 無 | 有（SPEC.md 含 FR IDs、ARCHITECTURE.md 覆蓋所有 modules）|
| **Risk Assessment** | 每 Phase 結束 | 每 Phase 結束 + 持續性監控（Hunter anomaly rate 等）|

---

**Status:** Pending Johnny's decision on start Stage
