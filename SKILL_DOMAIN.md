# methodology-v2 SKILL_DOMAIN.md

> **版本**: v6.12
> **用途**: 領域知識 — Agent 在實作前應了解的背景知識
> **載入時機**: Phase 3 實作前（Lazy Load）

---

## 1. ASPICE 基礎

### 1.1 ASPICE 過程 Groups

| Group | 說明 |
|-------|------|
| ACQ (Acquisition) | 採購相關過程 |
| SYS (System) | 系統工程過程 |
| SWE (Software Engineering) | 軟體工程過程 |
| SUP (Support) | 支援過程 |
| MAN (Management) | 管理過程 |
| PROCESS (Process Improvement) | 過程改進 |

### 1.2 Phase 與 ASPICE 映射

| Phase | ASPICE Group | 關鍵過程 |
|-------|-------------|---------|
| Phase 1 | SYS/SWE | SRS 需求獲取、分析、規格 |
| Phase 2 | SYS/SWE | SAD 架構設計 |
| Phase 3 | SWE | SWE.1 到 SWE.5 實作、測試、集成 |
| Phase 4 | SWE/SUP | SWE.4 測試、SUP.9 測試驗證 |
| Phase 5-8 | MAN/SUP | SUP.1 缺陷管理、SUP.8 配置管理 |

### 1.3 ASPICE 能力等級 (LC)

| 等級 | 簡稱 | 描述 |
|------|------|------|
| LC 0 | Incomplete | 過程未執行或未達標 |
| LC 1 | Performed | 過程已執行但無嚴格管理 |
| LC 2 | Managed | 過程已管理（有度量、文件化）|
| LC 3 | Established | 過程已建立（基於組織標準）|
| LC 4 | Predictable | 過程可預測（定量管理）|
| LC 5 | Innovating | 過程持續創新優化 |

---

## 2. 邏輯正確性原則

### 2.1 核心約束

| 約束類型 | 說明 | 驗證方法 |
|----------|------|---------|
| 輸出 ≤ 輸入 | 字串處理結果長度不超過輸入 | `assert len(output) <= len(input)` |
| 邊界一致 | 單一情況與多情況邏輯一致 | 單元素 vs 多元素測試 |
| Lazy Init | 外部依賴不在 `__init__` 直接呼叫 | 代碼審查 |

### 2.2 常見邏輯缺陷模式

| 模式 | 問題 | 防範 |
|------|------|------|
| 輸出膨脹 | 合併/拼接後輸出 > 輸入總和 | 負面測試驗證 |
| 邊界遺漏 | `if len(x)==1` 與一般情況結果不一致 | 邊界測試 |
| 初始化崩潰 | `__init__` 中直接呼叫外部依賴 | Lazy Init pattern |
| 標點丢失 | 文字處理時標點符號被刪除 | 領域特定測試 |

### 2.3 邏輯審查檢查清單

- [ ] 字串操作：輸出長度 ≤ 輸入長度
- [ ] 分支邏輯：`if len(x)==1` 與一般情況結果一致
- [ ] 外部依賴：全部使用 Lazy Init
- [ ] 標點處理（TTS 領域）：標點有保留

---

## 3. Constitution 憲章系統

### 3.1 四維度定義

| 維度 | Phase 1-4 門檻 | Phase 5-8 門檻 |
|------|---------------|---------------|
| 正確性 | = 100% | ≥ 80% |
| 安全性 | = 100% | ≥ 80% |
| 可維護性 | > 70% | ≥ 70% |
| 測試覆蓋率 | > 80% | ≥ 80% |

### 3.2 Constitution 類型對應

| Phase | Constitution Type |
|-------|------------------|
| Phase 1 | `srs` |
| Phase 2 | `sad` |
| Phase 3 | `code` |
| Phase 4 | `test_plan` |
| Phase 5-8 | `all` |

### 3.3 Constitution Runner 命令

```bash
# 檢查所有 Constitution
python3 quality_gate/constitution/runner.py

# 檢查特定類型
python3 quality_gate/constitution/runner.py --type srs
python3 quality_gate/constitution/runner.py --type sad
python3 quality_gate/constitution/runner.py --type test_plan
```

---

## 4. A/B 協作機制

### 4.1 角色定義

| 角色 | Persona | 職責 | 禁止事項 |
|------|---------|------|----------|
| Agent A | `architect` | 實作、撰寫 | 自寫自審 |
| Agent A | `developer` | 代碼實作 | 自寫自審 |
| Agent A | `qa` | 測試規劃 | Tester = Developer |
| Agent A | `devops` | 部署、配置 | 配置不完整 |
| Agent B | `reviewer` | 審查、確認 | 代替 A 修改 |

### 4.2 A/B 次數定義

| Phase | 最少 A/B 次數 |
|-------|--------------|
| Phase 1 | 1 |
| Phase 2 | 1 |
| Phase 3 | 每模組 1 |
| Phase 4 | 2 |
| Phase 5 | 2 |
| Phase 6 | 1 |
| Phase 7 | 1 |
| Phase 8 | 1 + 封版審查 |

