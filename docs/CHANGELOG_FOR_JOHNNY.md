# Johnny 使用者更新摘要（v6.45 → v6.61）

> **適用版本**: v6.61
> **更新日期**: 2026-04-07
> **給**: Johnny (呂小麟)

---

## 快速摘要：這次更新了什麼？

| 版本 | 主要改善 |
|------|---------|
| v6.61 | **CQG+SAB 系統：linter/complexity/coverage/fitness/baseline/SAB drift** |
| v6.54 | **HR-05/09 檢查 + 自動化** |
| v6.48 | **8 個 Phase 都有專屬提示** |
| v6.49 | **子代理管理（Need-to-Know + On-Demand）** |
| v6.50 | **四維度目標（10/10）** |
| v6.51 | 100% 持平 Auto-Research 優化版 |
| v6.53 | **上階段產出自動繼承** |

---

## 對你有影響的改變

### 1. CQG — Computational Quality Gate（v6.61）

**以前**: Quality Gate 只靠人工審查，無自動度量
**現在**: 一套度量驅動的 Quality Gate 工具，全部自動化

#### CQG 工具族

| 工具 | 用途 |
|------|------|
| LinterAdapter | 統一 pylint/eslint/golangci-lint 輸出為標準格式 |
| ComplexityChecker | Cyclomatic Complexity 分析，抓到太複雜的函式 |
| CoverageAnalyzer | 未覆蓋函式的「關鍵性」分析（critical/high/medium） |
| FitnessFunctions | 架構健康分數：耦合、內聚、穩定性、可重用性 |
| BaselineManager | Phase-Gate 後建立 Baseline，之後比對 drift |

#### SAB: Software Architecture Baseline

- `SAD.md` → 解析成結構化 `SabSpec` → 建立 `sab-phase2.json`
- Phase 3+ 比對當前架構與 SAB 的 drift（偏離度）
- Drift 超閾值 → 警告或阻擋

#### Phase 整合

| Phase | CQG 檢查 |
|-------|----------|
| Phase 2 | `_check_sab()` — 建立 SAB（從 SAD.md） |
| Phase 3+ | `_check_fitness()` — SAB drift detection |
| Any | `_check_linter()`, `_check_complexity()`, `_check_coverage_analyzer()` |

#### 安裝
```bash
pip install -r requirements-cqg.txt
```

---

### 2. plan-phase 現在更完整（v6.48+）

**以前**: 只有 Phase 3 有完整提示  
**現在**: 所有 8 個 Phase 都有專屬提示

```
Phase 1: 需求規格 → 有完整 Developer/Reviewer Prompt
Phase 2: 架構設計 → 有完整 Developer/Reviewer Prompt
Phase 3: 代碼實現 → 有完整 Developer/Reviewer Prompt
...
Phase 8: 配置管理 → 有完整 Developer/Reviewer Prompt
```

### 2. Section 3.5: 上階段產出自動繼承（v6.53+）

**以前**: 需要手動確認上階段產出  
**現在**: plan-phase 自動顯示上階段產出狀態

```
## 3.5 上階段產出承接（Phase 3 前置產出）

| 產出 | 狀態 | 路徑 |
|------|:-----:|------|
| ✅ 需求規格 | ✅ | SRS.md (8 FR, 4 NFR) |
| ✅ 系統架構 | ✅ | SAD.md (5 modules) |
```

### 3. 四維度目標（v6.50+）

**以前**: 沒有明確的迭代目標  
**現在**: 每個 Phase 都有四維度 10/10 目標

| 維度 | 目標 |
|------|------|
| 規範符合度 | 10/10 |
| A/B 協作 | 10/10 |
| 子代理管理 | 10/10 |
| 測試覆蓋率 | 10/10 |

### 4. HR-05/09 自動化檢查（v6.54+）

**以前**: HR-05（methodology-v2 優先）和 HR-09（Claims Verifier）只是口頭規定  
**現在**: Constitution 會自動檢查

```python
# HR-05: 檢查文檔是否引用 methodology-v2
# HR-09: 檢查 claims 是否有 citations
```

---

## 你需要知道的新功能

### 1. sessions_spawn.log 自動創建（v6.54+）

**以前**: 如果 sessions_spawn.log 不存在會报错  
**現在**: run-phase 會自動創建

```
✅ [PRE-FLIGHT] Created sessions_spawn.log
```

### 2. ToolRegistry 整合（v6.54+）

**以前**: ToolRegistry 是獨立的  
**現在**: run-phase 會自動檢查工具註冊

```
✅ [PRE-FLIGHT] ToolRegistry: 5 tools registered
```

### 3. IntegrationManager 追蹤（v6.53+）

**以前**: HR-12（5 輪限制）和 HR-13（時間限制）需要手動追蹤  
**現在**: 自動追蹤並提醒

```
✅ [PRE-FLIGHT] IterationManager initialized
   - Tracking HR-12: A/B 審查 > 5 輪 → PAUSE
   - Tracking HR-13: Phase 執行 > 預估 ×3 → PAUSE
```

---

## plan-phase 輸出現在有幾個章節？

| 版本 | 章節數 |
|------|--------|
| v6.45 | 18 章 |
| v6.50 | 19 章 |
| **v6.54** | **19+ 章** |

**Section 3.5 是新增的**（上階段產出承接）

---

## 你應該做什麼？

### 執行 plan-phase 的時候

```bash
# 以前
python cli.py plan-phase --phase 3 --detailed

# 現在（一樣）
python cli.py plan-phase --phase 3 --detailed
```

**不需要做任何改變**，輸出會自動包含所有改善。

### 執行 run-phase 的時候

```bash
# 以前
python cli.py run-phase --phase 3

# 現在（一樣）
python cli.py run-phase --phase 3
```

**新功能會自動啟動**：
- sessions_spawn.log 自動創建
- ToolRegistry 自動檢查
- IntegrationManager 自動追蹤

---

## 常見問題

### Q: 這些改變會影響現有專案嗎？

**A**: 不會。plan-phase 和 run-phase 是生成和執行計劃的工具，不會修改現有專案的產出。

### Q: 我需要更新任何設定嗎？

**A**: 不需要。新功能預設啟動。

### Q: 如果我不想用某個新功能？

**A**: 目前沒有選項可以關閉特定功能。如果有需要，請告訴我。

---

## 版本對照表

| 功能 | v6.45 | v6.54 | 變化 |
|------|:------:|:------:|------|
| 8 個 Phase 提示 | ❌ | ✅ | 新增 |
| 四維度 10/10 | ❌ | ✅ | 新增 |
| Section 3.5 | ❌ | ✅ | 新增 |
| HR-05 檢查 | ❌ | ✅ | 新增 |
| HR-09 檢查 | ❌ | ✅ | 新增 |
| sessions_spawn.log 自動創建 | ❌ | ✅ | 新增 |
| IntegrationManager | ❌ | ✅ | 新增 |
| ToolDispatcher | ❌ | ✅ | 新增 |

---

## 下一步

如果你對這些改變有任何問題或建議，請告訴我。我可以：

1. **解釋**任何一個功能的細節
2. **演示**新功能的實際輸出
3. **調整**特定行為（如果需要）

---

*最後更新: 2026-04-05*
