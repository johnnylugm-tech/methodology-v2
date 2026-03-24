# methodology-v2 Enforcement Handbook

> v5.37.0 - 新團隊完全上手指南

---

## 🚨 開始之前

新團隊請先完成 [CHECKLIST.md](../CHECKLIST.md)（前置檢查清單）！

---

## 📋 什麼是 Enforcement？

Enforcement = **強制執行**。讓 AI Agent 無法「走捷徑」，必須按照規範流程執行。

### 三層保護

| 層次 | 元件 | 職責 |
|------|------|------|
| **Layer 1** | Policy Engine | 流程政策、BLOCK 等級 |
| **Layer 2** | Execution Registry | 執行記錄、不可偽造 |
| **Layer 3** | Constitution as Code | 業務規則、違反阻擋 |

---

## 🛡️ 7 大 Enforcement 政策

| # | Policy ID | 說明 | 等級 |
|---|-----------|------|------|
| 1 | commit-has-task-id | Commit 必須有 `[TASK-XXX]` | BLOCK |
| 2 | quality-gate-90 | Quality Gate >= 90 | BLOCK |
| 3 | no-bypass-commands | 禁止使用 `--no-verify` | BLOCK |
| 4 | test-coverage-80 | 測試覆蓋率 >= 80% | BLOCK |
| 5 | security-score-95 | 安全分數 >= 95 | BLOCK |
| 6 | aspice-docs-required | ASPICE 文檔必須存在 | BLOCK |
| 7 | phase-artifact-reference | Phase 必須引用上階段產物 | BLOCK |

---

## 📄 ASPICE 文檔檢查

### 為什麼要檢查？

確保每個 Phase 都有對應的文檔，符合工程標準。

### 檢查的 Phase

| Phase | ASPICE 參考 | 必需文檔 |
|-------|-------------|----------|
| Phase 1: 需求分析 | SWE.1, SWE.2 | SRS_TEMPLATE.md |
| Phase 2: 架構設計 | SWE.5 | SAD_TEMPLATE.md |
| Phase 3: 實作與整合 | SWE.6 | 實作檔案 |
| Phase 4: 測試 | SWE.7 | TEST_PLAN_TEMPLATE.md |
| Phase 5: 驗證與交付 | SWE.4, SUP.8 | RELEASE_NOTES |
| Phase 6: 品質報告 | SUP.9 | QUALITY_REPORT_TEMPLATE.md |
| Phase 7: 風險管理 | MAN.5 | RISK_ASSESSMENT_TEMPLATE.md |
| Phase 8: 配置管理 | SUP.8 | CHANGELOG.md |

### 執行檢查

```bash
python3 quality_gate/doc_checker.py
```

**結果**：100% 合規才算通過

---

## 🔄 Phase 產物傳遞

### 為什麼要檢查？

確保每個 Phase 的 Agent 引用上一個 Phase 的產物，避免「從零開始」的錯誤。

### Phase 依賴鏈

```
1-constitution (CONSTITUTION.md, constitution/)
        ↓
2-specify (requirements.md, SPEC.md, 02-specify/)
        ↓
3-plan (architecture.md, roadmap.md, 03-plan/)
        ↓
4-implement (src/, 04-implement/)
        ↓
5-verify (gates.md, test-results.md, 05-verify/)
        ↓
6-release (CHANGELOG.md, RELEASE_NOTES*)
```

### 執行檢查

```bash
python3 quality_gate/phase_artifact_enforcer.py
```

**結果**：所有 Phase 依賴滿足才算通過

---

## ⚙️ CLI 命令

### 安裝 Enforcement

```bash
# 安裝 Git Hook
python3 cli.py enforcement install

# 安裝 Agent-Proof Hook（更嚴格）
python3 cli.py agent-proof-hook install
```

### 執行檢查

```bash
# 執行所有檢查
python3 cli.py enforcement run

# 查看狀態
python3 cli.py enforcement status

# ASPICE 文檔檢查
python3 quality_gate/doc_checker.py

# Phase 產物檢查
python3 quality_gate/phase_artifact_enforcer.py
```

