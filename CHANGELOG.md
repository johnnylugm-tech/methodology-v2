## v6.68 (2026-04-07)

### feat: P0 Integration Fix — 自動化串連所有觸發點

讓 v6.61-v6.67 的所有模組真正自動化串在一起，不是「做好放在那裡等著被用」。

#### Fix 1: Constitution → Feedback Loop 自動觸發
- `quality_gate/constitution/__init__.py` — `run_constitution_check()` 現在接受可選 `feedback_store` 參數
- 有 violations 時自動透過 `ConstitutionFeedbackAdapter.on_constitution_check_complete()` 提交到 FeedbackStore

#### Fix 2: Quality Gate → Feedback Loop 自動觸發（合併 WithFeedback 為 default）
- `core/quality_gate/__init__.py` — `AutoQualityGate.__init__()` 現在接受可選 `feedback_store` 參數
- `AutoQualityGateWithFeedback` 邏輯合併進 `AutoQualityGate`（不通過繼承）
- 有 violations 時自動透過 `QualityGateFeedbackAdapter.on_quality_gate_complete()` 提交

#### Fix 3: BVS → Feedback Loop 自動觸發
- `constitution/bvs_runner.py` — `BVSRunner.__init__()` 現在接受可選 `feedback_store` 參數
- `run()` 完成後自動將 invariant violations 提交到 FeedbackStore

#### Fix 4: Feedback verification 失敗 → Self-Correction 自動觸發
- `core/feedback/closure.py` — `verify_and_close()` 現在接受可選 `self_correction_engine` 參數
- verification 失敗時自動觸發 Self-Correction Engine
- 成功 → status 改為 `verified`；需要 review → `pending_human_review`；失敗 → `manual_required`

#### Fix 5: 統一工廠函數 `core/orchestration.py`
新建 `core/orchestration.py`，提供統一的初始化入口：
```python
from core.orchestration import (
    create_integrated_gate,    # Quality Gate + Feedback
    create_bvs_runner,          # BVS + Feedback
    create_self_correcting_closure,  # Closure + Self-Correction
    create_full_pipeline,       # 全部串在一起
)
```

#### 驗證方式
```python
from core.orchestration import create_full_pipeline

pipeline = create_full_pipeline("/path/to/project", phase=3)
store = pipeline["store"]
gate = pipeline["gate"]
bvs = pipeline["bvs"]
closure = pipeline["closure"]

# Constitution check → violations 自動進 Feedback Loop
from quality_gate.constitution import run_constitution_check
result = run_constitution_check("srs", "docs", phase=3, feedback_store=store)

# Quality Gate → violations 自動進 Feedback Loop
gate_result = gate.check(phase=2, artifacts={...})

# Closure → verification 失敗自動觸發 Self-Correction
closure_result = closure.close_with_correction(feedback_id)

# Dashboard
from core.feedback.dashboard import print_dashboard
print_dashboard(store)
```

---

## v6.67 (2026-04-07)

### feat: Self-Correction Engine — Automated Error Fix & Learning

Self-Correction Engine 是 **Feedback Loop 的 Closure Action**，當 verification 失敗時自動觸發修正。不是獨立系統，是 P2-2 Feedback Loop 的下一層。

#### Key Changes
- Three-Tier Correction Strategy (Auto-Fix / AI-Assisted / Manual-Required)
- 8 Auto-Fix rules (patch_syntax, isort_autofix, remove_unused, ruff_format, extract_function, add_test_stub, regenerate_import, ai_fix_logic)
- CorrectionLibrary — MD5-based retrieval with JSON persistence, learns from past corrections
- 51 tests across all modules

#### Module Structure (`core/self_correction/`)
```
├── self_correction_engine.py        # Main engine
├── strategies/
│   ├── base.py                     # BaseStrategy + PatchResult
│   ├── patch_syntax.py
│   ├── isort_autofix.py
│   ├── remove_unused.py
│   ├── ruff_format.py
│   ├── extract_function.py
│   └── add_test_stub.py
├── ai_corrector.py                 # AICorrectorProtocol + Mock fallback
├── correction_library.py           # CorrectionLibrary + JSON persistence
├── closure_with_self_correction.py # Feedback Loop integration
├── metrics.py                      # SelfCorrectionMetrics
└── test_*.py                      # 51 tests
```

---

## v6.29.0 (2026-04-07)

