# methodology-v2 → v3.0 TDD 驗證方案
## 每個 Feature 的測試驅動開發現劃

**版本**: 1.0
**日期**: 2026-04-17
**目的**: 採用 TDD 手法，每個 feature 先定義「如何驗證」，再實作

---

## TDD 原則

```
1. 先寫測試（Red）
2. 實作最小代碼通過測試（Green）
3. 重構（Refactor）
4. 下一個 feature
```

---

## P0 組件驗證方案

---

### P0-1：MCP Protocol

#### 測試檔案結構

```
tests/
├── unit/
│   ├── test_mcp_spec_server.py
│   ├── test_mcp_audit_server.py
│   ├── test_mcp_risk_server.py
│   ├── test_mcp_test_server.py
│   ├── test_mcp_git_server.py
│   └── test_mcp_hallucination_server.py
└── integration/
    ├── test_mcp_tool_bridge.py
    └── test_mcp_service_discovery.py
```

#### Test Cases

| Test ID | 測試名稱 | 驗證內容 | 預期結果 |
|---------|---------|---------|---------|
| MCP-UT-001 | `test_spec_server_read_spec` | 讀取 spec.yaml | 返回正確內容 |
| MCP-UT-002 | `test_spec_server_write_annotation` | 寫入 YAML 註解 | 檔案更新 |
| MCP-UT-003 | `test_audit_server_write_journal` | 寫入 immutable log | append-only |
| MCP-UT-004 | `test_risk_server_query_score` | 查詢 8-維度分數 | 返回 0-10 分數 |
| MCP-UT-005 | `test_test_server_run_pytest` | 執行 pytest | 返回 pass/fail |
| MCP-UT-006 | `test_git_server_get_branch` | 查詢 current branch | 返回 branch name |
| MCP-UT-007 | `test_hallucination_server_query_uaf` | 呼叫 UAF 分數 | 返回 uncertainty score |
| MCP-INT-001 | `test_tool_bridge_mcp_to_native` | MCP schema → native tool | 正確映射 |
| MCP-INT-002 | `test_service_discovery_whitelist` | 白名單過濾 | 未授權 server 被拒 |

#### TDD 步驟

```
Step 1: Red
  → 寫 MCP-UT-001 ~ MCP-UT-007（全部 FAIL）

Step 2: Green
  → 實作 mcp_spec_server.py（最小通過）
  → 實作 mcp_audit_server.py
  → 實作 mcp_risk_server.py
  → ...

Step 3: Refactor
  → 統一 MCP server 介面格式
  → 提取 base class
```

#### 驗收標準

- [ ] MCP-UT-001 ~ MCP-UT-007 全部 PASS
- [ ] MCP-INT-001 ~ MCP-INT-002 全部 PASS
- [ ] Coverage ≥ 80%

---

### P0-2：HOTL/HITL/HOOTL 分級治理

#### 測試檔案結構

```
tests/
├── unit/
│   ├── test_tiered_governance.py
│   ├── test_risk_scorer.py
│   └── test_gate_policy.py
└── integration/
    └── test_tier_integration.py
```

#### Test Cases

| Test ID | 測試名稱 | 驗證內容 | 預期結果 |
|---------|---------|---------|---------|
| TIER-UT-001 | `test_risk_score_hoorl` | risk < 4 | mode = "HOOTL" |
| TIER-UT-002 | `test_risk_score_hotl` | risk 4-6 | mode = "HOTL" |
| TIER-UT-003 | `test_risk_score_hitl` | risk > 6 | mode = "HITL" |
| TIER-UT-004 | `test_phase7_forces_hotl` | Phase 7 任何 risk | mode = "HOTL" |
| TIER-UT-005 | `test_g1_architecture_mandatory` | G1 gate | 不可繞過 |
| TIER-UT-006 | `test_g4_deployment_mandatory` | G4 gate | 不可繞過 |
| TIER-INT-001 | `test_tier_switch_on_risk_change` | risk 從 3→5 | mode 從 HOOTL→HOTL |
| TIER-INT-002 | `test_escalation_to_hitl` | risk > 6 + G1 | 觸發 HITL approval |

#### TDD 步驟

```
Step 1: Red
  → 寫 TIER-UT-001 ~ TIER-UT-006（全部 FAIL）

Step 2: Green
  → 實作 tiered_governance.py（最小通過）
  → 實作 risk_scorer.py
  → 實作 gate_policy.py

Step 3: Refactor
  → 統一 gate 介面
  → 新增 audit log鉤子
```

