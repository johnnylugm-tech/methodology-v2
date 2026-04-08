# 九大 IMPROVEMENT 方案手冊 (v6.61-v6.74)

> 整理：Musk Agent | 日期：2026-04-08
> 適用版本：methodology-v2 v6.74

---

## P0-1：Computational Sensors｜代碼品質即時感測器

**版本**：v6.69 | **整合位置**：`quality_gate/unified_gate.py` | **啟動時機**：`UnifiedGate.check_all()` 每次執行

### 方法

ComputationalSensors 是 UnifiedGate 的第四層檢查，封裝四種靜態分析感測器：

1. **Linter Sensor**：統一介面整合 pylint / eslint / golangci-lint，輸出標準化錯誤格式
2. **Complexity Sensor**：使用 radon/lizard 計算圈複雜度，超過閾值（預設10）則視為 violation
3. **Coverage Sensor**：解析 coverage.xml + AST call graph，揪出 high-impact 未覆蓋函式（≥5 refs）
4. **Maintainability Sensor**：計算可維護性指數，低於閾值觸發警告

### 觸發時機

```
UnifiedGate.check_all()
  → _check_fitness()        [P0-2]
  → _check_sensors()        [P0-1] ← 在這裡
  → _check_baseline_drift() [P0-3]
```

### 實作細節

```python
# quality_gate/unified_gate.py
def _check_sensors(self) -> CheckResult:
    if not SENSORS_AVAILABLE:
        return CheckResult(...)  # L1: skip
    report = self.sensors.scan()
    score = report.weighted_score * 100
    return CheckResult(passed=report.passed, score=score, ...)
```

模組不可用時回傳 skip（L1），非 error — 確保 CI 不因環境缺失而失敗。Violation 結果進入 Quality Gate violations 清單，參與 Phase Gate 評分。

---

## P0-2：Architecture Fitness｜架構健康度量

**版本**：v6.61 | **整合位置**：`quality_gate/unified_gate.py` | **啟動時機**：`UnifiedGate.check_all()` 每次執行

### 方法

FitnessFunctions 以代碼結構指標衡量架構健康度，取代主觀評估：

- **Coupling（耦合）**：Afferent Coupling (Ca) + Efferent Coupling (Ce) → Instability I = Ce/(Ca+Ce)。I 越接近 1 表示越不穩定
- **Cohesion（內聚）**：LCOM2（Lack of Cohesion of Methods），數值越高表示類職責越分散
- **Stability**：I < 0.3 為 Stable，I > 0.7 為 Unstable
- **Reusability**：耦合 × 內聚的衍生指標，0-100 標準化分數

### 觸發時機

`_check_fitness()` 是 UnifiedGate CQG 區塊的第一個檢查，發生於 `check_all()` 的 CQG phase。

### 實作細節

```python
# quality_gate/unified_gate.py
self.fitness = FitnessFunctions(str(self.project_path))  # line 242

checks.append(self._check_fitness())   # line 577
checks.append(self._check_baseline_drift())  # line 578
```

每個 Phase 的 Fitness 結果會被 SAB drift detection 參考，用於判斷架構是否偏離原設計。

---

## P0-3：Drift Monitor｜架構偏離監控

**版本**：v6.61 | **整合位置**：`quality_gate/unified_gate.py` | **啟動時機**：Phase 2 建立 SAB；Phase 3+ 比對 drift

### 方法

Drift Monitor 追蹤實際架構與初始設計（SAD.md → SabSpec）之間的漂移，透過三層機制運作：

1. **SAB（Software Architecture Baseline）**：Phase 2 的 SAD.md 被解析為結構化 SabSpec，成為後續 drift detection 的比較基準
2. **Fitness Drift Detection**：Phase 3+ 比對當前 Coupling/Cohesion 指標與 Phase 2 的 SAB
3. **Baseline Drift Detection**：BaselineManager 在每個 Phase-Gate 建立快照，close_phase 時執行 `_check_baseline_drift()` 比對