### feat: Feedback Loop — Standardized Quality Signal Collection & Closure

**Feedback Loop** 是一個統一框架，用於收集、分類、優先排序和追蹤開發生命週期中所有來源的品質信號。

#### 核心模組 (`core/feedback/`)
- `sources_schema.py` — 定義 9 種 feedback 來源
- `feedback.py` — StandardFeedback + FeedbackStore
- `severity.py` — 5×5 Severity Matrix（impact × urgency 交互）
- `router.py` — SLA + Routing Engine
- `closure.py` — Source-specific closure verification
- `constitution_adapter.py` — Constitution → Feedback 整合
- `constitution_closure.py` — Constitution closure verifier
- `quality_gate_adapter.py` — Quality Gate → Feedback 整合
- `quality_gate_hook.py` — AutoQualityGate with feedback hook
- `metrics.py` — DashboardMetrics
- `dashboard.py` — ASCII Dashboard
- `export.py` — JSON / Prometheus export
- `test_*.py` — 240 tests total

#### 整合對象
| Source | Integration | Auto-Submit |
|--------|-------------|------------|
| Constitution HR-01~HR-15 | `ConstitutionFeedbackAdapter` | ✅ |
| Quality Gate violations | `AutoQualityGateWithFeedback` | ✅ |
| Linter errors | `QualityGateFeedbackAdapter` | ✅ |
| Complexity alerts | `QualityGateFeedbackAdapter` | ✅ |
| Test failures | Via Quality Gate | ✅ |
| Architecture drift | Via CQG-P2 | ✅ |

#### SLA Configuration
| Severity | Response | Resolution | Escalation |
|----------|----------|------------|------------|
| Critical | 15 min | 4 hours | Immediate |
| High | 1 hour | 24 hours | 1 hour |
| Medium | 4 hours | 3 days | Daily |
| Low | 1 day | Next sprint | Weekly |

---

## v6.65 (2026-04-07)

### 新增功能

#### IMPROVEMENT_P2-1: Steering Loop - AB Workflow 方向控制

##### 核心組件
- `steering/steering_loop.py`: SteeringLoop 方向控制引擎
  - `LLMJudgeScorer`: LLM 裁判評分（替代假評分）
  - `SteeringConfig`: 可配置迭代參數
  - `IterationStage`: 三階段迭代（Exploration/Competition/Convergence）
  - 歷史持久化（跨 session 累積）

##### 整合組件
- `steering/integrations.py`: 與現有系統整合
  - `SteeringBVSIntegrator`: BVS 行為驗證整合
  - `SteeringConstitutionIntegrator`: HR-07/09/15 整合
  - `SteeringCQGIntegrator`: CQG 代碼品質整合
  - `HR12Resolution`: HR-12 矛盾解決方案

##### 三大修正
- 評分機制：假評分 → LLM 裁判
- Efficiency：token越少越好 → quality/tokens
- Convergence：delta大就停 → delta小才停

---

## v6.64 (2026-04-07)

### 新增功能

#### IMPROVEMENT_P1-3: AI Test Suite (P0 + P1 + P2)

##### P0: Enhanced Test Generator (test_generator.py)
- Real edge case values (INT_MAX, MIN_INT, unicode, nan, etc.)
- Cyclomatic complexity calculation
- Error type extraction from try/except
- Return analysis
- Actual parameterized test generation (982 lines, fully operational)

##### P1: LLM Test Generator (quality_gate/ai_test_suite/)
- `llm_test_generator.py`: AI-powered test generation
  - analyze_code_structure() with LLM
  - extract_invariants() for property-based testing
  - generate_test_suite() with HR-17 compliance
  - All AI-generated tests marked with `# AI-GENERATED - REVIEW REQUIRED`
- `edge_case_generator.py`: Shared edge case generation

##### P2: Integration
- `cli.py`: CLI interface for test generation
  - `python -m quality_gate.ai_test_suite.cli --target src/ --context SRS.md SAD.md`
- `pytest_result_checker.py`: New `check_ai_generated_tests()` method for HR-17 compliance

---

## [v6.63] - 2026-04-07

### 🚀 Added

#### HR-09 Claims Verifier System (IMPROVEMENT_P1-2)
HR-09: "Claims must be verified" — claim 內容必須被 citations 實際支持