#### 驗收標準

- [ ] TIER-UT-001 ~ TIER-UT-006 全部 PASS
- [ ] TIER-INT-001 ~ TIER-INT-002 全部 PASS
- [ ] Coverage ≥ 80%

---

## P1 組件驗證方案

---

### P1-1：Kill-Switch 熔斷機制

#### 測試檔案結構

```
tests/
├── unit/
│   └── test_circuit_breaker.py
└── integration/
    └── test_kill_switch_integration.py
```

#### Test Cases

| Test ID | 測試名稱 | 驗證內容 | 預期結果 |
|---------|---------|---------|---------|
| KILL-UT-001 | `test_circuit_breaker_opens_on_failure_rate` | failure > 5% | state = "OPEN" |
| KILL-UT-002 | `test_circuit_breaker_opens_on_latency` | latency > 5000ms | state = "OPEN" |
| KILL-UT-003 | `test_circuit_breaker_half_open` | 60s 後 | state = "HALF_OPEN" |
| KILL-UT-004 | `test_circuit_breaker_closes_on_recovery` | HALF_OPEN + 50% success | state = "CLOSED" |
| KILL-UT-005 | `test_kill_switch_halts_all_agents` | 觸發 kill | 所有 agent terminate() |
| KILL-UT-006 | `test_kill_switch_logs_incident` | 觸發 kill | 寫入 audit log |
| KILL-INT-001 | `test_kill_switch_within_5_seconds` | 觸發到 halt | < 5000ms |

#### TDD 步驟

```
Step 1: Red
  → 寫 KILL-UT-001 ~ KILL-UT-006（全部 FAIL）

Step 2: Green
  → 實作 circuit_breaker.py（最小通過）
  → 實作 kill_switch.py
  → 實作 halt_all_agents()

Step 3: Refactor
  → 統一熔斷閾值 config
  → 新增 metric 上報
```

#### 驗收標準

- [ ] KILL-UT-001 ~ KILL-UT-006 全部 PASS
- [ ] KILL-INT-001 PASS（< 5s）
- [ ] Coverage ≥ 80%

---

### P1-2：Multi-Agent Debate（5-Agent）

#### 測試檔案結構

```
tests/
├── unit/
│   ├── test_planner_agent.py
│   ├── test_devils_advocate.py
│   ├── test_truth_validator.py
│   └── test_judge_agent.py
├── integration/
│   ├── test_debate_round.py
│   └── test_consensus_engine.py
```

#### Test Cases

| Test ID | 測試名稱 | 驗證內容 | 預期結果 |
|---------|---------|---------|---------|
| DEBATE-UT-001 | `test_planner_generates_decision_log` | Planner 輸出 | 含 decision_id, alternatives, confidence |
| DEBATE-UT-002 | `test_da_raises_challenges` | DA 輸出 | ≥ 5 challenges |
| DEBATE-UT-003 | `test_truth_validator_fact_checks` | Truth Validator | 返回 claim_verdict |
| DEBATE-UT-004 | `test_judge_detects_consensus` | cosine > 0.85 | verdict = "consensus" |
| DEBATE-UT-005 | `test_judge_detects_escalate` | 3 rounds 無共識 | verdict = "escalate" |
| DEBATE-UT-006 | `test_judge_detects_veto` | red-line violation | verdict = "veto" |
| DEBATE-INT-001 | `test_debate_3_rounds_to_consensus` | 完整 debate | consensus reached |
| DEBATE-INT-002 | `test_debate_escalates_after_3_rounds` | 分歧 debate | escalate triggered |

#### TDD 步驟

```
Step 1: Red
  → 寫 DEBATE-UT-001 ~ DEBATE-UT-006（全部 FAIL）

Step 2: Green
  → 實作 planner agent
  → 實作 devils_advocate agent
  → 實作 truth_validator agent
  → 實作 judge agent
  → 實作 consensus.py

Step 3: Refactor
  → 統一 agent prompt 格式
  → 提取 debate_state.py
```

#### 驗收標準

- [ ] DEBATE-UT-001 ~ DEBATE-UT-006 全部 PASS
- [ ] DEBATE-INT-001 ~ DEBATE-INT-002 全部 PASS
- [ ] Coverage ≥ 80%

---

### P1-3：UAF+CLAP+MetaQA 幻覺偵測

