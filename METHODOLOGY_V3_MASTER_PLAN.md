# methodology-v2 → v3.0 完整整合方案（合併版）

**版本**: 1.1（合併優化版）
**日期**: 2026-04-17
**基於**: Johnny Lu 方案 v1.0 + Musk 分析 v1.0
**目標**: 將 methodology-v2 升級至 v3.0 企業級標準
**團隊規模**: 3-5 人
**預估工期**: 8 週（全職）

---

## 一、執行摘要

### v3.0 核心價值

| 問題 | v3.0 解決方案 |
|-----|-------------|
| Agent 偷懶 | Effort Metrics + 決策日誌追蹤 |
| 走捷徑 | 5-Agent Debate 強制多元觀點 |
| 幻覺 | UAF+CLAP+MetaQA 三層偵測 |
| 作假 | Implementation Gap Detection |
| 自我感覺良好 | Confidence Calibration |
| 無標準介面 | MCP Protocol 標準化 |
| 固定人類介入 | HOTL/HITL/HOOTL 分級治理 |
| 失控無阻斷 | Kill-Switch (<5s) |
| 無合規對應 | EU AI Act + NIST + RSP v3.0 |

### methodology-v2 現況

| 項目 | 狀態 |
|------|------|
| **GitHub 版本** | v8.6 ✅ |
| **成熟度** | v1.0 等級（個人/小團隊可用，企業級不足）|
| **需升級至** | v3.0 企業級標準 |

---

## 二、組件整合評估（完整版）

| 優先級 | 組件 | 整合複雜度 | 架構衝擊 | 落地方式 |
|--------|------|-----------|---------|---------|
| **P0** | MCP Protocol | 低 | 可漸進 | 新增 adapter 層，不動核心 |
| **P0** | HOTL/HITL/HOOTL 分級治理 | 低 | 可漸進 | 重構現有 governance + hitl_controller |
| **P1** | Kill-Switch 熔斷機制 | 低 | 可漸進 | 新增 circuit_breaker.py |
| **P1** | Multi-Agent Debate（5-Agent）| 中 | 可漸進 | 新增 debate_engine，複用 steering_loop |
| **P1** | UAF+CLAP+MetaQA 幻覺偵測 | 中 | 可漸進 | 整合進 Constitution/BVS |
| **P1** | Implementation Gap Detection | 中 | 可漸進 | 新增 gap_detector.py |
| **P1** | 8-維度風險評估 | 低 | 可漸進 | 新增 risk_assessment_engine.py |
| **P1** | LangGraph 協調 | 中 | 中等 | langgraph_migrator 已存在，需激活 |
| **P2** | Langfuse 可觀測性 | 中 | 可漸進 | 替換現有 Span/Trace 實作 |
| **P2** | EU AI Act / NIST 合規 | 高 | 破壞性 | 新增 compliance 模組 |

---

## 三、架構總覽

```
┌──────────────────────────────────────────────────────────────┐
│ Layer 6: Compliance (EU AI Act · NIST AI RMF · RSP v3.0) │
├──────────────────────────────────────────────────────────────┤
│ Layer 5: Observability (Langfuse / W&B Weave / OTel) │
├──────────────────────────────────────────────────────────────┤
│ Layer 4: Tiered Governance (HOTL · HITL · HOOTL) │
├──────────────────────────────────────────────────────────────┤
│ Layer 3: Hallucination Detection (UAF + CLAP + MetaQA) │
│            + Implementation Gap Detection │
├──────────────────────────────────────────────────────────────┤
│ Layer 2: 5-Agent Debate Core │
│ Planner ⇄ SpecCritic ⇄ Devil's Advocate ⇄ TruthValidator ⇄ Judge │
│ (LangGraph orchestration) │
├──────────────────────────────────────────────────────────────┤
│ Layer 1: MCP Interface (Tools · Resources · Prompts) │
│ + Agents.md (每 Agent 行為規範) │
└──────────────────────────────────────────────────────────────┘
```

---

## 四、Layer 1: MCP 標準化介面

### 4.1 現況分析
- `mcp_adapter/mcp_adapter.py` 已存在，實現基本非同步 client/server
- `tool_registry.py` 負責 tool 註冊與派發
- **缺口**：無 stdio transport、無 service discovery、無 MCP official SDK

### 4.2 MCP Servers 清單