##### New Files
- `constitution/claim_extractor.py` — 從 result text 提取 claims (keywords: should/must/will/is designed to)
- `constitution/citation_parser.py` — 解析 citation 格式 (SRS.md#L45, SAD.md#§3.2, etc.)
- `constitution/claim_verifier.py` — 交叉驗證 claim vs citations

##### BVS Integration
- `invariant_engine.py` 新增 HR-09 invariant
- HR-09 invariants now in BVS check list: HR-03/07/09/10/12/13/15 + TH-07

##### Key Distinction
- HR-07: citations 是否存在 (presence check)
- HR-09: citations 是否真的支持 claim 內容 (inferential check)

---

## v6.62 (2026-04-07)

### 新增功能

#### BVS: Behaviour Validation System (IMPROVEMENT_P1-1)
BVS 驗證 AI Agent 行為是否符合 Constitution HR 規則，補足 CQG 只看代碼不看病行為的缺口。

##### BVS-P0: Invariant Engine (constitution/invariant_engine.py)
- 7 個 HR rules → BehavioralInvariant
- HR-03: Phase execution order (critical)
- HR-07: Artifact citation required (high)
- HR-10: Subagent isolation (high)
- HR-12: A/B review threshold (medium)
- HR-13: Phase timeout (medium)
- HR-15: Artifact read before proceeding (critical)
- TH-07: Confidence calibration (medium)
- InvariantViolation dataclass + InvariantEngine.check_batch()

##### BVS-P1: Execution Logger (constitution/execution_logger.py)
- 從 sessions_spawn.log 收集執行日誌
- ExecutionLogEntry dataclass 標準化格式
- 支援 SubagentResult 直接消費

##### BVS-P2: BVS Runner (constitution/bvs_runner.py)
- 整合 InvariantEngine + ExecutionLogger
- BVSRunner.run(phase) → phase 專屬檢查
- BVSRunner.run_all_phases() → 全 Phase 彙總

##### Constitution Runner 整合
- Phase 3+ 自動執行 BVS 檢查
- BVS violations 進入 Constitution check violations 清單
- 向後相容：BVS 不可用時自動 skip

### 修復
- `unified_gate.py`: 傳遞 current_phase 至 run_constitution_check()，修復 BVS Phase 3+ 觸發

---

## [v6.61] - 2026-04-07

### 🚀 Added

#### CQG-P0: Computational Quality Gate
- `quality_gate/linter_adapter.py` — 統一多語言 linter 輸出
  - 支援 pylint (Python), eslint (JS/TS), golangci-lint (Go)
  - 標準化 `LinterResult`: score, errors, warnings, violations
- `quality_gate/complexity_checker.py` — Cyclomatic Complexity 分析
  - 支援 radon (Python), lizard (多語言)
  - 標準化 `ComplexityResult`: avg/max complexity, violations

#### CQG-P1: Coverage & Baseline
- `quality_gate/coverage_analyzer.py` — Coverage 缺口分析
  - 解析 coverage.xml + AST call graph
  - 根據引用數分級：critical(≥5 refs), high(≥3), medium(≥1)
- `integrity/baseline_manager.py` — Phase-Gate Baseline 管理
  - `capture_baseline()` — Phase-Gate 後建立快照
  - `check_drift()` — 與 baseline 比對 drift

#### CQG-P2: Fitness Functions
- `quality_gate/fitness_functions.py` — 架構健康度量
  - Coupling: Ca, Ce, Instability (I = Ce/(Ca+Ce))
  - Cohesion: LCOM2
  - Stability: Stable/Unstable 分類
  - Reusability: 耦合+內聚的衍生指標

#### SAB: Software Architecture Baseline
- `quality_gate/sab_spec.py` — SabSpec dataclass (結構化 SAB 格式)
- `quality_gate/sab_parser.py` — 從 SAD.md 解析生成 SabSpec
- Drift Detection 鏈:
  - Phase 2: `_check_sab()` → 建立 sab-phase2.json
  - Phase 3+: `_check_fitness()` → 讀 SAB → 計算 drift
  - Phase 3+: `_check_baseline_drift()` → BaselineManager drift detection

#### 整合變更
- `quality_gate/unified_gate.py` — 新增 5 個 CQG 檢查方法
  - `_check_linter()`, `_check_complexity()`
  - `_check_coverage_analyzer()`, `_check_fitness()`, `_check_sab()`
- `install_cqg.sh` + `requirements-cqg.txt` — CQG 依賴安裝

### 📝 Documentation
- SKILL.md 新增 CQG 工具說明章節
- CHANGELOG_FOR_JOHNNY.md 新增 v6.61 CQG+SAB 條目

### 依賴
- `pylint>=3.0.0`
- `radon>=6.0.0`
- `coverage>=7.0.0`

---

## [v6.60] - 2026-04-06

### 🚀 Added
- **sessions_spawn_logger.py v6.60**:
  - `_read_entries()` / `_write_entries()` — 瓦片式讀寫
  - `log_update(session_id, **updates)` — 兩階段更新（PENDING → COMPLETED/FAILED）
  - `get_summary()` — 加入 `status_counts`（PENDING/COMPLETED/FAILED 統計）
- **subagent_isolator.py v6.60**:
  - 移除 `_write_log()` 和 `_log_file`
  - 使用 `SessionsSpawnLogger` 統一管理
  - `spawn()` 前後分階段 log（PENDING → COMPLETED/FAILED）

### 🐛 Fixed
- N/A

### 📝 Documentation
- N/A

---

## [v6.59] - 2026-04-06

### 🚀 Added
- **sessions_spawn_logger.py**: New module for structured spawn logging
- **Pre-flight validation**: Integrated into cli.py (+14 lines)

### 🐛 Fixed
- N/A

### 📝 Documentation
- N/A

---

## [v6.54] - 2026-04-05

### 🚀 Added
- **HR-05/09 explicit checks**: `check_hr05_methodology_priority()`, `check_hr09_claims_verifier()`
- **sessions_spawn.log auto-create**: Auto-created in run-phase pre-flight
- **ToolRegistry integration**: Integrated in run-phase pre-flight

### 🐛 Fixed
- N/A

### 📝 Documentation
- JOHNNY_HANDBOOK.md updated to v6.54

---

## [v6.53] - 2026-04-05

### 🚀 Added
- **parse_phase_artifacts.py**: Phase 產出自動繼承（Section 3.5）
- **integration_manager.py**: 迭代自動追蹤（HR-12/13）
- **tool_dispatcher.py**: 工具自動觸發（spawn/message/error/complete）
- **Section 3.5**: 新增上階段產出承接

### 🐛 Fixed
- N/A

### 📝 Documentation
- Section 3.5: 上階段產出承接 added to plan template

---

## [v6.49] - 2026-04-05

### 🚀 Added
- **Sub-Agent Management (v6.49)**: `cli_phase_subagent.py`
  - Need-to-Know + On-Demand for all 8 phases
  - Phase-specific tool timing (spawn/KC/CM/QG/checkpoint)
  - SubagentIsolator + fresh_messages per phase
  - Dynamic {subagent_mgmt} section in plan template

- **Phase Prompts Module (v6.48)**: `cli_phase_prompts.py`
  - All 8 phases have independent Developer/Reviewer prompts
  - Phase 1: SRS制定/審查
  - Phase 2: SAD+ADR 制定/審查
  - Phase 3: 代碼實作/審查 (full FR support)
  - Phase 4: TEST_PLAN/RESULTS
  - Phase 5: Baseline/Monitoring
  - Phase 6: QUALITY_REPORT
  - Phase 7: 風險管理
  - Phase 8: 配置管理

- **IntegrationManager (v6.48)**: 迭代修復管理
  - HR-12 5輪限制自動追蹤
  - get_repair_suggestions()
  - get_repair_flow()

- **ToolDispatcher (v6.48)**: 動態工具觸發
  - on_spawn/on_message/on_error/on_complete

### 🐛 Fixed
- **Phase prompts all 8 phases**: Now with Need-to-Know + On-Demand

# CHANGELOG

> methodology-v2 版本變更記錄

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v6.46] - 2026-04-04

