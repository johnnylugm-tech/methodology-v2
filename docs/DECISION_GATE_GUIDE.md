# Decision Gate - 決策分類閘道指南

> v5.42 - 讓每一個技術決策都有踪跡可循

---

## 🎯 什麼是 Decision Gate？

Decision Gate 是 methodology-v2 的**決策分類閘道**，確保所有技術決策都有：
- 明確的風險等級
- 清楚的確認流程
- 完整的決策紀錄

---

## 🔴🟡🔵 三級風險分類

| 等級 | 決策類型 | 處理方式 |
|------|----------|----------|
| 🔴 HIGH | 架構、API、核心演算法 | 必須照 spec，需 user 確認 |
| 🟡 MEDIUM | 預設值、工具選型 | 列出選項 + 建議 |
| 🔵 LOW | 目錄結構、檔案命名 | 可自主決定 |

---

## 🚀 快速開始

### Step 1: 分類一個決策

```bash
python3 cli.py decision classify chunk_size "Embedding chunk size"
```

**輸出範例：**
```
✅ Decision classified:
   ID: D-A1B2C3
   Risk: 🟡 MEDIUM
   Type: config_default
   ⚠️  Requires user confirmation!
   Options: 512, 800, 1024
   Recommendation: 800
```

### Step 2: 列出所有決策

```bash
python3 cli.py decision list
```

### Step 3: 確認 HIGH 風險決策

```bash
python3 cli.py decision confirm D-A1B2C3 "800"
```

---

## 📊 決策風險矩陣

| 風險級別 | 決策類型 | 處理方式 |
| ---- | ------------- | -------- |
| 🔴 高 | 演算法、API 選擇、架構 | 必須照 spec |
| 🟡 中 | 預設值、工具選型 | 列出選項建議 |
| ⚪ 低 | 目錄結構、檔案命名 | 可自主決定 |

---

## 📁 決策紀錄

所有決策都記錄在：
```
.methodology/decisions/
    └── decision_log.json
```

---

## 🤔 常見問題

### Q: 為什麼要分類決策？

A: 避免在開發過程中「隨機」決定重大事項，導致後期重構成本高。

### Q: LOW 風險決策需要記錄嗎？

A: 不需要，Decision Gate 自動分類，只記錄 MEDIUM 和 HIGH。

### Q: 如果 spec 沒有規定的決策？

A: 視為 MEDIUM 或 HIGH 風險，需要與 user 確認。

---

## 📚 相關文件

| 文件 | 內容 |
|------|------|
| [WORKFLOW.md](./WORKFLOW.md) | 完整工作流程 |
| [QUALITY_WATCH_GUIDE.md](./QUALITY_WATCH_GUIDE.md) | 持續監控 |

---

*最後更新：2026-03-24*