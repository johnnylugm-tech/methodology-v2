# Changelog - methodology-v2

## v5.12.0 (2026-03-22)

### 🚀 新功能

#### P0: 正確性與品質保障
- **Timeout 規範**：最小 5 分鐘，公式 `timeout = 評估時間 × 1.5`
- **A/B 雙重驗證**：Reflection 自我審查 + Agent B 預先驗證
- **Kickoff 檢查清單**：8 項基礎設施檢查
- **狀態區分**：待處理 → 進行中 → 驗證中 → 已完成/失敗

#### P0: 錯誤處理與 HITL
- **錯誤分類細化**：L1-L6（輸入→工具→執行→系統→認證→臨界）
- **明確 HITL 節點**：5 種情況需人工介入
- **斷點設計 (Checkpoint)**：支援任務中斷/恢復

#### P1: 錯誤恢復與診斷
- **錯誤恢復策略**：網路超時、API 限流、認證失敗、服務不可用、資料不一致
- **錯誤日誌與診斷**：完整記錄錯誤資訊

#### P2: 健康檢查與熔斷
- **健康檢查機制**：API 響應時間、錯誤率、超時率、資源使用
- **熔斷與降級**：CLOSED → OPEN → HALF_OPEN → CLOSED

#### P3: 智慧重試
- **重試策略配置**：最大重試次數、退避策略、jitter

#### P1: P2P 機制下的任務分工
- **P2P + A/B 融合架構**：設計 → 實作 → 整合 → 測試
- **角色定義**：Architect / Developer / Reviewer / Integrator / QA
- **設計驗證清單**：Agent A 交付前、Agent B 實作前
- **依賴管理圖譜**：明確依賴關係
- **衝突處理**：接口衝突、資源衝突、依賴衝突
- **P2P 訊息優先級**：P0-P3 四級優先級
- **智慧任務分配**：負載、技能匹配、歷史表現、可用性

### 📚 文檔
- 新增 [docs/GETTING_STARTED_v5.12.md](docs/GETTING_STARTED_v5.12.md) - 新手上路指南
- 更新 README.md - 版本歷史
- 更新 USER_GUIDE.md - v5.12.0 新功能指南

---

## v5.11.0 (2026-03-22)

### 新功能
- HITL (Human-in-the-Loop) 系統
- Unified Config 統一配置中心
- P2P Orchestrator P2P 協調器

### 文檔
- 新增 case30_p2p_orchestrator.md
- 新增 case31_hitl.md
- 新增 P2P_HITL_GUIDE.md

---

## v5.10.0 (2026-03-22)

### 新功能
- Unified Config 統一配置

---

## v5.9.0 (2026-03-22)

### 新功能
- Hybrid A/B Workflow 混合分流工作流

---

## v5.8.0 (2026-03-20)

### 新功能
- CrewAI 整合 (AgentPersona, ToolRegistry - 8 種工具)
- Trend Optimization: 強化 Guardrails 安全模組

---

## v5.6.0 (2026-03-21)

### 新功能
- Three-Phase Executor
- Fault Tolerant (Retry + Circuit Breaker + Fallback + Output Validator)
- Smart Orchestrator
- AutoOptimizer

---

## v4.5.0 - v5.5.0

### 新功能
- 15 個 Extensions 整合
- PM Mode
- Real Data Connectors
- CLI Interface
- Agent Evaluation Framework

---

*詳細版本歷史請參考 [README.md](README.md)*
