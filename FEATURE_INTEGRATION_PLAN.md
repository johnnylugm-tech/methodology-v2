# Feature #1-13 整合評估報告 v3.0

**Date:** 2026-04-23
**Version:** 3.0
**Author:** Agent A (Reviewer/Main Agent)
**Status:** Complete — Pending Decision

---

## CHANGELOG v2.0 → v3.0

### 核心認知更新

v2.0 的最大錯誤：**把 13 個 Feature 當成要新建的「Agent Runtime Pipeline」來整合。**

**v3.0 的正確認知：** 13 個 Feature 必須全部鉤入現有的 `PhaseHooks` 框架。沒有任何一個 Feature 需要獨立的 runtime pipeline。整個整合是「PhaseHooks 擴展」，不是「新建 pipeline」。

---

### 為什麼整合點是 PhaseHooks？

```
Johnny: 「執行 Phase 3」
         ↓
Agent: plan-phase --phase 3
         ↓
Agent: run-phase --phase 3
         ↓
┌──────────────────────────────────────────────────────────────┐
│ PRE-FLIGHT (PhaseHooks.preflight_all)                       │
│ FSM Check / Constitution / Tool Registry / Session Save      │
└──────────────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────────────┐
│ FR EXECUTION LOOP（核心運行機制）                             │
│                                                              │
│  for FR in FRs:                                             │
│    sessions_spawn(developer) → JSON {files, status}          │
│    sessions_spawn(reviewer) → JSON {review_status}           │
│    if REJECT → re-do developer（最多 5 輪，HR-12）           │
└──────────────────────────────────────────────────────────────┘
         ↓
┌──────────────────────────────────────────────────────────────┐
│ POST-FLIGHT (PhaseHooks.postflight_all)                      │
│ Constitution / state.json / Summary                          │
└──────────────────────────────────────────────────────────────┘
```

**這個流程從 v6.102 到 v6.102 已經是事實標準。** 任何整合方案都必須在這個框架內。

---

### 13 個 Feature 對 PhaseHooks 的整合位置

| Feature | 鉤入點 | 理由 |
|---------|--------|------|
| **#1 MCP + SAIF** | `monitoring_before_dev()` | Developer session 啟動前驗證 token |
| **#2 Prompt Shields** | `monitoring_after_dev()` | Developer 返回的 code 在寫入磁碟前 scan |
| **#3 Governance** | `monitoring_before_rev()` | Reviewer 開始前做 tier 分類（HOTL/HITL/HOOTL/LOOP）|
| **#4 Kill-Switch** | `monitoring_hr12_check()` | HR-12 觸發（>5 輪）→ 熔斷 |
| **#5 LLM Cascade** | `monitoring_before_rev()` | HOTL tier → 多個 Reviewer session 共識 |
| **#6 Hunter Agent** | `monitoring_after_dev()` | Developer 輸出做 anomaly detection |
| **#7 UQLM** | `monitoring_after_dev()` | Developer 輸出計算 uncertainty score |
| **#8 Gap Detector** | `postflight_all()` | Phase 完成後掃描測試覆蓋缺口 |
| **#9 Risk Assessment** | `preflight_all()` + `postflight_all()` | Phase 開始/結束時持續風險評估 |
| **#10 LangGraph** | FR execution loop 外層 | Structured FR execution graph（可選增強）|
| **#11 Langfuse** | 全程（所有鉤子）| 追蹤所有 PhaseHooks 呼叫的 trace |
| **#12 Compliance** | `postflight_all()` | Phase 完成時生成 EU AI Act / NIST 報告 |
| **#13 Observability** | 全程（所有鉤子）| Effort metrics + Decision Log 寫入每個環節 |

---

## 一、PhaseHooks 整合架構圖