| MCP Server | 功能 | 需新增/改動 |
|------------|------|-------------|
| `mcp_spec_server` | 讀寫 spec + YAML 註解 | **NEW** |
| `mcp_audit_server` | Immutable decision journal | 擴充現有 trace |
| `mcp_risk_server` | 8 維度即時風險分數 | **NEW** |
| `mcp_test_server` | pytest 執行 + 覆蓋率 | 整合現有 wrapper |
| `mcp_git_server` | Git 操作 | **NEW** |
| `mcp_hallucination_server` | UAF/CLAP 呼叫 | **NEW** |

### 4.3 Agents.md 規範檔

每個 Agent 配一份 `Agents.md`，定義其：
- 身份 / 職責
- 可用 MCP servers（白名單）
- 行為紅線（禁止操作）
- 升級路徑（何時 escalate）

**範例** (`agents/planner/Agents.md`):
```markdown
# Agent: Planner
## Identity
Role: 規格與架構設計者
Model: claude-sonnet-4.5

## MCP Servers (Whitelist)
- mcp_spec (read/write)
- mcp_audit (write)
- mcp_risk (read)

## Red Lines
- 禁止執行 code (不在白名單)
- 禁止繞過 Devil's Advocate

## Escalation
- confidence < 0.7 → 觸發 HITL
- detected contradiction → halt + human review
```

### 4.4 實作結構

```
mcp/
├── __init__.py
├── mcp_spec_server.py         # NEW
├── mcp_audit_server.py        # 擴充
├── mcp_risk_server.py         # NEW
├── mcp_test_server.py          # 整合
├── mcp_git_server.py           # NEW
├── mcp_hallucination_server.py # NEW
└── agents/                     # 每 agent 規範檔
    ├── planner/Agents.md
    ├── spec_critic/Agents.md
    ├── devils_advocate/Agents.md
    ├── truth_validator/Agents.md
    └── judge/Agents.md
```

### 4.5 預期產出
- 6 個 MCP servers
- 5 份 Agents.md 規範檔
- stdio transport + service discovery

---

## 五、Layer 2: Multi-Agent Debate（5-Agent）

### 5.1 現況分析
- `steering/steering_loop.py` 是 2-Agent（Planner + Critic）
- 缺口：無 Devil's Advocate、無 Truth Validator、無 Judge

### 5.2 5-Agent 角色定義

| 角色 | 功能 | 現有/新增 |
|------|------|----------|
| **Planner** | 生成 spec + decision log | 現有，擴充日誌格式 |
| **SpecCritic** | Constitution 驗證 | 現有，升級 MCP |
| **Devil's Advocate** | 5-10 強制挑戰 | **NEW（核心）** |
| **Truth Validator** | 事實查核 | **NEW（核心）** |
| **Judge** | 不同 model family 仲裁 | **NEW（核心）** |

### 5.3 Decision Log 格式（Planner 輸出）

```yaml
planner_decision_trace:
  decision_id: "arch-001"
  choice: "Microservices architecture"
  alternatives_considered:
    - "Monolith (rejected: scaling concerns)"
    - "Serverless (rejected: vendor lock-in)"
    - "Event-driven (rejected: complexity)"
  confidence_score: 7.5/10
  effort_minutes: 120
  key_assumptions:
    - "Team has K8s expertise"
    - "Budget supports $50k/year"
  uncertainties:
    - "Service boundary TBD"
    - "Distributed transaction strategy TBD"
```

### 5.4 Devil's Advocate Prompt

```
你必須挑戰 Planner 的每個核心決策。必問：
1. 這個決策的證據是什麼？
2. 為什麼拒絕其他 3+ alternatives？
3. 團隊真的有能力執行嗎？
4. 隱藏成本是多少？
5. 如果錯了，最壞情況是什麼？

每個挑戰必須包含 severity (CRITICAL/HIGH/MEDIUM)。
```

### 5.5 Judge 仲裁邏輯

```python
def judge_evaluate(state):
  # 使用不同 model family 避免同源污染
  if cosine_similarity(state.positions) > 0.85:
    return "consensus"
  elif state.round >= 3:
    return "escalate"
  elif state.red_line_violation:
    return "veto"
```

### 5.6 Debate 終止條件

| 條件 | 結果 |
|------|------|
| **Consensus** | Judge 評定 3 方論點收斂（cosine sim > 0.85）→ 通過 |
| **Escalate** | 3 輪後仍分歧 → 觸發 HITL |
| **Veto** | DA/Truth Validator 發現 red-line 違反 → 立即 halt |

### 5.7 實作結構