#### 測試檔案結構

```
tests/
├── unit/
│   ├── test_uaf.py
│   ├── test_clap.py
│   └── test_metaqa.py
└── integration/
    └── test_hallucination_pipeline.py
```

#### Test Cases

| Test ID | 測試名稱 | 驗證內容 | 預期結果 |
|---------|---------|---------|---------|
| UAF-UT-001 | `test_uaf_high_entropy` | token 分布均勻 | uncertainty > 0.5 |
| UAF-UT-002 | `test_uaf_low_self_consistency` | N 次採樣不一致 | uncertainty > 0.5 |
| UAF-UT-003 | `test_uaf_low_grounding` | claim 與 doc 不符 | uncertainty > 0.5 |
| UAF-UT-004 | `test_uaf_combined_score` | 公式驗證 | score = 0.3*H + 0.4*(1-SC) + 0.3*G |
| CLAP-UT-001 | `test_clap_attention_probe` | attention signal | 返回 anomaly score |
| CLAP-UT-002 | `test_clap_for_openweight` | Llama model | 正常運作 |
| META-UT-001 | `test_metaqa_qa_generation` | 從 claims 生成 QA | QA pairs > 0 |
| META-UT-002 | `test_metaqa_consistency_check` | 一週前 claim vs 現在 | 返回 drift % |
| HALL-INT-001 | `test_hallucination_pipeline` | UAF + CLAP + MetaQA | 分層輸出 |

#### TDD 步驟

```
Step 1: Red
  → 寫 UAF-UT-001 ~ HALL-INT-001（全部 FAIL）

Step 2: Green
  → 實作 uaf.py
  → 實作 clap.py
  → 實作 metaqa.py
  → 實作 hallucination_pipeline.py

Step 3: Refactor
  → 統一 threshold config
  → 新增 benchmark
```

#### 驗收標準

- [ ] UAF-UT-001 ~ UAF-UT-004 全部 PASS
- [ ] CLAP-UT-001 ~ CLAP-UT-002 全部 PASS
- [ ] META-UT-001 ~ META-UT-002 全部 PASS
- [ ] HALL-INT-001 PASS
- [ ] Coverage ≥ 80%

---

### P1-4：Implementation Gap Detection

#### 測試檔案結構

```
tests/
├── unit/
│   ├── test_base64_vs_aes.py
│   ├── test_todo_water.py
│   ├── test_empty_catch.py
│   └── test_hardcoded_secrets.py
└── integration/
    └── test_gap_detector.py
```

#### Test Cases

| Test ID | 測試名稱 | 驗證內容 | 預期結果 |
|---------|---------|---------|---------|
| GAP-UT-001 | `test_detect_base64_in_crypto` | Base64冒充AES | flag = True |
| GAP-UT-002 | `test_detect_real_aes` | 真實AES實現 | flag = False |
| GAP-UT-003 | `test_detect_todo_water` | test.todo 未實現 | count > 0 |
| GAP-UT-004 | `test_detect_empty_catch` | AST 分析空 catch | count > 0 |
| GAP-UT-005 | `test_detect_hardcoded_secret` | API key in code | count > 0 |
| GAP-INT-001 | `test_gap_detector_full_scan` | 完整 repo scan | 返回 gap list |

#### TDD 步驟

```
Step 1: Red
  → 寫 GAP-UT-001 ~ GAP-INT-001（全部 FAIL）

Step 2: Green
  → 實作 base64_vs_aes.py
  → 實作 todo_water.py
  → 實作 empty_catch.py
  → 實作 hardcoded_secrets.py
  → 實作 gap_detector.py

Step 3: Refactor
  → 統一 AST 分析框架
```

#### 驗收標準

- [ ] GAP-UT-001 ~ GAP-UT-005 全部 PASS
- [ ] GAP-INT-001 PASS
- [ ] Coverage ≥ 80%

---

### P1-5：8-維度風險評估

#### 測試檔案結構

```
tests/
├── unit/
│   └── test_risk_assessment.py
└── integration/
    └── test_risk_integration.py
```

#### Test Cases