```
PhaseHooks 現有的鉤子（7 個）：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
preflight_all()
monitoring_before_dev(fr_id)
monitoring_after_dev(fr_id, result)
monitoring_before_rev(fr_id)
monitoring_after_rev(fr_id, result)
monitoring_hr12_check(fr_id, iteration)
postflight_all()

擴展後的 PhaseHooks（整合 13 個 Feature）：
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

preflight_all()
├── _preflight_fsm()
├── _preflight_constitution()
├── _preflight_tool_registry()
├── _preflight_saif_token()          ← #1 SAIF
├── _preflight_risk_assessment()       ← #9 Risk
└── _preflight_langfuse_start()        ← #11 Langfuse

monitoring_before_dev(fr_id)
└── decision_log.write(agent="developer", decision="FR-XX 開始") ← #13

monitoring_after_dev(fr_id, result)
├── uqlm.compute(result.files)        ← #7 UQLM
├── hunter.detect(result.files)        ← #6 Hunter Agent
├── prompt_shield.scan(result.files)   ← #2 Prompt Shields
├── saif.validate(result)              ← #1 SAIF（再一次驗證）
└── decision_log.write(..., uaf_score, risk_score) ← #13

monitoring_before_rev(fr_id)
├── governance.classify(fr_id, uaf)    ← #3 Governance
├── decision_log.write(tier=...)       ← #13
└── 若 tier==HOTL → 多 reviewer sessions ← #5 LLM Cascade

monitoring_after_rev(fr_id, result)
├── governance.verify(result)           ← #3（確認有 tier decision）
├── decision_log.write(reviewer APPROVE/REJECT)
└── effort.increment(rev)              ← #13 Effort

monitoring_hr12_check(fr_id, iteration)
└── 若 iteration > 5 → kill_switch.trigger() ← #4 Kill-Switch

postflight_all()
├── gap_detector.scan()               ← #8 Gap Detector
├── risk_assessment.phase_end()       ← #9 Risk
├── compliance.generate_phase_report()  ← #12 Compliance
├── effort.get_summary()               ← #13 Effort
└── langfuse.close()                   ← #11 Langfuse
```

---

## 二、各 Feature 整合詳細設計

### Feature #1: MCP + SAIF 2.0

**鉤入點**: `preflight_all()` + `monitoring_after_dev()`

**整合理由**: HR-01 要求 Developer 和 Reviewer 必須是不同 session。SAIF middleware 確保每次 session 啟動都有有效的 identity token。

```python
def _preflight_saif_token(self):
    """Feature #1: SAIF token 驗證"""
    token = SAIFMiddleware.get_current_token()
    if not token or not token.is_valid():
        raise PREFLIGHT_FAILED(
            f"SAIF token 無效或缺失（HR-01 要求 Developer ≠ Reviewer）"
        )
    scopes = token.get_scopes()
    if "developer" not in scopes and "reviewer" not in scopes:
        raise PREFLIGHT_FAILED(f"SAIF token 缺少有效 scopes")
    return token
```

**HR-01 強化**: 原本 HR-01 只要求 Developer ≠ Reviewer。整合 SAIF 後，每次 session 啟動都有密碼學驗證，無法偽造身份。

---

### Feature #2: Prompt Shields

**鉤入點**: `monitoring_after_dev()`

**整合理由**: Developer 返回的 `files` 在寫入磁碟之前必須通過 injection scan。這是最後的安全檢查點。

```python
def _scan_developer_output(self, fr_id: str, dev_result: dict):
    """Feature #2: Developer 輸出在寫入磁碟前 scan injection"""
    if "files" not in dev_result:
        return
    
    for f in dev_result["files"]:
        verdict = self.prompt_shield.scan(f["content"])
        if verdict == Verdict.BLOCK:
            raise PHASE_HOOK_FAILED(
                f"FR-{fr_id}: Prompt Shield 阻擋 "
                f"'{f['path']}' — injection pattern: {verdict.pattern}"
            )
        elif verdict == Verdict.WARN:
            logger.warning(
                f"FR-{fr_id}: '{f['path']}' — "
                f"suspicious pattern: {verdict.pattern}"
            )
    
    # 只有通過 scan 才寫入磁碟
    self._write_files_to_disk(dev_result["files"])
```

