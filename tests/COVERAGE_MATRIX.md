# UnifiedGate 測試覆蓋矩陣

> **版本**：v5.96
> **更新日期**：2026-03-30
> **目標**：確認 UnifiedGate 所有 13+ 檢查工具都被測試覆蓋

---

## 總覽

| 指標 | 數值 |
|------|------|
| 總檢查工具數 | 13 (核心) + 11 (擴展) |
| 測試覆蓋工具數 | 13 |
| 核心覆蓋率 | 100% |
| 總測試數 | 110+ |

---

## UnifiedGate 13 核心檢查工具覆蓋矩陣

| # | 檢查工具 | 模組 | Phase | 測試檔案 | 測試數 | 覆蓋狀態 |
|---|----------|------|-------|----------|--------|----------|
| 1 | Document Checker | `doc_checker.py` | All | `test_unified_gate.py` | 4 | ✅ |
| 2 | Constitution Checker | `constitution/` | All | `test_constitution_runner.py` | 33 | ✅ |
| 3 | Phase Reference Checker | `phase_artifact_enforcer.py` | All | `test_phase_artifact_enforcer.py` | - | ✅ |
| 4 | Spec Logic Checker | `scripts/spec_logic_checker.py` | 7 | `test_spec_logic_checker.py` | 19 | ✅ |
| 5 | FR ID Tracker | `fr_id_tracker.py` | 2 | `test_unified_gate.py` | 2 | ✅ |
| 6 | Threat Analyzer | `threat_analyzer.py` | 3 | `test_unified_gate.py` | 2 | ✅ |
| 7 | Coverage Checker | `coverage_checker.py` | 3 | `test_unified_gate.py` | 2 | ✅ |
| 8 | Issue Tracker | `issue_tracker.py` | 4 | `test_unified_gate.py` | 2 | ✅ |
| 9 | Risk Status Checker | `risk_status_checker.py` | 4 | `test_unified_gate.py` | 2 | ✅ |
| 10 | Folder Structure Checker | `folder_structure_checker.py` | All | `test_unified_gate.py` | 2 | ✅ |
| 11 | Phase Enforcer | `phase_enforcer.py` | All | `test_phase_enforcer.py` | 29 | ✅ |
| 12 | TC Trace Checker | `tc_trace_checker.py` | 5 | `test_unified_gate.py` | 2 | ✅ |
| 13 | FR Coverage Checker | `fr_coverage_checker.py` | 2 | `test_unified_gate.py` | 2 | ✅ |

---

## 擴展檢查工具（Phase 5-8）

| # | 檢查工具 | 模組 | Phase | 覆蓋狀態 | 備註 |
|---|----------|------|-------|----------|------|
| 14 | Verification Constitution | `constitution/verification_constitution_checker.py` | 5 | ✅ | 已整合 |
| 15 | Quality Report Constitution | `constitution/quality_report_constitution_checker.py` | 6 | ✅ | 已整合 |
| 16 | Risk Management Constitution | `constitution/risk_management_constitution_checker.py` | 7 | ✅ | 已整合 |
| 17 | Configuration Constitution | `constitution/configuration_constitution_checker.py` | 8 | ✅ | 已整合 |
| 18 | FR Verification Method | `fr_verification_method_checker.py` | 2 | ✅ | 已整合 |
| 19 | Error Handling Checker | `error_handling_checker.py` | 4 | ✅ | 已整合 |
| 20 | Module Tracking Checker | `module_tracking_checker.py` | 3 | ✅ | 已整合 |
| 21 | Compliance Matrix Checker | `compliance_matrix_checker.py` | 5 | ✅ | 已整合 |
| 22 | Negative Test Checker | `negative_test_checker.py` | 4 | ✅ | 已整合 |
| 23 | Pytest Result Checker | `pytest_result_checker.py` | 4 | ✅ | 已整合 |
| 24 | Root Cause Checker | `root_cause_checker.py` | 7 | ✅ | 已整合 |

---

## PhaseEnforcer L3 三層檢查覆蓋

| 層次 | 權重 | 檢查內容 | 測試覆蓋 |
|------|------|----------|----------|
| L1 結構檢查 | 25% | 規格追蹤、A/B 審查記錄、DEVELOPMENT_LOG | ✅ `test_phase_enforcer.py` |
| L2 內容檢查 | 25% | SPEC.md、TEST_PLAN、TEST_RESULTS | ✅ `test_phase_enforcer.py` |
| L3 代碼檢查 | 50% | Agent Quality Guard（分數 ≥ 90，等級 A）| ✅ `test_phase_enforcer.py` |

---

## 測試套件總覽

| 測試檔案 | 測試數 | 覆蓋範圍 |
|----------|--------|----------|
| `tests/test_unified_gate.py` | 29 | UnifiedGate 核心功能 |
| `tests/test_phase_enforcer.py` | 29 | PhaseEnforcer 三層檢查 |
| `tests/test_constitution_runner.py` | 33 | Constitution 合規檢查 |
| `tests/test_spec_logic_checker.py` | 19 | 規格邏輯正確性 |
| `tests/test_phase_enforcer_smoke.py` | 9 | PhaseEnforcer 獨立 smoke test |
| `tests/test_unified_gate_coverage.py` | - | 覆蓋矩陣驗證工具 |
| `tests/test_doc_checker.py` | - | 文件檢查器 |
| `tests/test_phase_artifact_enforcer.py` | - | Phase 產物強制執行 |

**總測試數：110+**

---

## 如何使用本矩陣

1. **驗證覆蓋**：運行 `python -m tests.test_unified_gate_coverage` 確認所有檢查工具都被測試覆蓋
2. **新增檢查工具**：在新檢查工具加入 UnifiedGate 後，同時更新本矩陣和對應測試
3. **缺口分析**：識別沒有測試覆蓋的檢查工具，補全測試案例

---

## 驗證命令

```bash
# 運行所有 quality gate 測試
cd skills/methodology-v2
python -m pytest tests/test_unified_gate.py tests/test_phase_enforcer.py tests/test_constitution_runner.py tests/test_spec_logic_checker.py -v

# 運行覆蓋矩陣驗證
python -m tests.test_unified_gate_coverage --detail

# 運行 smoke test
python -m pytest tests/test_phase_enforcer_smoke.py -v
```

---

*最後更新：v5.96*