| Test ID | 測試名稱 | 驗證內容 | 預期結果 |
|---------|---------|---------|---------|
| RISK-UT-001 | `test_correctness_dimension` | TH-01,02 mapping | score 0-10 |
| RISK-UT-002 | `test_completeness_dimension` | TH-03 mapping | score 0-10 |
| RISK-UT-003 | `test_testability_dimension` | TH-05,06 mapping | score 0-10 |
| RISK-UT-004 | `test_maintainability_dimension` | TH-05 mapping | score 0-10 |
| RISK-UT-005 | `test_security_dimension` | TH-04 mapping | score 0-10 |
| RISK-UT-006 | `test_performance_dimension` | TH-07 mapping | score 0-10 |
| RISK-UT-007 | `test_usability_dimension` | TH-14 mapping | score 0-10 |
| RISK-UT-008 | `test_reliability_dimension` | TH-08 mapping | score 0-10 |
| RISK-UT-009 | `test_weighted_overall_score` | 加權平均 | 0-10 分數 |
| RISK-UT-010 | `test_risk_tier_mapping` | 分數 → HOOTL/HITL/HOOTL | tier 正確 |
| RISK-INT-001 | `test_risk_score_from_project` | 完整 project scan | 返回完整報告 |

#### TDD 步驟

```
Step 1: Red
  → 寫 RISK-UT-001 ~ RISK-UT-010（全部 FAIL）

Step 2: Green
  → 實作 risk_assessment_engine.py（維度評分）
  → 實作 risk_dimension_mapper.py（TH mapping）

Step 3: Refactor
  → 統一維度權重 config
```

#### 驗收標準

- [ ] RISK-UT-001 ~ RISK-UT-010 全部 PASS
- [ ] RISK-INT-001 PASS
- [ ] Coverage ≥ 80%

---

### P1-6：LangGraph 協調

#### 測試檔案結構

```
tests/
├── unit/
│   └── test_langgraph_debate.py
└── integration/
    └── test_langgraph_checkpoint.py
```

#### Test Cases

| Test ID | 測試名稱 | 驗證內容 | 預期結果 |
|---------|---------|---------|---------|
| LANG-UT-001 | `test_graph_state_transition` | Planner→Critic→DA→Judge | 狀態正確 |
| LANG-UT-002 | `test_checkpoint_save` | 保存 checkpoint | 可恢復 |
| LANG-UT-003 | `test_checkpoint_restore` | 從 checkpoint 恢復 | 狀態一致 |
| LANG-INT-001 | `test_debate_from_checkpoint` | 失敗後恢復 | 從上個節點繼續 |
| LANG-INT-002 | `test_full_debate_trace` | 完整 trace | 可重現 |

#### TDD 步驟

```
Step 1: Red
  → 寫 LANG-UT-001 ~ LANG-INT-002（全部 FAIL）

Step 2: Green
  → 激活 langgraph_migrator.py
  → 實作 checkpoint 邏輯

Step 3: Refactor
  → 統一 state schema
```

#### 驗收標準

- [ ] LANG-UT-001 ~ LANG-UT-003 全部 PASS
- [ ] LANG-INT-001 ~ LANG-INT-002 全部 PASS
- [ ] Coverage ≥ 80%

---

## P2 組件驗證方案

---

### P2-1：Langfuse 可觀測性

#### 測試檔案結構

```
tests/
├── unit/
│   └── test_langfuse_client.py
└── integration/
    └── test_trace_completeness.py
```

#### Test Cases

| Test ID | 測試名稱 | 驗證內容 | 預期結果 |
|---------|---------|---------|---------|
| LANGF-UT-001 | `test_trace_has_required_fields` | 必要欄位 | uaf_score, risk_score 等 |
| LANGF-UT-002 | `test_compliance_tags` | EU AI Act 欄位 | 正確格式 |
| LANGF-UT-003 | `test_span_nesting` | parent_id 鏈 | 正確嵌套 |
| LANGF-INT-001 | `test_end_to_end_trace` | 完整 trace | 所有欄位填充 |
| LANGF-INT-002 | `test_dashboard_metrics` | 即時 dashboard | 數據正確 |

#### TDD 步驟

```
Step 1: Red
  → 寫 LANGF-UT-001 ~ LANGF-INT-002（全部 FAIL）

Step 2: Green
  → 實作 langfuse_client.py
  → 實作 trace_formatter.py
  → 實作 dashboard.py

Step 3: Refactor
  → 向後相容現有 Span class
```

#### 驗收標準

- [ ] LANGF-UT-001 ~ LANGF-UT-003 全部 PASS
- [ ] LANGF-INT-001 ~ LANGF-INT-002 全部 PASS
- [ ] Coverage ≥ 80%