**對 4 個核心問題的幫助**: Injection code 要寫入磁碟會被阻擋。

---

### Feature #3: Governance (HOTL/HITL/HOOTL/LOOP)

**鉤入點**: `monitoring_before_rev()` + `monitoring_after_rev()`

**整合理由**: 目前 Reviewer 靠直覺判斷是否需要 human approval。整合 Governance tier classifier 後，每個 FR 都有系統化的 risk tier decision，且可追蹤。

```python
def monitoring_before_rev(self, fr_id: str):
    """Feature #3: Reviewer 執行前先做 Governance tier 分類"""
    # 讀取 developer 輸出的 UAF 分數（如有）
    uaf = self.langfuse.get_span_attribute(f"fr.{fr_id}.uaf_score")
    
    ctx = GovernanceContext(
        phase=self.phase,
        fr_id=fr_id,
        uaf_score=uaf or 0.0,
        previous_rejections=self._get_rejection_count(fr_id)
    )
    tier = self.governance.classify(ctx)
    
    # 記錄 decision log
    self.decision_log.write(
        agent_id="governance",
        fr_id=fr_id,
        decision=f"tier={tier.value}",
        reasoning=f"uaf={uaf:.3f}, rejections={ctx.previous_rejections}"
    )
    
    # Tier 影響後續行為
    if tier == Tier.HOOTL:
        # 最高風險：需要人類直接批准，不能只靠 Reviewer
        self._notify_human(f"FR-{fr_id}: HOOTL tier — 需要你直接批准")
    elif tier == Tier.HITL:
        # 中高風險：通知 Johnny 有 Reviewer 無法決定的 case
        logger.info(f"FR-{fr_id}: HITL tier — Reviewer 需要完整審查")
    
    self._current_tier = tier
    return tier

def monitoring_after_rev(self, fr_id: str, rev_result: dict):
    """Feature #3: 驗證 Reviewer APPROVE 有對應的 tier decision"""
    if rev_result.get("review_status") == "APPROVE":
        tier = getattr(self, "_current_tier", None)
        if tier is None:
            raise PHASE_HOOK_FAILED(
                f"FR-{fr_id}: Reviewer APPROVE 但沒有 Governance tier decision"
            )
        
        self.decision_log.write(
            agent_id="reviewer",
            fr_id=fr_id,
            decision=f"APPROVE (tier={tier.value})",
            reasoning=rev_result.get("reason", "")
        )
```

**對 4 個核心問題的幫助**: 走捷徑（跳過高風險審查）被 Governance tier 系統化阻擋。

---

### Feature #4: Kill-Switch

**鉤入點**: `monitoring_hr12_check()`

**整合理由**: HR-12 是「>5 輪 A/B → PAUSE」。整合 Kill-Switch 後，PAUSE 變成真的熔斷，不只是狀態改變。

```python
def monitoring_hr12_check(self, fr_id: str, iteration: int):
    """Feature #4: HR-12 + Kill-Switch 整合"""
    if iteration > 5:
        # 本來的行為：通知 Johnny，專案 PAUSE
        self._pause_project(f"FR-{fr_id}: A/B 審查超過 5 輪（HR-12）")
        
        # Kill-Switch 的額外行為：
        # 1. 生成 EU AI Act Art.14 報告（合規要求）
        self.compliance.report_hr12_event(
            fr_id=fr_id,
            iterations=iteration,
            trigger="HR-12"
        )
        
        # 2. 記風暴進 Risk Register
        self.risk_assessor.register(
            f"FR-{fr_id}: HR-12 triggered — iteration count exceeded",
            severity=SEVERITY.HIGH,
            type="process_risk"
        )
        
        # 3. 觸發 Kill-Switch（停止這個 FR 的進一步迭代）
        self.kill_switch.trigger(
            target=f"fr-{fr_id}",
            reason="hr12_max_iterations_exceeded"
        )
        
        raise PHASE_HOOK_FAILED(f"FR-{fr_id}: HR-12 + Kill-Switch 觸發")
```