### 觸發時機

```
Phase 2: SAD 存在 → _check_sab() → 建立 sab-phase2.json（基準線）
Phase 3+: _check_fitness() → 計算 drift score
          _check_baseline_drift() → BaselineManager.check_drift()
```

### 實作細節

Drift score 計算方式：`current_fitness - baseline_fitness`（標準化後）。超過閾值（預設 0.15）則觸發 Violation，寫入 Phase-Gate report。

---

## P1-1：Behaviour Harness (BVS)｜AI 行為驗證系統

**版本**：v6.62（v6.71 整合至 create_full_pipeline）| **整合位置**：`orchestration.py`、`constitution/bvs_runner.py` | **啟動時機**：Phase 3+ 自動；`close_phase()` 手動

### 方法

BVS 補足 CQG 只看「代碼靜態品質」不看「Agent 行為是否符合 Constitution 規則」的缺口。核心是 Invariant Engine + Execution Logger：

- **Invariant Engine**：將 8 條 HR 規則翻譯為可驗證的 behavioral invariant（HR-03/07/09/10/12/13/15 + TH-07）
- **Execution Logger**：從 sessions_spawn.log 解析實際執行動作，比對 invariant 是否被滿足
- **BVS Runner**：整合兩者，輸出 phase 專屬的 violations 報告

### 觸發時點

| 時機 | 方式 |
|------|------|
| Phase 3+ Constitution check | 自動：Constitution runner 在 Phase 3+ 呼叫 BVS |
| `create_full_pipeline()["run_bvs"](phase)` | 手動：程式化呼叫 |
| `create_full_pipeline()["close_phase"](phase)` | 自動：phase 關閉時一併執行 |

### 實作細節

v6.71 新增 `run_bvs(phase)` 和 `close_phase(phase)` 兩個方法，回傳 `{phase, bvs_report, closure_results}`。BVS violations 自動提交至 FeedbackStore，Dashboard 可見。

---

## P1-2：Inferential Sensors｜Claims 推理鏈驗證

**版本**：v6.63 | **整合位置**：`quality_gate/constitution/hr09_checker.py` | **啟動時機**：Constitution HR-09 check 執行時（每 Phase）

### 方法

HR-09 是 Constitution 中「Claim 必須被 citations 實際支持」的規則。不同於 HR-07（只看 citation 是否存在），HR-09 驗證 inference chain 的品質：

1. **Claim Extractor**：從文字中提取 claims（關鍵字：should/must/will/is designed to）
2. **Citation Parser**：解析 `SRS.md#L45` 這類格式，定位到實際 artifact 內容
3. **Inferential Sensor**：用 LLM 評估 claim 的關鍵詞是否出現在 citation 內容中，輸出 0-1 的驗證率

### 觸發時機

```python
# quality_gate/constitution/hr09_checker.py
from constitution.inferential_sensor import InferentialSensor

self.inferential_sensor = InferentialSensor(...)
assessment = self.inferential_sensor.assess(claim=claim, citation=citation)
```

每次 Constitution check 執行 HR-09 時自動呼叫。驗證率低於閾值（預設 0.6）則 HR-09 失敗，進 Constitution violations。

### HR-07 vs HR-09 區別

- **HR-07**：citations 是否存在（presence check）
- **HR-09**：citations 是否真的支持 claim 內容（inferential check）

---

## P1-3：AI Test Suite｜LLM 驅動測試生成

**版本**：v6.64 | **整合位置**：`cli.py`（v6.70 新增 CLI 整合）| **啟動時機**：手動 CLI 呼叫

### 方法

AI Test Suite 解決「測試不足」的長期痛點，分三層：