---

### P2-2：EU AI Act / NIST 合規

#### 測試檔案結構

```
tests/
├── unit/
│   ├── test_eu_ai_act.py
│   ├── test_nist_rmf.py
│   └── test_compliance_matrix.py
└── integration/
    └── test_compliance_audit.py
```

#### Test Cases

| Test ID | 測試名稱 | 驗證內容 | 預期結果 |
|---------|---------|---------|---------|
| COMP-UT-001 | `test_art14_human_oversight` | HOTL/HITL 對應 | True |
| COMP-UT-002 | `test_art14_ai_limits` | Agents.md 對應 | True |
| COMP-UT-003 | `test_art14_bias_awareness` | DA + UAF 對應 | True |
| COMP-UT-004 | `test_art14_interpret_outputs` | Langfuse viewer | True |
| COMP-UT-005 | `test_art14_human_override` | HITL Gate | True |
| COMP-UT-006 | `test_art14_interrupt` | Kill-switch | True |
| COMP-UT-007 | `test_nist_govern` | Agents.md + Constitution | True |
| COMP-UT-008 | `test_nist_map` | TRACEABILITY_MATRIX | True |
| COMP-UT-009 | `test_nist_measure` | Langfuse + UAF/CLAP | True |
| COMP-UT-010 | `test_nist_manage` | Gate policy + Kill-switch | True |
| COMP-INT-001 | `test_full_compliance_audit` | 完整 Art.14 對照 | 100% 覆蓋 |

#### TDD 步驟

```
Step 1: Red
  → 寫 COMP-UT-001 ~ COMP-INT-001（全部 FAIL）

Step 2: Green
  → 實作 eu_ai_act.py
  → 實作 nist_rmf.py
  → 實作 compliance_matrix.py
  → 實作 compliance_reporter.py

Step 3: Refactor
  → 統一合規欄位格式
```

#### 驗收標準

- [ ] COMP-UT-001 ~ COMP-UT-010 全部 PASS
- [ ] COMP-INT-001 PASS
- [ ] Coverage ≥ 80%

---

## 測試覆蓋率目標

| Component | 目標覆蓋率 |
|-----------|-----------|
| P0-1 MCP Protocol | ≥ 80% |
| P0-2 分級治理 | ≥ 80% |
| P1-1 Kill-Switch | ≥ 80% |
| P1-2 5-Agent Debate | ≥ 80% |
| P1-3 幻覺偵測 | ≥ 80% |
| P1-4 Gap Detection | ≥ 80% |
| P1-5 風險評估 | ≥ 80% |
| P1-6 LangGraph | ≥ 80% |
| P2-1 Langfuse | ≥ 80% |
| P2-2 合規 | ≥ 80% |

---

## 測試執行命令

```bash
# 執行所有測試
pytest tests/ -v --cov=.

# 執行單一 component 測試
pytest tests/unit/test_mcp_spec_server.py -v

# 執行 integration 測試
pytest tests/integration/ -v

# 產生 coverage 報告
pytest tests/ --cov=. --cov-report=html
```

---

## CI/CD 整合

```yaml
# .github/workflows/tdd.yml
name: TDD Verification
on:
  push:
    branches: [methodology-v3]
  pull_request:
    branches: [methodology-v3]

jobs:
  tdd:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install pytest pytest-cov
      - name: Run TDD tests
        run: pytest tests/ -v --cov=.
      - name: Coverage gate
        run: |
          COVERAGE=$(pytest tests/ --cov=. --cov-report=term | grep "TOTAL" | awk '{print $NF}')
          if (( $(echo "$COVERAGE < 80" | bc -l) )); then
            echo "Coverage $COVERAGE < 80%"
            exit 1
          fi
```

---

## TDD 流程總結

```
┌─────────────────────────────────────────────────────┐
│ TDD Cycle (每個 feature)                            │
├─────────────────────────────────────────────────────┤
│                                                     │
│  1. Red：寫測試（定義驗收標準）                      │
│     └── 測試失敗（功能不存在）                        │
│                                                     │
│  2. Green：實作最小代碼通過測試                      │
│     └── 測試通過（功能存在但可能不完整）              │
│                                                     │
│  3. Refactor：重構提升品質                          │
│     └── 測試仍通過（行為不變）                       │
│                                                     │
│  4. Repeat：下一個 feature                           │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

*文件版本：1.0*
*更新日期：2026-04-17*