```
agents/
├── planner/
│   ├── Agents.md
│   └── prompt.py
├── spec_critic/
│   ├── Agents.md
│   └── prompt.py
├── devils_advocate/        # NEW
│   ├── Agents.md
│   └── prompt.py
├── truth_validator/        # NEW
│   ├── Agents.md
│   └── prompt.py
└── judge/
    ├── Agents.md          # NEW
    └── prompt.py          # NEW

debate/
├── __init__.py
├── consensus.py           # NEW
├── langgraph_debate.py    # NEW
└── debate_state.py       # NEW
```

---

## 六、Layer 3: 三層幻覺偵測 + Implementation Gap

### 6.1 UAF（Uncertainty-Aware Fusion）

```python
def uncertainty_aware_fusion(logits, samples, grounding_matches):
  entropy = calculate_token_entropy(logits)  # 0-1
  self_consistency = cross_sample_consistency(samples)  # 0-1
  grounding = grounding_matches / total_claims  # 0-1

  score = 0.3*entropy + 0.4*(1-self_consistency) + 0.3*(1-grounding)
  return score  # > 0.5 = HIGH UNCERTAINTY
```

### 6.2 CLAP（Cross-Layer Attention Probing）

- 適用於 open-weight model（Llama-3, Qwen-2.5）
- Claude/GPT 退而求其次用 logprobs

### 6.3 MetaQA（定期回測）

- 每週抽出過去 decisions 中的事實斷言
- 生成 QA pairs，用 HCMBench 評估

### 6.4 Implementation Gap Detection（實作一致性偵測）

| Gap 類型 | 偵測方式 |
|-----------|---------|
| **Base64 vs AES** | AST 分析：密碼學實作一致性 |
| **test.todo 灌水** | Assertion count：假的測試覆蓋率 |
| **Empty catch** | AST 分析：錯誤處理是否真的實作 |
| **Hardcoded secrets** | 規則掃描 |

### 6.5 實作結構

```
detection/
├── __init__.py
├── uaf.py                  # UAF 引擎
├── clap.py                 # CLAP 分類器
├── metaqa.py               # MetaQA 回測
└── gap_detector.py         # Implementation Gap
```

---

## 七、Layer 4: 分級治理

### 7.1 三級定義

| 風險分 | 模式 | 人類角色 | 觸發條件 |
|--------|------|---------|----------|
| **0-3** | **HOOTL** | 事後抽樣審計 | 完全自動 |
| **4-6** | **HOTL** | 即時監看，可中斷 | Dashboard 監看 |
| **7-10** | **HITL** | 必經決策點，需簽核 | 審批 Gate |

### 7.2 8 維度風險評估（Constitution TH 對應）

| v3.0 維度 | Constitution TH | 測量方式 | 閾值 |
|-----------|---------------|---------|------|
| 正確性 (Correctness) | TH-01=100%, TH-02=100% | Constitution correctness score | ≥ 95% |
| 完整性 (Completeness) | TH-03=100% | Constitution completeness score | ≥ 90% |
| 可測試性 (Testability) | TH-05>90%, TH-06>90% | Coverage + Test pass rate | ≥ 85% |
| 可維護性 (Maintainability) | TH-05>90% | Cyclomatic complexity | ≤ 10 |
| 安全性 (Security) | TH-04=100% | Security constitution check | = 100% |
| 效能 (Performance) | TH-07=100% | Performance test pass rate | = 100% |
| 可用性 (Usability) | TH-14=100% | UAT pass rate | = 100% |
| 可靠性 (Reliability) | TH-08≥80% | MTBF, fault tolerance | ≥ 80% |

### 7.3 維度權重

```yaml
dimensions:
  technical_feasibility: 20%
  security_maturity: 15%
  schedule_realism: 15%
  operational_readiness: 10%
  scope_creep_risk: 10%
  dependency_risk: 10%
  validation_coverage: 10%
  organizational_alignment: 10%
```

### 7.4 Kill-Switch 觸發條件

```python
CIRCUIT_BREAKER_THRESHOLDS = {
  "failure_rate": 0.05,       # 5% 錯誤率
  "latency_ms": 5000,         # > 5s 延遲
  "failure_count_trigger": 3,  # 連續 3 次失敗
  "recovery_timeout": 60,     # 60s 後嘗試 HALF_OPEN
}

def kill_switch_trigger(error_rate, latency_p99):
  if error_rate > 0.05 or latency_p99 > 5000:
    halt_all_agents()       # < 5 秒停止
    notify_on_call()
    log_incident()
```

### 7.5 不可降級 Gate（對應 EU AI Act Art.14）

| Gate | 名稱 | 原因 |
|------|------|------|
| **G1** | 架構決策 | 無法繞過的 oversight |
| **G4** | 部署前 | 無法繞過的 oversight |