1. **P0: Enhanced Test Generator**（`test_generator.py`）：根據函式簽名自動生成邊界值測試（INT_MAX, MIN_INT, unicode, NaN, empty list 等）
2. **P1: LLM Test Generator**（`llm_test_generator.py`）：用 LLM 分析 code structure + 提取 invariants，生成 property-based test
3. **P2: CLI Interface**（`quality_gate/ai_test_suite/cli.py`）：統一 CLI 入口

### 觸發時機

```bash
# CLI 觸發
python cli.py quality-gate ai-test -t src/ -c SRS.md -c SAD.md

# 可用 alias
python cli.py qg ai-test -t app/ --model gpt-4
```

### 實作細節

LLM 生成測試時自動標記 `# AI-GENERATED - REVIEW REQUIRED`，並透過 `check_ai_generated_tests()` 確保 HR-17 合規。所有產出寫入 `tests/generated/`，需人工審查後才能進正式 suite。

---

## P2-1：Steering Loop｜AB Workflow 方向控制引擎

**版本**：v6.65（v6.72 新增 CLI 整合）| **整合位置**：`cli.py`、`steering/steering_loop.py` | **啟動時機**：手動 CLI 呼叫

### 方法

Steering Loop 是 AB 迭代的裁判引擎，解決「兩個輸出哪個更好」的判斷問題：

1. **LLM Judge Scorer**：用 LLM 當裁判，評估 A/B 兩個輸出在各維度的分數（correctness, efficiency, clarity, security）
2. **三階段迭代**：Exploration（前 N 輪自由競爭）→ Competition（差異明顯）→ Convergence（收斂）
3. **歷史持久化**：`.methodology/steering_history.json` 跨 session 累積，引導越來越精準

### 觸動時機

```bash
# 執行引導
python cli.py steering run --project . --phase 3

# 查看狀態
python cli.py steering status

# 查看歷史
python cli.py steering history
```

### 三大修正（相較於假評分）

| 問題 | 修正 |
|------|------|
| 假評分 | → LLM Judge 裁判 |
| Token 越多越好 | → quality/tokens 效率指標 |
| Delta 大就停 | → Delta 小才停（收斂判斷）|

---

## P2-2：Feedback Loop｜品質信號收集與閉環框架

**版本**：v6.66 | **整合位置**：`orchestration.py`、`core/feedback/` | **啟動時機**：透過 orchestration 統一觸發，Feedback 自動入庫

### 方法

Feedback Loop 是所有品質信號的中央集線器，將來自不同來源的 issues 統一收集 → 分類 → 路由 → 追蹤 → 關閉：

**9 種 Feedback 來源**：

| 來源 | 整合方式 | 自動提交 |
|------|----------|----------|
| Constitution HR violations | ConstitutionFeedbackAdapter | ✅ |
| Quality Gate violations | AutoQualityGateWithFeedback | ✅ |
| Linter errors | QualityGateFeedbackAdapter | ✅ |
| Complexity alerts | QualityGateFeedbackAdapter | ✅ |
| Test failures | Via Quality Gate | ✅ |
| Architecture drift | Via CQG-P2 | ✅ |
| BVS violations | BVSRunner.auto_submit | ✅ |
| User reports | 手動 API | - |
| Metrics anomalies | Cron/Sensor | ✅ |

**SLA 分級**：Critical（15min 回應）/ High（1hr）/ Medium（4hr）/ Low（1day）

### 觸發時機

```python
from orchestration import create_full_pipeline

pipeline = create_full_pipeline("/path/to/project", phase=3)
store = pipeline["store"]  # FeedbackStore 實例
```

任何 quality check 完成後自動寫入 store。Dashboard 顯示所有 open feedback。

### 核心模組

- `feedback.py`：StandardFeedback dataclass + FeedbackStore
- `severity.py`：5×5 Severity Matrix（impact × urgency）
- `router.py`：SLA + Routing Engine
- `closure.py`：Source-specific closure verification
- `dashboard.py`：ASCII Dashboard 即時狀態