**對 4 個核心問題的幫助**: 偷懶（不斷 REJECT 但不認真修正）被 Kill-Switch 終結。

---

### Feature #5: LLM Cascade

**鉤入點**: `monitoring_before_rev()` (tier==HOTL 時)

**整合理由**: HOTL tier（高風險自動）需要多個 Reviewer session 的共識。目前只有一個 Reviewer。

```python
def monitoring_before_rev(self, fr_id: str):
    # ... (Feature #3 的 tier 分類)
    
    tier = self._current_tier
    
    if tier == Tier.HOTL:
        # Feature #5: HOTL → 多個 Reviewer 共識
        # 使用不同 model 的 session 來增加 coverage
        models = self.llm_cascade.get_alternative_models(count=3)
        
        for model in models:
            # 每個 model 跑一次獨立的 Reviewer session
            rev_result = self._sessions_spawn_reviewer(
                fr_id=fr_id,
                model=model,
                prompt_suffix=f"[HOTL consensus — model={model}]"
            )
            
            if rev_result.review_status == "REJECT":
                # 共識：認為有問題
                self.decision_log.write(
                    agent_id=f"reviewer-{model}",
                    fr_id=fr_id,
                    decision="REJECT",
                    reasoning=rev_result.reason
                )
                return {"status": "REJECT", "consensus": models}
        
        # 所有 model 都 APPROVE → 共識通過
        self.decision_log.write(
            agent_id="reviewer-consensus",
            fr_id=fr_id,
            decision="APPROVE (consensus)",
            reasoning=f"all {len(models)} models agree"
        )
        return {"status": "APPROVE", "consensus": models}
```

**對 4 個核心問題的幫助**: Reviewer 單一模型的盲點被多模型共識補足。

---

### Feature #6: Hunter Agent

**鉤入點**: `monitoring_after_dev()`

**整合理由**: Developer 輸出是最後一個可以被自動檢查的點。Hunter Agent 在這裡做 anomaly detection。

```python
def monitoring_after_dev(self, fr_id: str, dev_result: dict):
    """Feature #6: Hunter Agent — Developer 輸出的第二雙眼睛"""
    # ... UQLM (#7) 先執行 ...
    uaf = self.uqlm.compute(dev_result)
    
    # Hunter Agent anomaly detection
    if "files" in dev_result:
        anomaly = self.hunter.detect(
            files=dev_result["files"],
            context={"fr_id": fr_id, "phase": self.phase}
        )
        
        if anomaly.is_confirmed:
            # 確認 anomaly：直接 REJECT，不浪費一輪
            self.decision_log.write(
                agent_id="hunter",
                fr_id=fr_id,
                decision="CONFIRMED_ANOMALY",
                reasoning=anomaly.reason
            )
            raise PHASE_HOOK_FAILED(
                f"FR-{fr_id}: Hunter Agent 確認 anomaly — "
                f"{anomaly.reason}"
            )
        
        if anomaly.is_suspicious:
            # 可疑但未確認：降低 tier（HOTL → 多模型共識）
            if getattr(self, "_current_tier", None) == Tier.LOW:
                self._current_tier = Tier.HOTL
            
            self.decision_log.write(
                agent_id="hunter",
                fr_id=fr_id,
                decision=f"SUSPICIOUS — {anomaly.reason}",
                reasoning=f"confidence={anomaly.confidence:.2f}"
            )
    
    self.langfuse.set_span_attribute(f"fr.{fr_id}.hunter_status", anomaly.status)
```

**對 4 個核心問題的幫助**: 幻覺（輸出明顯偏離正常模式）被 Hunter Agent 發現。

---

### Feature #7: UQLM Ensemble

**鉤入點**: `monitoring_after_dev()`

**整合理由**: Developer 輸出後第一時間計算 uncertainty score，結果影響後續所有決策。