### 🐛 Fixed
- **Version Consistency**: All components now at v6.45.0

### 📝 Documentation
- **AUDIT_v6.45.md**: Audit report for v6.40-v6.45
- **JOHNNY_HANDBOOK.md**: Updated to v6.46 with 18 chapters

---

## [v6.45] - 2026-04-04

### 🐛 Fixed
- **OUTPUT path**: Now correctly shows `app/processing/lexicon_mapper.py` from SAD parsing
- **Forbidden infrastructure**: Clarified as deprecated
- **FR enrichment**: Developer Prompt receives correct module name

---

## [v6.44] - 2026-04-04

### 🐛 Fixed
- **Pre-flight deliverable check**: Searches subdirectories for SAD.md, skips Phase outputs

---

## [v6.43] - 2026-04-04

### 🚀 Added
- **Developer/Reviewer Prompt On Demand restrictions**
- **Tool Usage Timing section** (Section 9)
- **HR-15 citations line number emphasis**

### 🐛 Fixed
- Anti-Dump rule in prompts

---

## [v6.42] - 2026-04-04

### 🚀 Added
- **Agent A/B roles per phase** (8 different role combinations)
- **Reviewer Prompt template** with REJECT_IF conditions

---

## [v6.41] - 2026-04-04

### 🚀 Added
- **`--detailed` flag**: Merges FR tasks into single plan file

