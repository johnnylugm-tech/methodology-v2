# ADR - Architecture Decision Records

> v5.44 - 正式記錄架構決策

---

## 🎯 什麼是 ADR？

ADR 是正式的架構決策記錄，包含：
- 決策的背景
- 決策的內容
- 決策的後果
- 被拒絕的替代方案

---

## 🚀 快速開始

```bash
# 建立 ADR
python3 cli.py adr create "使用 PostgreSQL 作為主要資料庫"

# 列出所有 ADR
python3 cli.py adr list

# 查看 ADR
python3 cli.py adr get 001

# 更新狀態
python3 cli.py adr status 001 accepted

# 導出為 Markdown
python3 cli.py adr export

# 生成報告
python3 cli.py adr report
```

---

## 📄 ADR 格式

每個 ADR 包含：

| 欄位 | 說明 |
|------|------|
| Title | 決策標題 |
| Status | proposed/accepted/rejected/superseded |
| Context | 決策背景 |
| Decision | 決策內容 |
| Consequences | 決策後果 |
| Alternatives | 被拒絕的替代方案 |

---

## 📁 ADR 存放位置

```
.methodology/decisions/
    ├── adr_index.json
    └── adr-001.json
```

---

## 📚 相關文件

| 文件 | 內容 |
|------|------|
| [CODE_METRICS_GUIDE.md](./CODE_METRICS_GUIDE.md) | 代碼品質指南 |
| [TECHNICAL_DEBT_GUIDE.md](./TECHNICAL_DEBT_GUIDE.md) | 技術債務指南 |

---

*最後更新：2026-03-24*