---

## P2-3：Self-Correction Engine｜自動修正與學習

**版本**：v6.67 | **整合位置**：`orchestration.py`、`core/self_correction/` | **啟動時機**：Feedback verification 失敗時自動觸發

### 方法

Self-Correction Engine 是 Feedback Loop 的 Closure Action。當 `verify_and_close()` 發現修正後仍不符合預期，自動進入修正流程：

**三層修正策略**：

| 等級 | 策略 | 觸發條件 |
|------|------|----------|
| L1 | Auto-Fix | 8 種可自動修復規則（patch_syntax, isort, ruff_format 等） |
| L2 | AI-Assisted | 無法自動修復時，呼叫 LLM 給予修正建議 |
| L3 | Manual-Required | 需要人工介入 |

**8 種 Auto-Fix 規則**：`patch_syntax` / `isort_autofix` / `remove_unused` / `ruff_format` / `extract_function` / `add_test_stub` / `regenerate_import` / `ai_fix_logic`

**CorrectionLibrary**：以 MD5(錯誤類型+檔案+上下文) 為 key 緩存修正歷史，learns from past corrections，避免重複犯錯。

### 觸發時機

```python
# Feedback Loop verification 失敗時自動觸發
from orchestration import create_self_correcting_closure

closure = create_self_correcting_closure(feedback_store)
result = closure.verify_and_close(feedback_id)
# 內部自動：verify → 失敗 → self_correction_engine.correct() → re-verify
```

流程：`Feedback → verification 失敗 → Self-Correction → re-verify → 成功則 status 改 verified / 仍失敗則 pending_human_review`

---

## 啟動時序圖

```
Phase 1-2:
  UnifiedGate.check_all()
    → _check_fitness()      [P0-2] ← 建立 Phase 2 SAB
    → _check_sensors()      [P0-1]
    → _check_baseline_drift()[P0-3] ← Phase 2 SAB capture
    → _check_constitution() [P1-1] ← BVS Phase 3+ 才執行

Phase 3+:
  UnifiedGate.check_all()
    → _check_fitness()      [P0-2] ← drift vs SAB
    → _check_sensors()      [P0-1]
    → _check_baseline_drift()[P0-3] ← Baseline drift
    → _check_constitution() [P1-1] → HR-09 [P1-2] → BVS [P1-1]
    → ConstitutionFeedback → FeedbackStore [P2-2]

close_phase(phase):
  → Feedback closure [P2-2]
  → Self-Correction [P2-3]（verification 失敗時）
  → run_bvs(phase) [P1-1]
  → BVS violations → FeedbackStore [P2-2]

CLI 手動觸發（任何 Phase）：
  → qg ai-test [P1-3]
  → steering run/status/history [P2-1]
```

---

## 整合狀態總覽（v6.74）

| 方案 | 整合位置 | 自動啟用 | 版本 |
|------|----------|----------|------|
| P0-1 Computational Sensors | UnifiedGate.check_all() | ✅ | v6.69 |
| P0-2 Architecture Fitness | UnifiedGate.check_all() | ✅ | v6.61 |
| P0-3 Drift Monitor | UnifiedGate.check_all() | ✅ | v6.61 |
| P1-1 Behaviour Harness | create_full_pipeline() | ✅（Phase 3+）| v6.62/v6.71 |
| P1-2 Inferential Sensors | hr09_checker.py | ✅（HR-09 check）| v6.63 |
| P1-3 AI Test Suite | cli.py | ❌（CLI 手動）| v6.64/v6.70 |
| P2-1 Steering Loop | cli.py | ❌（CLI 手動）| v6.65/v6.72 |
| P2-2 Feedback Loop | orchestration.py | ✅ | v6.66 |
| P2-3 Self-Correction | orchestration.py | ✅（verify 失敗時）| v6.67 |

---

*最後更新：2026-04-08 | v6.74*