---

## [v6.40] - 2026-04-04

### 🚀 Added
- **Template-based Plan Generation (v6.32)**: `templates/plan_phase_template.md`
  - 16 章節完整 plan 模板
  - Template-based 替換所有 placeholder

- **SAD Parser + Deliverable Structure (v6.34)**: `cli.py`
  - 自動解析 SAD.md FR→module→file mapping
  - 動態產生 deliverable structure tree
  - FR-by-FR table 含正確路徑

- **TH Thresholds Table (v6.36)**: `cli.py`
  - Phase 1-8 完整 TH 閾值
  - 含驗證命令

- **External Docs Section (v6.36)**: `cli.py`
  - Phase 1-8 外部文檔列表
  - 含用途說明

- **--detailed Flag (v6.37)**: `cli.py`
  - 生成含 FR 詳細任務的 plan
  - 呼叫 generate_full_plan.py

- **generate_full_plan.py (v6.39)**: `scripts/generate_full_plan.py`
  - 支援所有 Phase（1-8）
  - Phase-specific parser（SRS, SAD, TEST_PLAN, etc.）

### 🐛 Fixed
- **Version Consistency (v6.40)**
  - cli.py: v6.32 → v6.40
  - generate_full_plan.py: v6.38 → v6.39
  - SKILL.md: v6.29 → v6.40
  - Section duplication fixed

### 📝 Documentation
- **JOHNNY_HANDBOOK.md v6.40**
  - 新增 16 章節說明
  - 新增 FR 解析流程說明
  - 更新 plan-phase 用法（含 --detailed）
  - 新增 generate_full_plan.py 用法

- **docs/AUDIT_v6.39.md**
  - 完整性、正確性、一致性審計報告

---

## [v6.12] - 2026-03-31

### 🚀 Added
- **SKILL.md 融合版 (v6.12)**: `SKILL.md`
  - 精簡版核心 (~1,000 行)，Agent 執行時真正需要的內容
  - 基於 v6.03.0 分離架構，融合 v6.05-11 新功能
  - 章節結構：執行協議 → 硬規則 → 閾值配置 → Phase 路由表 → Phase 定義 → 工具速查 → STAGE_PASS

- **SKILL_TEMPLATES.md**: 新增模板庫
  - T1-T8 Phase 模板（SRS, SAD, CODE, TEST, BASELINE, QUALITY, RISK, CONFIG）
  - 單元測試三類模板（正向/邊界/負面）
  - 邏輯審查對話模板
  - A/B 審查通用模板

- **SKILL_DOMAIN.md**: 新增領域知識庫
  - ASPICE 基礎（過程 Groups、能力等級）
  - 邏輯正確性原則（核心約束、缺陷模式）
  - Constitution 憲章系統（四維度）
  - A/B 協作機制、單元測試三類、監控告警
  - 風險管理五維度、配置管理 SUP.8

### 📝 Documentation
- 外部化原則落實：SKILL.md 只放核心，模板和領域知識分離
- Lazy Loading 規則明確定義

---

## [v6.02] - 2026-03-31

### 🚀 Added
- **Integrity Tracker + Constitution 整合**: `quality_gate/integrity_tracker.py`
  - 誠信追蹤系統（100 分起始，每次違規扣分）
  - 違規類型：subagent_claim, fake_qg_result, skip_phase, qa_equals_developer
  - 信任等級：FULL_TRUST ≥ 80 / PARTIAL_TRUST 50-79 / LOW_TRUST < 50

---

## [v5.98] - 2026-03-30

### 🛠️ Fixed