### 調整配置

```bash
# 查看當前配置
python3 cli.py enforcement config

# 修改閾值
# 編輯 enforcement_config.default.json
```

---

## 🎯 新團隊快速開始

### Step 1: 安裝並初始化

```bash
git clone https://github.com/johnnylugm-tech/methodology-v2.git
cd methodology-v2
python3 cli.py init
```

### Step 2: 安裝 Hook

```bash
python3 cli.py enforcement install
python3 cli.py agent-proof-hook install
```

### Step 3: 確認檢查通過

```bash
# 文檔檢查
python3 quality_gate/doc_checker.py

# Phase 產物檢查
python3 quality_gate/phase_artifact_enforcer.py

# 全部檢查
python3 cli.py enforcement run
```

### Step 4: 開始開發

現在你可以開始開發了！每個 commit 都會自動檢查：

- ✅ Commit message 格式
- ✅ Quality Gate 分數
- ✅ 測試覆蓋率
- ✅ 安全分數
- ✅ ASPICE 文檔
- ✅ Phase 產物引用

---

## 📊 閾值配置

| 維度 | 預設值 | 可調整範圍 |
|------|--------|-----------|
| Quality Gate | >= 90 | 70-100 |
| Security | >= 95 | 80-100 |
| Coverage | >= 80 | 60-100 |

調整方式：編輯 `enforcement_config.default.json`

---

## 🔧 常見問題

### Q: 檢查失敗怎麼辦？

A: 根據錯誤訊息修復：
- 文檔缺失 → 建立對應文檔
- Phase 引用缺失 → 在 prompt 中引用上階段產物
- 品質不足 → 優化程式碼

### Q: 可以繞過檢查嗎？

A: **不行**。所有 BYPASS 都被禁止（`no-bypass-commands` 政策）。

### Q: 可以調整閾值嗎？

A: 可以。編輯 `enforcement_config.default.json`，但建議保持預設值以確保品質。

---

## 🔄 Quality Watch 整合

Enforcement Framework 現在與 Quality Watch 無縫整合：

| 觸發方式 | 檢查範圍 | 速度 |
|----------|----------|------|
| 檔案存檔 | 當前檔案 | 即時 |
| git commit | 所有變更 | 秒級 |
| 定期報告 | 完整檢查 | 分鐘級 |

### 啟動流程

```bash
python3 cli.py init "my-project"
# → 建立 .methodology/
# → 啟動 quality_watch daemon
# → 持續監控直到 finish
```

### 與 Git Hooks 的區別

| 項目 | Git Hooks | Quality Watch |
|------|-----------|---------------|
| 觸發時機 | commit 時 | 每次存檔 |
| 阻擋點 | commit | 存檔 |
| 通知方式 | 拒絕 commit | 日誌 + 警告 |
| 適用場景 | 代碼進入 repository | 代碼正在編寫 |

**建議**：兩者同時啟用，形成完整防護網。

---

## 🔧 Quality Watch CLI

```bash
# 狀態
python3 quality_watch.py status

# 日誌
python3 quality_watch.py log

# 停止
python3 quality_watch.py stop
```

詳細說明：[QUALITY_WATCH_GUIDE.md](./QUALITY_WATCH_GUIDE.md)

---

## 📚 相關文件

- [CHECKLIST.md](../CHECKLIST.md) - 前置檢查清單
- [GETTING_STARTED.md](GETTING_STARTED.md) - 快速開始
- [ENFORCEMENT_GETTING_STARTED.md](ENFORCEMENT_GETTING_STARTED.md) - Enforcement 詳細說明
- [WORKFLOW.md](WORKFLOW.md) - 完整工作流程
- [ASPICE_MAPPING.md](ASPICE_MAPPING.md) - ASPICE 對照表
- [docs/templates/](docs/templates/) - 文檔模板

---

## 🚀 下一步

1. 完成 [CHECKLIST.md](../CHECKLIST.md)
2. 執行 `python3 cli.py enforcement run` 確認通過
3. 開始你的第一個專案！

---

*最後更新：2026-03-24 (v5.35.0)*