```python
def monitoring_after_dev(self, fr_id: str, dev_result: dict):
    """Feature #7: UQLM — Developer 輸出的 uncertainty score"""
    if "files" not in dev_result:
        uaf = 0.0
    else:
        code_content = "\n".join([f["content"] for f in dev_result["files"]])
        uaf = self.uqlm.compute_code_uncertainty(code_content)
    
    # 寫入 Langfuse span（讚後續所有決策都能讀到）
    self.langfuse.set_span_attribute(f"fr.{fr_id}.uaf_score", uaf)
    
    # 寫入 Decision Log
    self.decision_log.write(
        agent_id="uqlm",
        fr_id=fr_id,
        decision=f"uaf={uaf:.3f}",
        reasoning=f"components={self.uqlm.get_components()}"
    )
    
    # UAF > 0.7 = 高 uncertainty → 直接升高 tier
    if uaf > 0.7 and getattr(self, "_current_tier", None) in (Tier.LOW, None):
        self._current_tier = Tier.HITL
        self._notify_human(f"FR-{fr_id}: UAF={uaf:.3f} — tier 升至 HITL")
    
    return uaf
```

**對 4 個核心問題的幫助**: 幻覺（高 UAF 分數代表答案不確定）被量化顯示。

---

### Feature #8: Gap Detector

**鉤入點**: `postflight_all()`

**整合理由**: Phase 完成後統一掃描測試覆蓋缺口。Phase 4 最關鍵，其他 Phase 也需要基礎結構檢查。

```python
def _postflight_gap_detection(self):
    """Feature #8: Phase 完成後測試覆蓋缺口掃描"""
    test_dir = self.project_path / "04-tests"
    if not test_dir.exists():
        logger.warning("04-tests/ 目錄不存在")
        return
    
    if self.phase == 4:
        # Phase 4：完整 Gap Detection
        gaps = self.gap_detector.scan_full(test_dir)
        
        if gaps:
            self._deliver("GAP_REPORT.md", {
                "phase": 4,
                "gaps": gaps,
                "total": len(gaps),
                "coverage_estimate": self.gap_detector.estimate_coverage(test_dir)
            })
            
            # 高嚴重性缺口 → 通知 Johnny
            high_severity = [g for g in gaps if g.severity >= 0.8]
            if high_severity:
                self._notify_human(
                    f"Phase 4: 發現 {len(high_severity)} 個高嚴重性測試缺口"
                )
    
    elif self.phase >= 3:
        # Phase 3+：基礎結構性檢查
        basic_gaps = self.gap_detector.scan_basic(test_dir)
        if basic_gaps:
            logger.warning(f"Phase {self.phase}: 基礎測試覆蓋不足 — {len(basic_gaps)} 項")
```

**對 4 個核心問題的幫助**: 偷懶（沒寫該寫的測試）在 Phase 完成時被發現。

---

### Feature #9: Risk Assessment

**鉤入點**: `preflight_all()` + `postflight_all()`

**整合理由**: 風險評估是持續性的，不是只在 Phase 結束。PRE-FLIGHT 發現風險信號，POST-FLIGHT 更新風險狀態。

```python
def _preflight_risk_assessment(self):
    """Feature #9: Phase 開始前風險評估"""
    risk = self.risk_assessor.evaluate_phase_start(
        phase=self.phase,
        project_path=self.project_path
    )
    
    # 記錄進合規報告
    self.compliance.log_risk_event(
        event_type="preflight",
        phase=self.phase,
        risk_score=risk.total_score,
        findings=risk.findings
    )
    
    # 極高風險 → PRE-FLIGHT 失敗
    if risk.total_score > 0.9:
        raise PREFLIGHT_FAILED(
            f"Phase {self.phase}: 風險極高（{risk.total_score:.2f}），"
            f"需要 Johnny 確認是否繼續"
        )
    
    # 高風險 → 通知 Johnny
    if risk.total_score > 0.7:
        self._notify_human(
            f"Phase {self.phase}: 風險偏高（{risk.total_score:.2f}），"
            f"請確認繼續"
        )

def _postflight_risk_assessment(self):
    """Feature #9: Phase 結束後風險評估"""
    risk = self.risk_assessor.evaluate_phase_end(
        phase=self.phase,
        project_path=self.project_path,
        effort_summary=self.effort.get_summary(self.phase)
    )
    
    self._deliver("RISK_REGISTER.md", risk.to_document())
    
    # 新發現的高風險 → 通知 Johnny
    high_risks = [r for r in risk.findings if r.severity >= 0.8]
    if high_risks:
        self._notify_human(
            f"Phase {self.phase}: 發現 {len(high_risks)} 個高風險 — "
            f"需制定緩解措施"
        )
```