- **Phase enum 擴展（6 → 9 phases）**: `quality_gate/phase_artifact_enforcer.py`
  - 新增 `SYSTEM_TEST`, `QUALITY`, `RISK`, `CONFIG` 四個 Phase
  - `PHASE_ARTIFACTS` mapping 更新為 9 階段完整映射
  - 支援 ASPICE Phase 5-8 追溯性檢查

- **FrameworkEnforcer ASPICE mapping 更新**: `enforcement/framework_enforcer.py`
  - `required_by_phase` dict 鍵名更新與 Phase enum 同步
  - `check_aspice_completeness` 與 `check_phase_traceability` now fully cover all 8 ASPICE phases

---

## [v5.97] - 2026-03-30

### 📝 Documentation
- **Version Release SOP**: `docs/VERSION_SOP.md`
  - 規範版本發布流程（測試 → CHANGELOG → 版本號 → git tag → GitHub）
  - 版本號規則與標籤創建時機
  - 常見問題 FAQ

- **UnifiedGate Coverage Matrix (Markdown)**: `tests/COVERAGE_MATRIX.md`
  - 13 核心檢查工具覆蓋狀態
  - 11 擴展檢查工具（Phase 5-8）
  - PhaseEnforcer L3 三層檢查覆蓋矩陣
  - 測試套件總覽（110+ 測試）

---

## [v5.96] - 2026-03-29

### 🚀 Added
- **PhaseEnforcer Independent Smoke Test**: `quality_gate/phase_enforcer_smoke.py`
  - 不需要 Ralph Mode 依賴
  - 可獨立運行測試
  - 包含 6 個測試案例

### 🧪 Testing
- **UnifiedGate Test Coverage Matrix**: `tests/test_unified_gate_coverage.py`
  - 驗證 25 個檢查工具的測試覆蓋
  - 包含 Required Coverage: 100%

### 📝 Development Log Checker
- **DEVELOPMENT_LOG 驗證器**: `scripts/dev_log_checker.py`
  - 驗證 session_id 記錄
  - 驗證 Decision Gate 格式
  - 驗證命令輸出存在

### 🔧 Agent Quality Guard Adapter
- **隔離外部依賴**: `quality_gate/agent_quality_guard_adapter.py`
  - 統一接口隔離外部依賴
  - Fallback 機制（外部不可用時使用本地檢查）
  - 分數閾值配置（預設 ≥ 90，等級 A）

---

## [v5.95] - 2026-03-29

### 🚀 Added
- **Core Test Suite**: 4 new test files for quality gate components
  - `test_spec_logic_checker.py` - spec_logic_checker tests
  - `test_unified_gate.py` - unified_gate tests
  - `test_phase_enforcer.py` - phase_enforcer tests
  - `test_constitution_runner.py` - constitution_runner tests

### 🧪 Testing
- Each test file includes: basic functionality, error handling, 3+ test cases

### 🎯 Smoke Test
- Ralph Mode smoke test integration in `ralph_mode/smoke_test.py`
  - Basic health check
  - Quick 5W1H structure validation

---

## [v5.94] - 2026-03-29

### 5W1H 整合優化
- Phase 1 新增獨立 5W1H 章節
- Phase 1 退出條件補齊 SPEC_TRACKING 完整性檢查
- Phase 4 補充 WHEN/WHERE/WHY/HOW 維度
- Phase 3 加入 phase_artifact_enforcer.py
- Phase 6-7 加入 session_id 記錄要求
- Phase 7 加入邏輯正確性閾值（≥ 90）
- Phase 8 統一監控時段（Phase 5 至今）

### 工具整合
- Phase 4 WHERE 加入 spec_logic_checker.py
- 代碼覆蓋率閾值明確化（Phase 3 ≥ 70%, Phase 4 ≥ 80%）
- 測試通過率閾值明確化（Phase 6-7 = 100%）
- SUP.8 配置管理說明

---

## [v5.93] - 2026-03-28

### 🚀 Added
- Phase 5-8 5W1H 完整整合審計修正
- BASELINE.md 完整規格（7 章節）
- MONITORING_PLAN.md A/B 監控閾值定義
- RISK_REGISTER.md 完整版（含 Decision Gate）
- CONFIG_RECORDS.md 完整版（8 章節）
- Phase 7 四層緩解措施（Prevent/Detect/Respond/Escalate）
- Phase 8 發布清單（七個區塊逐項確認）
- Phase 8 方法論閉環確認