### 4.3 A/B 審查維度（Phase 2）

1. 需求覆蓋完整性
2. 模組設計品質
3. 錯誤處理完整性
4. 技術選型合理性
5. 實作可行性

---

## 5. 單元測試三類

| 類型 | 說明 | 範例 |
|------|------|------|
| 正向測試（Happy Path）| 正常輸入的預期行為 | 正常文字分段 |
| 邊界測試（Boundary）| 邊界條件處理 | 空白輸入、超長輸入、單一元素 |
| 負面測試（Negative）| 邏輯約束驗證 | 合併後字符數 ≤ 原文 |

---

## 6. 監控與告警

### 6.1 四個監控維度

| 維度 | Phase 5 基線 | 告警閾值 |
|------|-------------|---------|
| 效能（回應時間）| 基線值 | > 基線值 20% |
| 可靠性（錯誤率）| 基線值 | > 1% |
| 資源（記憶體）| 基線值 | > 基線值 30% |
| 熔斷器 | 觸發次數 | > 5/min |

### 6.2 熔斷器模式

| 狀態 | 行為 |
|------|------|
| CLOSED | 正常運行 |
| OPEN | 快速失敗，不執行實際調用 |
| HALF_OPEN | 嘗試恢復 |

---

## 7. 風險管理

### 7.1 五維度風險識別

| 維度 | 說明 |
|------|------|
| 技術風險 | 技術選型、架構缺陷 |
| 資源風險 | 人力、預算不足 |
| 進度風險 | Deadline 延遲 |
| 品質風險 | 缺陷率、覆蓋率不足 |
| 外部風險 | 依賴方變更、法規變更 |

### 7.2 Decision Gate

| 風險等級 | 決策要求 |
|----------|---------|
| MEDIUM | 需記錄決策和理由 |
| HIGH | 需雙人確認（Agent A + Agent B）|
| CRITICAL | 需暫停並通知 Stakeholder |

### 7.3 四層緩解措施

| 層級 | 措施類型 |
|------|---------|
| Prevent | 預防措施，避免風險發生 |
| Detect | 檢測措施，early warning |
| Respond | 回應措施，發生後的處理 |
| Escalate | 上報措施，升级处理 |

---

## 8. 配置管理

### 8.1 SUP.8 配置項

| 項目 | 說明 |
|------|------|
| 軟體工作產品 | SRS, SAD, 代碼, 測試文檔 |
| 環境配置 | 開發/生產環境參數 |
| 依賴清單 | pip freeze, npm lock |
| 變更記錄 | Phase 5 以來的配置變更 |

### 8.2 回滾 SOP 觸發條件

- 錯誤率 > 5%
- 回應時間 > 基線值 50%
- 記憶體 > 基線值 50%
- 熔斷器 OPEN 持續 > 5 min

---

## 9. 命名規則

### 9.1 檔案命名

| 類型 | 命名規則 | 範例 |
|------|---------|------|
| 需求文檔 | `SRS.md` | 軟體需求規格 |
| 架構文檔 | `SAD.md` | 軟體架構設計 |
| 測試計劃 | `TEST_PLAN.md` | 測試規劃 |
| 測試結果 | `TEST_RESULTS.md` | 執行結果 |
| 基線 | `BASELINE.md` | 交付基線 |
| 品質報告 | `QUALITY_REPORT.md` | 品質分析 |
| 風險登記 | `RISK_REGISTER.md` | 風險追蹤 |
| 配置記錄 | `CONFIG_RECORDS.md` | 配置管理 |

### 9.2 FR/NFR 命名

| 類型 | 命名規則 | 範例 |
|------|---------|------|
| 功能需求 | `FR-XX` | `FR-01` |
| 非功能需求 | `NFR-XX` | `NFR-01` |
| 測試案例 | `TC-XX` | `TC-01` |
| 風險 | `R-XX` | `R-01` |
| ADR | `ADR-XX` | `ADR-001` |

---

## 10. Error Level Classification (L1-L6)

| 等級 | 類型 | 處理策略 | 範例 |
|------|------|---------|------|
| L1 | 輸入錯誤 | 立即返回錯誤訊息 | 參數格式錯誤 |
| L2 | 工具錯誤 | 重試 3 次，指數退避 | 網路超時、API 限流 |
| L3 | 執行錯誤 | 降級處理，使用 fallback | 第三方服務失敗 |
| L4 | 系統錯誤 | 熔斷 + 告警 | 連續失敗觸發熔斷 |
| L5 | 驗證失敗 | 停在當前 Step | Quality Gate 未通過 |
| L6 | 作假行為 | 終止，Integrity 扣分 | 假稱已執行 Quality Gate |

---

*SKILL_DOMAIN.md v6.12 | Domain Knowledge Reference*