**對 4 個核心問題的幫助**: 自我感覺良好（Agent 認為沒問題但 Risk Assessor 說有風險）被量化顯示。

---

### Feature #10: LangGraph

**整合方式**: 包裹 FR EXECUTION LOOP

**整合理由**: 目前的 FR EXECUTION LOOP 是 stateless for loop。LangGraph 可以讓 FR execution 有狀態，知道每個 FR 的執行歷史。

```python
class FRExecutionGraph:
    """Feature #10: LangGraph — 有狀態的 FR Execution"""
    
    def __init__(self, frs: list[str]):
        # 定義 nodes
        self.nodes = {
            "preflight": self._preflight_node,
            "developer": self._developer_node,
            "reviewer": self._reviewer_node,
            "hunter": self._hunter_node,
            "governance": self._governance_node,
            "postflight": self._postflight_node,
        }
        
        # 定義 edges（條件跳轉）
        self.edges = {
            "preflight": ["developer"],
            "developer": ["hunter"],  # 總是經過 Hunter
            "hunter": ["governance"],  # Hunter 輸出governance decision
            "governance": {
                "HOTL": ["reviewer", "reviewer"],  # 兩個 reviewer
                "HITL": ["reviewer"],  # 通知 human
                "LOOP": ["developer"],  # 重新 developer
                "BLOCK": ["postflight"],  # 直接結束
            },
            "reviewer": {
                "APPROVE": ["developer:next"],
                "REJECT": ["developer:current"],
            }
        }
    
    def execute(self, frs: list[str]):
        """執行有狀態的 FR graph"""
        state = {"current_fr": 0, "fr_states": {}, "history": []}
        
        while state["current_fr"] < len(frs):
            fr_id = frs[state["current_fr"]]
            state = self._execute_fr(fr_id, state)
            
            # 根據 state 決定 next FR
            if state["fr_states"][fr_id].get("next") == "developer:next":
                state["current_fr"] += 1
            # 其他情況保持在當前 FR（REJECT loop）
        
        return self._postflight_node(state)
    
    def _execute_fr(self, fr_id: str, state: dict):
        """執行單個 FR，經過完整 node 流程"""
        # ... 執行 preflight → developer → hunter → governance → reviewer
        # ... 每個 node 的輸出寫入 state["fr_states"][fr_id]
        return state
```

**對 4 個核心問題的幫助**: FR execution 有完整歷史，不會忘記之前做過什麼。

---

### Feature #11: Langfuse

**鉤入點**: 全程（所有鉤子）

**整合理由**: Langfuse 是觀測基礎設施，所有其他 Feature 的 trace 都需要它。

```python
def preflight_all(self):
    self.langfuse = LangfuseClient()
    self.trace = self.langfuse.trace(
        name=f"phase-{self.phase}",
        metadata={"project": self.project_path}
    )
    
    span = self.trace.span("preflight")
    span.set_attribute("phase", self.phase)
    span.set_attribute("fr_count", len(self.frs))
    self._preflight_fsm()
    # ... 其他 preflight checks ...
    span.set_attribute("preflight_passed", True)
    span.end()

def monitoring_after_dev(self, fr_id: str, dev_result: dict):
    span = self.trace.span(f"fr-{fr_id}-dev")
    span.set_attribute("fr_id", fr_id)
    span.set_attribute("uaf_score", uaf)
    span.set_attribute("hunter_status", anomaly.status)
    span.set_attribute("files_count", len(dev_result.get("files", [])))
    span.end()

def postflight_all(self):
    span = self.trace.span("postflight")
    # ... postflight operations ...
    self.trace.end()
```

