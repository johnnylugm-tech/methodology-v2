# Quality Watch - 持續品質監控指南

> v5.37.0 - 讓壞程式碼無處遁形

---

## 🎯 什麼是 Quality Watch？

Quality Watch 是 methodology-v2 的**持續品質監控 daemon**，在開發過程中即時檢查品質問題。

### 核心價值

| 問題 | 沒有 Quality Watch | 有 Quality Watch |
|------|-------------------|------------------|
| 壞程式碼 | 寫完後才發現 | 寫入當下就發現 |
| ASPICE 文檔 | 最後補 | 開發中就檢查 |
| 品質閘道 | PR 時才檢查 | 每次存檔都檢查 |
| 修復成本 | 高（事後補救）| 低（即時修正）|

---

## 🚀 快速開始

### Step 1: 啟動專案

```bash
cd my-project
python3 cli.py init "my-project"
```

**發生了什麼？**

```
methodology init
       ↓
1. 建立 .methodology/ 目錄
2. 複製 Enforcement 設定
3. 啟動 quality_watch daemon
       ↓
✅ Ready to develop!
```

### Step 2: 開發（Quality Watch 在背景監控）

```bash
# 開始寫程式
vim src/main.py

# 每次存檔...
# Quality Watch: 觸發 quality-gate check
# 如果有 CRITICAL 問題 → 立即顯示警告
```

### Step 3: 結束專案

```bash
python3 cli.py finish
```

**發生了什麼？**

```
methodology finish
       ↓
1. Quality Watch daemon 停止
2. 產出最終品質報告
3. 清理临时檔案
       ↓
✅ Project finished!
```

---

## 📋 Quality Watch 的三層防護

### Layer 1: 檔案監控（即時）

```
Agent 寫入檔案
       ↓
Watchdog 偵測到變更
       ↓
Quality Gate 檢查
       ↓
結果寫入 quality_log.json
```

### Layer 2: CLI 命令（隨選）

```bash
# 檢查狀態
python3 quality_watch.py status

# 單次檢查
python3 quality_watch.py watch

# 查看日誌
cat .methodology/quality_log.json
```

### Layer 3: 定期報告（可選）

```bash
# 啟動時鐘報告
python3 quality_watch.py start --report-interval 60
```

---

## 🔧 命令參考

### 啟動和停止

| 命令 | 說明 |
|------|------|
| `python3 cli.py init "name"` | 初始化並啟動 Quality Watch |
| `python3 cli.py finish` | 結束並停止 Quality Watch |
| `python3 quality_watch.py start` | 單獨啟動 daemon |
| `python3 quality_watch.py stop` | 停止 daemon |

### 監控和報告

| 命令 | 說明 |
|------|------|
| `python3 quality_watch.py status` | 查看 daemon 狀態 |
| `python3 quality_watch.py watch` | 執行一次檢查 |
| `python3 quality_watch.py log` | 查看品質日誌 |

### Quality Gate

| 命令 | 說明 |
|------|------|
| `python3 cli.py quality-gate check` | 執行所有檢查 |
| `python3 cli.py quality-gate doc` | 只檢查文檔 |
| `python3 cli.py quality-gate phase` | 只檢查 Phase 產物 |
| `python3 cli.py quality-gate aspice` | ASPICE 合規檢查 |

---

## 📊 檢查項目

### ASPICE 文檔檢查

| Phase | 需要文檔 | 檢查時機 |
|-------|----------|-----------|
| Phase 1 | SRS.md | 每次存檔 |
| Phase 2 | SAD.md | 每次存檔 |
| Phase 4 | TEST_PLAN.md | 每次存檔 |
| Phase 6 | QUALITY_REPORT.md | 每次存檔 |
| Phase 7 | RISK_ASSESSMENT.md | 每次存檔 |

### Policy Engine 檢查

| Policy ID | 說明 | 等級 |
|-----------|------|------|
| commit-has-task-id | Commit 必須有 TASK ID | BLOCK |
| quality-gate-90 | Quality Gate >= 90 | BLOCK |
| no-bypass-commands | 禁止使用 --no-verify | BLOCK |
| test-coverage-80 | 測試覆蓋率 >= 80% | BLOCK |
| security-score-95 | 安全分數 >= 95 | BLOCK |
| aspice-docs-required | ASPICE 文檔必須存在 | BLOCK |
| phase-artifact-reference | Phase 必須引用上階段產物 | BLOCK |

---

## 🎨 日誌格式

```json
{
  "timestamp": "2026-03-24T19:57:00",
  "passed": true,
  "file": "/path/to/file.py",
  "severity": "INFO"
}
```

或

```json
{
  "timestamp": "2026-03-24T19:57:00",
  "passed": false,
  "file": "/path/to/file.py",
  "severity": "CRITICAL",
  "error": "Missing SRS.md"
}
```

---

## ⚙️ 進階設定

### 自定義檢查間隔

```bash
python3 quality_watch.py start --interval 30
```

### 跳過特定檔案

在 `.methodology/config.json` 中：

```json
{
  "watch": {
    "exclude_patterns": [
      "*.test.py",
      "**/__pycache__/**",
      "**/node_modules/**"
    ]
  }
}
```

### 關閉即時監控（只用 CLI）

```bash
python3 quality_watch.py watch  # 只在需要時檢查
```

---

## 🤔 常見問題

### Q: Quality Watch 佔用多少資源？

A: 極少。Watchdog 使用作業系統的 inotify/FSEvents，幾乎不佔 CPU。

### Q: 可以同時監控多個專案嗎？

A: 可以。每個專案有自己的 PID 檔案。

### Q: daemon 當機了怎麼辦？

A: `methodology init` 會自動重啟。

### Q: 可以透過程式碼即時通知嗎？

A: 計畫中。將來會支援 Slack/Discord 通知。

---

## 📚 相關文件

| 文件 | 內容 |
|------|------|
| [ENFORCEMENT_HANDBOOK.md](./ENFORCEMENT_HANDBOOK.md) | Enforcement 完整手冊 |
| [ASPICE_MAPPING.md](./ASPICE_MAPPING.md) | ASPICE 對照表 |
| [CHECKLIST.md](../CHECKLIST.md) | 開始前檢查清單 |
| [GETTING_STARTED.md](./GETTING_STARTED.md) | 新手上路 |

---

*最後更新：2026-03-24*
