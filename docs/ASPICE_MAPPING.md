# ASPICE Work Product Mapping

> ASPICE v3.1 工作項目對照表 - methodology-v2 v5.35.0

---

## 📋 Overview

本文檔對照 ASPICE 3.1 標準的 16 個核心工作項目與 methodology-v2 模組的對應關係。

### ASPICE Process Reference

| Process | Name | Category |
|---------|------|----------|
| SWE.1 | Requirements Elicitation | Engineering |
| SWE.2 | System Requirements Specification | Engineering |
| SWE.3 | System Integration | Engineering |
| SWE.4 | System Qualification | Engineering |
| SWE.5 | Software Requirements Specification | Engineering |
| SWE.6 | Software Integration | Engineering |
| SWE.7 | Software Qualification | Engineering |
| SUP.8 | Configuration Management | Supporting |
| SUP.9 | Information Management | Supporting |
| SUP.10 | Change Request Management | Supporting |
| MAN.3 | Project Management | Management |
| MAN.5 | Risk Management | Management |

---

## 🎯 工作項目對照矩陣

### Engineering Processes (SWE.1 - SWE.7)

| ASPICE | 工作產品 | 對應模組 | 狀態 | 缺口 |
|--------|----------|----------|------|------|
| **SWE.1** | Requirements Elicitation | | | |
| | - Business Goals | task_splitter.py | ✅ | |
| | - Stakeholder Requests | workflow_graph.py | ✅ | |
| | - Operational Scenarios | task_splitter_v2.py | ✅ | |
| **SWE.2** | System Requirements Specification | | | |
| | - System Requirements Doc | doc_generator.py | ✅ | |
| | - Interface Specifications | structured_output.py | ✅ | |
| | - System Constraints | project.py | ✅ | |
| **SWE.3** | System Integration | | | |
| | - Integration Plan | delivery_manager.py | ✅ | |
| | - Integration Results | delivery_tracker.py | ✅ | |
| | - Interface Test Spec | test_framework.py | ✅ | |
| **SWE.4** | System Qualification | | | |
| | - System Test Plan | test_generator.py | ✅ | |
| | - System Test Spec | test_framework.py | ✅ | |
| | - System Test Results | agent_evaluator.py | ✅ | |
| **SWE.5** | Software Requirements Specification | | | |
| | - Software Requirements Doc | doc_generator.py | ✅ | SRS 模板 needed |
| | - Software Architecture Doc | doc_generator.py | ✅ | SAD 模板 needed |
| **SWE.6** | Software Integration | | | |
| | - Software Integration Plan | delivery_manager.py | ✅ | |
| | - Integration Build Spec | parallel_executor.py | ✅ | |
| | - Integration Results | delivery_tracker.py | ✅ | |
| **SWE.7** | Software Qualification | | | |
| | - Software Test Plan | test_generator.py | ✅ | |
| | - Software Test Spec | test_framework.py | ✅ | Test Plan 模板 needed |
| | - Test Progress Reports | agent_evaluator.py | ✅ | |

### Supporting Processes (SUP.8 - SUP.10)

| ASPICE | 工作產品 | 對應模組 | 狀態 | 缺口 |
|--------|----------|----------|------|------|
| **SUP.8** | Configuration Management | | | |
| | - Configuration Items | state_persistence.py | ✅ | |
| | - Baseline Spec | delivery_manager.py | ✅ | |
| | - Change Control Records | approval_flow.py | ✅ | |
| **SUP.9** | Information Management | | | |
| | - Project Archives | knowledge_base.py | ✅ | |
| | - Management Reports | dashboard.py | ✅ | Quality Report 模板 needed |
| | - Meeting Notes | memory/ | ✅ | |
| **SUP.10** | Change Request Management | | | |
| | - Change Request Log | approval_flow.py | ✅ | |
| | - Impact Analysis | risk_registry.py | ✅ | |
| | - Change Status Reports | project.py | ✅ | Risk Assessment 模板 needed |

### Management Processes (MAN.3, MAN.5)

| ASPICE | 工作產品 | 對應模組 | 狀態 | 缺口 |
|--------|----------|----------|------|------|
| **MAN.3** | Project Management | | | |
| | - Project Plan | project.py, sprint_planner.py | ✅ | |
| | - Schedule Management | gantt_chart.py, scheduler.py | ✅ | |
| | - Resource Allocation | resource_dashboard.py | ✅ | |
| | - Status Reports | progress_dashboard.py | ✅ | |
| **MAN.5** | Risk Management | | | |
| | - Risk Management Plan | risk_registry.py | ✅ | |
| | - Risk List | risk_registry.py | ✅ | |
| | - Risk Assessment Reports | risk_dashboard.py | ✅ | Risk Assessment 模板 needed |
| | - Risk Mitigation Actions | recovery_controller.py | ✅ | |