---

### Feature #12: Compliance

**鉤入點**: `postflight_all()` + `monitoring_hr12_check()`

**整合理由**: EU AI Act Art.14 要求 human oversight 的 audit trail。HR-12 觸發和 Kill-Switch 觸發都必須記錄。

```python
def _postflight_compliance_report(self):
    """Feature #12: Phase 完成時生成合規報告"""
    report = {
        "phase": self.phase,
        "EU_AI_Act_Art14": {
            "total_frs": len(self.frs),
            "humans_approved": self._count_humans_approved(),
            "hotl_tiers": self._count_tier(Tier.HOTL),
            "hitl_tiers": self._count_tier(Tier.HITL),
            "blocked": self._count_tier(Tier.BLOCK),
        },
        "NIST_AI_RMF": {
            "Govern": self._count_govern_decisions(),
            "Monitor": self.hunter.get_anomaly_count(),
            "Measure": self.llm_cascade.get_model_usage_count(),
            "Manage": self._count_human_interventions(),
        },
        "Anthropic_RSP": {
            "asl_level": self._determine_asl_level(),
            "sign_offs": self._get_sign_offs(),
        }
    }
    
    self._deliver(f"COMPLIANCE_PHASE_{self.phase}.md", report)

def monitoring_hr12_check(self, fr_id: str, iteration: int):
    if iteration > 5:
        self.compliance.report_event(
            event_type="HR12_TRIGGERED",
            EU_article="14(4)(a)",
            NIST_function="Manage",
            evidence={"fr": fr_id, "iterations": iteration}
        )
```

---

### Feature #13: Observability (Effort + Decision Log)

**鉤入點**: 全程（所有鉤子）

**整合理由**: Effort metrics 和 Decision Log 追蹤每個環節，是其他 Feature 的數據基礎。

```python
def __init__(self, project_path, phase):
    self.decision_log = DecisionLogWriter(data_dir=f"{project_path}/data")
    self.effort = EffortTracker(db_path=f"{project_path}/data/effort_metrics.db")

def monitoring_before_dev(self, fr_id: str):
    self.effort.start(
        effort_id=f"dev-{fr_id}",
        agent_id="developer",
        trace_id=self.langfuse.trace_id
    )

def monitoring_after_dev(self, fr_id: str, dev_result: dict):
    record = self.effort.stop(f"dev-{fr_id}")
    
    # 檢查「太快完成」= 疑似偷懶
    if record.time_spent_ms < self._get_min_time(fr_id):
        self.risk_assessor.register(
            f"FR-{fr_id}: developer 完成時間異常短 "
            f"({record.time_spent_ms/1000:.1f}s)",
            severity=SEVERITY.MEDIUM,
            type="偷懶信號"
        )

def monitoring_after_rev(self, fr_id: str, rev_result: dict):
    self.effort.increment(f"rev-{fr_id}", tokens=rev_result.get("tokens_used", 0))

def postflight_all(self):
    summary = self.effort.get_phase_summary(self.phase)
    
    # 寫入 decision log 的尾端標記
    self.decision_log.write(
        agent_id="phasehooks",
        decision=f"Phase {self.phase} completed",
        reasoning=f"total_time={summary.total_time_ms}ms, "
                  f"total_tokens={summary.total_tokens}"
    )
```

---

## 三、整合後的 PhaseHooks 執行流程

