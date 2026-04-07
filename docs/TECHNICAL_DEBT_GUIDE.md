# Technical Debt - 技術債務指南

> v5.44 - 追蹤和管理技術債務

---

## 🎯 什麼是 Technical Debt？

Technical Debt 是「現在選擇捷徑，未來必須付出代價」的代碼決策。

### 常見範例

| 債務 | 嚴重性 | 描述 |
|------|--------|------|
| 使用 eval() | 🔴 HIGH | 安全風險 |
| 硬編碼密碼 | 🔴 HIGH | 安全風險 |
| 缺少測試 | 🟠 HIGH | 維護困難 |
| 重複代碼 | 🟡 MEDIUM | 難以維護 |
| 無文檔 | 🔵 LOW | 理解困難 |

---

## 🚀 快速開始

```bash
# 添加技術債務
python3 cli.py debt add "使用 eval()" --severity high --ticket TASK-123

# 列出所有債務
python3 cli.py debt list

# 解決債務
python3 cli.py debt resolve debt-xxxxx

# 接受債務（決定不修復）
python3 cli.py debt accept debt-xxxxx "短期內沒有安全風險"

# 生成報告
python3 cli.py debt report
```

---

## 📁 債務存放位置

```
.methodology/debts/
    └── debt_registry.json
```

---

## 📚 相關文件

| 文件 | 內容 |
|------|------|
| [CODE_METRICS_GUIDE.md](./CODE_METRICS_GUIDE.md) | 代碼品質指南 |
| [ADR_GUIDE.md](./ADR_GUIDE.md) | ADR 指南 |

---

*最後更新：2026-03-24*