### 🔧 Changed
- Phase 5 邏輯正確性複查（spec_logic_checker.py ≥ 90 分）
- Phase 5 進入條件加入邏輯正確性門檻
- Phase 6 Constitution 門檻 ≥ 80%
- Phase 7 前置條件加入驗證測試通過率 = 100%
- Phase 8 新增 SUP.8 配置管理說明

---

## [v5.92] - 2026-03-28

### 🚀 Added
- Phase5+7+8_Plan_5W1H_AB.md 整合精華
- Phase 5 兩次 A/B 審查流程（基線審查 + 驗收報告審查）
- Phase 7 五維度風險識別
- Phase 7 Decision Gate 確認流程
- Phase 7 風險演練要求
- Phase 8 完整發布清單（七個區塊）
- Phase 8 回滾 SOP
- Phase 8 A/B 監控最終報告格式

---

## [v5.91] - 2026-03-27

### 🚀 Added
- Phase6_Plan_5W1H_AB.md 整合精華
- Phase 1-8 5W1H 整合審計修正（P0-P3）
- Constitution 憲章系統 Phase 6-8 全面檢查
- 代碼覆蓋率閾值明確化

---

## [v5.90] - 2026-03-26

### 🚀 Added
- Phase3_Plan_5W1H_AB.md 整合精華
- Phase4_Plan_5W1H_AB.md 整合精華
- 代碼規範、單元測試三類、集成測試模板
- TEST_PLAN/TEST_RESULTS 完整規格
- 同行邏輯審查對話模板

---

## [v5.89] - 2026-03-26

### 🚀 Added
- Phase3 代碼實現 A/B 協作流程完整定義
- 單元測試三類要求（正向/邊界/負面）
- 集成測試模板
- 同行邏輯審查對話模板

---

## [v5.88] - 2026-03-26

### 🚀 Added
- Phase2_Plan_5W1H_AB.md 整合精華
- SAD.md 最低要求、A/B 架構審查清單
- Conflict Log 格式
- Phase 2 A/B 架構審查紀錄模板

---

## [v5.87] - 2026-03-26

### 🚀 Added
- Phase1_Plan_5W1H_AB.md 整合精華
- DEVELOPMENT_LOG 格式、A/B 審查模板
- Constitution 憲章系統 Phase 1-4 整合

---

## [v5.86] - 2026-03-25

### 🚀 Added
- PhaseEnforcer L3 整合 Agent Quality Guard
- 三層檢查系統（結構 25% + 內容 25% + 代碼 50%）
- Phase 5-8 Constitution Checkers 新增

---

## [v5.85] - 2026-03-25

### 🚀 Added
- Ralph Mode 預設啟動
- Agent 建立新專案時自動啟動 Ralph Mode 監控
- CLI cmd_init 自動觸發 RalphScheduler

---

## [v5.82] - 2026-03-24

### 🚀 Added
- Ralph Mode 任務長時監控模組（v5.59）
- PhaseStateMachine 6 階段狀態機
- TaskPersistence 狀態持久化
- RalphScheduler 定時輪詢

## [v5.35.0] - 2026-03-23

### 🚀 Added
- M2.7 Self-Evolving Integration
  - `HybridAttention`: Lightning + Softmax 混合注意力機制
  - `SelfIteration`: 100+ 迭代自我優化能力
  - `FailureAnalyzer`: 失敗路徑分析模組
  - `HarnessOptimizer`: Agent Harness 自動調優

### 🛠️ Changed
- 升級 MiniMax M2.7 模型整合
- 優化自我演化工作流程

### 📝 Documentation
- 新增 `RELEASE_NOTES_v5.35.md`

---

## [v5.34.0] - 2026-03-22

### 🚀 Added
- Memory Governance 模組
  - 長期記憶管理
  - 上下文壓縮
  - 記憶檢索優化

### 🛠️ Changed
- 優化 agent_memory 效能
- 改進 observability 追蹤

### 📝 Documentation
- 新增 `RELEASE_NOTES_v5.33.md`

---

## [v5.33.0] - 2026-03-20

### 🚀 Added
- Self-Evolution 框架 v1.0
  - 自動效能評估
  - 迭代優化引擎
  - 失敗模式學習

### 🛠️ Changed
- 重構 auto_quality_gate 模組
- 增強 hybrid_workflow 邏輯