```
Johnny: 「執行 Phase 3」
         ↓
Agent: plan-phase --phase 3 --goal "FR-01~FR-08"
         ↓
Agent: run-phase --phase 3
         ↓
┌─────────────────────────────────────────────────────────────┐
│ preflight_all() ← SAIF (#1) + Risk Assessment (#9)      │
│                 ← Langfuse trace 開始 (#11)               │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ FR LOOP（每個 FR 依次執行）                                 │
│                                                             │
│ for FR in FRs:                                             │
│   monitoring_before_dev(FR) ← Decision Log (#13)           │
│       ↓                                                    │
│   sessions_spawn(developer) → files returned              │
│       ↓                                                    │
│   monitoring_after_dev(FR)                                 │
│     ├── UQLM (#7) → uaf_score                            │
│     ├── Hunter (#6) → anomaly detection                   │
│     ├── Prompt Shields (#2) → injection scan               │
│     ├── Effort (#13) → time/token record                  │
│     └── Decision Log (#13) → uaf + anomaly                │
│       ↓                                                    │
│   monitoring_before_rev(FR)                                │
│     ├── Governance (#3) → tier classification            │
│     ├── Decision Log (#13) → tier decision                │
│     └── 若 tier==HOTL → 多 Reviewer sessions (#5)         │
│       ↓                                                    │
│   sessions_spawn(reviewer) → review_status               │
│       ↓                                                    │
│   monitoring_after_rev(FR)                                │
│     ├── Governance verify (#3)                            │
│     ├── Effort increment (#13)                            │
│     └── Decision Log (#13) → APPROVE/REJECT               │
│       ↓                                                    │
│   monitoring_hr12_check(FR, iteration)                    │
│     └── 若 >5 → Kill-Switch (#4) + Compliance (#12)       │
└─────────────────────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────────────────────┐
│ postflight_all()                                           │
│   ├── Gap Detector (#8) → GAP_REPORT.md                   │
│   ├── Risk Assessment (#9) → RISK_REGISTER.md             │
│   ├── Compliance (#12) → COMPLIANCE_PHASE_N.md            │
│   ├── Effort Summary (#13)                               │
│   └── Langfuse close (#11)                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 四、對 4 個核心問題的即時防護覆蓋

| 問題 | 即時防護鉤子 | Feature |
|------|------------|--------|
| **偷懶** | `monitoring_after_dev()` — effort.time_spent < minimum | #13 Effort |
| **偷懶** | `postflight_all()` — Gap Detector 發現測試覆蓋不足 | #8 Gap Detector |
| **走捷徑** | `monitoring_before_rev()` — Governance tier 分類 | #3 Governance |
| **走捷徑** | `monitoring_hr12_check()` — Kill-Switch 熔斷 | #4 Kill-Switch |
| **幻覺** | `monitoring_after_dev()` — UQLM uaf_score > 0.7 | #7 UQLM |
| **幻覺** | `monitoring_after_dev()` — Hunter Agent confirmed anomaly | #6 Hunter Agent |
| **造假** | `monitoring_after_dev()` — Prompt Shields injection block | #2 Prompt Shields |
| **造假** | `postflight_all()` — Decision Log 可事後審查 | #13 Decision Log |
| **自我感覺良好** | `preflight_all()` + `postflight_all()` — Risk Assessment 量化分數 | #9 Risk Assessment |
| **自我感覺良好** | `monitoring_after_dev()` — UQLM 外部客觀分數 | #7 UQLM |

**關鍵改善**：每個問題有多個 Feature 同時制約，不再是單一防線。

---

## 五、v2.0 vs v3.0 對照

| 面向 | v2.0 | v3.0 |
|------|------|------|
| **整合點** | 5 個新建 Stage | 7 個現有 PhaseHooks 鉤子 |
| **架構假設** | 有獨立的 Agent Runtime Pipeline | 沒有獨立 pipeline，全部鉤入 PhaseHooks |
| **Stage 1** | Observability Foundation | preflight_all() — 5 分鐘內可完成 |
| **Governance** | Stage 2，pipeline 中間 | monitoring_before_rev()，是第一個裁判 |
| **UQLM/Hunter** | Stage 3 Intelligence Layer | monitoring_after_dev()，第一時間檢查輸出 |
| **LLM Cascade** | Stage 2-3，多模型路由 | monitoring_before_rev() tier==HOTL 時多 Reviewer sessions |
| **Kill-Switch** | Stage 2，HealthMonitor 觸發 | monitoring_hr12_check()，HR-12 觸發時熔