---

## 🔍 缺口分析 (Gap Analysis)

### 高優先級缺口 (需要立即補齊)

| 缺口 | ASPICE 參考 | 建議模板 | 狀態 |
|------|-------------|----------|------|
| SRS 模板 | SWE.5 | Software Requirements Specification | ❌ |
| SAD 模板 | SWE.5 | Software Architecture Description | ❌ |
| Test Plan 模板 | SWE.7 | Software Test Plan | ❌ |
| Quality Report 模板 | SUP.9 | Quality Report | ❌ |
| Risk Assessment 模板 | MAN.5 | Risk Assessment Report | ❌ |

### 中優先級缺口 (建議補齊)

| 缺口 | ASPICE 參考 | 建議文件 | 狀態 |
|------|-------------|----------|------|
| CHANGELOG | SUP.9 | Project CHANGELOG | ❌ |
| Naming Convention | SUP.9 | Documentation Naming Standards | ❌ |

---

## 📦 v5.35.0 模組對應

### M2.7 Self-Evolving 模組

| 模組 | ASPICE 對應 | 功能 |
|------|-------------|------|
| `HybridAttention` | SWE.5 | 需求優先級優化 |
| `SelfIteration` | SWE.7 | 測試迭代優化 |
| `FailureAnalyzer` | SUP.10 | 變更影響分析 |
| `HarnessOptimizer` | SWE.6 | 整合測試優化 |

### 新增模組 (v5.31 - v5.35)

| 版本 | 模組 | ASPICE 對應 |
|------|------|-------------|
| v5.31 | auto_quality_gate.py | SUP.9, MAN.5 |
| v5.32 | self_evolution | SWE.7, SUP.10 |
| v5.33 | memory_governance | SUP.9 |
| v5.35 | M2.7 Integration | SWE.6, SWE.7 |

---

## 📝 文檔需求矩陣

### Phase 1: 需求分析

| ASPICE | 必需文檔 | 現有 | 缺口 |
|--------|----------|------|------|
| SWE.1 | Business Goals, Stakeholder Requests | workflow_graph.py | ✅ |
| SWE.2 | System Requirements Specification | doc_generator.py | ✅ |
| SWE.5 | **SRS (Software Requirements Specification)** | ❌ | ❌ |

### Phase 2: 架構設計

| ASPICE | 必需文檔 | 現有 | 缺口 |
|--------|----------|------|------|
| SWE.5 | **SAD (Software Architecture Description)** | ❌ | ❌ |

### Phase 3: 實作與整合

| ASPICE | 必需文檔 | 現有 | 缺口 |
|--------|----------|------|------|
| SWE.6 | Integration Plan, Build Spec | delivery_manager.py | ✅ |
| SWE.7 | **Test Plan**, Test Spec, Test Results | test_generator.py | Test Plan ✅ |

### Phase 4: 驗證與交付

| ASPICE | 必需文檔 | 現有 | 缺口 |
|--------|----------|------|------|
| SWE.4 | System Test Results | agent_evaluator.py | ✅ |
| SUP.8 | Baseline Records | delivery_tracker.py | ✅ |
| SUP.9 | **Quality Report** | ❌ | ❌ |
| SUP.10 | Change Request Log | approval_flow.py | ✅ |

### Phase 5: 風險管理

| ASPICE | 必需文檔 | 現有 | 缺口 |
|--------|----------|------|------|
| MAN.3 | Project Plan, Schedule | project.py | ✅ |
| MAN.5 | **Risk Assessment Report** | risk_registry.py | Risk Assessment ✅ |

---

## ✅ Action Items

- [ ] 建立 SRS Template (`docs/templates/SRS_TEMPLATE.md`)
- [ ] 建立 SAD Template (`docs/templates/SAD_TEMPLATE.md`)
- [ ] 建立 Test Plan Template (`docs/templates/TEST_PLAN_TEMPLATE.md`)
- [ ] 建立 Quality Report Template (`docs/templates/QUALITY_REPORT_TEMPLATE.md`)
- [ ] 建立 Risk Assessment Template (`docs/templates/RISK_ASSESSMENT_TEMPLATE.md`)
- [ ] 建立 CHANGELOG.md
- [ ] 建立文檔命名規範 (`docs/naming_convention.md`)
- [ ] 建立 Quality Gate 文檔檢查模組 (`quality_gate/doc_checker.py`)

---

*最後更新: 2026-03-24 | methodology-v2 v5.35.0*
