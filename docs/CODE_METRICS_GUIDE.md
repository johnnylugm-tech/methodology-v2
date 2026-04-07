# Code Metrics - 代碼品質指標指南

> v5.44 - 追蹤代碼複雜度與耦合度

---

## 🎯 什麼是 Code Metrics？

Code Metrics 追蹤代碼的：
- **Cyclomatic Complexity** - 函數複雜度
- **Coupling** - 模組間耦合度
- **Instability** - 不穩定性指標

---

## 🚀 快速開始

```bash
# 生成代碼品質報告
python3 cli.py metrics report

# 查看歷史報告
python3 cli.py metrics history
```

---

## 📊 指標說明

### Cyclomatic Complexity

| 等級 | 複雜度 | 意義 |
|------|--------|------|
| ✅ 良好 | 1-10 | 簡單函數 |
| ⚠️ 中等 | 11-20 | 需要重構 |
| 🔴 複雜 | 21-30 | 高風險 |
| ❌ 極高 | > 30 | 必須重構 |

### Coupling Metrics

| 指標 | 說明 |
|------|------|
| Afferent | 被其他模組導入的數量 |
| Efferent | 導入其他模組的數量 |
| Instability | 不穩定性 (0-1)，越接近1越不穩定 |

---

## 📚 相關文件

| 文件 | 內容 |
|------|------|
| [TECHNICAL_DEBT_GUIDE.md](./TECHNICAL_DEBT_GUIDE.md) | 技術債務指南 |
| [ADR_GUIDE.md](./ADR_GUIDE.md) | ADR 指南 |

---

*最後更新：2026-03-24*