### 7.6 實作結構

```
governance/
├── __init__.py
├── tiered_governance.py    # P0：分級引擎
├── risk_scorer.py          # P1：8維度評估
├── gate_policy.py          # P1：Gate 政策
├── kill_switch.py          # P1：熔斷觸發
└── circuit_breaker.py       # P1：熔斷實現
```

---

## 八、Layer 5: 可觀測性

### 8.1 Langfuse 整合

**必備 Trace 欄位**（對應 NIST AI RMF Measure）：

```yaml
trace:
  trace_id: uuid
  agent_id: planner
  model: claude-sonnet-4.5
  prompt_hash: sha256
  input_tokens: 1234
  output_tokens: 567
  latency_ms: 890
  uaf_score: 0.12
  clap_flag: false
  risk_score: 5.2
  hitl_gate: G0
  human_decision: approved | rejected | escalated
  decided_by: user@org
  decision_rationale: "..."
  compliance_tags:
    - eu_ai_act_art14
    - nist_map_3.5
```

### 8.2 Dashboard 最低要求

- **即時**：當前 agent 活躍數 / 平均 uaf_score / HITL queue 深度
- **趨勢**：每日 debate rounds / escalation rate / hallucination rate
- **審計**：可依 trace_id 重現任一決策路徑

### 8.3 實作結構

```
observability/
├── __init__.py
├── langfuse_client.py      # Langfuse 適配層
├── dashboard.py             # Dashboard
└── trace_formatter.py      # NIST AI RMF 欄位格式
```

---

## 九、Layer 6: 合規對應

### 9.1 EU AI Act Article 14 對照

| 條文要求 | v3.0 實作 |
|---------|----------|
| 14(1) human oversight | HITL/HOTL 分級 |
| 14(4)(a) understand AI limits | Agents.md + model card |
| 14(4)(b) automation bias awareness | DA + UAF 警示 |
| 14(4)(c) interpret outputs | Langfuse trace viewer |
| 14(4)(d) human override | HITL Gate |
| 14(4)(e) interrupt system | Kill-switch (<5s) |

### 9.2 NIST AI RMF 對照

| NIST AI RMF 函數 | 對應 methodology-v2 機制 |
|----------------|------------------------|
| Govern | Agents.md + Constitution |
| Map | Phase 1 TRACEABILITY_MATRIX |
| Measure | Langfuse metrics + UAF/CLAP |
| Manage | Gate policy + Kill-switch |

### 9.3 Anthropic RSP v3.0 對接

- **ASL-3**（autonomous coding）：對應 v3.0 HITL G1/G4 強制簽核
- **ASL-4**：當前 v3.0 尚不建議放行

### 9.4 實作結構

```
compliance/
├── __init__.py
├── eu_ai_act.py             # EU AI Act 對照
├── nist_rmf.py              # NIST AI RMF 對照
├── compliance_matrix.py       # 合規矩陣
└── compliance_reporter.py    # 自動報告生成
```

---

## 十、8 週實施時程（含風險標註）

| 週 | 主題 | 交付物 | 依賴 | 風險 |
|----|------|--------|------|------|
| **W1** | MCP 基礎 | 6 MCP servers + 5 Agents.md + stdio transport | 無 | 低 |
| **W2** | Agents 升級 | Planner/Critic decision log 格式 | W1 | 低 |
| **W3** | Debate Core | DA + Truth Validator + Judge + LangGraph | W1, W2 | **中**（重構）|
| **W4** | 幻覺偵測 | UAF + CLAP + MetaQA + Gap Detector | W3 | **中**（新架構）|
| **W5** | 可觀測性 | Langfuse dashboard | W1 | 低 |
| **W6** | 分級治理 | HOTL/HITL/HOOTL + Kill-switch | W3, W4 | **中** |
| **W7** | 合規對應 | EU AI Act + NIST mapping | W6 | **高**（破壞性）|
| **W8** | 整合驗收 | 端到端測試 + 紅隊演練 | W1-W7 | 中 |

### 風險緩解策略

| 步驟 | 主要風險 | 緩解策略 |
|------|---------|---------|
| W3 Debate | steering_loop 重構破壞現有流程 | Feature flag，保留舊邏輯開關 |
| W4 幻覺偵測 | 三層架構複雜度超標 | 先實現 UAF（最簡單），再迭代 |
| W6 分級治理 | Kill-switch 誤觸發 | 先用 dry-run 模式驗證 |
| W7 合規 | Constitution 架構破壞 | 新增 `_COMPLIANCE.md` 而非修改現有 Constitution |