### 📝 Documentation
- 新增 `RELEASE_NOTES_v5.33.md`
- 更新 `NEW_TEAM_GUIDE.md`

---

## [v5.32.0] - 2026-03-18

### 🚀 Added
- M2.5 模型整合支援
- Enhanced Observability Module
  - 結構化日誌
  - 分散式追蹤
  - 指標視覺化

### 🛠️ Changed
- 升級 OpenTelemetry 整合
- 優化代碼覆蓋率工具鏈

### 📝 Documentation
- 新增 `RELEASE_NOTES_v5.32.md`

---

## [v5.31.0] - 2026-03-15

### 🚀 Added
- Auto Quality Gate v2.0
  - 多層品質檢查
  - 自定義規則引擎
  - Quality Metrics Dashboard

### 🛠️ Changed
- 重構 quality_gate 架構
- 整合 enforcement_config 模組
- 改進 approval_flow 體驗

### 📝 Documentation
- 新增 `RELEASE_NOTES_v5.31.md`
- 新增 `docs/GETTING_STARTED.md`
- 新增 `docs/naming_convention.md` (本版本)

---

## [v5.30.0] - 2026-03-10

### 🚀 Added
- Enterprise SSO Integration
  - Okta, Azure AD, LDAP 支援
  - OAuth 2.0 / SAML
- RBAC 權限管理系統
- 審計日誌增強

### 🛠️ Changed
- 升級 security_audit 模組
- 優化 enterprise_hub 擴展性

### 📝 Documentation
- 新增 `RELEASE_NOTES_v5.30.md`
- 更新 `USER_GUIDE.md`

---

## [v5.29.0] - 2026-03-05

### 🚀 Added
- LangGraph Migrator v1.0
  - AST 分析工具
  - 風險評估引擎
  - 自動化程式碼生成

### 🛠️ Changed
- 改進 framework_bridge 穩定性
- 優化 crewai_bridge 轉換邏輯

### 📝 Documentation
- 新增 `RELEASE_NOTES_v5.29.md`

---

## [v5.28.0] - 2026-02-28

### 🚀 Added
- P2P Team Configuration
  - 分散式 Agent 協作
  - MAP Protocol 支援
  - 動態團隊擴展

### 🛠️ Changed
- 重構 p2p_orchestrator 模組
- 優化訊息匯流排效能

### 📝 Documentation
- 新增 P2P HITL Guide

---

## [v5.27.0] - 2026-02-20

### 🚀 Added
- Cost Optimizer Module
  - 自動成本分析
  - 資源調度優化
  - ROI 追蹤儀表板

### 🛠️ Changed
- 整合 cost_allocator 與新的優化邏輯
- 改進收費機制

---

## [v5.26.0] - 2026-02-15

### 🚀 Added
- Test Generator v1.0
  - 自動化測試案例生成
  - 測試覆蓋率分析
  - 回歸測試推薦

### 🛠️ Changed
- 升級 test_framework 模組
- 優化 agent_evaluator 報告生成

---

## [v5.25.0] - 2026-02-10

### 🚀 Added
- Delivery Manager
  - 版本發布管理
  - Rollback 機制
  - 發布追蹤儀表板

### 🛠️ Changed
- 重構 delivery_tracker
- 整合現有發布流程

---

## [v5.0.0] - 2026-01-01

### 🚀 Added
- Methodology-v2 正式發布
- 完整 Agent 生命週期管理
- 多模型支援 (GPT, Claude, Gemini)
- 企業級安全與合規

---

## 遷移指南

### v5.30 → v5.35

主要變更：
- M2.7 整合需要更新配置
- Self-Evolution 模組為選用

```bash
# 升級步驟
pip install methodology-v2==5.35.0

# 如使用 M2.7，需更新 config
python cli.py migrate --from 5.30 --to 5.35
```

### v5.26 → v5.30

```bash
pip install methodology-v2==5.30.0
```

---

## 舊版本記錄

- [v5.30](./RELEASE_NOTES_v5.30.md)
- [v5.29](./RELEASE_NOTES_v5.29.md)
- [v5.26](./USER_GUIDE_v5.26.md)
- [v5.0](./GETTING_STARTED_v5.26.md)

---

*CHANGELOG generated by methodology-v2*
*For older releases, see RELEASE_NOTES_*.md files*