---

## 十一、資源評估

| 優先級 | 組件 | Agent 工時 | Johnny Review | 總時間 |
|--------|------|-----------|-------------|--------|
| W1 | MCP Protocol | 8h | 2h | ~2 天 |
| W2 | Agents 升級 | 4h | 1h | ~1 天 |
| W3 | Debate Core | 12h | 3h | ~3 天 |
| W4 | 幻覺偵測 | 15h | 4h | ~4 天 |
| W5 | 可觀測性 | 8h | 2h | ~2 天 |
| W6 | 分級治理 + Kill-switch | 10h | 3h | ~2.5 天 |
| W7 | 合規對應 | 20h | 6h | ~5 天 |
| W8 | 整合驗收 | 10h | 3h | ~2.5 天 |
| **合計** | | **87h** | **24h** | **~22 天** |

**對應 8 週**：3 人並行（29h/週 ÷ 3人 ≈ 10h/人/週）

---

## 十二、KPI 評估

| KPI | 目標 | 測量方式 |
|-----|------|----------|
| **幻覺發生率** | < 0.5% | UAF + MetaQA |
| **HITL 平均延遲** | < 2 小時 | Langfuse trace |
| **Debate 共識率** | > 85% (3 輪內) | Judge verdict |
| **Trace 完整度** | ≥ 99% | Langfuse |
| **合規稽核通過率** | 100% | Art.14 對照 |
| **開發者滿意度** | NPS ≥ 40 | 調查 |

---

## 十三、完整檔案結構

```
methodology-v2/
├── mcp/                              # W1
│   ├── mcp_spec_server.py
│   ├── mcp_audit_server.py
│   ├── mcp_risk_server.py
│   ├── mcp_test_server.py
│   ├── mcp_git_server.py
│   ├── mcp_hallucination_server.py
│   └── agents/
│       ├── planner/Agents.md
│       ├── spec_critic/Agents.md
│       ├── devils_advocate/Agents.md
│       ├── truth_validator/Agents.md
│       └── judge/Agents.md
│
├── agents/                           # W2
│   ├── planner/
│   │   ├── Agents.md
│   │   └── decision_log.py
│   ├── spec_critic/
│   │   ├── Agents.md
│   │   └── prompt.py
│   ├── devils_advocate/              # W3
│   │   ├── Agents.md
│   │   └── prompt.py
│   ├── truth_validator/              # W3
│   │   ├── Agents.md
│   │   └── prompt.py
│   └── judge/                        # W3
│       ├── Agents.md
│       └── prompt.py
│
├── debate/                           # W3
│   ├── consensus.py
│   ├── langgraph_debate.py
│   └── debate_state.py
│
├── detection/                        # W4
│   ├── uaf.py
│   ├── clap.py
│   ├── metaqa.py
│   └── gap_detector.py
│
├── governance/                      # W6
│   ├── tiered_governance.py
│   ├── risk_scorer.py
│   ├── gate_policy.py
│   ├── kill_switch.py
│   └── circuit_breaker.py
│
├── observability/                    # W5
│   ├── langfuse_client.py
│   ├── dashboard.py
│   └── trace_formatter.py
│
├── compliance/                       # W7
│   ├── eu_ai_act.py
│   ├── nist_rmf.py
│   ├── compliance_matrix.py
│   └── compliance_reporter.py
│
└── METHODOLOGY_V3_MASTER_PLAN.md     # 本文件
```

---

## 十四、v3.0 完整性核查

| v3.0 組件 | 分析狀態 | 對應章節 |
|-----------|---------|---------|
| MCP Protocol | ✅ | W1 |
| Multi-Agent Debate (5-Agent) | ✅ | W3 |
| UAF + CLAP + MetaQA | ✅ | W4 |
| Implementation Gap Detection | ✅ | W4 |
| HOTL / HITL / HOOTL | ✅ | W6 |
| Kill-Switch | ✅ | W6 |
| 8-維度風險評估 | ✅ | W6 |
| LangGraph | ✅ | W3 |
| Langfuse | ✅ | W5 |
| EU AI Act Art.14 | ✅ | W7 |
| NIST AI RMF | ✅ | W7 |
| Anthropic RSP v3.0 | ✅ | W7 |
| Decision Log YAML 格式 | ✅ | W2 |
| Agents.md 規範檔 | ✅ | W1 |

---

*文件版本：1.1（合併優化版）*
*更新日期：2026-04-17*
